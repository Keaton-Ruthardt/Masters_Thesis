/*
 * SmartBall Full Firmware — Seeed XIAO nRF52840
 *
 * Features:
 *   - 4x FlexiForce pressure sensors (A0-A3) with Newton calibration
 *   - H3LIS331DL accelerometer (velocity via integration)
 *   - LIS3MDL magnetometer (spin rate via DFT)
 *   - Pitch detection (accel threshold → sample → pressure dropout = release)
 *   - On-board DFT spin rate computation
 *   - On-board velocity estimation
 *   - BLE 5 streaming of raw data + computed metrics
 *
 * State machine:
 *   IDLE     → low power, waiting for motion
 *   SAMPLING → high-rate capture during pitch event
 *   COMPUTE  → DFT + velocity after release detected
 *   TRANSMIT → send results over BLE
 */

#include <ArduinoBLE.h>
#include <Wire.h>
#include <math.h>

// ── Board Target ──
// The custom SmartBall PCB routes signals to different nRF52840 pins than the
// XIAO dev board (verified against SmartBall_PCB.kicad_pcb netlist):
//   Pressure 3/4: P0.04/P0.05 (XIAO A2/A3 are P0.28/P0.29 — unconnected here)
//   I2C bus:      P0.26/P0.27 (XIAO Wire is P0.04/P0.05 — pressure nets here)
// Set to 1 when flashing the custom PCB, 0 for the XIAO breadboard.
#define CUSTOM_BOARD 1

#if CUSTOM_BOARD
#include <mbed.h>
mbed::AnalogIn ain2Raw(P0_4);          // sensor 3 on AIN2
mbed::AnalogIn ain3Raw(P0_5);          // sensor 4 on AIN3
arduino::MbedI2C WireSB(P0_26, P0_27); // custom board I2C bus
#define I2C_BUS WireSB
#else
#define I2C_BUS Wire
#endif

// ── I2C Addresses ──
#define H3LIS_ADDR  0x18
#define LIS3MDL_ADDR 0x1C

// ── Calibration ──
// FlexiForce A201-25 (111N / 25lb range)
// Tekscan: conductance (1/R) is linear with force
// Slope from manufacturer data: ~1.8 µS/N → calFactor = 1/slope in divider units
// Circuit: 3.3V → FlexiForce → ADC → 10kΩ → GND
// ADC conductance = ADC / (4095 - ADC), so:
//   Force(N) = conductance_adc * R_FIXED / (CAL_SLOPE)
// where CAL_SLOPE = 1.8e-6 S/N and R_FIXED = 10000
// Simplifies to: Force(N) = conductance_adc * 10000 / 1.8e-6... but easier:
//   Force(N) = conductance_adc * calFactor
// calFactor = R_FIXED * CAL_SLOPE_INV = derived below
//
// From Tekscan data: at 111N, R=5kΩ → conductance_adc = 10000/5000 = 2.0
// So calFactor = 111N / 2.0 = 55.5 N per unit conductance
// Each sensor varies ±10%, recalibrate with known weight if needed.
float calFactor[4] = {55.5, 55.5, 55.5, 55.5};
const float R_FIXED = 10000.0;

// ── H3LIS331DL scale ──
// ±400g mode: 16-bit signed, full scale = 800g
// Sensitivity: 800g / 65536 = 0.01221 g/LSB
const float ACCEL_SCALE = 0.01221;  // g per LSB
const float G_TO_MS2 = 9.80665;

// ── Sampling ──
const int SAMPLE_RATE = 1000;           // Hz
const int MAX_SAMPLES = 2000;           // 2 seconds max
const float SAMPLE_PERIOD = 1.0 / SAMPLE_RATE;

// ── Pitch Detection Thresholds ──
const float ACCEL_TRIGGER_G = 10.0;     // g's to start sampling (raise if false triggers)
const int RELEASE_COUNT = 20;            // consecutive zero-pressure samples = release
const float PRESSURE_ZERO_THRESH = 10.0; // ADC below this = no contact

