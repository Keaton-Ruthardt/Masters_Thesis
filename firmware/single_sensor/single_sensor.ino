/*
 * Single-sensor bench check — is this FlexiForce alive?
 *
 * Wiring:  3V3 -- sensor -- A0 -- 10kOhm -- GND   (center sensor pin unused)
 * Open Serial Plotter (best) or Serial Monitor @ 115200.
 *
 * Rest  ~ 0-150 raw.  Firm press climbs to hundreds/thousands, drops on release.
 * If it's pinned near 0 and never moves, or floats high (>2000) and jittery
 * with nothing pressing, the sensor or a connection is bad.
 */
#define SENSOR_PIN A0

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);   // 0..4095
}

void loop() {
  Serial.println(analogRead(SENSOR_PIN));
  delay(50);
}
