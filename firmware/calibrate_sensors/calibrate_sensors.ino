/*
 * FlexiForce A201-25 Single-Sensor Calibration
 *
 * Reads ONE FlexiForce sensor on pin 3 (A3) at high rate, averages over a
 * window, and streams clean CSV output. To calibrate the other sensors,
 * move the FlexiForce wire to pin 3 and re-run the procedure.
 *
 * Output format:
 *   millis, sensor_avg, sensor_min, sensor_max
 *
 * Procedure:
 *   1. Upload and open Serial Monitor at 115200 baud
 *   2. With NOTHING on the sensor, capture 10 sec of baseline
 *   3. Apply a known weight (e.g., 500g = 4.9N) to the sensor pad
 *   4. Hold for 5 sec, remove
 *   5. Repeat with different known weights (1N, 5N, 10N, 20N, 40N)
 *   6. Save serial output as CSV
 *   7. Run fit_calibration.py to compute calFactor
 *
 * Known weight references:
 *   - Empty water bottle: ~0.25 N
 *   - Full 500ml water bottle: ~4.9 N
 *   - Full 1L water bottle: ~9.8 N
 *   - 5 lb hand weight: ~22.2 N
 *   - 10 lb dumbbell: ~44.5 N
 */

const int SENSOR_PIN = A0;          // Pin 3 on XIAO nRF52840
const int REPORT_INTERVAL_MS = 100; // 10 Hz output

unsigned long lastReport = 0;
long sum = 0;
int minVal = 4095;
int maxVal = 0;
int sampleCount = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  analogReadResolution(12);

  Serial.println("=== FlexiForce Single-Sensor Calibration ===");
  Serial.println("Sensor on pin 3 (A3)");
  Serial.println();
  Serial.println("Procedure:");
  Serial.println("  1. Let baseline run 10 sec with nothing on sensor");
  Serial.println("  2. Apply known weight, hold 5 sec, remove");
  Serial.println("  3. Repeat with different weights");
  Serial.println();
  Serial.println("CSV header:");
  Serial.println("millis,sensor_avg,sensor_min,sensor_max");
}

void loop() {
  // Continuously sample
  int v = analogRead(SENSOR_PIN);
  sum += v;
  if (v < minVal) minVal = v;
  if (v > maxVal) maxVal = v;
  sampleCount++;

  // Report every 100 ms
  if (millis() - lastReport >= REPORT_INTERVAL_MS) {
    int avg = (sampleCount > 0) ? (sum / sampleCount) : 0;
    Serial.print(millis());
    Serial.print(",");
    Serial.print(avg);
    Serial.print(",");
    Serial.print(minVal);
    Serial.print(",");
    Serial.println(maxVal);

    // Reset accumulators
    sum = 0;
    minVal = 4095;
    maxVal = 0;
    sampleCount = 0;
    lastReport = millis();
  }
}