// ── Buffers ──
// Stored as raw int16 to save memory
int16_t pressureBuf[MAX_SAMPLES][4];
int16_t accelBuf[MAX_SAMPLES][3];
int16_t magBuf[MAX_SAMPLES][3];
int sampleCount = 0;
int releaseIndex = -1;
int zeroCount = 0;

// ── State Machine ──
enum State { IDLE, SAMPLING, COMPUTE, TRANSMIT };
State state = IDLE;

// ── Computed Metrics ──
float spinRateRPM = 0;
float velocityMPH = 0;
float peakForceN[4] = {0, 0, 0, 0};
float releaseTimeMs = 0;

// ── BLE ──
BLEService ballService("00001234-0000-1000-8000-00805f9b34fb");

// Raw streaming (same as before)
BLECharacteristic pressureChar("00001235-0000-1000-8000-00805f9b34fb",
                                BLERead | BLENotify, 8);
BLECharacteristic accelChar("00001236-0000-1000-8000-00805f9b34fb",
                             BLERead | BLENotify, 6);
BLECharacteristic magChar("00001237-0000-1000-8000-00805f9b34fb",
                           BLERead | BLENotify, 6);

// Computed pitch metrics: spinRPM(f32), velocityMPH(f32), peakForce[4](f32), releaseMs(f32) = 28 bytes
BLECharacteristic metricsChar("00001238-0000-1000-8000-00805f9b34fb",
                               BLERead | BLENotify, 28);

bool bleConnected = false;
unsigned long lastLiveUpdate = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("SmartBall Full Firmware v2.0");

  analogReadResolution(12);
  I2C_BUS.begin();
  I2C_BUS.setClock(400000); // 400kHz I2C for faster reads

  initSensors();
  initBLE();

  Serial.println("Ready. Waiting for pitch...");
  Serial.println("States: IDLE → SAMPLING → COMPUTE → TRANSMIT → IDLE");
}

void loop() {
  BLE.poll();

  BLEDevice central = BLE.central();
  if (central && central.connected()) {
    bleConnected = true;
  } else {
    bleConnected = false;
  }

  switch (state) {
    case IDLE:
      doIdle();
      break;
    case SAMPLING:
      doSampling();
      break;
    case COMPUTE:
      doCompute();
      break;
    case TRANSMIT:
      doTransmit();
      break;
  }
}

// ════════════════════════════════════════
// STATE: IDLE — wait for motion
// ════════════════════════════════════════
void doIdle() {
  // Stream live data at 10Hz so the dashboard/nRF Connect can verify all channels
  if (millis() - lastLiveUpdate >= 100) {
    lastLiveUpdate = millis();
    sendLiveData();
  }

  // Check for pitch start
  int16_t ax, ay, az;
  readAccel(&ax, &ay, &az);
  float gMag = sqrt((float)ax * ax + (float)ay * ay + (float)az * az) * ACCEL_SCALE;

  if (gMag > ACCEL_TRIGGER_G) {
    Serial.println(">>> PITCH DETECTED — sampling...");
    sampleCount = 0;
    releaseIndex = -1;
    zeroCount = 0;
    state = SAMPLING;
  }
}

// ════════════════════════════════════════
// STATE: SAMPLING — capture all channels at 1kHz
// ════════════════════════════════════════
void doSampling() {
  unsigned long sampleStart = micros();

  // Read pressure
  pressureBuf[sampleCount][0] = readPressureCh(0);
  pressureBuf[sampleCount][1] = readPressureCh(1);
  pressureBuf[sampleCount][2] = readPressureCh(2);
  pressureBuf[sampleCount][3] = readPressureCh(3);

  // Read accelerometer
  readAccel(&accelBuf[sampleCount][0],
            &accelBuf[sampleCount][1],
            &accelBuf[sampleCount][2]);

  // Read magnetometer
  readMag(&magBuf[sampleCount][0],
          &magBuf[sampleCount][1],
          &magBuf[sampleCount][2]);

  // Check for release (all pressure sensors near zero)
  if (releaseIndex < 0) {
    bool allZero = true;
    for (int i = 0; i < 4; i++) {
      if (pressureBuf[sampleCount][i] > PRESSURE_ZERO_THRESH) {
        allZero = false;
        break;
      }
    }

    // Need RELEASE_COUNT consecutive zero readings to confirm release
    if (allZero) {
      zeroCount++;
      if (zeroCount >= RELEASE_COUNT) {
        releaseIndex = sampleCount - RELEASE_COUNT;
        Serial.print(">>> RELEASE at sample ");
        Serial.println(releaseIndex);
      }
    } else {
      zeroCount = 0;
    }
  }

  sampleCount++;

  // Stop conditions: buffer full or 500ms after release
  bool bufferFull = (sampleCount >= MAX_SAMPLES);
  bool postRelease = (releaseIndex > 0 &&
                      (sampleCount - releaseIndex) > 500);

  if (bufferFull || postRelease) {
    Serial.print(">>> SAMPLING DONE — ");
    Serial.print(sampleCount);
    Serial.println(" samples captured");
    state = COMPUTE;
    return;
  }

  // Wait for next sample (maintain 1kHz)
  while ((micros() - sampleStart) < 1000) {
    // spin wait
  }
}

