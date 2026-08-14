"""Master analysis for the v2 instrumented-baseball sessions.

Reads the three cleaned 480 Hz session files, parses the per-pitch outcome tags,
segments pitches from the pressure stream, extracts the grip-force features
defined in the thesis, and runs the pre-specified statistical analysis.

    python thesis_analysis_v2.py

Outputs
    results/per_pitch_features.csv   tidy one-row-per-pitch feature table
    results/stats_report.md          full numeric report for the thesis
    figures/*.png                    thesis figures

Design notes
  * Outcome values live in the marker column, typed at capture. There is no
    join by sequence position, so a missed radar reading cannot misalign the
    dataset -- it simply leaves that pitch unpaired.
  * Absolute force is NOT comparable between pitchers (hand geometry, pad
    registration, per-sensor calibration). All grip-outcome inference is on
    within-pitcher centred variables.
  * "pointer" is sensor S1 on a fastball but S3 on a curveball. Features are
    resolved to FINGER using the per-grip map, never to a fixed channel.
"""
import os
import re
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

DATA = "Final-Clean-Data"
SESSIONS = {"P1": "pitcher1_session_480hz.csv",
            "P2": "pitcher2_session_480hz.csv",
            "P3": "pitcher3_session_480hz.csv"}
PARTICIPANTS = "participants.csv"

# Effort labelling rule, fixed by the pitcher before any outcome was inspected.
# Precedence, highest first:
#   1. an explicit 'NN%' prefix on the pitch's own marker
#   2. the effort declared by the most recent 'effort=NN' state marker
#   3. DEFAULT_EFFORT_PCT -- an untagged pitch is a maximum-effort pitch
# An 'NN%' prefix labels only its own pitch; it does NOT change the running
# state. Carrying a prefix forward mislabels the pitches that follow a
# submaximal block: in P3 three untagged fastballs at 72.4-76.4 mph follow an
# explicit 80 % block whose pitches ran 63.2-68.2 mph, so they are plainly
# maximum effort and inheriting '80 %' would corrupt the effort control.
# Effort is never inferred from velocity -- that is circular and would
# manufacture the very association the analysis exists to test.
DEFAULT_EFFORT_PCT = 100.0

CH = ("s1", "s2", "s3", "s4")
CAL = {"s1": 119.0, "s2": 129.0, "s3": 148.0, "s4": 157.0}
SENSOR = {"s1": "BK", "s2": "RM", "s3": "KA", "s4": "CG"}
ADC_MAX = 4095

PITCH_MAPS = {
    "fastball":  {"s1": "pointer", "s2": "middle", "s3": "thumb",   "s4": None},
    "curveball": {"s1": "thumb",   "s2": None,     "s3": "pointer", "s4": "middle"},
    "slider":    {"s1": "thumb",   "s2": None,     "s3": "pointer", "s4": "middle"},
}
FINGERS = ("pointer", "middle", "thumb")

# event detection
MIN_FINGER_N = 2.0        # a finger counts as loaded above this
MIN_FINGERS = 2           # a pitch loads at least this many
# Separation between distinct pitches. Must be well below the interval between
# consecutive throws but above any sub-threshold dip WITHIN one pitch. At 600 ms
# adjacent pitches merged into single events, producing physically impossible
# release leads of +/-560 to 595 ms -- longer than a whole pitch.
EVENT_GAP_MS = 250
MAX_EVENT_MS = 900        # a single pitch never spans longer; longer = merged
REL_FRAC = 0.10           # contact lost below this fraction of that finger's peak
# Window before release that F_release averages over. Fixed at 10 ms -- about
# five samples at 480 Hz. The release-window study found the association with
# velocity strengthens monotonically as the window narrows, and 10 ms was the
# narrowest definition that stayed significant under effort control while still
# spanning enough samples to be robust to single-sample noise. Declared here,
# ahead of the re-analysis, so the primary measure is not chosen after the fact.
REL_WINDOW_MS = 10
MATCH_WINDOW_MS = 40000   # a tag must follow its pitch within this

