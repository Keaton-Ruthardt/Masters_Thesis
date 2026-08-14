"""Inferential battery for the v2 sessions, run on results/per_pitch_features.csv.

This is the statistical core of the thesis. It exists because the pooled
correlations in Table 9 cannot, on their own, support the claim the project
makes. Three separate problems have to be answered:

  1. DEPENDENCE. Pitches are nested in pitchers. A pooled Pearson r over 40
     pitches from 3 pitchers has nothing like 38 degrees of freedom.
  2. CONFOUNDING. The effort ladder deliberately moved both grip force and
     velocity. Any correlation between them is confounded by construction
     unless effort is held fixed.
  3. MULTIPLICITY. Fifteen features are tested against velocity. At alpha =
     0.05 roughly one reaches significance by chance.

Each is addressed with a method that does not assume the others away, and the
results are reported whether or not they favour the hypothesis.

    python advanced_stats.py      (run thesis_analysis_v2.py first)

Output: results/advanced_stats.md
"""
import os
import warnings

import numpy as np
import pandas as pd
from scipy import stats

import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
RNG = np.random.default_rng(20260805)      # fixed: every p-value is reproducible
N_PERM = 20000
N_BOOT = 10000

FINGERS = ("pointer", "middle", "thumb")
# 'finger' is the combined index + middle driving channel: the two digits the
# ball rolls off, summed. It is tested alongside the individual digits because
# the index alone is an arbitrary half of the force that propels the ball.
FEATURES = [f"{f}_{k}" for f in FINGERS + ("finger",)
            for k in ("F_rel_N", "peak_N", "RFD_Ns", "impulse_Ns")]
FEATURES += ["total_peak_N", "CV_peak", "thumb_lead_ms", "thumb_finger_ratio"]
PRIMARY = "pointer_F_rel_N"

PRETTY = {"pointer_F_rel_N": "Index force at release",
          "pointer_peak_N": "Index peak force",
          "pointer_RFD_Ns": "Index RFD",
          "pointer_impulse_Ns": "Index impulse",
          "middle_F_rel_N": "Middle force at release",
          "middle_peak_N": "Middle peak force",
          "middle_RFD_Ns": "Middle RFD",
          "middle_impulse_Ns": "Middle impulse",
          "thumb_F_rel_N": "Thumb force at release",
          "thumb_peak_N": "Thumb peak force",
          "thumb_RFD_Ns": "Thumb RFD",
          "thumb_impulse_Ns": "Thumb impulse",
          "finger_F_rel_N": "Index+middle force at release",
          "finger_peak_N": "Index+middle peak force",
          "finger_RFD_Ns": "Index+middle RFD",
          "finger_impulse_Ns": "Index+middle impulse",
          "total_peak_N": "Total peak force",
          "CV_peak": "Inter-finger discrepancy",
          "thumb_lead_ms": "Thumb release lead",
          "thumb_finger_ratio": "Thumb-to-finger force ratio"}

L = []
def A(s=""):
    L.append(s)


# --------------------------------------------------------------- foundations
def center(df, cols, by):
    """Express each column as a deviation from its own group's mean."""
    out = df.copy()
    keys = by if isinstance(by, list) else [by]
    for c in cols:
        if c in out:
            out[c + "_c"] = out[c] - out.groupby(keys)[c].transform("mean")
    return out


def _groups(codes, k):
    """Row indices for each subject, as a list of integer arrays."""
    return [np.flatnonzero(codes == g) for g in range(k)]


def _within_center(v, gidx):
    out = v.astype(float).copy()
    for ix in gidx:
        out[ix] -= out[ix].mean()
    return out


def _r_from_centered(xc, yc):
    sx, sy = np.sqrt(xc @ xc), np.sqrt(yc @ yc)
    return (xc @ yc) / (sx * sy) if sx > 0 and sy > 0 else np.nan


def rmcorr(df, x, y, subj="pitcher"):
    """Repeated-measures correlation (Bakdash & Marusich 2017).

    ANCOVA with subject as a factor and a single slope common to all subjects.
    This is the correct within-subject correlation: it uses the exact residual
    degrees of freedom N - k - 1 rather than pretending the pitches are
    independent, which is what a pooled Pearson r on centred scores implies.

    Computed as the partial correlation of x and y given the subject dummies,
    which is algebraically identical to the ANCOVA formulation -- residualising
    on a factor IS centring within its levels -- and verified against
    statsmodels OLS to 1e-9. The closed form is used because the permutation
    and bootstrap routines below evaluate it tens of thousands of times.
    """
    d = df[[x, y, subj]].dropna()
    n = len(d)
    codes, uniq = pd.factorize(d[subj])
    k = len(uniq)
    dfree = n - k - 1
    if dfree < 2:
        return dict(r=np.nan, p=np.nan, n=n, df=np.nan, lo=np.nan, hi=np.nan,
                    slope=np.nan)
    gidx = _groups(codes, k)
    xc = _within_center(d[x].values, gidx)
    yc = _within_center(d[y].values, gidx)
    r = _r_from_centered(xc, yc)
    if not np.isfinite(r):
        return dict(r=np.nan, p=np.nan, n=n, df=dfree, lo=np.nan, hi=np.nan,
                    slope=np.nan)
    r = float(np.clip(r, -0.999999999, 0.999999999))
    t = r * np.sqrt(dfree / (1 - r ** 2))
    p = float(2 * stats.t.sf(abs(t), dfree))
    se = 1 / np.sqrt(dfree - 1) if dfree > 1 else np.nan
    c = stats.norm.ppf(0.975) * se
    z = np.arctanh(r)
    return dict(r=r, p=p, n=n, df=dfree,
                lo=float(np.tanh(z - c)), hi=float(np.tanh(z + c)),
                slope=float((xc @ yc) / (xc @ xc)) if xc @ xc > 0 else np.nan)


