/*
 * SmartBall — Pressure Logger Firmware (XIAO nRF52840)  [v2 HARNESS 2026-07-31]
 *
 * Samples 4x FlexiForce A301 at 120 Hz and streams each sample over BLE.
 * Pairs with analysis/ble_logger/ble_logger.py:
 *   Local name   : "SmartBall"
 *   Service UUID : 00001234-0000-1000-8000-00805f9b34fb
 *   Char UUID    : 00001235-0000-1000-8000-00805f9b34fb  (Read | Notify)
 *   Packet (12B) : uint32 t_ms + 4x uint16 raw ADC, little-endian,
 *                  channel order = sensors (S1, S2, S3, S4)
 *
 * Sensors sit at FIXED positions on the ball; which finger contacts which
 * sensor depends on the grip and is handled downstream (ble_logger.py asks
 * for the pitch type and tags every row). Physical wiring (v2 ferrule harness):
 *   S1 -> A0 (black),  S2 -> A1 (white),  S3 -> A2 (green),  S4 -> A3 (purple)
 * Adjacent pins are fine here: every connection is a housed female contact, so
 * there is no bare metal or flux on the pad row — that was v1's bridge mechanism.
 * Channel isolation is verified by isolation_test.ino, not by pin spacing.
 * PIN_ORDER below reads pins so the packet stays (S1, S2, S3, S4); per-sensor
 * calFactors (analysis/calibration/calfactors_v3.csv) are
 *   S1=BK 119, S2=RM 129, S3=KA 148, S4=CG 157.
 *
 * Raw ADC is streamed (no on-board force conversion); calibration is applied
 * in post-processing. 120 Hz sits under the measured ~151 Hz BLE notify
 * ceiling for clean, uniform delivery at throwing distance.
 */

#include <ArduinoBLE.h>

// Pins in packet-channel order: S1, S2, S3, S4
const int PIN_ORDER[4] = {A0, A1, A2, A3};

const uint32_t SAMPLE_HZ = 120;
const uint32_t SAMPLE_INTERVAL_US = 1000000UL / SAMPLE_HZ;  // 8333 us

BLEService ballService("00001234-0000-1000-8000-00805f9b34fb");
BLECharacteristic pressureChar("00001235-0000-1000-8000-00805f9b34fb",
                               BLERead | BLENotify, 12);
// Battery telemetry: uint16 millivolts, notified every 2 s. The CHG LED is
// buried once the ball is potted, so this is how charge state is verified
// through the sealed ball: on the charger the voltage climbs and holds
// ~4150-4200 mV; off the charger it slowly sags. Also a field battery gauge.
BLECharacteristic batteryChar("00001236-0000-1000-8000-00805f9b34fb",
                              BLERead | BLENotify, 2);

uint32_t lastSampleUs = 0;
uint32_t lastBattMs = 0;

uint16_t readBatteryMv() {
  // XIAO nRF52840: P0.31 reads VBAT through a 1M/510k divider that is only
  // connected while P0.14 is driven LOW. 12-bit ADC, 3.3 V full scale:
  // VBAT = adc/4095 * 3300 * (1510/510) mV. Divider tolerance ~±3% — read
  // the TREND (rising vs sagging), not the third digit.
  uint32_t adc = analogRead(P0_31);
  return (uint16_t)((unsigned long long)adc * 3300ULL * 1510ULL
                    / (4095ULL * 510ULL));
}

void setup() {
  Serial.begin(115200);           // debug only; ball runs on LiPo in the field
  analogReadResolution(12);       // 0..4095
  pinMode(P0_14, OUTPUT);         // VBAT_ENABLE: LOW connects the divider
  digitalWrite(P0_14, LOW);       // (~2 uA drain through 1.51M — negligible)

  if (!BLE.begin()) {
    while (1) { delay(1000); }    // BLE init failed — nothing useful to do
  }
  // Request a short connection interval (units of 1.25 ms: 6 = 7.5 ms,
  // 12 = 15 ms). Without this the central settles at ~20+ ms and only ~1
  // notification lands per connection event → ~48 Hz instead of 120 Hz.
  BLE.setConnectionInterval(6, 12);
  BLE.setLocalName("SmartBall");
  BLE.setDeviceName("SmartBall");
  BLE.setAdvertisedService(ballService);
  ballService.addCharacteristic(pressureChar);
  ballService.addCharacteristic(batteryChar);
  BLE.addService(ballService);
  BLE.advertise();
  Serial.println("SmartBall advertising (120 Hz pressure logger)");
}

void loop() {
  BLEDevice central = BLE.central();
  if (!central) return;

  Serial.print("Connected: ");
  Serial.println(central.address());
  lastSampleUs = micros();

  while (central.connected()) {
    uint32_t nowUs = micros();
    if ((uint32_t)(nowUs - lastSampleUs) < SAMPLE_INTERVAL_US) continue;
    lastSampleUs += SAMPLE_INTERVAL_US;   // fixed-rate, no drift accumulation

    // 12-byte packet: uint32 t_ms + 4x uint16 ADC (little-endian on Cortex-M4)
    uint8_t packet[12];
    uint32_t tMs = millis();
    memcpy(packet, &tMs, 4);
    for (int c = 0; c < 4; c++) {
      uint16_t adc = (uint16_t)analogRead(PIN_ORDER[c]);
      memcpy(packet + 4 + 2 * c, &adc, 2);
    }
    pressureChar.writeValue(packet, sizeof(packet));

    if (millis() - lastBattMs >= 2000) {
      lastBattMs = millis();
      uint16_t mv = readBatteryMv();
      batteryChar.writeValue((uint8_t *)&mv, 2);
    }
  }

  Serial.println("Disconnected — advertising again");
  BLE.advertise();
}
