/*
 * FlexiForce Calibration Sketch
 *
 * Place a known weight on each sensor and record the ADC reading.
 * The FlexiForce conductance (1/R) is approximately linear with force.
 *
 * Formula: Force(N) = (ADC / (4095 - ADC)) * (1 / R_fixed) * cal_factor
 *
 * Procedure:
 * 1. Upload this sketch
 * 2. Open Serial Monitor (115200)
 * 3. With nothing on the sensor, note the baseline (should be ~0)
 * 4. Place a known weight on the sensor's round dot
 * 5. Record the stable ADC value
 * 6. Repeat for each sensor
 * 7. The sketch computes the calibration factor for you
 */

const float KNOWN_WEIGHT_N = 4.9; // ← Change this to your weight in Newtons
                                   // 500g = 4.9N, 1kg = 9.8N, 1lb = 4.45N

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  analogReadResolution(12);

  Serial.println("=== FlexiForce Calibration ===");
  Serial.print("Known weight: ");
  Serial.print(KNOWN_WEIGHT_N);
  Serial.println(" N");
  Serial.println();
  Serial.println("Place known weight on each sensor one at a time.");
  Serial.println("Readings update every 500ms.");
  Serial.println("S0=Index, S1=Middle, S2=Thumb, S3=Ring");
  Serial.println();
}

void loop() {
  for (int i = 0; i < 4; i++) {
    int adc = analogRead(A0 + i);
    float conductance = 0;
    float cal_factor = 0;

    if (adc > 5 && adc < 4090) {
      conductance = (float)adc / (4095.0 - (float)adc);
      cal_factor = KNOWN_WEIGHT_N / conductance;
    }

    Serial.print("S");
    Serial.print(i);
    Serial.print(": ADC=");
    Serial.print(adc);
    Serial.print("  Cond=");
    Serial.print(conductance, 4);

    if (cal_factor > 0) {
      Serial.print("  CalFactor=");
      Serial.print(cal_factor, 2);
      Serial.print(" N");
    }

    Serial.print("    ");
  }
  Serial.println();
  delay(500);
}