FINGER_COLOR = {"pointer": "#1f6fd0", "middle": "#d2600f", "thumb": "#b02a8a"}
INK, INK2, MUTED, GRID = "#1a1d21", "#4a4f56", "#7c7f86", "#e3e2dd"
SURFACE = "#fcfcfb"

os.makedirs("results", exist_ok=True)
os.makedirs("figures", exist_ok=True)


# ---------------------------------------------------------------- marker tags
STATE_RE = re.compile(r"^(pitch_type|effort)\s*=\s*(.+)$", re.I)


def parse_tag(s):
    """Pull outcome values out of a hand-typed marker.

    Handles the formats actually present in the captures:
        '73.8'                  velocity only
        '80%68.2'               effort prefix + velocity
        '100%78.7 + 1689'       effort prefix + velocity + spin
        'warmup77.1+1607'       warm-up throw, velocity + spin
        '77.1+1607'             velocity + spin rate
        '77.0 hz18.9 ivb7.0'    velocity + break, unit-prefixed
        '71.9 -11.6hz 0ivb'     velocity + break, unit-suffixed
    Returns dict or None if the marker carries no pitch outcome.
    """
    s = str(s).strip()
    if not s or STATE_RE.match(s):
        return None
    out = {}
    m = re.match(r"^\s*warm[\s-]?up\s*", s, re.I)
    if m:
        # A warm-up throw. Tagged with a velocity but thrown outside the effort
        # protocol, so it carries no effort label and is held out of every
        # inferential model. Retained for descriptives and for the count audit.
        out["warmup"] = True
        s = s[m.end():]
    m = re.match(r"^(\d{2,3})\s*%\s*", s)
    if m:
        out["effort_pct"] = float(m.group(1))
        out["effort_source"] = "explicit_prefix"
        s = s[m.end():]
    # Velocity is the LEADING number once the prefixes are stripped, in every
    # marker format captured. Taking it positionally is what makes the movement
    # formats safe. Deriving it instead by stripping the hz/ivb/spin tokens and
    # reading what was left silently discarded the velocity of
    # '77.0 hz18.9 ivb7.0': the alternation matched '77.0 hz' as a suffix-form
    # break token, leaving '7.0', which fails the plausibility check. Those
    # pitches then had no outcome and dropped out of every analysis.
    m = re.match(r"^\s*(\d{2,3}(?:\.\d+)?)", s)
    if m:
        v = float(m.group(1))
        if 40 <= v <= 110:                       # plausible mph
            out["velo_mph"] = v
        s = s[m.end():]
    m = re.search(r"\+\s*(\d{3,5})", s)          # spin, e.g. +1607
    if m:
        out["spin_rpm"] = float(m.group(1))
        s = s[:m.start()] + " " + s[m.end():]
    # Break tokens. In every marker captured the number is written ADJACENT to
    # its unit, on one side or the other: 'hz18.9' or '-11.6hz'. Requiring
    # adjacency is what tells those two forms apart. Allowing a space made the
    # prefix pattern reach across the gap in '71.9 -11.6hz 0ivb' and capture
    # the 0 of '0ivb' as the horizontal break, discarding the real -11.6.
    for key, unit in (("hz_break", "hz"), ("ivb", "ivb")):
        for p in (rf"{unit}(-?\d+(?:\.\d+)?)", rf"(-?\d+(?:\.\d+)?){unit}"):
            m = re.search(p, s, re.I)
            if m:
                out[key] = float(m.group(1))
                s = s[:m.start()] + " " + s[m.end():]
                break
    return out or None


# ------------------------------------------------------------------- features
def to_n(adc, ch):
    a = np.clip(np.asarray(adc, float), 0, ADC_MAX - 1)
    return CAL[ch] * a / (ADC_MAX - a)


