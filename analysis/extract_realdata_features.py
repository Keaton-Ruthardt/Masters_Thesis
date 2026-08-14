"""Extract per-pitch grip features for the 2026-07-15 ORU session and attach
marker labels by block order (markers lag throws 20-200 s, so the built-in
nearest-in-time labeler can't be used; sequence within a block is ground truth).

Writes ble_logger/realdata_features.csv — one row per throw, ready to merge
with the TrackMan sheet on marker/order.
"""

import csv
import sys

sys.path.insert(0, "pitch_analysis")
import numpy as np
from pitch_analysis import (DEFAULT_CAL, FEATURE_COLUMNS, extract_features,
                            filter_events, load_session, segment_auto)

SRC = "ble_logger/realdata_clean.csv"
ASSIGN = "ble_logger/realdata_assignment.csv"
OUT = "ble_logger/realdata_features.csv"

s = load_session(SRC, dict(DEFAULT_CAL))
t, total = s["t_s"], s["total"]
events = filter_events(segment_auto(total, 5.0, 2.0), t, 0.02,
                       total=total, min_peak=10.0)
rows = extract_features(s, events)

# Attach marker labels from the order-based assignment (row k <-> event k).
assign = list(csv.DictReader(open(ASSIGN)))
assert len(assign) == len(rows), (len(assign), len(rows))
for r, a in zip(rows, assign):
    r["marker_label"] = a["marker"]

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FEATURE_COLUMNS)
    w.writeheader()
    w.writerows(rows)

print(f"wrote {OUT}  ({len(rows)} pitches)")
print()
print(f"{'#':>3} {'marker':<8} {'type':<10} {'peakN':>6} {'RFD':>8} "
      f"{'impulse':>8} {'ptr_N':>6} {'mid_N':>6} {'thb_N':>6}")
for r in rows:
    print(f"{r['pitch_index']:>3} {r['marker_label']:<8} {r['pitch_type']:<10} "
          f"{r['peak_force_N']:>6.1f} {r['rate_of_force_development_N_per_s']:>8.0f} "
          f"{r['impulse_N_s']:>8.3f} {str(r['pointer_peak_N']):>6} "
          f"{str(r['middle_peak_N']):>6} {str(r['thumb_peak_N']):>6}")