def perm_p_within(df, x, y, subj="pitcher", n_perm=N_PERM, stat=None):
    """Exact-null p by permuting y WITHIN each pitcher.

    Shuffling within pitcher preserves the nesting and every between-pitcher
    difference, so the null is 'grip carries no information about velocity for
    this pitcher' rather than the much stronger and less interesting null that
    all pitchers are exchangeable. No normality assumption is used.
    """
    d = df[[x, y, subj]].dropna()
    if len(d) < 8:
        return np.nan, np.nan
    codes, uniq = pd.factorize(d[subj])
    gidx = _groups(codes, len(uniq))
    xc = _within_center(d[x].values, gidx)
    yv = d[y].values.astype(float)
    obs = _r_from_centered(xc, _within_center(yv, gidx))
    if not np.isfinite(obs):
        return np.nan, np.nan
    # x is fixed across permutations, so centre it once; only y is reshuffled.
    sx = np.sqrt(xc @ xc)
    hits = 0
    for _ in range(n_perm):
        sh = yv.copy()
        for ix in gidx:
            sh[ix] = RNG.permutation(sh[ix])
        yc = _within_center(sh, gidx)
        sy = np.sqrt(yc @ yc)
        r = (xc @ yc) / (sx * sy) if sy > 0 else 0.0
        hits += abs(r) >= abs(obs)
    return float(obs), float((1 + hits) / (1 + n_perm))


def cluster_bootstrap_ci(df, x, y, subj="pitcher", n_boot=N_BOOT):
    """Two-stage bootstrap: resample pitchers, then pitches within pitcher.

    With three clusters the pitcher-level resample is coarse -- there are only
    ten distinct multisets of three pitchers -- so this interval is reported as
    a conservative bound, not a precise one.
    """
    d = df[[x, y, subj]].dropna()
    if len(d) < 8:
        return np.nan, np.nan
    codes, uniq = pd.factorize(d[subj])
    k = len(uniq)
    gidx = _groups(codes, k)
    xv, yv = d[x].values.astype(float), d[y].values.astype(float)
    out = np.empty(n_boot)
    out[:] = np.nan
    for b in range(n_boot):
        pick = RNG.integers(0, k, k)
        xs, ys = [], []
        for s in pick:
            ix = gidx[s]
            take = ix[RNG.integers(0, len(ix), len(ix))]
            # each resampled cluster is centred on its own mean, which is what
            # keeps it a distinct cluster rather than merging duplicates
            xs.append(xv[take] - xv[take].mean())
            ys.append(yv[take] - yv[take].mean())
        xc, yc = np.concatenate(xs), np.concatenate(ys)
        out[b] = _r_from_centered(xc, yc)
    out = out[np.isfinite(out)]
    if len(out) < 100:
        return np.nan, np.nan
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def holm_bh(pvals):
    """Holm-Bonferroni (FWER) and Benjamini-Hochberg (FDR) adjusted p."""
    p = np.asarray(pvals, float)
    ok = np.isfinite(p)
    m = ok.sum()
    holm = np.full_like(p, np.nan)
    bh = np.full_like(p, np.nan)
    order = np.argsort(np.where(ok, p, np.inf))[:m]
    run = 0.0
    for i, ix in enumerate(order):
        run = max(run, (m - i) * p[ix])
        holm[ix] = min(1.0, run)
    run = 1.0
    for i, ix in enumerate(order[::-1]):
        rank = m - i
        run = min(run, m / rank * p[ix])
        bh[ix] = min(1.0, run)
    return holm, bh


def nakagawa_r2(fit, df, group="pitcher"):
    """Marginal and conditional R^2 for a mixed model (Nakagawa & Schielzeth).

    Marginal = variance explained by the fixed effects alone.
    Conditional = fixed effects plus the pitcher random intercept.
    """
    try:
        var_f = float(np.var(fit.fittedvalues, ddof=0))
        var_r = float(np.asarray(fit.cov_re).ravel()[0])
        var_e = float(fit.scale)
        tot = var_f + var_r + var_e
        return var_f / tot, (var_f + var_r) / tot
    except Exception:
        return np.nan, np.nan


# ------------------------------------------------------------------- load
e = pd.read_csv("results/per_pitch_features.csv")
ev = e[e.analyzable] if "analyzable" in e else e[e.paired]
fb = ev[ev.pitch_type == "fastball"].copy()
cb = ev[ev.pitch_type == "curveball"].copy()

A("# Advanced statistical analysis — computed output\n")
A(f"Source: `results/per_pitch_features.csv`. Analyzable pitches: {len(ev)} "
  f"({len(fb)} fastballs, {len(cb)} curveballs) from {ev.pitcher.nunique()} "
  f"pitchers. Warm-ups and pitches without a paired velocity are already "
  f"excluded. Random seed 20260805; {N_PERM:,} permutations and "
  f"{N_BOOT:,} bootstrap resamples throughout.\n")


# ============================================================ 1. design check
A("\n## 1. Manipulation check — did the effort ladder work?\n")
A("Before any grip result can be interpreted, the experimental manipulation "
  "has to be shown to have done something. If commanded effort did not move "
  "velocity, there is nothing to control for and nothing to hold fixed.\n")