// ════════════════════════════════════════
// STATE: COMPUTE — DFT spin rate + velocity
// ════════════════════════════════════════
void doCompute() {
  Serial.println(">>> COMPUTING metrics...");

  // ── 1. Spin Rate via DFT ──
  spinRateRPM = computeSpinRate();
  Serial.print("  Spin Rate: ");
  Serial.print(spinRateRPM, 0);
  Serial.println(" RPM");

  // ── 2. Velocity via Acceleration Integration ──
  velocityMPH = computeVelocity();
  Serial.print("  Velocity: ");
  Serial.print(velocityMPH, 1);
  Serial.println(" mph");

  // ── 3. Peak Force per Finger ──
  computePeakForces();
  Serial.print("  Peak Force (N): ");
  for (int i = 0; i < 4; i++) {
    Serial.print(peakForceN[i], 1);
    if (i < 3) Serial.print(", ");
  }
  Serial.println();

  // ── 4. Release Time ──
  if (releaseIndex > 0) {
    releaseTimeMs = (float)releaseIndex * 1000.0 / SAMPLE_RATE;
    Serial.print("  Release at: ");
    Serial.print(releaseTimeMs, 0);
    Serial.println(" ms into pitch");
  }

  state = TRANSMIT;
}

// ════════════════════════════════════════
// STATE: TRANSMIT — send over BLE
// ════════════════════════════════════════
void doTransmit() {
  Serial.println(">>> TRANSMITTING...");

  // Pack computed metrics: spin(4) + velocity(4) + peakForce[4](16) + releaseMs(4) = 28 bytes
  uint8_t metricsBuf[28];
  memcpy(&metricsBuf[0],  &spinRateRPM, 4);
  memcpy(&metricsBuf[4],  &velocityMPH, 4);
  memcpy(&metricsBuf[8],  &peakForceN[0], 4);
  memcpy(&metricsBuf[12], &peakForceN[1], 4);
  memcpy(&metricsBuf[16], &peakForceN[2], 4);
  memcpy(&metricsBuf[20], &peakForceN[3], 4);
  memcpy(&metricsBuf[24], &releaseTimeMs, 4);

  if (bleConnected) {
    metricsChar.writeValue(metricsBuf, 28);
    Serial.println("  Sent metrics over BLE.");
  }

  // Print summary
  Serial.println();
  Serial.println("════════════════════════════════");
  Serial.println("  PITCH SUMMARY");
  Serial.println("════════════════════════════════");
  Serial.print("  Spin Rate:  ");
  Serial.print(spinRateRPM, 0);
  Serial.println(" RPM");
  Serial.print("  Velocity:   ");
  Serial.print(velocityMPH, 1);
  Serial.println(" mph");
  Serial.print("  Index:      ");
  Serial.print(peakForceN[0], 1);
  Serial.println(" N");
  Serial.print("  Middle:     ");
  Serial.print(peakForceN[1], 1);
  Serial.println(" N");
  Serial.print("  Thumb:      ");
  Serial.print(peakForceN[2], 1);
  Serial.println(" N");
  Serial.print("  Ring:       ");
  Serial.print(peakForceN[3], 1);
  Serial.println(" N");
  Serial.print("  Release:    ");
  Serial.print(releaseTimeMs, 0);
  Serial.println(" ms");
  Serial.print("  Samples:    ");
  Serial.println(sampleCount);
  Serial.println("════════════════════════════════");
  Serial.println();
  Serial.println("Ready for next pitch...");

  state = IDLE;
}

