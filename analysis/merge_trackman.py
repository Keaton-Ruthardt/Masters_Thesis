"""Merge the per-pitch grip features with the TrackMan sheet (2026-07-15).

Mapping is BY ORDER within pitch-type block (markers lag throws; sequence is
ground truth). Reconciliation against the filled TrackMan rows:

  logger mark1-4    <-> P1_FF_60_01..04   (4 throws, ~66 mph)
  logger mark5-8    <-> P1_FF_80_01..04   (4 throws, ~74 mph)
  logger mark9-14   <-> P1_FF_100_01..06  (6 throws, ~78-86 mph; 100_07/08 not thrown)
  logger mark15-22  <-> P1_CB_100_01..08  (8 throws; CB_80 rows not thrown)
  logger mark23-24  <-> sheet rows P1_FF_REG_06/07 -- CONFIRMED by user 2026-07-16:
                        these were INSTRUMENTED-ball throws recorded in the REG rows
                        by mistake. Relabeled P1_FF_100_07/08 (end-of-session, fatigued).
                        NOTE: consequently NO regulation-ball data was collected;
                        the A/B flight validation did not happen this session.

Writes results_dataset.csv (24 pitches) and prints quick-look stats.
"""

import csv
import sys

sys.path.insert(0, "pitch_analysis")
import numpy as np

FEATURES = "ble_logger/realdata_features.csv"
SHEET = "real- session_procedure.csv"
OUT = "results_dataset.csv"

feats = list(csv.DictReader(open(FEATURES)))
sheet = [r for r in csv.DictReader(open(SHEET)) if r["velo_mph"].strip()]

# TrackMan rows in thrown order (only rows with data)
tm_ff = [r for r in sheet if r["pitch_id"].startswith("P1_FF_") and "REG" not in r["pitch_id"]]
tm_cb = [r for r in sheet if r["pitch_id"].startswith("P1_CB_")]
tm_reg = [r for r in sheet if "REG" in r["pitch_id"]]

lg_ff = [f for f in feats if f["pitch_type"] == "fastball"][:14]
lg_cb = [f for f in feats if f["pitch_type"] == "curveball"]
lg_last = [f for f in feats if f["pitch_type"] == "fastball"][14:]

assert len(tm_ff) == len(lg_ff) == 14, (len(tm_ff), len(lg_ff))
assert len(tm_cb) == len(lg_cb) == 8, (len(tm_cb), len(lg_cb))

# Relabel the two mislabeled sheet rows (confirmed instrumented throws).
assert len(tm_reg) == len(lg_last) == 2, (len(tm_reg), len(lg_last))
for i, r in enumerate(tm_reg):
    r["pitch_id"] = f"P1_FF_100_{7 + i:02d}"
    r["type"] = "FF"
    r["effort_pct"] = "100"

merged = []
for tm, lg in zip(tm_ff + tm_cb + tm_reg, lg_ff + lg_cb + lg_last):
    row = {
        "pitch_id": tm["pitch_id"],
        "pitch_type": tm["type"],
        "effort_pct": tm["effort_pct"],
        "velo_mph": float(tm["velo_mph"]),
        "spin_rpm": float(tm["spin_rpm"]),
        "logger_marker": lg["marker_label"],
    }
    for k in ("peak_force_N", "pointer_peak_N", "middle_peak_N", "thumb_peak_N",
              "rate_of_force_development_N_per_s", "impulse_N_s",
              "time_to_peak_s", "grip_duration_s",
              "pointer_frac", "middle_frac", "thumb_frac", "finger_balance_cv"):
        row[k] = lg[k]
    merged.append(row)

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(merged[0].keys()))
    w.writeheader()
    w.writerows(merged)
print(f"wrote {OUT}: {len(merged)} pitches (16 FF incl. 2 relabeled + 8 CB)\n")

# ── quick-look stats ──
ff = [m for m in merged if m["pitch_type"] == "FF"]
cb = [m for m in merged if m["pitch_type"] == "CB"]

def arr(rows, k):
    return np.array([float(r[k]) for r in rows])

print(f"=== Fastball effort ladder (n={len(ff)}) ===")
for eff in ("60", "80", "100"):
    g = [m for m in ff if m["effort_pct"] == eff]
    v, s, p = arr(g, "velo_mph"), arr(g, "spin_rpm"), arr(g, "peak_force_N")
    print(f"  {eff:>3}% (n={len(g)}): velo {v.mean():.1f}±{v.std():.1f}  "
          f"spin {s.mean():.0f}±{s.std():.0f}  peak grip {p.mean():.1f}±{p.std():.1f} N")

def r(x, y):
    return float(np.corrcoef(x, y)[0, 1])

vf, sf = arr(ff, "velo_mph"), arr(ff, "spin_rpm")
print(f"\n=== Grip -> outcome correlations, fastballs (n={len(ff)}, "
      "ladder-induced range) ===")
for k, label in [("peak_force_N", "peak grip force"),
                 ("impulse_N_s", "impulse"),
                 ("pointer_peak_N", "pointer peak"),
                 ("rate_of_force_development_N_per_s", "RFD")]:
    x = arr(ff, k)
    print(f"  {label:<16} vs velo r={r(x, vf):+.3f}   vs spin r={r(x, sf):+.3f}")

vc, sc = arr(cb, "velo_mph"), arr(cb, "spin_rpm")
print("\n=== Curveballs (n=8, all 100%) ===")
print(f"  velo {vc.mean():.1f}±{vc.std():.1f}  spin {sc.mean():.0f}±{sc.std():.0f}")
for k, label in [("peak_force_N", "peak grip force"), ("pointer_peak_N", "pointer peak")]:
    x = arr(cb, k)
    print(f"  {label:<16} vs velo r={r(x, vc):+.3f}   vs spin r={r(x, sc):+.3f}")

print("\n=== FF vs CB grip signature (100% effort only) ===")
ff100 = [m for m in ff if m["effort_pct"] == "100"]
for k in ("peak_force_N", "pointer_frac", "middle_frac", "thumb_frac"):
    a, b = arr(ff100, k), arr(cb, k)
    print(f"  {k:<16} FF {a.mean():6.2f}   CB {b.mean():6.2f}")
