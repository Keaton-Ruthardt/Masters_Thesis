/*
 * SmartBall — 4-Sensor Serial Test (bench check before sealing)
 *
 * Prints all four sensors, labeled by SENSOR NUMBER and finger, so each
 * channel can be verified one at a time before the ball is sealed.
 *
 * PHYSICAL WIRING (v2 ferrule harness, 2026-08-03):
 *   Sensor 1 (index)  -> A0  black   [BK, calFactor 119]
 *   Sensor 2 (middle) -> A1  white   [RM, calFactor 129]
 *   Sensor 3 (thumb)  -> A2  green   [KA, calFactor 148]
 *   Sensor 4 (ring)   -> A3  purple  [CG, calFactor 157]
 * Adjacent pins are acceptable in v2: every connection is a housed female
 * contact, so there is no bare metal or flux on the pad row — the mechanism
 * that bridged v1. Isolation is proven by isolation_test.ino, not pin spacing.
 *
 * Open Serial Monitor at 115200 baud (or Serial Plotter for live curves).
 * Press each sensor pad one at a time: only its column should jump
 * (rest ~20-200, firm press ~1000-2500+).
 */

// Pin for each sensor, indexed by sensor number: [0]=S1 ... [3]=S4
const int SENSOR_PIN[4] = {A0, A1, A2, A3};
const char* SENSOR_NAME[4] = {"S1_index", "S2_middle", "S3_thumb", "S4_ring"};

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);   // readings 0..4095
  delay(1500);                // give the Serial Monitor time to attach
  Serial.println("SmartBall 4-sensor test  (S1=A0 blk  S2=A1 wht  S3=A2 grn  S4=A3 pur)");
}

void loop() {
  // "name:value" pairs work in both Serial Monitor and Serial Plotter
  for (int s = 0; s < 4; s++) {
    Serial.print(SENSOR_NAME[s]);
    Serial.print(":");
    Serial.print(analogRead(SENSOR_PIN[s]));
    Serial.print(s < 3 ? "\t" : "\n");
  }
  delay(100);   // 10 Hz — easy to read while pressing pads
}
