# SmartBall BLE Logger

Streams the XIAO nRF52840 SmartBall's 200 Hz grip-pressure notifications to a
timestamped CSV for post-processing against TrackMan.

Pairs with `firmware/pressure_logger/pressure_logger.ino`.

## Setup

```bash
pip install -r requirements.txt
```

## Run

Power the ball **on the LiPo** (not USB) so it advertises as `SmartBall`, then:

```bash
python ble_logger.py --out session_2026-07-11.csv
```

- Press **ENTER** between pitches to drop a marker row (type a label first, e.g.
  `fastball7`, then ENTER). Use these to align each pitch with its TrackMan row.
- **Ctrl+C** stops cleanly, flushes the file, and prints a summary
  (samples logged, estimated dropped packets, effective rate).

### Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--out FILE` | `smartball_<timestamp>.csv` | output path |
| `--name NAME` | `SmartBall` | BLE local name to connect to |
| `--duration S` | run until Ctrl+C | auto-stop after S seconds |
| `--scan-timeout S` | `20` | scan timeout before giving up |
| `--no-force` | off | log raw ADC only (skip force columns) |
| `--quiet` | off | suppress the live readout |

## Output columns

`wall_iso, wall_unix_ms, ball_t_ms, idx, mid, thb, rng, idx_N, mid_N, thb_N, rng_N, marker`

- **`ball_t_ms`** — the ball's own `millis()` clock; use this for sample-to-sample
  timing and pitch segmentation.
- **`wall_*`** — laptop wall clock for coarse alignment to TrackMan session time.
- **`idx/mid/thb/rng`** — raw 12-bit ADC. **This is the source of truth.**
- **`*_N`** — convenience force estimate using the firmware conductance model
  (`G = adc/(4095-adc)`, `F = G·calFactor`). `thb`/`rng` calFactors are still
  placeholders (150) pending the S3/S4 calibration fits — re-derive force in
  analysis from raw ADC once those land.

## Notes

- Segment pitches by the grip build-up / release-dropout in the pressure signal,
  cross-checked against the ENTER markers.
- Dropped-packet estimate assumes 5 ms spacing (200 Hz); a `ball_t_ms` jump > 7 ms
  is counted as missed samples. Some loss is expected over BLE — the ball clock
  keeps analysis honest.