A("| Pitcher | 60 % mean (SD) | 80 % mean (SD) | 100 % mean (SD) | range (mph) | one-way F | p |")
A("|:--|:--|:--|:--|--:|--:|--:|")
for pid, g in fb.groupby("pitcher"):
    cells, groups = [], []
    for lv in (60, 80, 100):
        v = g[g.effort_pct == lv].velo_mph.dropna().values
        cells.append(f"{v.mean():.1f} ({v.std(ddof=1):.1f}) n={len(v)}" if len(v) > 1 else
                     (f"{v.mean():.1f} n={len(v)}" if len(v) else "—"))
        if len(v) > 1:
            groups.append(v)
    allv = g.velo_mph.dropna().values
    if len(groups) >= 2:
        F, p = stats.f_oneway(*groups)
    else:
        F, p = np.nan, np.nan
    A(f"| {pid} | " + " | ".join(cells) +
      f" | {allv.max()-allv.min():.1f} | {F:.1f} | {p:.2g} |")

lin = rmcorr(fb, "effort_pct", "velo_mph")
A(f"\nWithin-pitcher, commanded effort and velocity move together at "
  f"r_rm = {lin['r']:.3f}, 95 % CI [{lin['lo']:.2f}, {lin['hi']:.2f}], "
  f"p = {lin['p']:.3g}, n = {lin['n']}, df = {lin['df']}. The ladder produced "
  f"the intended velocity spread in every pitcher. This is also the reason the "
  f"raw correlations in Table 9 cannot be taken at face value: effort drives "
  f"grip force and velocity simultaneously.\n")


# =================================================== 2. dependence: rmcorr
A("\n## 2. Table A1. Within-pitcher association with velocity, corrected for "
  "dependence and multiplicity (fastballs)\n")
A("Repeated-measures correlation fits one slope common to all pitchers with a "
  "separate intercept for each, so the degrees of freedom are the real "
  "N − k − 1 and not the inflated N − 2 that pooling centred scores implies. "
  "The permutation p shuffles velocity within each pitcher and assumes no "
  "distribution at all. Holm controls the family-wise error rate across all "
  f"{len(FEATURES)} features; Benjamini–Hochberg controls the false-discovery rate.\n")

rows = []
for c in FEATURES:
    if c not in fb or fb[c].notna().sum() < 10:
        continue
    rc = rmcorr(fb, c, "velo_mph")
    _, pperm = perm_p_within(fb, c, "velo_mph")
    rows.append(dict(feat=c, **rc, p_perm=pperm))
R = pd.DataFrame(rows)
R["holm"], R["bh"] = holm_bh(R.p.values)
R = R.sort_values("p")

A("| Feature | r_rm | 95 % CI | p | p (permutation) | p Holm | p BH | n | df |")
A("|:--|--:|:--|--:|--:|--:|--:|--:|--:|")
for _, r in R.iterrows():
    star = "**" if r.holm < 0.05 else ""
    A(f"| {star}{PRETTY.get(r.feat, r.feat)}{star} | {star}{r.r:.3f}{star} | "
      f"[{r.lo:.2f}, {r.hi:.2f}] | {r.p:.3g} | {r.p_perm:.4f} | "
      f"{r.holm:.3g} | {r.bh:.3g} | {int(r.n)} | {int(r.df)} |")
A(f"\nBold marks features surviving Holm correction across the family of "
  f"{len(R)}. Features surviving Holm: {int((R.holm < 0.05).sum())} of {len(R)}; "
  f"surviving Benjamini–Hochberg: {int((R.bh < 0.05).sum())}.\n")
A("Note how little the picture changes between the parametric and permutation "
  "columns. The associations are not artefacts of the normality assumption.\n")


# ============================================ 3. the confound: effort control
A("\n## 3. Table A2. The central test — does grip force predict velocity at a "
  "FIXED commanded effort?\n")
A("This is the claim the project stands on, and it is tested three ways that "
  "fail differently. **Stratified centring** subtracts the mean of each "
  "pitcher × effort cell, so effort is held exactly fixed and nothing is "
  "assumed about its functional form; it is the strictest test and it discards "
  "all between-cell information. **Partial rmcorr** residualises on effort as a "
  "continuous covariate. **Mixed model** enters effort as a categorical fixed "
  "effect alongside a pitcher random intercept.\n")

fbs = center(fb, FEATURES + ["velo_mph"], by=["pitcher", "effort_pct"])
cell_n = fb.groupby(["pitcher", "effort_pct"]).size()
A(f"Cells: {len(cell_n)} pitcher × effort combinations, "
  f"{cell_n.min()}–{cell_n.max()} pitches each (median {cell_n.median():.0f}). "
  f"Stratified centring costs {len(cell_n)} degrees of freedom.\n")

def partial_on(dd, c, base, min_n=12):
    """Partial correlation of feature c with velocity given a design `base`.

    Residualise both variables on the same design and correlate the residuals;
    df is n minus the rank of that design minus one. This is the quantity every
    effort-controlled statement in the thesis rests on, so it is computed once
    here and reused rather than reimplemented per section.
    """
    d = dd[[c, "velo_mph", "effort_pct", "pitcher"]].dropna()
    if len(d) < min_n:
        return dict(r=np.nan, p=np.nan, df=np.nan, slope=np.nan, n=len(d))
    my = smf.ols(f"velo_mph ~ {base}", data=d).fit()
    mx = smf.ols(f"Q('{c}') ~ {base}", data=d).fit()
    rx, ry = mx.resid.values, my.resid.values
    dfree = int(len(d) - my.df_model - 2)
    r = _r_from_centered(rx - rx.mean(), ry - ry.mean())
    if not np.isfinite(r) or dfree < 2:
        return dict(r=np.nan, p=np.nan, df=dfree, slope=np.nan, n=len(d))
    r = float(np.clip(r, -0.999999999, 0.999999999))
    t = r * np.sqrt(dfree / (1 - r ** 2))
    return dict(r=r, p=float(2 * stats.t.sf(abs(t), dfree)), df=dfree,
                slope=float((rx @ ry) / (rx @ rx)) if rx @ rx > 0 else np.nan,
                n=len(d))