def finger_frames(d, pitch):
    """Force in newtons keyed by finger, for the grip in force."""
    amap = PITCH_MAPS[pitch]
    return {amap[c]: to_n(d[c].values, c) for c in CH if amap[c]}


def find_events(t, load):
    hot = np.where(load > MIN_FINGER_N * MIN_FINGERS)[0]
    if not len(hot):
        return []
    splits = np.where(np.diff(t[hot]) > EVENT_GAP_MS)[0]
    return [g for g in np.split(hot, splits + 1)
            if len(g) >= 20 and (t[g[-1]] - t[g[0]]) <= MAX_EVENT_MS]


def release_metrics(t, f):
    peak = float(f.max())
    if peak <= 0:
        return None
    pi = int(f.argmax())
    above = np.where(f[pi:] > REL_FRAC * peak)[0]
    if not len(above):
        return None
    ri = pi + int(above[-1])
    win = (t >= t[ri] - REL_WINDOW_MS) & (t <= t[ri])
    return dict(peak_N=peak, t_peak=float(t[pi]), t_rel=float(t[ri]),
                F_rel=float(f[win].mean()) if win.any() else float(f[ri]))


def extract(pid, path):
    d = pd.read_csv(path, low_memory=False)
    t_all = d.ball_t_ms.values.astype(float)

    # ---- tags. Effort precedence: explicit prefix > active state marker >
    # DEFAULT_EFFORT_PCT. Only an 'effort=NN' state marker moves the running
    # state; an 'NN%' prefix labels its own pitch and nothing after it.
    tags, state_effort = [], np.nan
    mk = d.marker.astype(str)
    for idx in np.where((mk.notna()) & (mk.str.strip() != "") & (mk != "nan"))[0]:
        raw = mk.iloc[idx]
        st = STATE_RE.match(raw.strip())
        if st:
            if st.group(1).lower() == "effort":
                state_effort = float(re.sub(r"[^\d.]", "", st.group(2)) or "nan")
            continue
        p = parse_tag(raw)
        if p:
            p.setdefault("warmup", False)
            if p["warmup"]:
                p["effort_pct"], p["effort_source"] = np.nan, "warmup"
            elif "effort_pct" not in p:
                if np.isfinite(state_effort):
                    p["effort_pct"] = state_effort
                    p["effort_source"] = "state_marker"
                else:
                    p["effort_pct"] = DEFAULT_EFFORT_PCT
                    p["effort_source"] = "default_max"
            p["t_tag"] = t_all[idx]
            p["raw_tag"] = raw
            tags.append(p)

    # ---- events, per grip block so the finger map is right
    rows, traces = [], []
    for pitch, blk in d.groupby("pitch_type", sort=False):
        if pitch not in PITCH_MAPS:
            continue
        t = blk.ball_t_ms.values.astype(float)
        ff = finger_frames(blk, pitch)
        load = np.sum([np.clip(v, 0, None) for v in ff.values()], axis=0)
        for g in find_events(t, load):
            act = sum(1 for v in ff.values() if v[g].max() >= MIN_FINGER_N)
            if act < MIN_FINGERS:
                continue
            r = dict(pitcher=pid, pitch_type=pitch,
                     t_start=float(t[g[0]]), t_end=float(t[g[-1]]),
                     n_samples=len(g))
            rel = {}
            for finger, v in ff.items():
                seg, tt = v[g], t[g]
                m = release_metrics(tt, seg)
                if not m:
                    continue
                rel[finger] = m
                dur = np.diff(tt)
                r[f"{finger}_peak_N"] = m["peak_N"]
                r[f"{finger}_F_rel_N"] = m["F_rel"]
                r[f"{finger}_t_rel"] = m["t_rel"]
                r[f"{finger}_impulse_Ns"] = float(np.sum(seg[:-1] * dur) / 1000.0)
                rise = seg[:int(seg.argmax()) + 1]
                if len(rise) > 3:
                    dv = np.diff(rise) / (np.diff(tt[:len(rise)]) / 1000.0)
                    r[f"{finger}_RFD_Ns"] = float(np.nanmax(dv))
            if len(rel) < MIN_FINGERS:
                continue
            # release ordering and inter-finger balance
            if "thumb" in rel:
                fing = [rel[f]["t_rel"] for f in ("pointer", "middle") if f in rel]
                if fing:
                    r["thumb_lead_ms"] = float(min(fing) - rel["thumb"]["t_rel"])
            if "pointer" in rel and "middle" in rel:
                r["pointer_middle_gap_ms"] = float(
                    rel["middle"]["t_rel"] - rel["pointer"]["t_rel"])
            peaks = np.array([rel[f]["peak_N"] for f in rel])
            r["total_peak_N"] = float(peaks.sum())
            r["CV_peak"] = float(peaks.std(ddof=1) / peaks.mean()) if len(peaks) > 1 else np.nan
            for f in rel:
                r[f"{f}_share"] = float(rel[f]["peak_N"] / peaks.sum())

            # Combined driving-finger channel. The ball is propelled by the
            # index and middle fingers acting together -- they are the pair the
            # ball rolls off, and their summed normal force is what opposes the
            # thumb. Testing the index alone measures an arbitrary half of that
            # force and discards the rest, so the sum is carried as a feature in
            # its own right and the thumb-to-finger ratio with it.
            if "pointer" in rel and "middle" in rel:
                for src, dst in (("peak_N", "finger_peak_N"),
                                 ("F_rel_N", "finger_F_rel_N"),
                                 ("impulse_Ns", "finger_impulse_Ns"),
                                 ("RFD_Ns", "finger_RFD_Ns")):
                    a, b = r.get(f"pointer_{src}"), r.get(f"middle_{src}")
                    if a is not None and b is not None:
                        r[dst] = float(a) + float(b)
                if "thumb" in rel and r.get("finger_peak_N"):
                    r["thumb_finger_ratio"] = float(
                        r["thumb_peak_N"] / r["finger_peak_N"])
            rows.append(r)
            traces.append((pid, pitch, blk.iloc[g].copy()))

    ev = pd.DataFrame(rows).sort_values("t_start").reset_index(drop=True)

    # ---- attach each tag to the nearest preceding unclaimed event
    for c in ("velo_mph", "spin_rpm", "hz_break", "ivb", "effort_pct"):
        ev[c] = np.nan
    for c in ("raw_tag", "effort_source"):
        ev[c] = None
    ev["warmup"] = False          # bool from the start; pandas 3 will not
    used = set()                  # coerce a bool into a float column
    for tg in sorted(tags, key=lambda x: x["t_tag"]):
        cand = ev[(ev.t_end <= tg["t_tag"]) &
                  (tg["t_tag"] - ev.t_end < MATCH_WINDOW_MS)]
        cand = cand[~cand.index.isin(used)]
        if not len(cand):
            continue
        i = cand.index[-1]
        used.add(i)
        for k, v in tg.items():
            if k != "t_tag":
                ev.loc[i, k] = v
    ev["warmup"] = ev.warmup.fillna(False).astype(bool)
    ev["paired"] = ev.velo_mph.notna()
    # An event enters an inferential model only if it carries a tagged outcome
    # and was thrown inside the effort protocol. Warm-ups stay in the counts.
    ev["analyzable"] = ev.paired & ~ev.warmup
    return ev, traces


