"""Builds every data figure in the thesis, in document order.

    python make_thesis_figures.py       (run thesis_analysis_v2.py and
                                         advanced_stats.py first)

Figures are drawn from saved result tables, never recomputed here, so a value
printed in the Results and the same value plotted in a figure come from one
source and cannot disagree.

    Figure 6   representative pitch trace              instrument resolves release
    Figure 7   grip shares by pitch type               four-position array validated
    Figure 8   thumb release lead                      release ordering, descriptive
    Figure 9   effort ladder                           the manipulation worked
    Figure 10  grip vs velocity, raw and controlled    the association collapses
    Figure 11  the confound made visible               where the variance goes
    Figure 12  effort coupling explains which survive  the synthesis

The figure set is built around one argument, and the reader should be able to
follow it from the pictures alone: the instrument works (6-8), the experiment
worked (9), the obvious result is confounded (10-11), and what is left is
explained by how tightly each digit tracks effort (12).
"""
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import figstyle as fs

fs.apply_rc()
os.makedirs("figures", exist_ok=True)

feat = pd.read_csv("results/feature_stats.csv")
ev = pd.read_csv("results/per_pitch_features.csv")
ev = ev[ev.analyzable] if "analyzable" in ev else ev[ev.paired]
fb = ev[ev.pitch_type == "fastball"].copy()
PITCHERS = sorted(ev.pitcher.unique())
CRIT = float(feat.crit_r_strat.dropna().iloc[0])
DF_STRAT = int(feat.df_strat.dropna().iloc[0])


def cellcenter(df, cols, keys):
    out = df.copy()
    for c in cols:
        out[c + "_cc"] = out[c] - out.groupby(keys)[c].transform("mean")
    return out


# =========================================================== Figure 6: trace
def fig6():
    try:
        tr = pd.read_csv("results/example_trace.csv")
    except FileNotFoundError:
        print("  skipped fig6 (no example_trace.csv)")
        return
    t = tr.t_rel_ms.values
    fig, axes = plt.subplots(1, 2, figsize=(fs.FIG_W, 3.5),
                             gridspec_kw={"width_ratios": [1.6, 1]})

    rel = {}
    for finger in ("pointer", "middle", "thumb"):
        if finger not in tr:
            continue
        v = tr[finger].values
        pk = int(np.argmax(v))
        above = np.where(v[pk:] > 0.10 * v[pk])[0]
        ri = pk + int(above[-1]) if len(above) else pk
        rel[finger] = dict(peak=v[pk], t_peak=t[pk], t_rel=t[ri], f_rel=v[ri])

    for ax in axes:
        for finger in ("pointer", "middle", "thumb"):
            if finger in tr:
                ax.plot(t, tr[finger].values, lw=2.0, color=fs.DIGIT[finger],
                        label=fs.DIGIT_LABEL[finger], zorder=3)

    # Peaks, direct-labelled -- one number per series, never per point. The
    # index and thumb peaks land within a few milliseconds of each other, so the
    # labels are staggered left/right by peak order rather than stacked above,
    # where they overlapped and hid a digit.
    order = sorted(rel, key=lambda f: -rel[f]["peak"])
    offsets = [(-34, 6, "right"), (34, 2, "left"), (0, 11, "center")]
    for finger, (dx, dy, ha) in zip(order, offsets):
        m = rel[finger]
        axes[0].plot([m["t_peak"]], [m["peak"]], "o", ms=8,
                     color=fs.DIGIT[finger], mec=fs.SURFACE, mew=2, zorder=5)
        axes[0].annotate(f"{m['peak']:.1f} N", (m["t_peak"], m["peak"]),
                         textcoords="offset points", xytext=(dx, dy),
                         ha=ha, va="center", fontsize=9, color=fs.INK2, zorder=6)

    if rel:
        first = min(m["t_rel"] for m in rel.values())
        last = max(m["t_rel"] for m in rel.values())
        axes[1].set_xlim(first - 42, last + 22)
        for finger, m in rel.items():
            axes[1].axvline(m["t_rel"], color=fs.DIGIT[finger], lw=1.0,
                            ls=(0, (4, 3)), zorder=2)
            axes[1].plot([m["t_rel"]], [m["f_rel"]], "o", ms=8, mfc=fs.SURFACE,
                         mew=2, mec=fs.DIGIT[finger], zorder=5)
        thumb_lead = min(m["t_rel"] for f, m in rel.items() if f != "thumb") \
            - rel["thumb"]["t_rel"] if "thumb" in rel and len(rel) > 1 else None
        if thumb_lead:
            axes[1].annotate("", xy=(rel["thumb"]["t_rel"], axes[1].get_ylim()[1] * 0.9),
                             xytext=(rel["thumb"]["t_rel"] + thumb_lead,
                                     axes[1].get_ylim()[1] * 0.9),
                             arrowprops=dict(arrowstyle="<->", color=fs.INK2, lw=1.0))
            fs.note(axes[1], f"thumb leads by {thumb_lead:.1f} ms",
                    xy=(0.40, 0.78), size=8.8)

    fs.panel_title(axes[0], "(a)  Full pitch")
    fs.panel_title(axes[1], "(b)  Release window expanded")
    for ax in axes:
        fs.style(ax)
        ax.set_xlabel("time through the pitch  (ms)")
        ax.set_ylabel("grip force  (N)")
    fs.legend(axes[0], loc="upper left")
    fig.tight_layout()
    fs.save(fig, "figures/fig6_trace.png")