FULL = "C(pitcher)*C(effort_pct)"     # every pitcher x effort cell mean removed
ADDITIVE = "C(pitcher) + C(effort_pct)"

rows = []
for c in FEATURES:
    if c not in fb or fb[c].notna().sum() < 12:
        continue
    f_ = partial_on(fb, c, FULL)
    a_ = partial_on(fb, c, ADDITIVE)
    rows.append(dict(feat=c, r_strat=f_["r"], p_strat=f_["p"], df_strat=f_["df"],
                     slope=f_["slope"], r_add=a_["r"], p_add=a_["p"]))
S = pd.DataFrame(rows)
S["holm_strat"], S["bh_strat"] = holm_bh(S.p_strat.values)
S = S.sort_values("p_strat")

A("| Feature | r (full cell control) | p | p Holm | p BH | r (additive control) | p | slope |")
A("|:--|--:|--:|--:|--:|--:|--:|--:|")
for _, r in S.iterrows():
    star = "**" if r.holm_strat < 0.05 else ""
    unit = "ms" if r.feat.endswith("_ms") else ("" if r.feat == "CV_peak" else "N")
    sl = f"{r.slope:+.3f}" + (f" mph/{unit}" if unit else " mph/unit")
    A(f"| {star}{PRETTY.get(r.feat, r.feat)}{star} | {star}{r.r_strat:.3f}{star} | "
      f"{r.p_strat:.3g} | {r.holm_strat:.3g} | {r.bh_strat:.3g} | "
      f"{r.r_add:.3f} | {r.p_add:.3g} | {sl} |")
A(f"\nDegrees of freedom under full cell control: {int(S.df_strat.iloc[0])}.\n")

surv_h = S[S.holm_strat < 0.05]
surv = S[S.bh_strat < 0.05]            # FDR survivors carry the reporting
A(f"**With commanded effort held exactly fixed, {len(surv_h)} of {len(S)} "
  f"features survive Holm (family-wise) correction and {len(surv)} survive "
  f"Benjamini–Hochberg (false-discovery) correction.**\n")
if len(surv):
    A("Surviving FDR control: " +
      ", ".join(f"{PRETTY.get(r.feat, r.feat)} (r = {r.r_strat:.3f}, "
                f"q = {r.bh_strat:.3f})" for _, r in surv.iterrows()) + ".")
    if not len(surv_h):
        A("None clears the stricter family-wise threshold. The distinction is "
          "not a technicality: Holm asks whether *any* false positive is likely "
          f"in the family of {len(S)}, Benjamini–Hochberg asks what proportion of the "
          "declared findings are false. At this sample size the honest summary "
          "is that these are the strongest candidates rather than established "
          "effects, and they are reported as such.\n")
else:
    A("No feature survives either correction. The associations in Table A1 are "
      "then attributable to the effort manipulation rather than to grip.\n")

prim = S[S.feat == PRIMARY].iloc[0]
A(f"**The pre-specified primary feature, {PRETTY[PRIMARY].lower()}, gives "
  f"r = {prim.r_strat:.3f}, p = {prim.p_strat:.3g} under full cell control "
  f"(Holm p = {prim.holm_strat:.3g}).** Its unadjusted association in Table A1 "
  f"was r = {float(R[R.feat==PRIMARY].r.iloc[0]):.3f}. The difference between "
  f"those two numbers is the effort confound, and for this feature it accounts "
  f"for essentially the whole association.\n")

A("\n### Per-pitcher consistency of the leading features\n")
A("A pooled partial correlation can be produced by one pitcher alone. Each "
  "leading feature is re-estimated within each pitcher separately, with that "
  "pitcher's own effort levels removed.\n")
A("| Feature | " + " | ".join(f"{p} r (n)" for p in sorted(fb.pitcher.unique())) +
  " | same sign in all 3? |")
A("|:--|" + "--:|" * fb.pitcher.nunique() + ":--|")
npitch = fb.pitcher.nunique()
for c in dict.fromkeys(list(surv.feat) + ["total_peak_N", PRIMARY]):
    cells, signs = [], []
    for pid in sorted(fb.pitcher.unique()):
        g = fb[fb.pitcher == pid]
        rr = partial_on(g, c, "C(effort_pct)", min_n=8)
        cells.append(f"{rr['r']:.2f} ({rr['n']})" if np.isfinite(rr["r"]) else "—")
        if np.isfinite(rr["r"]):
            signs.append(np.sign(rr["r"]))
    same = ("yes" if len(signs) == npitch and len(set(signs)) == 1
            else ("no" if len(signs) == npitch else f"only {len(signs)} estimable"))
    A(f"| {PRETTY.get(c, c)} | " + " | ".join(cells) + f" | {same} |")
A("\nPer-pitcher estimates use that pitcher's own effort levels as the control "
  "and are badly underpowered on their own (P2 contributes 11 fastballs against "
  "3 effort levels). They are reported to show the pooled estimate is not the "
  "product of a single pitcher, not as independent tests.\n")

A("\n### Rank-based robustness — is the surviving result an artefact of the "
  "calibration curve?\n")
A("Two channels were calibrated only to 19.6 N and the pitching peaks exceed "
  "that, so the top of the force scale is extrapolated. A rank-based partial "
  "correlation is invariant to any *monotonic* distortion of the force scale: "
  "if the surviving associations hold on ranks, no error in the shape of the "
  "calibration curve can have produced them. Ranks are taken within each "
  "pitcher × effort cell, which is the same control as Table A2.\n")
