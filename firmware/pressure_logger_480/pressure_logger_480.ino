/*
 * SmartBall — Pressure Logger, 480 Hz batched  (XIAO nRF52840)  [2026-08-05]
 *
 * Same hardware and BLE identity as pressure_logger.ino, but decouples the
 * SAMPLE rate from the NOTIFICATION rate by sending several samples per packet.
 *
 * WHY: the pitch peak is broad (~100 ms) and 120 Hz resolved it fine. The
 * RELEASE is not — the whole transition is ~20-30 ms, which is only 3-4 samples
 * at 120 Hz, and force-at-release is the measurement that matters. At 480 Hz the
 * same transition gets 12-16 samples, and the pointer-vs-middle release order
 * (they differ by roughly 5-15 ms) becomes resolvable per pitch instead of only
 * in aggregate.
 *
 * The BLE notification rate is UNCHANGED at 120/s — well under the measured
 * ~151 Hz ceiling. Only the packet gets bigger.
 *
 *   Local name   : "SmartBall"
 *   Service UUID : 00001234-0000-1000-8000-00805f9b34fb
 *   Char UUID    : 00001235-0000-1000-8000-00805f9b34fb  (Read | Notify)
 *   Packet (36B) : uint32 t_US of the FIRST sample in the batch (MICROseconds,
 *                  not ms — the 120 Hz sketch sends ms; ble_logger.py keys off
 *                  the packet size), then 4 x {4x uint16 raw ADC}, little-endian.
 *                  Sample k in the batch is at t_us + k*(1e6/SAMPLE_HZ).
 *                  Channel order within a sample = S1, S2, S3, S4.
 *
 * WHY MICROSECONDS: stamping the batch with millis() quantises an 8.33 ms batch
 * to 1 ms, and reconstructed sample times then overlap across batch boundaries —
 * measured at 2.9% of samples going backwards by up to 4.25 ms, which is the
 * same size as the pointer-vs-middle release gap being measured. micros() wraps
 * every ~71.6 min; the logger detects the wrap and accumulates.
 *
 * *** IF THIS DOESN'T STREAM: set SAMPLES_PER_PACKET to 2. ***
 * 36 bytes needs a negotiated ATT MTU above the 23-byte default. Most centrals
 * (Windows/Bleak included) negotiate up automatically, but if notifications
 * never arrive, 2 samples/packet = 20 bytes, which fits the default MTU with no
 * negotiation at all, and still gives 240 Hz — double the old resolution.
 * ble_logger.py reads the packet length and adapts either way.
 *
 * Physical wiring (v2 ferrule harness):
 *   S1 -> A0 (black),  S2 -> A1 (white),  S3 -> A2 (green),  S4 -> A3 (purple)
 * calFactors (analysis/calibration/calfactors_v3.csv):
 *   S1=BK 119, S2=RM 129, S3=KA 148, S4=CG 157.
 */

#include <ArduinoBLE.h>

// Pins in packet-channel order: S1, S2, S3, S4
const int PIN_ORDER[4] = {A0, A1, A2, A3};

const uint32_t SAMPLE_HZ = 480;
const uint8_t  SAMPLES_PER_PACKET = 4;      // 4 -> 36 B/pkt, 120 notif/s
                                            // 2 -> 20 B/pkt, fits default MTU
const uint32_t SAMPLE_INTERVAL_US = 1000000UL / SAMPLE_HZ;   // 2083 us
const uint8_t  PACKET_LEN = 4 + SAMPLES_PER_PACKET * 8;      // 36

BLEService ballService("00001234-0000-1000-8000-00805f9b34fb");
BLECharacteristic pressureChar("00001235-0000-1000-8000-00805f9b34fb",
                               BLERead | BLENotify, PACKET_LEN);
// Battery telemetry: uint16 millivolts, notified every 2 s. The CHG LED is
// buried once the ball is potted, so this is how charge state is verified
// through the sealed ball.
BLECharacteristic batteryChar("00001236-0000-1000-8000-00805f9b34fb",
                              BLERead | BLENotify, 2);

uint8_t  packet[4 + 8 * 8];      // headroom for up to 8 samples/packet
uint8_t  sampleCount = 0;
uint32_t batchTus = 0;           // micros() at the batch's first sample
uint32_t lastSampleUs = 0;
uint32_t lastBattMs = 0;

uint16_t readBatteryMv() {
  // XIAO nRF52840: P0.31 reads VBAT through a 1M/510k divider that is only
  // connected while P0.14 is driven LOW. Divider tolerance ~±3% — read the
  // TREND (rising vs sagging), not the third digit.
  uint32_t adc = analogRead(P0_31);
  return (uint16_t)((unsigned long long)adc * 3300ULL * 1510ULL
                    / (4095ULL * 510ULL));
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);       // 0..4095
  pinMode(P0_14, OUTPUT);         // VBAT_ENABLE: LOW connects the divider
  digitalWrite(P0_14, LOW);

  if (!BLE.begin()) {
    while (1) { delay(1000); }
  }
  // Units of 1.25 ms: 6 = 7.5 ms, 12 = 15 ms. Without this the central settles
  // at ~20+ ms and only ~1 notification lands per connection event.
  BLE.setConnectionInterval(6, 12);
  BLE.setLocalName("SmartBall");
  BLE.setDeviceName("SmartBall");
  BLE.setAdvertisedService(ballService);
  ballService.addCharacteristic(pressureChar);
  ballService.addCharacteristic(batteryChar);
  BLE.addService(ballService);
  BLE.advertise();
  Serial.print("SmartBall advertising ("); Serial.print(SAMPLE_HZ);
  Serial.print(" Hz, "); Serial.print(SAMPLES_PER_PACKET);
  Serial.print(" samples/pkt, "); Serial.print(PACKET_LEN);
  Serial.println(" B)");
}

void loop() {
  BLEDevice central = BLE.central();
  if (!central) return;

  Serial.print("Connected: ");
  Serial.println(central.address());
  lastSampleUs = micros();
  sampleCount = 0;

  while (central.connected()) {
    uint32_t nowUs = micros();
    if ((uint32_t)(nowUs - lastSampleUs) < SAMPLE_INTERVAL_US) continue;
    lastSampleUs += SAMPLE_INTERVAL_US;   // fixed-rate, no drift accumulation

    if (sampleCount == 0) batchTus = nowUs;      // stamp the first of the batch

    uint8_t *slot = packet + 4 + sampleCount * 8;
    for (int c = 0; c < 4; c++) {
      uint16_t adc = (uint16_t)analogRead(PIN_ORDER[c]);
      memcpy(slot + 2 * c, &adc, 2);
    }
    sampleCount++;

    if (sampleCount >= SAMPLES_PER_PACKET) {
      memcpy(packet, &batchTus, 4);
      pressureChar.writeValue(packet, PACKET_LEN);
      sampleCount = 0;
    }

    if (millis() - lastBattMs >= 2000) {
      lastBattMs = millis();
      uint16_t mv = readBatteryMv();
      batteryChar.writeValue((uint8_t *)&mv, 2);
    }
  }

  Serial.println("Disconnected — advertising again");
  sampleCount = 0;
  BLE.advertise();
}