// ════════════════════════════════════════
// DFT SPIN RATE
// ════════════════════════════════════════
float computeSpinRate() {
  // Use magnetometer data from free flight (after release)
  int startIdx = (releaseIndex > 0) ? releaseIndex : sampleCount / 2;
  int endIdx = sampleCount;
  int N = endIdx - startIdx;

  if (N < 50) return 0; // not enough data

  // Cap at 512 samples for speed
  if (N > 512) N = 512;

  // Frequency resolution = sampleRate / N
  float freqRes = (float)SAMPLE_RATE / N;

  // Search 5-50 Hz (300-3000 RPM)
  int binLow = max(1, (int)(5.0 / freqRes));
  int binHigh = min(N / 2, (int)(50.0 / freqRes));

  float maxMag = 0;
  int peakBin = 0;

  // DFT over magnetometer — try all 3 axes, pick strongest peak
  // First remove DC offset (mean) from each axis to prevent low-bin leakage
  for (int axis = 0; axis < 3; axis++) {
    float mean = 0;
    for (int n = 0; n < N; n++) {
      mean += (float)magBuf[startIdx + n][axis];
    }
    mean /= N;
    // Subtract mean in-place (modifies buffer but we don't need raw values after)
    for (int n = 0; n < N; n++) {
      magBuf[startIdx + n][axis] -= (int16_t)mean;
    }
  }

  for (int axis = 0; axis < 3; axis++) {
    for (int k = binLow; k <= binHigh; k++) {
      float realPart = 0;
      float imagPart = 0;

      for (int n = 0; n < N; n++) {
        float angle = 2.0 * M_PI * k * n / N;
        float sample = (float)magBuf[startIdx + n][axis];
        realPart += sample * cos(angle);
        imagPart -= sample * sin(angle);
      }

      float mag = sqrt(realPart * realPart + imagPart * imagPart);
      if (mag > maxMag) {
        maxMag = mag;
        peakBin = k;
      }
    }
  }

  // Noise floor check — if peak magnitude is too low, no real spin detected
  // Average magnitude across all bins as noise estimate
  float avgMag = 0;
  for (int k = binLow; k <= binHigh; k++) {
    float rp = 0, ip = 0;
    for (int n = 0; n < N; n++) {
      float angle = 2.0 * M_PI * k * n / N;
      rp += (float)magBuf[startIdx + n][0] * cos(angle);
      ip -= (float)magBuf[startIdx + n][0] * sin(angle);
    }
    avgMag += sqrt(rp * rp + ip * ip);
  }
  avgMag /= (binHigh - binLow + 1);

  // Peak must be at least 3x the average to be a real signal
  if (maxMag < avgMag * 3.0) return 0;

  float peakFreq = peakBin * freqRes;

  // Convert to RPM
  return peakFreq * 60.0;
}