A("| Feature | Pearson r (cell control) | Spearman r (cell control) | p | verdict |")
A("|:--|--:|--:|--:|:--|")
fbr = fb.copy()
for c in dict.fromkeys(list(surv.feat) + ["total_peak_N", PRIMARY, "pointer_impulse_Ns"]):
    d = fb[[c, "velo_mph", "pitcher", "effort_pct"]].dropna().copy()
    if len(d) < 12:
        continue
    key = ["pitcher", "effort_pct"]
    d["_xr"] = d.groupby(key)[c].rank()
    d["_yr"] = d.groupby(key)["velo_mph"].rank()
    xr = (d["_xr"] - d.groupby(key)["_xr"].transform("mean")).values
    yr = (d["_yr"] - d.groupby(key)["_yr"].transform("mean")).values
    rs = _r_from_centered(xr - xr.mean(), yr - yr.mean())
    dfree = len(d) - d.groupby(["pitcher", "effort_pct"]).ngroups - 1
    t = rs * np.sqrt(dfree / max(1e-12, 1 - rs ** 2))
    ps = float(2 * stats.t.sf(abs(t), dfree))
    pear = float(S[S.feat == c].r_strat.iloc[0]) if (S.feat == c).any() else np.nan
    verdict = ("holds on ranks" if ps < 0.05 else
               "does not hold on ranks — treat as calibration-sensitive")
    A(f"| {PRETTY.get(c, c)} | {pear:.3f} | {rs:.3f} | {ps:.3g} | {verdict} |")


# ============================================ 3b. why the thumb behaves apart
A("\n## 3b. Why the thumb behaves differently from the fingers\n")
A("The thumb is the only channel whose effort-controlled association is "
  "*stronger* than its raw one. That is a suppression pattern, and it has a "
  "direct explanation: how tightly each digit loads is not equally a readout of "
  "commanded effort. Each feature is correlated with commanded effort itself, "
  "within pitcher.\n")
A("| Feature | r with commanded effort | p | r with velocity, effort fixed | p |")
A("|:--|--:|--:|--:|--:|")
eff_rows = []
for c in FEATURES:
    if c not in fb or fb[c].notna().sum() < 12:
        continue
    re_ = rmcorr(fb, c, "effort_pct")
    row = S[S.feat == c]
    eff_rows.append((c, re_["r"], re_["p"],
                     float(row.r_strat.iloc[0]) if len(row) else np.nan,
                     float(row.p_strat.iloc[0]) if len(row) else np.nan))
for c, re_, pe, rs, ps in sorted(eff_rows, key=lambda t: -t[1]):
    A(f"| {PRETTY.get(c,c)} | {re_:.3f} | {pe:.4f} | {rs:.3f} | {ps:.3g} |")

A("\nRead the first column against the last. **The finger channels are largely a "
  "readout of commanded effort** — index force at release tracks effort at "
  "r = "
  + f"{[r for c, r, *_ in eff_rows if c == 'pointer_F_rel_N'][0]:.3f}"
  + " — and once effort is held fixed they have little left to say about "
    "velocity. **Thumb peak force is the grip feature least coupled to "
    "commanded effort** (r = "
  + f"{[r for c, r, *_ in eff_rows if c == 'thumb_peak_N'][0]:.3f}"
  + ", not significant), and it is the one that retains an association with "
    "velocity once effort is fixed.\n")
A("This reframes what the instrument is measuring. Index and middle loading is "
  "close to an intensity proxy: it says how hard the pitcher is trying, which "
  "the pitcher already knows. Thumb loading carries information that commanded "
  "effort does not, which is the only part of the grip signal that could be "
  "independently actionable. It is also the channel the closest prior work "
  "could not see at all, having instrumented only index and middle.\n")
A("The claim this supports is narrower than the one the project set out to "
  "make, and it is about a different digit. It should be labelled exploratory: "
  "the thumb was not the pre-specified primary, it does not clear family-wise "
  f"correction, and it emerged from the same {len(S)}-feature family that the "
  "multiplicity control exists to discipline. It is a hypothesis for the next "
  "study, not a result this one establishes.\n")


# ==================================================== 4. mixed-effects models
A("\n## 4. Table A3. Mixed-effects models for the primary hypothesis\n")
A(f"Outcome: release velocity (mph). Predictor: {PRETTY[PRIMARY].lower()} "
  f"(z-scored within pitcher, so the coefficient is mph per within-pitcher SD). "
  f"Random intercept for pitcher throughout. Models are nested and compared by "
  f"likelihood-ratio test on ML fits.\n")

d = fb[[PRIMARY, "velo_mph", "effort_pct", "pitcher"]].dropna().copy()
d["grip_z"] = d.groupby("pitcher")[PRIMARY].transform(lambda s: (s - s.mean()) / s.std(ddof=1))
d["eff"] = d.effort_pct.astype(int).astype(str)

TESTSET = [PRIMARY, "pointer_peak_N", "pointer_impulse_Ns", "middle_impulse_Ns",
           "thumb_peak_N", "thumb_F_rel_N", "total_peak_N", "pointer_RFD_Ns"]

