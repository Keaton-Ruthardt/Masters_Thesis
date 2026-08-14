# An Instrumented Baseball for Per-Finger Grip Force Measurement

Reproducibility materials for the MS thesis *An Instrumented Baseball for Per-Finger
Grip Force Measurement: Finger Force Tracks Delivery Effort Rather Than Release Velocity*
(Keaton Ruthardt, MS Computer Science — Data Science, Oral Roberts University, 2026).

A regulation baseball instrumented with four thin-film force sensors under the leather
cover, sampling all channels at 480 Hz and streaming over Bluetooth Low Energy, paired
per pitch with TrackMan radar release velocity. Total build cost under $300.

## What the study found

Measured the way the field currently measures it — with a graded submaximal effort
ladder — grip force predicts release velocity strongly and broadly: index + middle
force at release reaches *r* = 0.59, and 15 of 20 grip features remain significant
after Holm correction.

Holding commanded effort fixed removes that association. Index + middle force at
release falls to *r* = 0.33 (n.s.), and its unique contribution to velocity variance
is **ΔR² = 0.000**, against 0.759 for commanded effort alone. A mixed-effects model
agrees (χ²(1) = 0.47, *p* = 0.49).

Three thumb-dominated features survive Benjamini–Hochberg correction (*q* = 0.035);
none clears family-wise correction, and all are reported as **exploratory**.

The conclusion is that finger grip force, measured under a submaximal effort protocol,
is largely a readout of delivery effort rather than a determinant of release velocity.

## Layout

| Path | Contents |
|---|---|
| `thesis/` | The thesis (`MSCS_Paper.docx`) and its Quarto source, bibliography, and CSL style |
| `defense/` | Defense presentation, including a copy with speaker notes |
| `Masters_Thesis_and_Defense.zip` | Thesis and presentation bundled together |
| `firmware/` | Arduino sketches for the Seeed XIAO nRF52840 |
| `acquisition/` | `ble_logger.py` — BLE client, writes raw counts to CSV |
| `calibration/` | Per-sensor calibration procedure, fitting script, factors, raw captures |
| `analysis/` | Feature extraction, statistics, and figure generation |
| `analysis/results/` | Derived, de-identified data and generated statistical reports |
| `figures/` | Figures as they appear in the thesis |
| `hardware/` | KiCad PCB project, schematic and layout PDFs, bill of materials |
| `docs/` | Illustrated build guides, project plan, proposal |

### Firmware

- `pressure_logger_480/` — **deployed** acquisition firmware. 480 Hz, four samples per packet.
- `pressure_logger/` — earlier 120 Hz single-sample version; the host logger supports both.
- `isolation_test/` — channel-isolation gate.
- `sensor_test/`, `single_sensor/`, `calibrate_sensors/` — bench-check sketches.

Built with the Arduino IDE and the Seeed nRF52 **mbed-enabled** board package. The
non-mbed package fails to link.

## Wire protocol

The pressure characteristic carries a **36-byte packet**: a 32-bit unsigned microsecond
timestamp for the first sample in the batch, followed by four sample groups of four
16-bit unsigned ADC values each, little-endian, in channel order S1 through S4. Sample
*k* within a batch occurs at the batch timestamp plus *k* × 2083 µs.

The earlier firmware sends a 12-byte packet: a 32-bit millisecond timestamp followed by
four 16-bit ADC values. `ble_logger.py` derives the batch size from the packet length
and works against either version without modification.

## Data dictionary

Each logged CSV row contains:

| Column | Meaning |
|---|---|
| `wall_iso` | Host wall-clock time, ISO 8601, UTC |
| `wall_unix_ms` | Host wall-clock time, integer ms since the Unix epoch |
| `ball_t_ms` | The instrument's own timebase in ms — **the authoritative timing column** |
| `s1`–`s4` | Raw ADC counts, 0–4095, in channel order |
| `s1_N`–`s4_N` | Convenience force values in newtons |
| `marker` | Operator-typed per-pitch tag (pitch id, effort, outcome) |

Raw counts are the archived source of truth. Calibration is applied downstream in
analysis, never on the ball, so it can be revised without re-collecting data.

## Force conversion

For a sensor of resistance *R*ₛ in series with a fixed 10 kΩ resistor, the divider node
read by the 12-bit ADC gives a conductance ratio

```
G = ADC / (4095 - ADC)
F = c * G
```

where *c* is the per-sensor calibration factor in `calibration/calfactors_v3.csv`,
fitted through the origin by least squares over twenty applied-mass trials per sensor
(R² = 0.961 to 0.995).

## Reproducing the analysis

```bash
pip install numpy pandas scipy statsmodels matplotlib
cd analysis
python thesis_analysis_v2.py     # feature extraction -> results/
python advanced_stats.py         # corrections, variance decomposition, bootstrap
python make_thesis_figures.py    # figures
```

A fixed random seed (20260805) makes every reported *p*-value reproducible: 20,000
permutations and 10,000 bootstrap resamples throughout.

Note that `thesis_analysis_v2.py` reads raw session captures, which are not distributed
here (see below). The derived feature table it produces, `analysis/results/per_pitch_features.csv`,
**is** included, and `advanced_stats.py` and `make_thesis_figures.py` run from it directly.

## Participant data

Raw per-pitch session captures are **not included**, in accordance with the
participant-privacy commitments described in the thesis. Participants consented to their
data being used in the study; that consent did not extend to public redistribution of
raw records.

Derived, de-identified summary data sufficient to reproduce the reported figures and
models are provided in `analysis/results/`. Pitchers are identified only as P1, P2, P3.

## Licensing

- **Code and firmware** — [MIT License](LICENSE)
- **Documentation, figures, and build records** — [CC BY 4.0](LICENSE-DOCS)

Both are permissive and allow reuse with attribution, which is the intent for a
reproducibility release: you should be able to rebuild the instrument and re-run the
analysis without seeking further permission.

Third-party software is used in accordance with its own licenses, none of which impose
copyleft obligations on this project's code. TrackMan, PitchLogic, Kookaburra,
FlexiForce, Tekscan, Seeed, and Nordic Semiconductor are trademarks of their respective
owners, used nominatively to identify the products actually used or discussed. No
endorsement is implied.

## Safety

The instrument places a lithium-polymer cell and rigid electronics inside a ball thrown
at speed. If you rebuild it, read `docs/BALL_INTEGRATION_GUIDE.md` first. Epoxy is poured
in ~15 g layers with each cured before the next, because the exotherm of a single large
pour is a genuine thermal hazard to an enclosed LiPo cell, and the cell is wrapped before
potting. The ball is retired — not repaired — if the cover is breached, the potted block
loosens, the cell swells or fails to hold charge, or the channel-isolation test fails
after an impact. The cell cannot be removed once potted, so retirement means disposal of
the whole assembly through appropriate lithium-battery disposal.

## Citation

```bibtex
@mastersthesis{ruthardt2026instrumented,
  author = {Ruthardt, Keaton},
  title  = {An Instrumented Baseball for Per-Finger Grip Force Measurement:
            Finger Force Tracks Delivery Effort Rather Than Release Velocity},
  school = {Oral Roberts University},
  year   = {2026},
  type   = {MS thesis}
}
```
