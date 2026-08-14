"""Shared figure styling for the thesis figure set.

One visual language across every figure, so a reader who learns it once on
Figure 6 can read Figure 12 without relearning anything.

ENCODING CONTRACT
  hue   = DIGIT      index blue / middle orange / thumb violet
  shape = PITCHER    P1 circle / P2 square / P3 triangle
  grey  = CONTEXT    de-emphasised marks that are present for comparison only

Colour follows the entity, never its rank or its position in a sort, so the
thumb is violet in every figure whether it is the subject or the background.

The three digit hues were validated as a categorical set against the light
chart surface under the all-pairs rule (scatter and small-multiple forms put
every pair on screen simultaneously):

    worst all-pairs CVD separation   deltaE 13.0 (deuteranopia), 17.4 (tritanopia)
    worst all-pairs normal vision    deltaE 16.3
    contrast against surface         all three >= 3:1

Text never wears a series colour. Values, labels and legends are ink; a
coloured mark beside them carries the identity.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------- palette
DIGIT = {"pointer": "#2a78d6",      # blue
         "middle":  "#eb6834",      # orange
         "thumb":   "#4a3aa7",      # violet
         "finger":  "#2a78d6",      # combined index+middle reads as the blue family
         "total":   "#6f6e69"}      # composites are a neutral, not a digit hue

DIGIT_LABEL = {"pointer": "Index", "middle": "Middle", "thumb": "Thumb",
               "finger": "Index + middle", "total": "All digits"}

PITCHER_MARKER = {"P1": "o", "P2": "s", "P3": "^"}

# Context / de-emphasis. Used wherever one series is the point and the rest are
# there for comparison -- the emphasis form, not a fourth categorical hue.
CONTEXT = "#9c9b95"
CONTEXT_FILL = "#d9d8d2"

# Ink tokens. Text and rules only.
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#7c7f86"
GRID = "#e3e2dd"
SURFACE = "#fcfcfb"
RULE = "#b8b7b1"

# Reserved status colour, used only for the significance threshold rules.
THRESHOLD = "#b02a2a"

FIG_W = 6.5          # full text width of the thesis page, inches
DPI = 300


def apply_rc():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.facecolor": SURFACE,
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.linewidth": 0.8,
        "lines.solid_capstyle": "round",
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
    })


def style(ax, grid="y"):
    """Recessive grid and axes: the data is the ink, the frame is not."""
    if grid in ("y", "both"):
        ax.grid(True, axis="y", color=GRID, lw=0.8, zorder=0)
    if grid in ("x", "both"):
        ax.grid(True, axis="x", color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE)
    ax.tick_params(colors=MUTED, labelsize=9, length=3, width=0.8)
    for lab in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lab.set_color(INK2)


def panel_title(ax, text, pad=8):
    ax.set_title(text, fontsize=10.5, color=INK, loc="left", pad=pad)


def legend(ax, **kw):
    """Legend in ink, no box, so it never competes with the marks."""
    kw.setdefault("frameon", False)
    kw.setdefault("fontsize", 9)
    kw.setdefault("handletextpad", 0.5)
    leg = ax.legend(**kw)
    for t in leg.get_texts():
        t.set_color(INK2)
    return leg


def note(ax, text, xy=(0.03, 0.965), color=None, size=9, weight="normal",
         box=True):
    """Direct annotation inside the plot area, in ink.

    Carries an opaque surface plate by default. Statistics printed inside a
    scatter WILL land on a mark sooner or later, and a half-occluded p-value is
    worse than no p-value -- an early draft of Figure 10 rendered p = 0.064 with
    the 6 hidden under a data point, which reads as 0.004.
    """
    bbox = dict(facecolor=SURFACE, edgecolor="none", alpha=0.88,
                boxstyle="round,pad=0.28") if box else None
    ax.annotate(text, xy, xycoords="axes fraction", fontsize=size,
                color=color or INK2, va="top", ha="left", weight=weight,
                zorder=7, bbox=bbox)


def fitline(ax, x, y, color, lw=1.6, ls="-", zorder=2, extend=0.02):
    """Least-squares line drawn only across the observed range of x."""
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return None
    b = np.polyfit(x[m], y[m], 1)
    span = x[m].max() - x[m].min()
    xs = np.linspace(x[m].min() - extend * span, x[m].max() + extend * span, 60)
    ax.plot(xs, np.polyval(b, xs), lw=lw, ls=ls, color=color, zorder=zorder,
            solid_capstyle="round")
    return b


def scatter_by_pitcher(ax, df, xcol, ycol, color, size=42, alpha=0.9,
                       edge=SURFACE, zorder=3, label_pitchers=False):
    """Marks coloured by digit, shaped by pitcher.

    A 2 px surface-coloured ring separates overlapping marks so a dense
    cluster still reads as individual pitches rather than a blob.
    """
    for pid, g in df.groupby("pitcher"):
        ax.scatter(g[xcol], g[ycol], s=size, marker=PITCHER_MARKER.get(pid, "o"),
                   facecolor=color, edgecolor=edge, linewidth=1.1,
                   alpha=alpha, zorder=zorder,
                   label=pid if label_pitchers else None)


def pitcher_shape_legend(ax, pitchers, loc="lower right", title=None):
    """Shape legend for pitcher identity, drawn in ink with no colour meaning."""
    handles = [plt.Line2D([], [], marker=PITCHER_MARKER.get(p, "o"), ls="",
                          markerfacecolor=CONTEXT, markeredgecolor=SURFACE,
                          markeredgewidth=1.1, markersize=7, label=p)
               for p in pitchers]
    leg = ax.legend(handles=handles, loc=loc, frameon=False, fontsize=8.5,
                    title=title, handletextpad=0.4, borderpad=0.2,
                    labelspacing=0.35)
    for t in leg.get_texts():
        t.set_color(INK2)
    if leg.get_title():
        leg.get_title().set_color(MUTED)
        leg.get_title().set_fontsize(8.5)
    return leg


def crit_r(dfree, alpha=0.05):
    """Smallest |r| that reaches significance at the given residual df."""
    from scipy import stats
    t = stats.t.ppf(1 - alpha / 2, dfree)
    return float(np.sqrt(t ** 2 / (t ** 2 + dfree)))


def save(fig, path):
    fig.savefig(path, dpi=DPI, facecolor="white", bbox_inches="tight",
                pad_inches=0.03)
    plt.close(fig)
    print(f"  wrote {path}")