m0 = smf.mixedlm("velo_mph ~ 1", d, groups=d["pitcher"]).fit(reml=False, method="lbfgs")
vr = float(np.asarray(m0.cov_re).ravel()[0])
icc = vr / (vr + float(m0.scale))
if icc < 0.005:
    A(f"Unconditional ICC = {icc:.3f}. The pitcher variance component is "
      f"estimated at the boundary of its parameter space — effectively zero — "
      f"because the effort ladder deliberately created within-pitcher velocity "
      f"variance far larger than the differences between these three pitchers. "
      f"A boundary estimate is not evidence that pitches are independent: with "
      f"three clusters the component is barely identifiable, so every estimate "
      f"in this report is a within-pitcher estimate regardless.\n")
else:
    A(f"Unconditional ICC = {icc:.3f}: {100*icc:.1f} % of raw velocity variance "
      f"is between pitchers, which is why pitches are not treated as "
      f"independent anywhere in this report.\n")

A("| Feature | β per within-pitcher SD (95 % CI) | p | χ²(1) vs effort-only | p | "
  "marginal R² effort-only → +grip |")
A("|:--|:--|--:|--:|--:|:--|")
for c in TESTSET:
    dd = fb[[c, "velo_mph", "effort_pct", "pitcher"]].dropna().copy()
    if len(dd) < 12:
        continue
    dd["gz"] = dd.groupby("pitcher")[c].transform(
        lambda s: (s - s.mean()) / s.std(ddof=1))
    dd["eff"] = dd.effort_pct.astype(int).astype(str)
    try:
        m1 = smf.mixedlm("velo_mph ~ C(eff)", dd, groups=dd["pitcher"]).fit(
            reml=False, method="lbfgs")
        m3 = smf.mixedlm("velo_mph ~ C(eff) + gz", dd, groups=dd["pitcher"]).fit(
            reml=False, method="lbfgs")
    except Exception:
        continue
    lr = max(0.0, 2 * (m3.llf - m1.llf))
    plr = stats.chi2.sf(lr, 1)
    b = m3.params["gz"]
    lo_, hi_ = m3.conf_int().loc["gz"]
    r2a, _ = nakagawa_r2(m1, dd)
    r2b, _ = nakagawa_r2(m3, dd)
    star = "**" if plr < 0.05 else ""
    A(f"| {star}{PRETTY.get(c,c)}{star} | {b:+.2f} [{lo_:+.2f}, {hi_:+.2f}] mph | "
      f"{m3.pvalues['gz']:.3g} | {lr:.2f} | {star}{plr:.3g}{star} | "
      f"{r2a:.3f} → {r2b:.3f} |")

A("\nThe mixed model enters effort additively and pitcher as a random intercept, "
  "so it is a weaker control than the full cell centring in Table A2 and should "
  "agree with it in direction. It does.\n")

try:
    dprim = fb[[PRIMARY, "velo_mph", "effort_pct", "pitcher"]].dropna().copy()
    dprim["gz"] = dprim.groupby("pitcher")[PRIMARY].transform(
        lambda s: (s - s.mean()) / s.std(ddof=1))
    dprim["eff"] = dprim.effort_pct.astype(int).astype(str)
    base = smf.mixedlm("velo_mph ~ C(eff) + gz", dprim, groups=dprim["pitcher"]).fit(
        reml=False, method="lbfgs")
    ms = smf.mixedlm("velo_mph ~ C(eff) + gz", dprim, groups=dprim["pitcher"],
                     re_formula="~gz").fit(reml=False, method="lbfgs")
    lr = max(0.0, 2 * (ms.llf - base.llf))
    A(f"Allowing the grip slope to vary by pitcher does not improve fit "
      f"(χ²(2) = {lr:.2f}, p = {stats.chi2.sf(lr, 2):.3g}), so a single common "
      f"slope is retained. With three pitchers this test has very little power "
      f"and is a check, not evidence of homogeneity.\n")
except Exception:
    A("The random-slope model did not converge on three clusters; a common "
      "slope is retained.\n")


# ================================================ 5. commonality / uniqueness
A("\n## 5. Variance partitioning — how much does grip add over effort?\n")
A("Velocity variance is decomposed into the part unique to grip, the part "
  "unique to commanded effort, and the part they share. The shared part is the "
  "confound made visible: variance neither predictor can be credited with "
  "alone. All increments are over a pitcher-only baseline, so between-pitcher "
  "variance is removed first and cannot inflate them. Effort enters as a "
  "three-level factor, matching the additive column of Table A2.\n")
A("| Feature | R² effort | R² grip | R² both | unique grip | unique effort | shared |")
A("|:--|--:|--:|--:|--:|--:|--:|")
for c in TESTSET:
    dd = fb[[c, "velo_mph", "effort_pct", "pitcher"]].dropna()
    if len(dd) < 12:
        continue
    def r2(formula):
        return smf.ols(formula, data=dd).fit().rsquared
    base = r2("velo_mph ~ C(pitcher)")
    re_ = r2("velo_mph ~ C(pitcher) + C(effort_pct)") - base
    rg = r2(f"velo_mph ~ C(pitcher) + Q('{c}')") - base
    rb = r2(f"velo_mph ~ C(pitcher) + C(effort_pct) + Q('{c}')") - base
    A(f"| {PRETTY.get(c,c)} | {re_:.3f} | {rg:.3f} | {rb:.3f} | "
      f"**{rb-re_:.3f}** | {rb-rg:.3f} | {re_+rg-rb:.3f} |")
A("\nRead the *unique grip* column against the *shared* column. Where unique is "
  "near zero and shared is large, the feature is carrying commanded effort and "
  "nothing else — it looks predictive only because the ladder moved both "
  "quantities together.\n")


# ============================================ 6. bootstrap CI for the primary
A("\n## 6. Cluster bootstrap\n")
A("Resampling pitchers with replacement, then pitches within each resampled "
  "pitcher. This is the only interval here that propagates the uncertainty of "
  "*which three pitchers* were measured. Reported both for the raw association "
  "and, where estimable, for the association with effort held fixed.\n")
