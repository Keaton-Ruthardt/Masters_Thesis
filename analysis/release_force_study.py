"""Which operationalization of 'force at release' actually predicts velocity?

Peak force can occur anywhere in the pitch, including during the wind-up where
it transfers no momentum to the ball. On mechanical grounds the force still
being applied in the final milliseconds before the ball leaves the hand should
carry more information about velocity than force earlier in the delivery. This
script tests that directly by recomputing the same association under
progressively narrower windows ending at the loss of contact.

Every window is evaluated twice:
  * raw within-pitcher, which is confounded by the effort ladder
  * with each pitcher x commanded-effort cell mean removed, which is the test
    that decides whether the window definition matters for anything real

Both the index and the thumb are reported, because the effort-controlled
analysis in advanced_stats.py finds the surviving association on the thumb.

    python release_force_study.py     (run thesis_analysis_v2.py first)

Outputs: results/release_force_variants.csv, results/release_window_report.md
"""
import os
import re

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

from thesis_analysis_v2 import (SESSIONS, DATA, PITCH_MAPS, finger_frames,
                                find_events, MIN_FINGER_N, MIN_FINGERS,
                                release_metrics, parse_tag, STATE_RE,
                                DEFAULT_EFFORT_PCT)

WINDOWS = (5, 10, 25, 50, 100)
L = []
def A(s=""):
    L.append(s)


rows = []
for pid, fn in SESSIONS.items():
    d = pd.read_csv(os.path.join(DATA, fn), low_memory=False)
    for pitch, blk in d.groupby("pitch_type", sort=False):
        if pitch not in PITCH_MAPS:
            continue
        t = blk.ball_t_ms.values.astype(float)
        ff = finger_frames(blk, pitch)
        load = np.sum([np.clip(v, 0, None) for v in ff.values()], axis=0)
        for grp in find_events(t, load):
            if sum(1 for v in ff.values() if v[grp].max() >= MIN_FINGER_N) < MIN_FINGERS:
                continue
            r = dict(pitcher=pid, pitch_type=pitch, t_end=float(t[grp[-1]]))
            # Combined driving channel: index and middle summed. Kept out of
            # `load` above, which is only used for event detection -- adding it
            # there would double-count those two fingers.
            chans = dict(ff)
            if "pointer" in ff and "middle" in ff:
                chans["finger"] = ff["pointer"] + ff["middle"]
            for finger, v in chans.items():
                seg, tt = v[grp], t[grp]
                m = release_metrics(tt, seg)
                if not m:
                    continue
                tr = m["t_rel"]
                r[f"{finger}_peak"] = m["peak_N"]
                for w in WINDOWS:
                    win = (tt >= tr - w) & (tt <= tr)
                    if win.sum() >= 2:
                        r[f"{finger}_F{w}"] = float(seg[win].mean())
                        r[f"{finger}_J{w}"] = float(np.trapezoid(seg[win], tt[win]) / 1000.0)
                w40 = (tt >= tr - 40) & (tt <= tr)
                if w40.sum() >= 3:
                    r[f"{finger}_secpk"] = float(seg[w40].max())
                post = (tt >= m["t_peak"]) & (tt <= tr + 20)
                if post.sum() > 4:
                    dv = np.diff(seg[post]) / (np.diff(tt[post]) / 1000.0)
                    r[f"{finger}_unload"] = float(-np.nanmin(dv))
            rows.append(r)

ev = pd.DataFrame(rows).sort_values("t_end").reset_index(drop=True)

# Reuse the master table's tag pairing and effort labelling rather than
# reimplementing it -- the two must not be allowed to drift apart.
mast = pd.read_csv("results/per_pitch_features.csv")
keep = ["pitcher", "t_end", "velo_mph", "effort_pct", "analyzable"]
ev = ev.merge(mast[[c for c in keep if c in mast]], on=["pitcher", "t_end"],
              how="left")
ev = ev[ev.get("analyzable", pd.Series(True, index=ev.index)).fillna(False)]
fb = ev[(ev.pitch_type == "fastball") & ev.velo_mph.notna()].copy()

CELLS = ["pitcher", "effort_pct"]
ncell = fb.groupby(CELLS).ngroups


def within(df, col, keys):
    return df[col] - df.groupby(keys)[col].transform("mean")


def assoc(df, col, keys, dfree_lost):
    d = df[[col, "velo_mph"] + keys].dropna()
    if len(d) < 12:
        return np.nan, np.nan, 0
    x = within(d, col, keys).values
    y = within(d, "velo_mph", keys).values
    sx, sy = np.sqrt(x @ x), np.sqrt(y @ y)
    if sx == 0 or sy == 0:
        return np.nan, np.nan, len(d)
    r = float(np.clip((x @ y) / (sx * sy), -0.999999, 0.999999))
    dfree = len(d) - dfree_lost - 1
    t = r * np.sqrt(dfree / (1 - r ** 2))
    return r, float(2 * stats.t.sf(abs(t), dfree)), len(d)


A("# Release-window study — how narrowly should 'force at release' be defined?\n")
A(f"Fastballs with a paired velocity: n = {len(fb)}. Sampling interval at "
  f"480 Hz is 2.083 ms, so a 5 ms window spans about 2.4 samples and a 10 ms "
  f"window about 4.8. Cell control removes the mean of each of the {ncell} "
  f"pitcher × commanded-effort combinations.\n")

for finger, label in (("finger", "Index + middle combined"),
                      ("pointer", "Index finger alone"),
                      ("thumb", "Thumb")):
    VARS = [(f"{finger}_peak", "Peak force, anywhere in the pitch")]
    VARS += [(f"{finger}_F{w}", f"Mean force, final {w} ms") for w in WINDOWS]
    VARS += [(f"{finger}_J{w}", f"Impulse over final {w} ms") for w in WINDOWS]
    VARS += [(f"{finger}_secpk", "Peak within final 40 ms"),
             (f"{finger}_unload", "Unloading rate at release")]
    A(f"\n## {label}\n")
    A("| Definition | r (pitcher-centred) | p | r (pitcher × effort cell-centred) | p | n |")
    A("|:--|--:|--:|--:|--:|--:|")
    for c, lab in VARS:
        if c not in fb or fb[c].notna().sum() < 12:
            continue
        r0, p0, n0 = assoc(fb, c, ["pitcher"], fb.pitcher.nunique())
        r1, p1, _ = assoc(fb, c, CELLS, ncell)
        star = "**" if np.isfinite(p1) and p1 < 0.05 else ""
        A(f"| {star}{lab}{star} | {r0:.3f} | {p0:.3g} | {star}{r1:.3f}{star} | "
          f"{p1:.3g} | {n0} |")

A("\n## Reading this table\n")
A("The left pair of columns removes only between-pitcher differences and is "
  "confounded by the effort ladder, which moved grip force and velocity "
  "together by design. The right pair holds commanded effort exactly fixed. A "
  "window definition earns its place only if it survives on the right.\n")
A("Windows narrower than about 10 ms are averaging fewer than five samples and "
  "are correspondingly noisy; any apparent advantage at 5 ms should be read "
  "with that in mind rather than as a real gain in resolution.\n")

ev.to_csv("results/release_force_variants.csv", index=False)
open("results/release_window_report.md", "w", encoding="utf-8").write("\n".join(L))
print(f"wrote results/release_window_report.md and "
      f"results/release_force_variants.csv  (n fastballs = {len(fb)})")