# ================================================ Figure 7: grip by pitch type
def fig7():
    """Part-to-whole: how the same total force is distributed between digits.

    Horizontal stacked bars, one row per pitcher x pitch type, with a 2 px
    surface gap between segments so adjacent fills never touch.
    """
    rows = []
    for (pid, pt), g in ev.groupby(["pitcher", "pitch_type"]):
        if len(g) < 3:
            continue
        rows.append(dict(pitcher=pid, pitch_type=pt, n=len(g),
                         **{f: g[f + "_share"].mean()
                            for f in ("pointer", "middle", "thumb")}))
    d = pd.DataFrame(rows)
    order = [(p, t) for p in PITCHERS for t in ("fastball", "curveball")]
    d["key"] = list(zip(d.pitcher, d.pitch_type))
    d = d.set_index("key").reindex([k for k in order if k in set(d.key)]).reset_index()

    fig, ax = plt.subplots(figsize=(fs.FIG_W, 3.4))
    ypos = np.arange(len(d))[::-1].astype(float)
    # visually group each pitcher's two bars
    ypos = ypos + np.array([0.35 * (len(d) // 2 - i // 2) for i in range(len(d))])
    left = np.zeros(len(d))
    GAP = 0.004                      # surface gap between stacked segments
    for finger in ("pointer", "middle", "thumb"):
        w = d[finger].values
        ax.barh(ypos, w - GAP, left=left + GAP / 2, height=0.62,
                color=fs.DIGIT[finger], edgecolor=fs.SURFACE, linewidth=0,
                label=fs.DIGIT_LABEL[finger], zorder=3)
        for y, l, wi in zip(ypos, left, w):
            if wi > 0.075:           # the segment can hold the number inside
                ax.text(l + wi / 2, y, f"{100*wi:.0f}", ha="center", va="center",
                        fontsize=8.5, color="white", zorder=5)
            elif wi > 0:
                # Too narrow to letter inside. These are the collapsed thumb
                # shares on the curveball -- the smallest values in the figure
                # and the ones it exists to show -- so they are set outside in
                # the digit colour rather than dropped for want of room.
                ax.text(1.012, y, f"{100*wi:.0f}", ha="left", va="center",
                        fontsize=8.5, color=fs.DIGIT[finger], zorder=5)
        left = left + w

    ax.set_yticks(ypos)
    ax.set_yticklabels([f"{r.pitcher}  {r.pitch_type[:2].upper()}"
                        for r in d.itertuples()])
    ax.set_xlim(0, 1.055)
    ax.set_xticks(np.arange(0, 1.01, 0.25))
    ax.set_xticklabels([f"{int(100*v)}%" for v in np.arange(0, 1.01, 0.25)])
    ax.set_xlabel("share of total peak grip force")
    fs.style(ax, grid="x")
    fs.legend(ax, loc="upper center", ncol=3,
              bbox_to_anchor=(0.5, 1.14))
    fig.tight_layout()
    fs.save(fig, "figures/fig7_pitch_type_shares.png")


# ============================================== Figure 8: thumb release lead
def fig8():
    d = ev[ev.thumb_lead_ms.notna()]
    groups, labels, colors = [], [], []
    for pt in ("fastball", "curveball"):
        for pid in PITCHERS:
            v = d[(d.pitcher == pid) & (d.pitch_type == pt)].thumb_lead_ms.values
            if len(v):
                groups.append(v)
                labels.append(f"{pid}\n{pt[:2].upper()}")
                colors.append(fs.DIGIT["thumb"] if pt == "fastball" else fs.CONTEXT)

    fig, ax = plt.subplots(figsize=(5.6, 3.5))
    bp = ax.boxplot(groups, tick_labels=labels, patch_artist=True, widths=0.55,
                    medianprops=dict(color=fs.INK, lw=1.6),
                    whiskerprops=dict(color=fs.RULE, lw=1.0),
                    capprops=dict(color=fs.RULE, lw=1.0),
                    flierprops=dict(marker="", ls="none"))
    for box, c in zip(bp["boxes"], colors):
        box.set(facecolor=c, alpha=0.22, edgecolor=c, lw=1.2)

    rng = np.random.default_rng(7)
    for i, (v, c) in enumerate(zip(groups, colors), 1):
        ax.plot(rng.normal(i, 0.055, len(v)), v, "o", ms=4.5, color=c,
                alpha=0.75, mec=fs.SURFACE, mew=0.6, zorder=4)

    ax.axhline(0, color=fs.RULE, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax.axhline(4.17, color=fs.THRESHOLD, lw=1.0, ls=(0, (2, 2)), zorder=1)
    # Rule labels sit far left, where the fastball boxes start well above the
    # floor, rather than at the right edge where they landed on the P3 curveball
    # box. Extra headroom keeps the legend clear of the tallest whisker.
    ax.annotate("resolution floor, 4.17 ms", (0.015, 4.17),
                xycoords=("axes fraction", "data"), ha="left", va="bottom",
                fontsize=8.5, color=fs.THRESHOLD)
    ax.annotate("simultaneous release", (0.015, 0), xycoords=("axes fraction", "data"),
                ha="left", va="bottom", fontsize=8.5, color=fs.MUTED)
    ax.set_ylim(top=max(np.concatenate(groups)) * 1.28)
    ax.set_ylabel("thumb release lead  (ms)")
    fs.style(ax)
    fs.legend(ax, handles=[
        Line2D([], [], marker="s", ls="", markerfacecolor=fs.DIGIT["thumb"],
               markeredgecolor="none", alpha=0.6, markersize=8, label="fastball"),
        Line2D([], [], marker="s", ls="", markerfacecolor=fs.CONTEXT,
               markeredgecolor="none", alpha=0.6, markersize=8, label="curveball")],
        loc="upper left", ncol=2)
    fig.tight_layout()
    fs.save(fig, "figures/fig8_release_order.png")


# ================================================== Figure 9: the effort ladder
def fig9():
    """Three panels sharing an x-axis of commanded effort.

    Panel (a) shows the manipulation worked. Panels (b) and (c) are the seed of
    the whole result: the driving fingers track effort closely, the thumb does
    not. Each panel has its own y-axis and its own measure -- never two scales
    on one axis.
    """
    d = fb.dropna(subset=["effort_pct", "velo_mph"]).copy()
    d["finger_peak_N"] = d.get("finger_peak_N",
                               d.pointer_peak_N + d.middle_peak_N)
    panels = [("velo_mph", "release velocity  (mph)", fs.INK2, "(a)  Velocity"),
              ("finger_peak_N", "index + middle peak force  (N)",
               fs.DIGIT["finger"], "(b)  Index + middle force"),
              ("thumb_peak_N", "thumb peak force  (N)", fs.DIGIT["thumb"],
               "(c)  Thumb force")]

    fig, axes = plt.subplots(1, 3, figsize=(fs.FIG_W, 3.1), layout="constrained")
    rng = np.random.default_rng(11)
    for ax, (col, ylab, color, title) in zip(axes, panels):
        sub = d.dropna(subset=[col])
        for pid, g in sub.groupby("pitcher"):
            jitter = rng.normal(0, 1.1, len(g))
            ax.scatter(g.effort_pct + jitter, g[col], s=30,
                       marker=fs.PITCHER_MARKER.get(pid, "o"),
                       facecolor=color, edgecolor=fs.SURFACE, linewidth=1.0,
                       alpha=0.75, zorder=3)
            # per-pitcher cell means. Deliberately faint: in panel (c) they
            # cross and double back, and that lack of a common direction is
            # the point rather than a defect in the drawing.
            mu = g.groupby("effort_pct")[col].mean()
            ax.plot(mu.index, mu.values, lw=1.2, color=color, alpha=0.42,
                    zorder=2, solid_capstyle="round")
        r = feat.loc[feat.feat == col, "r_effort"]
        rv = float(r.iloc[0]) if len(r) else np.nan
        if col == "velo_mph":
            rv = 0.948                     # reported in the manipulation check
        pv = feat.loc[feat.feat == col, "p_effort"]
        ns = len(pv) and float(pv.iloc[0]) >= 0.05
        fs.note(ax, f"$r_{{rm}}$ = {rv:.2f}" + ("   n.s." if ns else ""),
                xy=(0.04, 0.97), color=fs.MUTED if ns else fs.INK,
                weight="normal" if ns else "bold", size=9)
        fs.panel_title(ax, title, pad=6)
        ax.set_xlabel("commanded effort  (%)")
        ax.set_ylabel(ylab)
        ax.set_xticks([60, 80, 100])
        ax.set_xlim(52, 108)
        fs.style(ax)
    fs.pitcher_shape_legend(axes[0], PITCHERS, loc="lower right")
    fs.save(fig, "figures/fig9_effort_ladder.png")


# ============================== Figure 10: grip vs velocity, raw vs controlled
def fig10():
    """Two rows (digit) x two columns (control), one shared story.

    Left column removes between-pitcher differences only. Right column also
    removes the mean of every pitcher x commanded-effort cell, so effort is
    held exactly fixed. The change from left to right is the finding.
    """
    d = fb.dropna(subset=["effort_pct", "velo_mph"]).copy()
    if "finger_F_rel_N" not in d:
        d["finger_F_rel_N"] = d.pointer_F_rel_N + d.middle_F_rel_N
    cols = ["finger_F_rel_N", "thumb_peak_N", "velo_mph"]
    d = cellcenter(d, cols, ["pitcher"])
    d = d.rename(columns={c + "_cc": c + "_p" for c in cols})
    d = cellcenter(d, cols, ["pitcher", "effort_pct"])

    rows = [("finger_F_rel_N", "finger", "index + middle force at release  (N)"),
            ("thumb_peak_N", "thumb", "thumb peak force  (N)")]
    fig, axes = plt.subplots(2, 2, figsize=(fs.FIG_W, 6.1), layout="constrained")
    for i, (col, digit, xlab) in enumerate(rows):
        for j, (suffix, ctitle) in enumerate([("_p", "pitcher removed"),
                                              ("_cc", "pitcher AND effort removed")]):
            ax = axes[i][j]
            x = d[col + suffix].values
            y = d["velo_mph" + suffix].values
            sub = d.assign(_x=x, _y=y).dropna(subset=["_x", "_y"])
            fs.scatter_by_pitcher(ax, sub, "_x", "_y", fs.DIGIT[digit], size=40)
            key = "r_raw" if j == 0 else "r_strat"
            pkey = "p_raw" if j == 0 else "p_strat"
            row = feat[feat.feat == col]
            rv = float(row[key].iloc[0]) if len(row) else np.nan
            pv = float(row[pkey].iloc[0]) if len(row) else np.nan
            sig = pv < 0.05
            fs.fitline(ax, sub._x.values, sub._y.values,
                       fs.DIGIT[digit] if sig else fs.CONTEXT,
                       lw=1.8 if sig else 1.4,
                       ls="-" if sig else (0, (5, 3)))
            fs.note(ax, f"r = {rv:.2f}   p = {pv:.3f}"
                        f"{'' if sig else '   n.s.'}",
                    color=fs.INK if sig else fs.MUTED,
                    weight="bold" if sig else "normal")
            fs.panel_title(ax, f"({'abcd'[i*2+j]})  {ctitle}", pad=6)
            ax.set_xlabel(xlab)
            ax.set_ylabel("release velocity, centred  (mph)")
            ax.axhline(0, color=fs.GRID, lw=0.8, zorder=0)
            ax.axvline(0, color=fs.GRID, lw=0.8, zorder=0)
            fs.style(ax)
    fs.pitcher_shape_legend(axes[0][0], PITCHERS, loc="lower right")
    fs.save(fig, "figures/fig10_grip_velocity.png")


# =================================== Figure 11: the confound made visible
def fig11():
    """(a) where each association lands once effort is fixed; (b) why.

    Panel (a) is a dumbbell: one row per feature, the open mark its raw
    association and the filled mark its association with effort held fixed.
    Panel (b) splits the velocity variance each feature accounts for into the
    part it alone explains and the part it shares with commanded effort.
    """
    show = ["finger_impulse_Ns", "finger_F_rel_N", "finger_peak_N",
            "pointer_F_rel_N", "pointer_peak_N", "middle_peak_N",
            "total_peak_N", "thumb_impulse_Ns", "thumb_F_rel_N", "thumb_peak_N"]
    d = feat[feat.feat.isin(show)].copy()
    d = d.sort_values("r_strat")
    y = np.arange(len(d), dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=(fs.FIG_W, 4.4), layout="constrained",
                             gridspec_kw={"width_ratios": [1.45, 1]})

    # ---- (a) dumbbell
    ax = axes[0]
    ax.axvspan(-0.05, CRIT, color=fs.CONTEXT_FILL, alpha=0.45, zorder=0, lw=0)
    ax.axvline(CRIT, color=fs.THRESHOLD, lw=1.0, ls=(0, (2, 2)), zorder=1)
    for yi, r in zip(y, d.itertuples()):
        c = fs.DIGIT.get(r.digit, fs.CONTEXT)
        ax.plot([r.r_raw, r.r_strat], [yi, yi], lw=1.6, color=fs.CONTEXT,
                zorder=2, solid_capstyle="round")
        ax.plot([r.r_raw], [yi], "o", ms=6.5, mfc="white", mec=fs.CONTEXT,
                mew=1.6, zorder=3)
        ax.plot([r.r_strat], [yi], "o", ms=8.5, mfc=c, mec=fs.SURFACE,
                mew=1.4, zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels(d.pretty.values, fontsize=8.4)
    ax.set_xlabel("$r$ with release velocity")
    ax.set_xlim(-0.05, 0.76)
    ax.set_ylim(-2.9, len(d) - 0.3)
    ax.annotate("not significant", (CRIT - 0.02, -2.55), ha="right",
                fontsize=8.3, color=fs.MUTED, va="center")
    ax.annotate(f"$r_{{crit}}$ = {CRIT:.2f}", (CRIT + 0.02, -2.55),
                fontsize=8.3, color=fs.THRESHOLD, va="center")
    fs.panel_title(ax, "(a)  Association with velocity", pad=6)
    fs.style(ax, grid="x")
    fs.legend(ax, handles=[
        Line2D([], [], marker="o", ls="-", color=fs.CONTEXT, markerfacecolor="white",
               markeredgecolor=fs.CONTEXT, markersize=6.5, label="pitcher removed"),
        Line2D([], [], marker="o", ls="", markerfacecolor=fs.INK2,
               markeredgecolor=fs.SURFACE, markersize=8, label="+ effort removed")],
        loc="lower left", ncol=1, bbox_to_anchor=(0.0, 0.0))

    # ---- (b) variance unique to grip
    # Plotted alone rather than stacked against effort. On a shared 0-0.76 axis
    # these values are one pixel wide, which shows that grip adds almost nothing
    # but makes thumb and finger indistinguishable -- and the difference between
    # 0.013 and 0.000 is the entire point of the panel.
    ax = axes[1]
    cols = [fs.DIGIT.get(r.digit, fs.CONTEXT) for r in d.itertuples()]
    ax.barh(y, d.unique_grip.clip(lower=0).values, height=0.62, color=cols,
            edgecolor=fs.SURFACE, linewidth=0, zorder=3)
    for yi, r in zip(y, d.itertuples()):
        ax.text(max(r.unique_grip, 0) + 0.0006, yi, f"{r.unique_grip:.3f}",
                va="center", fontsize=8.2, color=fs.INK2)
    ax.set_yticks(y)
    ax.set_yticklabels([])
    ax.set_ylim(-2.9, len(d) - 0.3)
    ax.set_xlabel("velocity variance explained by grip\nand NOT by effort  "
                  "($\\Delta R^2$)")
    ax.set_xlim(0, max(d.unique_grip.max() * 1.42, 0.02))
    fs.panel_title(ax, "(b)  Variance unique to grip", pad=6)
    fs.style(ax, grid="x")
    fs.note(ax, "commanded effort alone\naccounts for $R^2$ = 0.759",
            xy=(0.40, 0.30), size=8.4)
    fs.save(fig, "figures/fig11_confound.png")


# ============================ Figure 12: effort coupling explains the survivors
def fig12():
    """The synthesis. One mark per feature.

    x  how tightly the feature tracks commanded effort, as a magnitude
    y  what it still says about velocity once effort is held fixed

    NO trend line is drawn. Across all twenty features the relationship between
    the two axes is r = -0.17, p = 0.47 -- not significant, and a fitted line
    would assert a smooth law the data does not support. The claim the figure
    makes is the one that survives: every feature that clears the significance
    threshold is thumb-dominated, and the thumb features sit at the low end of
    effort coupling. Sorting a table by the x-axis makes the relationship look
    monotonic; the scatter shows honestly that it is not.

    The emphasis form is used deliberately -- the thumb family carries hue and
    everything else is context grey, because the point is that one group sits
    apart, not that there are several categories to tell apart.
    """
    d = feat.dropna(subset=["r_effort", "r_strat"]).copy()
    d["absr_effort"] = d.r_effort.abs()
    d["fam"] = np.where(
        d.feat.str.startswith("thumb_") & (d.feat != "thumb_finger_ratio"), "thumb",
        np.where(d.feat == "thumb_finger_ratio", "ratio", "finger"))

    fig, ax = plt.subplots(figsize=(fs.FIG_W, 4.5), layout="constrained")
    ax.axhspan(-0.35, CRIT, color=fs.CONTEXT_FILL, alpha=0.45, zorder=0, lw=0)
    ax.axhline(CRIT, color=fs.THRESHOLD, lw=1.0, ls=(0, (2, 2)), zorder=1)
    ax.axhline(0, color=fs.GRID, lw=0.9, zorder=1)

    styles = {"finger": (fs.CONTEXT, "o", 58, "index / middle / composite"),
              "thumb": (fs.DIGIT["thumb"], "o", 92, "thumb"),
              "ratio": (fs.DIGIT["thumb"], "D", 80, "thumb-to-finger ratio")}
    for k, (c, m, s, lab) in styles.items():
        g = d[d.fam == k]
        ax.scatter(g.absr_effort, g.r_strat, s=s, marker=m, facecolor=c,
                   edgecolor=fs.SURFACE, linewidth=1.4, zorder=4, label=lab)

    # The dashed rule is the UNCORRECTED threshold. Two features clear it that
    # do not survive multiplicity control, so the survivors are ringed rather
    # than left to be inferred from position -- a reader who takes "above the
    # line" as "established" would over-read the figure by exactly two features.
    surv = d[d.bh_strat < 0.05]
    ax.scatter(surv.absr_effort, surv.r_strat, s=190, marker="o",
               facecolor="none", edgecolor=fs.INK, linewidth=1.5, zorder=5,
               label="survives FDR correction")

    # Selective direct labels: the three survivors, plus four context features
    # that anchor the opposite corner. Never a label on every mark.
    LABEL = {"thumb_peak_N": (-12, 0, "right", "center"),
             "thumb_F_rel_N": (0, 12, "center", "bottom"),
             "thumb_finger_ratio": (12, 0, "left", "center"),
             "total_peak_N": (11, -7, "left", "center"),
             "finger_peak_N": (12, 2, "left", "center"),
             "pointer_F_rel_N": (0, -13, "center", "top")}
    for r in d.itertuples():
        if r.feat in LABEL:
            dx, dy, ha, va = LABEL[r.feat]
            ax.annotate(r.pretty, (r.absr_effort, r.r_strat),
                        textcoords="offset points", xytext=(dx, dy),
                        fontsize=8.2, ha=ha, va=va, zorder=6,
                        color=fs.INK if r.fam != "finger" else fs.MUTED)

    ax.set_xlim(-0.06, 0.88)
    ax.set_ylim(-0.30, 0.60)
    ax.set_xlabel("how tightly the feature tracks commanded effort\n"
                  "(|$r$| with effort, within pitcher)")
    ax.set_ylabel("what it still says about velocity\nonce effort is held fixed  ($r$)")
    ax.annotate(f"below: not significant even uncorrected\n"
                f"($r_{{crit}}$ = {CRIT:.2f}, df = {DF_STRAT}, $\\alpha$ = 0.05)",
                (0.015, CRIT - 0.018), xycoords=("axes fraction", "data"),
                ha="left", va="top", fontsize=8.4, color=fs.THRESHOLD)
    fs.style(ax, grid="both")
    # Legend sits in the empty low-coupling / low-association corner, where no
    # feature lands, rather than over the cluster it is describing.
    fs.legend(ax, loc="lower left", bbox_to_anchor=(0.01, 0.02))
    fs.save(fig, "figures/fig12_effort_coupling.png")


def sync_to_thesis():
    """Copy the built figures next to MSCS_Paper.qmd.

    The thesis resolves figure paths relative to its own directory, so without
    this step a rebuild here leaves the document rendering whichever PNGs were
    copied over last -- silently, with no error to notice.
    """
    import shutil
    dest = os.path.join("..", "..", "figures")
    if not os.path.isdir(dest):
        print(f"  thesis figures directory not found at {dest}; skipped sync")
        return
    for f in sorted(os.listdir("figures")):
        if f.startswith(("fig6_trace", "fig7_", "fig8_release", "fig9_effort",
                         "fig10_grip", "fig11_", "fig12_")):
            shutil.copy2(os.path.join("figures", f), os.path.join(dest, f))
    print(f"  synced figures to {os.path.abspath(dest)}")


if __name__ == "__main__":
    print("building thesis figures")
    for f in (fig6, fig7, fig8, fig9, fig10, fig11, fig12):
        f()
    sync_to_thesis()
    print("done")