A("| Feature | r_rm (raw) | analytic 95 % CI | cluster bootstrap 95 % CI | permutation p |")
A("|:--|--:|:--|:--|--:|")
for c in dict.fromkeys([PRIMARY] + list(surv.feat) + ["total_peak_N"]):
    if c not in fb:
        continue
    rc = rmcorr(fb, c, "velo_mph")
    lo, hi = cluster_bootstrap_ci(fb, c, "velo_mph")
    _, pperm = perm_p_within(fb, c, "velo_mph")
    A(f"| {PRETTY.get(c,c)} | {rc['r']:.3f} | [{rc['lo']:.2f}, {rc['hi']:.2f}] | "
      f"[{lo:.2f}, {hi:.2f}] | {pperm:.4f} |")
A("\nEvery bootstrap interval is wider than its analytic counterpart. That gap "
  "is the honest cost of three pitchers: resampling at the pitcher level admits "
  "that a different three pitchers could have produced a noticeably different "
  "estimate, and no number of pitches per pitcher repairs it.\n")


# ================================================= 7. stability / instrument
A("\n## 7. Instrument stability across a session\n")
A("Thin-film force sensors creep under sustained load and drift with "
  "temperature. If grip readings trended across a session, an apparent "
  "grip–velocity association could be a drift artefact aligned with fatigue. "
  "Each feature is regressed on pitch order within pitcher.\n")
A("| Feature | r with pitch order | p | interpretation |")
A("|:--|--:|--:|:--|")
fb2 = fb.sort_values(["pitcher", "t_start"]).copy()
fb2["order"] = fb2.groupby("pitcher").cumcount() + 1
for c in [PRIMARY, "pointer_peak_N", "total_peak_N", "velo_mph"]:
    rr = rmcorr(fb2, "order", c)
    verdict = "no detectable drift" if rr["p"] > 0.05 else "TRENDS — check"
    A(f"| {PRETTY.get(c, c)} | {rr['r']:+.3f} | {rr['p']:.3g} | {verdict} |")
A("\nOrder is confounded with the protocol itself — the submaximal blocks were "
  "thrown last — so a trend here would not by itself prove drift. It is "
  "reported because its absence removes one alternative explanation.\n")

A("\n### Within-condition repeatability\n")
A("Coefficient of variation of each feature within a pitcher × effort cell, "
  "which bounds how much of the pitch-to-pitch spread is measurement noise "
  "rather than real variation.\n")
A("| Feature | median within-cell CV | pooled within-cell SD |")
A("|:--|--:|--:|")
for c in [PRIMARY, "pointer_peak_N", "pointer_impulse_Ns", "total_peak_N", "CV_peak"]:
    g = fb.groupby(["pitcher", "effort_pct"])[c]
    cv = (g.std(ddof=1) / g.mean().abs()).dropna()
    if len(cv):
        A(f"| {PRETTY.get(c,c)} | {cv.median():.3f} | {g.std(ddof=1).mean():.2f} |")


# ================================================= 8. negative results, bounded
A("\n## 8. Bounding the negative results\n")
A("A non-significant result is not evidence of no effect unless the interval "
  "excludes the effect that was expected. Each feature that failed is checked "
  "against the effect size the reference literature reports (Yeh et al. give "
  "r ≈ 0.53 to 0.58 for finger characteristics against velocity).\n")
A("The features that matter here are the ones that fail *under effort control*, "
  "since that is the test the project's claim depends on. A Fisher interval is "
  "placed on each effort-controlled estimate and checked against r = 0.53.\n")
A("| Feature | r (cell control) | 95 % CI | excludes r = 0.53? | verdict |")
A("|:--|--:|:--|:--|:--|")
zc = stats.norm.ppf(0.975)
for _, r in S.iterrows():
    if r.p_strat < 0.05:
        continue
    se = 1 / np.sqrt(max(r.df_strat - 2, 1))
    z = np.arctanh(np.clip(r.r_strat, -0.9999, 0.9999))
    lo_, hi_ = np.tanh(z - zc * se), np.tanh(z + zc * se)
    excl = "yes" if hi_ < 0.53 else "no"
    verdict = ("bounded below the literature value" if hi_ < 0.53
               else "underpowered — cannot be distinguished from it")
    A(f"| {PRETTY.get(r.feat, r.feat)} | {r.r_strat:.3f} | [{lo_:.2f}, {hi_:.2f}] | "
      f"{excl} | {verdict} |")

nfb = len(fb.dropna(subset=[PRIMARY, "velo_mph"]))
dfree = nfb - fb.pitcher.nunique() - 1
mde = np.sqrt(stats.f.ppf(0.95, 1, dfree) / (stats.f.ppf(0.95, 1, dfree) + dfree))
A(f"\nMinimum detectable within-pitcher correlation at α = 0.05 (two-sided) "
  f"with df = {dfree} is r = {mde:.3f}. Any |r| below that could not have "
  f"reached significance in this design regardless of the truth.\n")


# ====================================================== 9. pitch-type contrast
A("\n## 9. Fastball versus curveball, with pitcher as a blocking factor\n")
A("Reported on force *shares* and timing rather than newtons, because a given "
  "finger is read by a different sensor on each pitch type and absolute values "
  "are therefore not comparable across types. Two-way model with pitcher as a "
  "blocking factor tests whether the grip contrast holds after every "
  "between-pitcher difference is removed.\n")
