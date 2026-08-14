/*
 * SmartBall BLE Firmware — Seeed XIAO nRF52840
 * Streams 10 sensor channels over BLE:
 *   4x FlexiForce pressure (A0-A3)
 *   3x H3LIS331DL accelerometer (I2C 0x18)
 *   3x LIS3MDL magnetometer (I2C 0x1C)
 *
 * Connect with nRF Connect app to see live data.
 */

#include <ArduinoBLE.h>
#include <Wire.h>

// I2C addresses
#define H3LIS_ADDR 0x18
#define LIS3MDL_ADDR 0x1C

// BLE Service + Characteristics
BLEService ballService("00001234-0000-1000-8000-00805f9b34fb");

// Pressure: 4x int16 = 8 bytes
BLECharacteristic pressureChar("00001235-0000-1000-8000-00805f9b34fb",
                                BLERead | BLENotify, 8);

// Accelerometer: 3x int16 = 6 bytes
BLECharacteristic accelChar("00001236-0000-1000-8000-00805f9b34fb",
                             BLERead | BLENotify, 6);

// Magnetometer: 3x int16 = 6 bytes
BLECharacteristic magChar("00001237-0000-1000-8000-00805f9b34fb",
                           BLERead | BLENotify, 6);

bool deviceConnected = false;
unsigned long lastSend = 0;
const int SEND_INTERVAL = 20; // 50 Hz over BLE (fast enough for live view)

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("SmartBall BLE starting...");

  analogReadResolution(12);
  Wire.begin();

  // Init H3LIS331DL
  writeReg(H3LIS_ADDR, 0x20, 0x3F); // Normal mode, 1000Hz, XYZ on
  writeReg(H3LIS_ADDR, 0x23, 0x30); // ±400g

  // Init LIS3MDL
  writeReg(LIS3MDL_ADDR, 0x20, 0x7C); // Ultra-high perf, 80Hz
  writeReg(LIS3MDL_ADDR, 0x22, 0x00); // Continuous mode

  // Verify sensors
  Serial.print("H3LIS WHO_AM_I: 0x");
  Serial.println(readReg(H3LIS_ADDR, 0x0F), HEX); // should be 0x32
  Serial.print("LIS3MDL WHO_AM_I: 0x");
  Serial.println(readReg(LIS3MDL_ADDR, 0x0F), HEX); // should be 0x3D

  // Init BLE
  if (!BLE.begin()) {
    Serial.println("BLE failed!");
    while (1);
  }

  BLE.setLocalName("SmartBall");
  BLE.setAdvertisedService(ballService);
  ballService.addCharacteristic(pressureChar);
  ballService.addCharacteristic(accelChar);
  ballService.addCharacteristic(magChar);
  BLE.addService(ballService);
  BLE.advertise();

  Serial.println("BLE advertising as 'SmartBall'");
  Serial.println("Open nRF Connect and connect to SmartBall");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    if (!deviceConnected) {
      Serial.print("Connected: ");
      Serial.println(central.address());
      deviceConnected = true;
    }

    while (central.connected()) {
      unsigned long now = millis();
      if (now - lastSend >= SEND_INTERVAL) {
        lastSend = now;
        sendSensorData();
      }
    }

    Serial.println("Disconnected.");
    deviceConnected = false;
  }

  // Also print to serial when not connected (for debugging)
  unsigned long now = millis();
  if (!deviceConnected && now - lastSend >= 100) {
    lastSend = now;
    printSensorData();
  }
}

void sendSensorData() {
  // Read pressure sensors
  int16_t pressure[4];
  pressure[0] = analogRead(A0);
  pressure[1] = analogRead(A1);
  pressure[2] = analogRead(A2);
  pressure[3] = analogRead(A3);

  // Read H3LIS331DL
  int16_t accel[3];
  readMulti(H3LIS_ADDR, 0x28 | 0x80, (uint8_t*)accel, 6);

  // Read LIS3MDL
  int16_t mag[3];
  readMulti(LIS3MDL_ADDR, 0x28 | 0x80, (uint8_t*)mag, 6);

  // Send over BLE
  pressureChar.writeValue((uint8_t*)pressure, 8);
  accelChar.writeValue((uint8_t*)accel, 6);
  magChar.writeValue((uint8_t*)mag, 6);
}

void printSensorData() {
  int16_t pressure[4];
  pressure[0] = analogRead(A0);
  pressure[1] = analogRead(A1);
  pressure[2] = analogRead(A2);
  pressure[3] = analogRead(A3);

  int16_t accel[3];
  readMulti(H3LIS_ADDR, 0x28 | 0x80, (uint8_t*)accel, 6);

  int16_t mag[3];
  readMulti(LIS3MDL_ADDR, 0x28 | 0x80, (uint8_t*)mag, 6);

  Serial.print("P:"); Serial.print(pressure[0]); Serial.print(",");
  Serial.print(pressure[1]); Serial.print(",");
  Serial.print(pressure[2]); Serial.print(",");
  Serial.print(pressure[3]);
  Serial.print(" A:"); Serial.print(accel[0]); Serial.print(",");
  Serial.print(accel[1]); Serial.print(",");
  Serial.print(accel[2]);
  Serial.print(" M:"); Serial.print(mag[0]); Serial.print(",");
  Serial.print(mag[1]); Serial.print(",");
  Serial.println(mag[2]);
}

// I2C helpers
void writeReg(uint8_t addr, uint8_t reg, uint8_t val) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

uint8_t readReg(uint8_t addr, uint8_t reg) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(addr, (uint8_t)1);
  return Wire.read();
}

void readMulti(uint8_t addr, uint8_t reg, uint8_t* buf, uint8_t len) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(addr, len);
  for (uint8_t i = 0; i < len; i++) {
    buf[i] = Wire.read();
  }
}
