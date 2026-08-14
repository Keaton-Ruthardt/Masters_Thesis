/*
 * SmartBall — Channel Isolation Test  (build QC, 2026-07)
 *
 * Catches the fault that killed the first ball: adjacent channels bridging
 * so two "independent" sensors carry the same signal.
 *
 * HOW TO USE
 *   1. Flash, open Serial Monitor @ 115200.
 *   2. Leave all sensors untouched ~3 s so it can zero the baselines.
 *   3. Press ONE pad at a time, firmly.
 *   4. Read the verdict. The pressed channel should be the only one moving.
 *
 *      PASS  = every other channel stays under CROSSTALK_PCT of the driver.
 *      FAIL  = another channel follows it -> bridge or coupling. Fix BEFORE potting.
 *
 * Run this at EVERY stage: after wiring, after conformal coat, after potting,
 * after stitching, and before every data session.
 *
 * If a channel pair fails, check whether the ratio stays CONSTANT across
 * different press forces: constant ratio = electrical bridge (bad solder /
 * flux / touching wires). Varying ratio = mechanical coupling through the
 * ball (tolerable, but document it).
 */

// Pins in sensor order S1..S4. Adjacent pads are acceptable in v2 because every
// connection is a housed female contact — no bare metal or flux on the pad row,
// which was v1's bridging mechanism. This test is what verifies that holds.
const int PIN[4]   = {A0, A1, A2, A3};
const char* NAME[4] = {"S1", "S2", "S3", "S4"};

const int   DRIVE_MIN     = 60;   // raw ADC rise that counts as "being pressed"
const float CROSSTALK_PCT = 5.0;  // other channels must stay under this % of driver

int baseline[4] = {0, 0, 0, 0};

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  delay(2000);

  Serial.println("\n=== SmartBall channel isolation test ===");
  Serial.println("Keep hands OFF the sensors - zeroing baselines...");
  delay(3000);
  for (int c = 0; c < 4; c++) {
    long sum = 0;
    for (int i = 0; i < 64; i++) { sum += analogRead(PIN[c]); delay(3); }
    baseline[c] = sum / 64;
    Serial.print(NAME[c]); Serial.print(" baseline = "); Serial.println(baseline[c]);
  }
  Serial.println("\nNow press ONE pad at a time.\n");
}

void loop() {
  int v[4], driver = -1, dmax = 0;

  for (int c = 0; c < 4; c++) {
    v[c] = analogRead(PIN[c]) - baseline[c];
    if (v[c] < 0) v[c] = 0;
    if (v[c] > dmax) { dmax = v[c]; driver = c; }
  }

  if (dmax < DRIVE_MIN) { delay(50); return; }   // nothing pressed hard enough

  bool pass = true;
  Serial.print("press "); Serial.print(NAME[driver]);
  Serial.print(" ("); Serial.print(dmax); Serial.print(")  | others: ");

  for (int c = 0; c < 4; c++) {
    if (c == driver) continue;
    float pct = 100.0 * v[c] / dmax;
    Serial.print(NAME[c]); Serial.print("="); Serial.print(v[c]);
    Serial.print("("); Serial.print(pct, 1); Serial.print("%) ");
    if (pct > CROSSTALK_PCT) pass = false;
  }

  Serial.println(pass ? " -> PASS" : " -> *** FAIL: CROSSTALK ***");
  delay(250);   // one verdict per press, not per sample
}