def modelset(ev, pitch_type=None):
    """The rows every inferential model runs on: paired, non-warm-up."""
    d = ev[ev.analyzable]
    return d if pitch_type is None else d[d.pitch_type == pitch_type]


# ---------------------------------------------------------------- statistics
def fisher_ci(r, n, alpha=0.05):
    if not np.isfinite(r) or n < 4 or abs(r) >= 1:
        return (np.nan, np.nan)
    z, se = np.arctanh(r), 1 / np.sqrt(n - 3)
    from scipy.stats import norm
    c = norm.ppf(1 - alpha / 2) * se
    return tuple(np.tanh([z - c, z + c]))


def corr_p(x, y):
    from scipy.stats import pearsonr
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 4:
        return np.nan, np.nan, int(m.sum())
    r, p = pearsonr(x[m], y[m])
    return r, p, int(m.sum())


def within_centered(df, cols, by="pitcher"):
    out = df.copy()
    for c in cols:
        if c in out:
            out[c + "_c"] = out[c] - out.groupby(by)[c].transform("mean")
    return out


# -------------------------------------------------------------------- report
def main():
    allev, alltr = [], []
    for pid, fn in SESSIONS.items():
        ev, tr = extract(pid, os.path.join(DATA, fn))
        allev.append(ev)
        alltr += tr
        print(f"{pid}: {len(ev)} events, {int(ev.paired.sum())} paired")
    ev = pd.concat(allev, ignore_index=True)
    ev.to_csv("results/per_pitch_features.csv", index=False)

    L = []
    A = L.append
    A("# Data Analysis and Results — computed output\n")
    A(f"Generated from {len(SESSIONS)} sessions. "
      f"{len(ev)} pitch events detected, {int(ev.paired.sum())} paired with an outcome, "
      f"{int(ev.warmup.sum())} of those warm-ups, "
      f"{int(ev.analyzable.sum())} analyzable. "
      f"Force at release is the mean over the final {REL_WINDOW_MS} ms of contact.\n")

    # ---- Table 8: participants
    try:
        dem = pd.read_csv(PARTICIPANTS, comment="#").set_index("pitcher")
    except Exception:
        dem = pd.DataFrame()
    A("\n## Table 8. Participant characteristics and pitch counts\n")
    A("| Pitcher | Age (y) | Height (cm) | Mass (kg) | Fastballs | Curveballs "
      "| Warm-ups | Paired | Unpaired | Analyzable |")
    A("|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for pid, g in ev.groupby("pitcher"):
        r = dem.loc[pid] if pid in dem.index else None
        age = f"{int(r.age_y)}" if r is not None else "—"
        ht = f"{r.height_cm:.1f}" if r is not None else "—"
        ms = f"{r.mass_kg:.1f}" if r is not None else "—"
        A(f"| {pid} | {age} | {ht} | {ms} | {(g.pitch_type=='fastball').sum()} | "
          f"{(g.pitch_type=='curveball').sum()} | {int(g.warmup.sum())} | "
          f"{int(g.paired.sum())} | {int((~g.paired).sum())} | "
          f"{int(g.analyzable.sum())} |")
    if len(dem):
        A(f"| **All / mean** | {dem.age_y.mean():.1f} | {dem.height_cm.mean():.1f} | "
          f"{dem.mass_kg.mean():.1f} | {(ev.pitch_type=='fastball').sum()} | "
          f"{(ev.pitch_type=='curveball').sum()} | {int(ev.warmup.sum())} | "
          f"{int(ev.paired.sum())} | {int((~ev.paired).sum())} | "
          f"{int(ev.analyzable.sum())} |")
    A("\nAnthropometrics are reported to describe the sample. With three pitchers "
      "they cannot enter any model: a between-pitcher covariate is perfectly "
      "confounded with pitcher identity at n = 3.\n")

    # ---- effort labelling audit
    A("\n## Effort labelling audit\n")
    A("Every analyzable pitch carries an effort label from exactly one source. "
      "An explicit `NN%` prefix outranks an active `effort=NN` state marker, "
      "which outranks the maximum-effort default. Effort is never inferred "
      "from velocity.\n")
    A("| Pitcher | explicit prefix | state marker | default (max) | warm-up (excluded) |")
    A("|:--|--:|--:|--:|--:|")
    for pid, g in ev[ev.paired].groupby("pitcher"):
        s = g.effort_source.value_counts()
        A(f"| {pid} | {s.get('explicit_prefix',0)} | {s.get('state_marker',0)} | "
          f"{s.get('default_max',0)} | {s.get('warmup',0)} |")
    s = ev[ev.paired].effort_source.value_counts()
    A(f"| **All** | {s.get('explicit_prefix',0)} | {s.get('state_marker',0)} | "
      f"{s.get('default_max',0)} | {s.get('warmup',0)} |")
    A("\n| Pitcher | commanded effort levels present (analyzable) |")
    A("|:--|:--|")
    for pid, g in modelset(ev).groupby("pitcher"):
        lv = sorted(g.effort_pct.dropna().unique())
        A(f"| {pid} | " + ", ".join(f"{v:.0f} % (n = {int((g.effort_pct==v).sum())})"
                                    for v in lv) + " |")

    # ---- descriptives
    A("\n## Descriptive statistics — peak and release force by finger\n")
    A("| Pitcher | Pitch | Finger | n | peak mean±SD (N) | F_rel mean±SD (N) |")
    A("|:--|:--|:--|--:|:--|:--|")
    for (pid, pt), g in ev.groupby(["pitcher", "pitch_type"]):
        for f in FINGERS:
            pk, fr = f"{f}_peak_N", f"{f}_F_rel_N"
            if pk in g and g[pk].notna().sum():
                A(f"| {pid} | {pt} | {f} | {g[pk].notna().sum()} | "
                  f"{g[pk].mean():.1f} ± {g[pk].std():.1f} | "
                  f"{g[fr].mean():.1f} ± {g[fr].std():.1f} |")

    # ---- release ordering
    A("\n## Release ordering\n")
    d = ev[ev.thumb_lead_ms.notna()]
    A(f"Thumb lead over the first finger to release, n = {len(d)} pitches.\n")
    A("| Group | n | mean (ms) | SD | median | % thumb first | % above 4.17 ms floor |")
    A("|:--|--:|--:|--:|--:|--:|--:|")
    for lab, g in [("ALL", d)] + [(f"{p} {t}", x) for (p, t), x in
                                  d.groupby(["pitcher", "pitch_type"])]:
        v = g.thumb_lead_ms.values
        if len(v):
            A(f"| {lab} | {len(v)} | {v.mean():.1f} | {v.std():.1f} | "
              f"{np.median(v):.1f} | {100*(v>0).mean():.0f}% | {100*(v>4.17).mean():.0f}% |")
    from scipy.stats import wilcoxon, ttest_1samp
    v = d.thumb_lead_ms.values
    if len(v) > 5:
        try:
            w, pw = wilcoxon(v)
            t_, pt_ = ttest_1samp(v, 0)
            A(f"\nOne-sample tests against zero lead: t = {t_:.2f}, p = {pt_:.2g}; "
              f"Wilcoxon W = {w:.0f}, p = {pw:.2g}.\n")
        except Exception:
            pass
    g2 = ev[ev.pointer_middle_gap_ms.notna()].pointer_middle_gap_ms.values
    if len(g2):
        A(f"Pointer-to-middle gap: mean {g2.mean():.2f} ms, SD {g2.std():.2f}, "
          f"|gap| < 4.17 ms in {100*(np.abs(g2)<4.17).mean():.0f}% of pitches "
          f"(n = {len(g2)}). Sign split: {100*(g2>0).mean():.0f}% middle last.\n")

    # ---- primary + secondary hypotheses
    A("\n## Table 9. Grip features vs release velocity (fastballs)\n")
    A("Within-pitcher centred, pooled. Per-pitcher r shown for consistency.\n")
    A("| Feature | pooled r | 95% CI | p | n | P1 r (n) | P2 r (n) | P3 r (n) |")
    A("|:--|--:|:--|--:|--:|:--|:--|:--|")
    fb = modelset(ev, "fastball").copy()
    feats = [f"{f}_{k}" for f in FINGERS
             for k in ("F_rel_N", "peak_N", "RFD_Ns", "impulse_Ns")]
    feats += ["total_peak_N", "CV_peak", "thumb_lead_ms"]
    fb = within_centered(fb, feats + ["velo_mph"])
    for c in feats:
        cc = c + "_c"
        if cc not in fb or fb[cc].notna().sum() < 6:
            continue
        r, p, n = corr_p(fb[cc].values, fb["velo_mph_c"].values)
        lo, hi = fisher_ci(r, n)
        per = []
        for pid in ("P1", "P2", "P3"):
            g = fb[fb.pitcher == pid]
            if c in g and g[c].notna().sum() >= 4:
                rr, pp, nn = corr_p(g[c].values, g.velo_mph.values)
                per.append(f"{rr:.2f} ({nn})")
            else:
                per.append("—")
        A(f"| {c} | {r:.3f} | [{lo:.2f}, {hi:.2f}] | {p:.3g} | {n} | " + " | ".join(per) + " |")

    # ---- fastball vs curveball
    A("\n## Fastball vs curveball grip contrast (within pitcher, paired)\n")
    A("| Pitcher | Feature | FB mean | CB mean | diff | t | p |")
    A("|:--|:--|--:|--:|--:|--:|--:|")
    from scipy.stats import ttest_ind
    for pid, g in ev.groupby("pitcher"):
        fbg, cbg = g[g.pitch_type == "fastball"], g[g.pitch_type == "curveball"]
        if len(cbg) < 3:
            continue
        for c in ["thumb_lead_ms", "total_peak_N", "CV_peak",
                  "thumb_share", "pointer_share", "middle_share"]:
            if c in g and fbg[c].notna().sum() >= 3 and cbg[c].notna().sum() >= 3:
                a, b = fbg[c].dropna(), cbg[c].dropna()
                t_, p_ = ttest_ind(a, b, equal_var=False)
                A(f"| {pid} | {c} | {a.mean():.2f} | {b.mean():.2f} | "
                  f"{a.mean()-b.mean():+.2f} | {t_:.2f} | {p_:.3g} |")

    # ---- other outcomes where available
    for oc, lab in (("spin_rpm", "spin rate"), ("ivb", "induced vertical break"),
                    ("hz_break", "horizontal break")):
        sub = ev[ev[oc].notna()]
        if len(sub) >= 6:
            A(f"\n## Grip features vs {lab} (n = {len(sub)})\n")
            A("| Feature | r | p | n |")
            A("|:--|--:|--:|--:|")
            s = within_centered(sub, feats + [oc])
            for c in feats:
                cc = c + "_c"
                if cc in s and s[cc].notna().sum() >= 6:
                    r, p, n = corr_p(s[cc].values, s[oc + "_c"].values)
                    if np.isfinite(r):
                        A(f"| {c} | {r:.3f} | {p:.3g} | {n} |")

    open("results/stats_report.md", "w", encoding="utf-8").write("\n".join(L))

    # Export one representative fastball for the trace figure. Figures are drawn
    # by make_thesis_figures.py from saved tables, never from state that only
    # exists inside this run, so every figure is reproducible on its own.
    pick = None
    for (pid, pitch, blk) in alltr:
        if pitch == "fastball" and len(blk) > 200:
            pick = (pid, blk)
            break
    if pick is not None:
        pid, blk = pick
        out = blk[["ball_t_ms"]].copy()
        for finger, v in finger_frames(blk, "fastball").items():
            out[finger] = v
        out["pitcher"] = pid
        out["t_rel_ms"] = out.ball_t_ms - out.ball_t_ms.iloc[0]
        out.to_csv("results/example_trace.csv", index=False)
        print(f"wrote results/example_trace.csv ({pid}, {len(out)} samples)")
    print("wrote results/per_pitch_features.csv and results/stats_report.md")


if __name__ == "__main__":
    main()
