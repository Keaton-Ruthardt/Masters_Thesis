"""Force-vs-time traces for each finger across a pitch.

Reads a ble_logger CSV, converts raw ADC to newtons with the v3 calibration,
finds the pitch events, and plots one panel per pitch.

    python plot_pitch_traces.py newballtest.csv
    python plot_pitch_traces.py p1_ff_block1.csv --pitch fastball --out figs/p1.png

Single-theme (light) on purpose: these are print figures for the thesis.
"""
import argparse
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CHANNELS = ("s1", "s2", "s3", "s4")

# analysis/calibration/calfactors_v3.csv — channel is the pin, sensor is fixed to it
CAL = {"s1": 119.0, "s2": 129.0, "s3": 148.0, "s4": 157.0}
SENSOR = {"s1": "BK", "s2": "RM", "s3": "KA", "s4": "CG"}

# Which finger sits on which sensor, per grip (mirrors ble_logger.PITCH_MAPS)
PITCH_MAPS = {
    "fastball":  {"s1": "pointer", "s2": "middle", "s3": "thumb",   "s4": None},
    "curveball": {"s1": "thumb",   "s2": None,     "s3": "pointer", "s4": "middle"},
    "slider":    {"s1": "thumb",   "s2": None,     "s3": "pointer", "s4": "middle"},
}

# Categorical hues, fixed order by finger — validated (worst adjacent pair
# ΔE 20.2 deutan / 10.5 tritan, all six checks pass on a #fcfcfb surface).
FINGER_COLOR = {"pointer": "#1f6fd0", "middle": "#d2600f", "thumb": "#b02a8a"}

SURFACE = "#fcfcfb"
INK, INK2, MUTED, GRID = "#1a1d21", "#4a4f56", "#7c7f86", "#e3e2dd"

ADC_MAX = 4095
PEAK_MIN_N = 3.0      # a pitch has to reach this to count
GAP_MS = 400          # samples further apart than this are separate pitches

# Release metrics. Force AT release is zero by definition, so what we report is
# the force over the final window before contact is lost, and the order in which
# fingers let go. At ~119 Hz one sample is ~8.4 ms and the release transition is
# only 3-4 samples, so a per-pitch order gap below RESOLVE_MS is not resolvable —
# aggregate those across pitches instead of reading them individually.
REL_FRAC = 0.10       # contact considered lost below this fraction of the peak
REL_WINDOW_MS = 25    # window before release that F_release averages over
RESOLVE_SAMPLES = 2   # ordering gaps below this many samples are noise
MIN_ACTIVE_N = 2.0    # a finger counts as "on the ball" above this
MIN_ACTIVE_FINGERS = 2   # a real pitch loads at least this many fingers


def to_newtons(adc, ch):
    a = np.clip(np.asarray(adc, dtype=float), 0, ADC_MAX - 1)
    return CAL[ch] * a / (ADC_MAX - a)


def find_events(t_ms, total_n):
    """Contiguous runs above half the run's own peak, split on time gaps."""
    hot = np.where(total_n > max(PEAK_MIN_N, 0.25 * total_n.max()))[0]
    if len(hot) == 0:
        return []
    splits = np.where(np.diff(t_ms[hot]) > GAP_MS)[0]
    groups = np.split(hot, splits + 1)
    return [g for g in groups if len(g) >= 3]


def release_metrics(t, n):
    """When contact is lost, and how hard the finger was pressing just before.

    Returns (t_release, F_release, n_samples_on_falling_edge) or None.
    """
    peak = float(np.max(n))
    if peak <= 0:
        return None
    pi = int(np.argmax(n))
    above = np.where(n[pi:] > REL_FRAC * peak)[0]
    if len(above) == 0:
        return None
    ri = pi + int(above[-1])
    t_rel = float(t[ri])
    win = (t >= t_rel - REL_WINDOW_MS) & (t <= t_rel)
    f_rel = float(np.mean(n[win])) if win.any() else float(n[ri])
    edge = int(np.sum((t >= t_rel - REL_WINDOW_MS) & (t <= t_rel)))
    return t_rel, f_rel, edge


