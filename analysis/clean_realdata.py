"""One-shot cleaning for the 2026-07-15 ORU session (realdata.csv).

1. Rename the stray '\\' marker (typo on throw 3's late ENTER) to 'mark3'.
2. Re-segment with pitch-tuned parameters (min_dur 0.02 s, min_peak 10 N).
3. Assign events to markers IN ORDER within each pitch-type block —
   markers were pressed 20-60 s after each throw (solo operator walking
   back to the laptop), so nearest-in-time matching is unreliable;
   sequence within a block is what's trustworthy.
4. Write realdata_clean.csv and realdata_assignment.csv.
"""

import csv
import sys

sys.path.insert(0, "pitch_analysis")
import numpy as np
from pitch_analysis import (DEFAULT_CAL, filter_events, load_session,
                            segment_auto)

SRC = "ble_logger/realdata.csv"
CLEAN = "ble_logger/realdata_clean.csv"
ASSIGN = "ble_logger/realdata_assignment.csv"

# ── 1) marker fix ──
rows = list(csv.DictReader(open(SRC)))
fixed = 0
for r in rows:
    if r["marker"].strip() == "\\":
        r["marker"] = "mark3"
        fixed += 1
with open(CLEAN, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"marker rows renamed '\\' -> 'mark3': {fixed}")
print(f"wrote {CLEAN} ({len(rows)} rows)")

# ── 2) segment with tuned params ──
s = load_session(CLEAN, dict(DEFAULT_CAL))  # grip masking ON (default)
t, total = s["t_s"], s["total"]
events = filter_events(segment_auto(total, 5.0, 2.0), t, 0.02,
                       total=total, min_peak=10.0)
print(f"grip events detected: {len(events)}")

# ── 3) order-based assignment within pitch-type blocks ──
ptypes = s["pitch_type"]
markers = [(i, m) for i, m in s["markers"] if not m.startswith("pitch_type=")]

def block_of(sample_idx):
    return ptypes[sample_idx] if sample_idx < len(ptypes) else ""

# split markers and events into contiguous pitch-type blocks
def blocks(seq, idx_of):
    out = []
    for item in seq:
        b = block_of(idx_of(item))
        if not out or out[-1][0] != b:
            out.append((b, []))
        out[-1][1].append(item)
    return out

mblocks = blocks(markers, lambda m: m[0])
eblocks = blocks(events, lambda e: e[0])

assign = []
for (mb, ms), (eb, es) in zip(mblocks, eblocks):
    n = max(len(ms), len(es))
    for k in range(n):
        ev = es[k] if k < len(es) else None
        mk = ms[k] if k < len(ms) else None
        row = {
            "block": mb or eb,
            "marker": mk[1] if mk else "(no marker)",
            "marker_t_s": round(t[mk[0]], 1) if mk else "",
            "event_t_s": round(t[ev[0]], 1) if ev else "(no event)",
            "peak_N": round(float(np.max(total[ev[0]:ev[1] + 1])), 1) if ev else "",
        }
        assign.append(row)

with open(ASSIGN, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["block", "marker", "marker_t_s",
                                      "event_t_s", "peak_N"])
    w.writeheader()
    w.writerows(assign)

print(f"wrote {ASSIGN}")
print()
print(f"{'block':<10} {'marker':<10} {'marker_t':>9} {'event_t':>10} {'peak_N':>7}")
for a in assign:
    print(f"{a['block']:<10} {a['marker']:<10} {str(a['marker_t_s']):>9} "
          f"{str(a['event_t_s']):>10} {str(a['peak_N']):>7}")