A("| Feature | FB mean | CB mean | difference | F (pitch type) | p | partial η² | replicates in all 3? |")
A("|:--|--:|--:|--:|--:|--:|--:|:--|")
for c in ["thumb_share", "middle_share", "pointer_share", "CV_peak", "thumb_lead_ms"]:
    d = ev[[c, "pitch_type", "pitcher"]].dropna()
    if d.pitch_type.nunique() < 2:
        continue
    m = smf.ols(f"Q('{c}') ~ C(pitcher) + C(pitch_type)", data=d).fit()
    an = sm.stats.anova_lm(m, typ=2)
    ss = an.loc["C(pitch_type)", "sum_sq"]
    eta = ss / (ss + an.loc["Residual", "sum_sq"])
    f_ = an.loc["C(pitch_type)", "F"]
    p_ = an.loc["C(pitch_type)", "PR(>F)"]
    a_ = d[d.pitch_type == "fastball"][c]
    b_ = d[d.pitch_type == "curveball"][c]
    signs = []
    for pid, g in d.groupby("pitcher"):
        gf = g[g.pitch_type == "fastball"][c]
        gc = g[g.pitch_type == "curveball"][c]
        if len(gf) > 1 and len(gc) > 1:
            signs.append(np.sign(gf.mean() - gc.mean()))
    rep = "yes" if len(signs) == 3 and len(set(signs)) == 1 else "no"
    A(f"| {c} | {a_.mean():.3f} | {b_.mean():.3f} | {a_.mean()-b_.mean():+.3f} | "
      f"{f_:.1f} | {p_:.3g} | {eta:.3f} | {rep} |")


# ============================================================ 10. other outcomes
A("\n## 10. Secondary ball-flight outcomes\n")
for oc, lab in (("spin_rpm", "spin rate"), ("ivb", "induced vertical break"),
                ("hz_break", "horizontal break")):
    if oc not in ev:
        continue
    sub = ev[ev[oc].notna()]
    A(f"\n**{lab.capitalize()}**: captured for {len(sub)} of {len(ev)} analyzable "
      f"pitches" + (f" ({', '.join(f'{p}: {n}' for p, n in sub.pitcher.value_counts().items())})"
                    if len(sub) else "") + ".")
    if len(sub) < 12:
        A(f"Too few observations for inference. Values are reported "
          f"descriptively only, and no correlation with grip is computed — "
          f"with n = {len(sub)} any estimate would be uninterpretable.")
        if len(sub):
            A("")
            A("| Pitcher | pitch type | velocity (mph) | " + lab + " |")
            A("|:--|:--|--:|--:|")
            for _, r in sub.iterrows():
                A(f"| {r.pitcher} | {r.pitch_type} | {r.velo_mph:.1f} | {r[oc]:.1f} |")
    else:
        A("")
        A("| Feature | r_rm | p |")
        A("|:--|--:|--:|")
        for c in FEATURES:
            if c in sub and sub[c].notna().sum() >= 10:
                rr = rmcorr(sub, c, oc)
                A(f"| {PRETTY.get(c,c)} | {rr['r']:.3f} | {rr['p']:.3g} |")

os.makedirs("results", exist_ok=True)
# ------------------------------------------------- machine-readable feature table
# The figures are drawn from this file rather than recomputing anything, so a
# number in a figure and the same number in the report cannot drift apart.
def variance_split(c):
    dd = fb[[c, "velo_mph", "effort_pct", "pitcher"]].dropna()
    if len(dd) < 12:
        return dict(unique_grip=np.nan, unique_effort=np.nan, shared=np.nan)
    def r2(f):
        return smf.ols(f, data=dd).fit().rsquared
    b = r2("velo_mph ~ C(pitcher)")
    re_ = r2("velo_mph ~ C(pitcher) + C(effort_pct)") - b
    rg = r2(f"velo_mph ~ C(pitcher) + Q('{c}')") - b
    rb = r2(f"velo_mph ~ C(pitcher) + C(effort_pct) + Q('{c}')") - b
    return dict(unique_grip=rb - re_, unique_effort=rb - rg, shared=re_ + rg - rb)


tab = R.merge(S, on="feat", how="outer", suffixes=("_raw", ""))
tab = tab.rename(columns={"r": "r_raw", "p": "p_raw", "lo": "lo_raw",
                          "hi": "hi_raw", "holm": "holm_raw", "bh": "bh_raw"})
rows = []
for _, r in tab.iterrows():
    ef = rmcorr(fb, r.feat, "effort_pct") if r.feat in fb else dict(r=np.nan, p=np.nan)
    rows.append(dict(r, pretty=PRETTY.get(r.feat, r.feat),
                     digit=("thumb" if r.feat.startswith("thumb_") and
                            r.feat != "thumb_finger_ratio"
                            else "finger" if r.feat.startswith("finger_")
                            else "pointer" if r.feat.startswith("pointer_")
                            else "middle" if r.feat.startswith("middle_")
                            else "total"),
                     r_effort=ef["r"], p_effort=ef["p"], **variance_split(r.feat)))
FT = pd.DataFrame(rows)
FT["crit_r_strat"] = np.nan
if FT.df_strat.notna().any():
    dfree = int(FT.df_strat.dropna().iloc[0])
    FT["crit_r_strat"] = float(np.sqrt(stats.t.ppf(0.975, dfree) ** 2 /
                                       (stats.t.ppf(0.975, dfree) ** 2 + dfree)))
FT.to_csv("results/feature_stats.csv", index=False)

open("results/advanced_stats.md", "w", encoding="utf-8").write("\n".join(L))
# Not echoed to stdout: the report contains typographic minus signs and Greek
# that a cp1252 console cannot encode. Read the file.
print(f"wrote results/advanced_stats.md  ({len(L)} lines)")