// ════════════════════════════════════════
// VELOCITY ESTIMATION
// ════════════════════════════════════════
float computeVelocity() {
  // Integrate acceleration magnitude from start to release
  int endIdx = (releaseIndex > 0) ? releaseIndex : sampleCount;

  // Find throw start (first sustained high acceleration)
  int startIdx = 0;
  for (int i = 0; i < endIdx; i++) {
    float gMag = sqrt((float)accelBuf[i][0] * accelBuf[i][0] +
                       (float)accelBuf[i][1] * accelBuf[i][1] +
                       (float)accelBuf[i][2] * accelBuf[i][2]) * ACCEL_SCALE;
    if (gMag > ACCEL_TRIGGER_G) {
      startIdx = i;
      break;
    }
  }

  // Remove gravity bias (average of first 10 samples before trigger)
  float gravX = 0, gravY = 0, gravZ = 0;
  int biasStart = max(0, startIdx - 50);
  int biasEnd = max(0, startIdx - 5);
  int biasCount = biasEnd - biasStart;

  if (biasCount > 0) {
    for (int i = biasStart; i < biasEnd; i++) {
      gravX += (float)accelBuf[i][0];
      gravY += (float)accelBuf[i][1];
      gravZ += (float)accelBuf[i][2];
    }
    gravX /= biasCount;
    gravY /= biasCount;
    gravZ /= biasCount;
  }

  // Integrate acceleration to get velocity
  float vx = 0, vy = 0, vz = 0;

  for (int i = startIdx; i < endIdx; i++) {
    float ax = ((float)accelBuf[i][0] - gravX) * ACCEL_SCALE * G_TO_MS2;
    float ay = ((float)accelBuf[i][1] - gravY) * ACCEL_SCALE * G_TO_MS2;
    float az = ((float)accelBuf[i][2] - gravZ) * ACCEL_SCALE * G_TO_MS2;

    vx += ax * SAMPLE_PERIOD;
    vy += ay * SAMPLE_PERIOD;
    vz += az * SAMPLE_PERIOD;
  }

  // Speed magnitude in m/s
  float speedMS = sqrt(vx * vx + vy * vy + vz * vz);

  // Convert to mph
  return speedMS * 2.23694;
}

// ════════════════════════════════════════
// PEAK FORCES
// ════════════════════════════════════════
void computePeakForces() {
  for (int sensor = 0; sensor < 4; sensor++) {
    float maxForce = 0;
    for (int i = 0; i < sampleCount; i++) {
      float adc = (float)pressureBuf[i][sensor];
      if (adc > PRESSURE_ZERO_THRESH && adc < 4090) {
        // Convert ADC to conductance ratio: G_ratio = R_fixed / R_sensor
        // From voltage divider: ADC = 4095 * R_fixed / (R_sensor + R_fixed)
        // So: R_sensor = R_fixed * (4095/ADC - 1)
        // G_ratio = 1/R_sensor = ADC / (R_fixed * (4095 - ADC))
        // Force = G_ratio * R_fixed * calFactor = (ADC / (4095 - ADC)) * calFactor
        float conductance = adc / (4095.0 - adc);
        float force = conductance * calFactor[sensor];
        if (force > maxForce) maxForce = force;
      }
    }
    peakForceN[sensor] = maxForce;
  }
}

// ════════════════════════════════════════
// LIVE DATA (sent during IDLE for debugging)
// ════════════════════════════════════════
void sendLiveData() {
  int16_t pressure[4];
  pressure[0] = readPressureCh(0);
  pressure[1] = readPressureCh(1);
  pressure[2] = readPressureCh(2);
  pressure[3] = readPressureCh(3);

  int16_t accel[3], mag[3];
  readAccel(&accel[0], &accel[1], &accel[2]);
  readMag(&mag[0], &mag[1], &mag[2]);

  if (bleConnected) {
    pressureChar.writeValue((uint8_t*)pressure, 8);
    accelChar.writeValue((uint8_t*)accel, 6);
    magChar.writeValue((uint8_t*)mag, 6);
  }

  // Serial output
  Serial.print("P:");
  Serial.print(pressure[0]); Serial.print(",");
  Serial.print(pressure[1]); Serial.print(",");
  Serial.print(pressure[2]); Serial.print(",");
  Serial.print(pressure[3]);
  Serial.print(" A:");
  Serial.print(accel[0]); Serial.print(",");
  Serial.print(accel[1]); Serial.print(",");
  Serial.print(accel[2]);
  Serial.print(" M:");
  Serial.print(mag[0]); Serial.print(",");
  Serial.print(mag[1]); Serial.print(",");
  Serial.println(mag[2]);
}