def plot_pitch(ax, d, idx, pitch, title):
    t = d["ball_t_ms"].values[idx]
    t = t - t[0]
    amap = PITCH_MAPS[pitch]

    peaks, rels = {}, {}
    for ch in CHANNELS:
        finger = amap[ch]
        if finger is None:
            continue
        n = to_newtons(d[ch].values[idx], ch)
        ax.plot(t, n, lw=2.0, color=FINGER_COLOR[finger], solid_capstyle="round",
                label=f"{finger}  ({SENSOR[ch]})", zorder=3)
        peaks[finger] = (t[int(np.argmax(n))], float(np.max(n)))
        r = release_metrics(t, n)
        if r:
            rels[finger] = r

    # selective direct labels: peak value only, in ink not series colour
    for finger, (pt, pv) in peaks.items():
        ax.plot([pt], [pv], "o", ms=8, color=FINGER_COLOR[finger],
                mec=SURFACE, mew=2, zorder=4)
        ax.annotate(f"{pv:.1f} N", (pt, pv), textcoords="offset points",
                    xytext=(0, 11), ha="center", fontsize=9.5, color=INK2)

    # release: hollow marker on each curve, one shared label for the last finger
    if rels:
        last = max(rels, key=lambda f: rels[f][0])
        for finger, (tr, fr, _) in rels.items():
            ax.plot([tr], [fr], "o", ms=8, mfc=SURFACE, mew=2,
                    mec=FINGER_COLOR[finger], zorder=4)
        tr_last = rels[last][0]
        ax.axvline(tr_last, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=1)
        ax.annotate(f"release — {last} last",
                    (tr_last, ax.get_ylim()[1]), textcoords="offset points",
                    xytext=(6, -12), ha="left", fontsize=9.5, color=MUTED)

    ax.set_title(title, fontsize=12, color=INK, loc="left", pad=10)
    ax.set_xlabel("time through the pitch  (ms)", fontsize=10, color=INK2)
    ax.set_ylabel("grip force  (N)", fontsize=10, color=INK2)
    ax.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9.5)
    ax.set_facecolor(SURFACE)
    leg = ax.legend(frameon=False, fontsize=10, loc="upper left")
    for txt in leg.get_texts():
        txt.set_color(INK2)


def main():
    p = argparse.ArgumentParser(description="Plot per-finger force traces for each pitch")
    p.add_argument("csv")
    p.add_argument("--pitch", choices=sorted(PITCH_MAPS),
                   help="override the pitch_type column")
    p.add_argument("--out", help="output PNG (default: <csv stem>_traces.png)")
    p.add_argument("--max-pitches", type=int, default=6)
    args = p.parse_args()

    d = pd.read_csv(args.csv)
    pitch = args.pitch or (str(d["pitch_type"].dropna().iloc[0])
                           if "pitch_type" in d and d["pitch_type"].notna().any()
                           else "fastball")

    amap = PITCH_MAPS[pitch]
    t_all = d["ball_t_ms"].values
    dt = float(np.median(np.diff(t_all)))          # 8.4 ms @120 Hz, 2.08 @480
    resolve_ms = RESOLVE_SAMPLES * dt
    pad = int(round(200.0 / dt))                   # ~200 ms of context each side

    total = sum(to_newtons(d[ch].values, ch) for ch in CHANNELS if amap[ch])
    events = find_events(t_all, total)

    # A press on one pad is not a pitch — require several fingers loaded.
    kept = []
    for g in events:
        active = sum(1 for ch in CHANNELS if amap[ch]
                     and to_newtons(d[ch].values[g], ch).max() >= MIN_ACTIVE_N)
        if active >= MIN_ACTIVE_FINGERS:
            kept.append(g)
    if not kept:
        print(f"No pitch events found in {args.csv} "
              f"(peak {total.max():.1f} N; needs >={MIN_ACTIVE_FINGERS} fingers "
              f">={MIN_ACTIVE_N} N)")
        return

    print(f"sample interval {dt:.2f} ms ({1000/dt:.0f} Hz) — "
          f"ordering resolvable above {resolve_ms:.1f} ms")
    events = [np.arange(max(0, g[0] - pad), min(len(d), g[-1] + pad)) for g in kept]
    events = sorted(events, key=lambda g: -total[g].max())[:args.max_pitches]

    n = len(events)
    cols = min(2, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(7.0 * cols, 4.4 * rows),
                             squeeze=False, facecolor="white")
    for k, idx in enumerate(events):
        ax = axes[k // cols][k % cols]
        plot_pitch(ax, d, idx, pitch, f"Pitch {k + 1} — {pitch}")
    for k in range(n, rows * cols):
        axes[k // cols][k % cols].axis("off")

    fig.tight_layout()
    out = args.out or os.path.splitext(args.csv)[0] + "_traces.png"
    fig.savefig(out, dpi=200, facecolor="white")
    print(f"{n} pitch(es) -> {out}\n")
    print(f"{'pitch':>5} {'finger':>8} {'peak_N':>7} {'F_rel_N':>8} "
          f"{'t_rel_ms':>9} {'edge_n':>7}")
    for k, idx in enumerate(events):
        t = d["ball_t_ms"].values[idx]
        t = t - t[0]
        rows = {}
        for ch in CHANNELS:
            finger = amap[ch]
            if finger is None:
                continue
            nn = to_newtons(d[ch].values[idx], ch)
            r = release_metrics(t, nn)
            rows[finger] = (float(nn.max()), r)
            if r:
                print(f"{k+1:>5} {finger:>8} {nn.max():7.1f} {r[1]:8.1f} "
                      f"{r[0]:9.0f} {r[2]:7d}")
        # release ordering, flagged when the gap is below what 119 Hz can resolve
        got = {f: v[1][0] for f, v in rows.items() if v[1]}
        if len(got) >= 2:
            order = sorted(got, key=lambda f: got[f])
            gaps = [got[order[i + 1]] - got[order[i]] for i in range(len(order) - 1)]
            seq = "  <  ".join(order)
            flag = "" if all(g >= resolve_ms for g in gaps) else \
                   (f"   [gap {min(gaps):.1f} ms < {resolve_ms:.1f} ms "
                    f"— not resolvable, aggregate]")
            print(f"        release order: {seq}{flag}\n")


if __name__ == "__main__":
    main()
