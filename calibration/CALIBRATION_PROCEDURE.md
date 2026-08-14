# FlexiForce A201 Calibration Procedure

## Goal
Determine a per-sensor calibration constant that converts raw ADC readings into Newtons of force, with documented accuracy.

## What You Need
- Breadboard prototype with all 4 FlexiForce sensors wired and working
- Known weights covering the expected force range:
  - Empty cup or no load (0 N baseline)
  - Light: 500 mL water bottle (~4.9 N)
  - Medium: 1 L water bottle (~9.8 N) or 1 kg dumbbell (~9.8 N)
  - Heavy: 5 lb hand weight (~22.2 N)
  - Optional: 10 lb dumbbell (~44.5 N)
- A flat hard surface
- Python 3 with numpy and matplotlib installed

## Setup
1. Place the breadboard prototype flat on a table with all 4 FlexiForce sensors face-up and free to be pressed
2. Open Arduino IDE and load `firmware/calibrate_sensors/calibrate_sensors.ino`
3. Upload to the XIAO nRF52840
4. Open Serial Monitor at 115200 baud
5. Click "Save Output to File" or be ready to copy-paste the output

## Data Collection (Repeat for Each Weight)

### Step 1: Baseline (0 N)
- With nothing touching any sensor, let the firmware stream for 10 seconds
- This captures the noise floor for each sensor

### Step 2: Apply Weight to Sensor 0 (Index Finger Sensor on A0)
- Carefully place the known weight directly on the round sensing pad of Sensor 0
- Make sure the weight is centered and not pressing on adjacent sensors
- Let it sit undisturbed for 5 seconds
- Remove the weight

### Step 3: Apply Weight to Sensor 1, 2, 3
- Repeat Step 2 for each remaining sensor

### Step 4: Repeat for Different Weights
- Repeat Steps 2-3 with each of your available weights
- More data points produce a better fit. Aim for at least 3 weights per sensor.

## Saving the Data
1. Stop the serial capture
2. Save the captured output as a CSV file (e.g., `calibration_run.csv`)
3. Open the CSV in Excel or any spreadsheet editor
4. Add two new columns at the end: `label` and `force_n`
5. For each 5-second weight-applied window, find a row near the middle of that window and fill in:
   - `label`: e.g., `S0_4.9N` or `baseline`
   - `force_n`: the applied force in Newtons (e.g., `4.9` or `0`)
6. Save the annotated CSV

Example annotated row:
```
millis,S0_avg,S0_min,S0_max,S1_avg,...,label,force_n
12500,1023,1018,1031,12,...,S0_4.9N,4.9
```

## Running the Fit
```bash
cd C:\Users\Jkeat\MastersBall\instrumented-baseball\analysis\calibration
python fit_calibration.py path\to\calibration_run.csv
```

Outputs:
- `calibration_report.png` -- A 4-panel plot showing the conductance-vs-force fit for each sensor, with R-squared value
- `calibration_constants.json` -- Machine-readable calibration constants for each sensor

## Updating the Firmware
After the fit, edit `smartball_full.ino` and update the calFactor array with the new per-sensor values from `calibration_constants.json`:

```cpp
// Before (uniform):
float calFactor[4] = {55.5, 55.5, 55.5, 55.5};

// After (from calibration):
float calFactor[4] = {52.3, 57.1, 54.8, 56.0};  // example values
```

## Acceptance Criteria
- Each sensor should have an R-squared of at least 0.95 against the linear conductance model
- Sensor-to-sensor variation in calFactor should be within plus or minus 15 percent of the average
- The calibration plot is acceptable thesis evidence for Sprint 3 deliverable