// ════════════════════════════════════════
// SENSOR I/O
// ════════════════════════════════════════
// Pressure channels 0-3. On the custom board, channels 2/3 live on P0.04/P0.05
// which the XIAO variant doesn't expose as analog pins, so read them via mbed
// AnalogIn (16-bit, scaled down to match the 12-bit analogRead range).
int16_t readPressureCh(int ch) {
  switch (ch) {
    case 0: return analogRead(A0);  // P0.02 = AIN0 on both boards
    case 1: return analogRead(A1);  // P0.03 = AIN1 on both boards
#if CUSTOM_BOARD
    case 2: return ain2Raw.read_u16() >> 4;
    case 3: return ain3Raw.read_u16() >> 4;
#else
    case 2: return analogRead(A2);
    case 3: return analogRead(A3);
#endif
  }
  return 0;
}

void initSensors() {
  // H3LIS331DL
  writeReg(H3LIS_ADDR, 0x20, 0x3F); // Normal mode, 1000Hz, XYZ
  writeReg(H3LIS_ADDR, 0x23, 0x30); // ±400g

  uint8_t whoH = readReg(H3LIS_ADDR, 0x0F);
  Serial.print("H3LIS331DL WHO_AM_I: 0x");
  Serial.print(whoH, HEX);
  Serial.println(whoH == 0x32 ? " OK" : " ERROR");

  // LIS3MDL
  // FAST_ODR + medium-performance = 560Hz output. 80Hz UHP mode capped spin
  // measurement at 2400 RPM (Nyquist); real fastballs exceed that.
  writeReg(LIS3MDL_ADDR, 0x20, 0x22); // Medium perf XY, FAST_ODR → 560Hz
  writeReg(LIS3MDL_ADDR, 0x21, 0x00); // ±4 gauss
  writeReg(LIS3MDL_ADDR, 0x22, 0x00); // Continuous mode
  writeReg(LIS3MDL_ADDR, 0x23, 0x04); // Z-axis medium perf to match XY

  uint8_t whoM = readReg(LIS3MDL_ADDR, 0x0F);
  Serial.print("LIS3MDL WHO_AM_I: 0x");
  Serial.print(whoM, HEX);
  Serial.println(whoM == 0x3D ? " OK" : " ERROR");
}

void initBLE() {
  if (!BLE.begin()) {
    Serial.println("BLE init failed!");
    while (1);
  }

  BLE.setLocalName("SmartBall");
  BLE.setAdvertisedService(ballService);
  ballService.addCharacteristic(pressureChar);
  ballService.addCharacteristic(accelChar);
  ballService.addCharacteristic(magChar);
  ballService.addCharacteristic(metricsChar);
  BLE.addService(ballService);
  BLE.advertise();

  Serial.println("BLE advertising as 'SmartBall'");
}

void readAccel(int16_t* x, int16_t* y, int16_t* z) {
  I2C_BUS.beginTransmission(H3LIS_ADDR);
  I2C_BUS.write(0x28 | 0x80);
  I2C_BUS.endTransmission(false);
  I2C_BUS.requestFrom(H3LIS_ADDR, 6);
  *x = I2C_BUS.read() | (I2C_BUS.read() << 8);
  *y = I2C_BUS.read() | (I2C_BUS.read() << 8);
  *z = I2C_BUS.read() | (I2C_BUS.read() << 8);
}

void readMag(int16_t* x, int16_t* y, int16_t* z) {
  I2C_BUS.beginTransmission(LIS3MDL_ADDR);
  I2C_BUS.write(0x28 | 0x80);
  I2C_BUS.endTransmission(false);
  I2C_BUS.requestFrom(LIS3MDL_ADDR, 6);
  *x = I2C_BUS.read() | (I2C_BUS.read() << 8);
  *y = I2C_BUS.read() | (I2C_BUS.read() << 8);
  *z = I2C_BUS.read() | (I2C_BUS.read() << 8);
}

void writeReg(uint8_t addr, uint8_t reg, uint8_t val) {
  I2C_BUS.beginTransmission(addr);
  I2C_BUS.write(reg);
  I2C_BUS.write(val);
  I2C_BUS.endTransmission();
}

uint8_t readReg(uint8_t addr, uint8_t reg) {
  I2C_BUS.beginTransmission(addr);
  I2C_BUS.write(reg);
  I2C_BUS.endTransmission(false);
  I2C_BUS.requestFrom(addr, (uint8_t)1);
  return I2C_BUS.read();
}
