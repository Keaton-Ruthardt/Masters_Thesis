# Advanced statistical analysis — computed output

Source: `results/per_pitch_features.csv`. Analyzable pitches: 63 (41 fastballs, 22 curveballs) from 3 pitchers. Warm-ups and pitches without a paired velocity are already excluded. Random seed 20260805; 20,000 permutations and 10,000 bootstrap resamples throughout.


## 1. Manipulation check — did the effort ladder work?

Before any grip result can be interpreted, the experimental manipulation has to be shown to have done something. If commanded effort did not move velocity, there is nothing to control for and nothing to hold fixed.

| Pitcher | 60 % mean (SD) | 80 % mean (SD) | 100 % mean (SD) | range (mph) | one-way F | p |
|:--|:--|:--|:--|--:|--:|--:|
| P1 | 67.9 (1.0) n=4 | 73.4 (0.8) n=4 | 78.1 (2.4) n=7 | 14.8 | 42.3 | 3.7e-06 |
| P2 | 62.5 (0.9) n=4 | 71.7 (1.0) n=4 | 81.0 (1.3) n=3 | 20.9 | 263.9 | 5e-08 |
| P3 | 59.2 (1.1) n=4 | 65.5 (2.2) n=4 | 73.9 (1.7) n=7 | 18.6 | 97.0 | 3.9e-08 |

Within-pitcher, commanded effort and velocity move together at r_rm = 0.946, 95 % CI [0.90, 0.97], p = 1.2e-19, n = 41, df = 37. The ladder produced the intended velocity spread in every pitcher. This is also the reason the raw correlations in Table 9 cannot be taken at face value: effort drives grip force and velocity simultaneously.


## 2. Table A1. Within-pitcher association with velocity, corrected for dependence and multiplicity (fastballs)

Repeated-measures correlation fits one slope common to all pitchers with a separate intercept for each, so the degrees of freedom are the real N − k − 1 and not the inflated N − 2 that pooling centred scores implies. The permutation p shuffles velocity within each pitcher and assumes no distribution at all. Holm controls the family-wise error rate across all 20 features; Benjamini–Hochberg controls the false-discovery rate.

| Feature | r_rm | 95 % CI | p | p (permutation) | p Holm | p BH | n | df |
|:--|--:|:--|--:|--:|--:|--:|--:|--:|
| **Index+middle impulse** | **0.630** | [0.39, 0.79] | 1.75e-05 | 0.0001 | 0.000349 | 0.000349 | 41 | 37 |
| **Middle impulse** | **0.597** | [0.35, 0.77] | 6e-05 | 0.0000 | 0.00114 | 0.000357 | 41 | 37 |
| **Index+middle peak force** | **0.594** | [0.34, 0.77] | 6.81e-05 | 0.0002 | 0.00123 | 0.000357 | 41 | 37 |
| **Index+middle force at release** | **0.590** | [0.34, 0.76] | 7.74e-05 | 0.0001 | 0.00132 | 0.000357 | 41 | 37 |
| **Index impulse** | **0.586** | [0.33, 0.76] | 8.92e-05 | 0.0001 | 0.00143 | 0.000357 | 41 | 37 |
| **Middle force at release** | **0.526** | [0.25, 0.72] | 0.000589 | 0.0006 | 0.00883 | 0.00177 | 41 | 37 |
| **Index+middle RFD** | **0.524** | [0.25, 0.72] | 0.000621 | 0.0005 | 0.00883 | 0.00177 | 41 | 37 |
| **Thumb impulse** | **0.514** | [0.24, 0.71] | 0.000808 | 0.0014 | 0.0105 | 0.00198 | 41 | 37 |
| **Index force at release** | **0.511** | [0.23, 0.71] | 0.000892 | 0.0007 | 0.0107 | 0.00198 | 41 | 37 |
| **Index peak force** | **0.503** | [0.22, 0.71] | 0.0011 | 0.0017 | 0.0121 | 0.00219 | 41 | 37 |
| **Middle peak force** | **0.496** | [0.21, 0.70] | 0.00132 | 0.0019 | 0.0132 | 0.0024 | 41 | 37 |
| **Total peak force** | **0.481** | [0.20, 0.69] | 0.00192 | 0.0031 | 0.0173 | 0.00291 | 41 | 37 |
| **Middle RFD** | **0.479** | [0.19, 0.69] | 0.00201 | 0.0027 | 0.0173 | 0.00291 | 41 | 37 |
| **Index RFD** | **0.479** | [0.19, 0.69] | 0.00204 | 0.0017 | 0.0173 | 0.00291 | 41 | 37 |
| **Thumb force at release** | **0.450** | [0.16, 0.67] | 0.00401 | 0.0045 | 0.024 | 0.00534 | 41 | 37 |
| Thumb RFD | 0.360 | [0.05, 0.61] | 0.0242 | 0.0156 | 0.121 | 0.0302 | 41 | 37 |
| Inter-finger discrepancy | -0.356 | [-0.60, -0.05] | 0.0259 | 0.0195 | 0.121 | 0.0305 | 41 | 37 |
| Thumb peak force | 0.351 | [0.04, 0.60] | 0.0284 | 0.0426 | 0.121 | 0.0315 | 41 | 37 |
| Thumb release lead | 0.134 | [-0.19, 0.43] | 0.414 | 0.4251 | 0.829 | 0.436 | 41 | 37 |
| Thumb-to-finger force ratio | 0.072 | [-0.25, 0.38] | 0.663 | 0.6738 | 0.829 | 0.663 | 41 | 37 |

Bold marks features surviving Holm correction across the family of 20. Features surviving Holm: 15 of 20; surviving Benjamini–Hochberg: 18.

Note how little the picture changes between the parametric and permutation columns. The associations are not artefacts of the normality assumption.


## 3. Table A2. The central test — does grip force predict velocity at a FIXED commanded effort?

This is the claim the project stands on, and it is tested three ways that fail differently. **Stratified centring** subtracts the mean of each pitcher × effort cell, so effort is held exactly fixed and nothing is assumed about its functional form; it is the strictest test and it discards all between-cell information. **Partial rmcorr** residualises on effort as a continuous covariate. **Mixed model** enters effort as a categorical fixed effect alongside a pitcher random intercept.

Cells: 9 pitcher × effort combinations, 3–7 pitches each (median 4). Stratified centring costs 9 degrees of freedom.

| Feature | r (full cell control) | p | p Holm | p BH | r (additive control) | p | slope |
|:--|--:|--:|--:|--:|--:|--:|--:|
| Thumb force at release | 0.486 | 0.00418 | 0.0836 | 0.0351 | 0.298 | 0.0728 | +0.126 mph/N |
| Thumb peak force | 0.484 | 0.00435 | 0.0836 | 0.0351 | 0.379 | 0.0207 | +0.079 mph/N |
| Total peak force | 0.475 | 0.00526 | 0.0947 | 0.0351 | 0.345 | 0.0365 | +0.052 mph/N |
| Thumb-to-finger force ratio | 0.420 | 0.015 | 0.256 | 0.0752 | 0.379 | 0.0206 | +2.564 mph/N |
| Index+middle peak force | 0.381 | 0.0285 | 0.456 | 0.113 | 0.236 | 0.16 | +0.110 mph/N |
| Thumb impulse | 0.370 | 0.0339 | 0.508 | 0.113 | 0.322 | 0.0516 | +0.495 mph/N |
| Index+middle force at release | 0.326 | 0.0638 | 0.894 | 0.161 | 0.062 | 0.713 | +0.097 mph/N |
| Middle impulse | 0.326 | 0.0644 | 0.894 | 0.161 | 0.249 | 0.137 | +1.403 mph/N |
| Index peak force | 0.305 | 0.0847 | 1 | 0.173 | 0.242 | 0.15 | +0.123 mph/N |
| Index force at release | 0.302 | 0.0881 | 1 | 0.173 | 0.042 | 0.807 | +0.125 mph/N |
| Middle peak force | 0.295 | 0.0951 | 1 | 0.173 | 0.116 | 0.495 | +0.152 mph/N |
| Index+middle impulse | 0.275 | 0.121 | 1 | 0.201 | 0.205 | 0.224 | +0.542 mph/N |
| Middle force at release | 0.218 | 0.222 | 1 | 0.342 | 0.066 | 0.696 | +0.129 mph/N |
| Index RFD | -0.210 | 0.24 | 1 | 0.343 | -0.002 | 0.991 | -0.000 mph/N |
| Index impulse | 0.198 | 0.269 | 1 | 0.358 | 0.140 | 0.407 | +0.610 mph/N |
| Index+middle RFD | -0.158 | 0.381 | 1 | 0.477 | 0.042 | 0.803 | -0.000 mph/N |
| Thumb release lead | 0.138 | 0.442 | 1 | 0.52 | 0.210 | 0.213 | +0.038 mph/ms |
| Thumb RFD | -0.030 | 0.867 | 1 | 0.963 | -0.045 | 0.792 | -0.000 mph/N |
| Middle RFD | -0.014 | 0.94 | 1 | 0.963 | 0.113 | 0.506 | -0.000 mph/N |
| Inter-finger discrepancy | -0.008 | 0.963 | 1 | 0.963 | 0.055 | 0.745 | -0.099 mph/unit |

Degrees of freedom under full cell control: 31.

**With commanded effort held exactly fixed, 0 of 20 features survive Holm (family-wise) correction and 3 survive Benjamini–Hochberg (false-discovery) correction.**

Surviving FDR control: Thumb force at release (r = 0.486, q = 0.035), Thumb peak force (r = 0.484, q = 0.035), Total peak force (r = 0.475, q = 0.035).
None clears the stricter family-wise threshold. The distinction is not a technicality: Holm asks whether *any* false positive is likely in the family of 20, Benjamini–Hochberg asks what proportion of the declared findings are false. At this sample size the honest summary is that these are the strongest candidates rather than established effects, and they are reported as such.

**The pre-specified primary feature, index force at release, gives r = 0.302, p = 0.0881 under full cell control (Holm p = 1).** Its unadjusted association in Table A1 was r = 0.511. The difference between those two numbers is the effort confound, and for this feature it accounts for essentially the whole association.


### Per-pitcher consistency of the leading features

A pooled partial correlation can be produced by one pitcher alone. Each leading feature is re-estimated within each pitcher separately, with that pitcher's own effort levels removed.

| Feature | P1 r (n) | P2 r (n) | P3 r (n) | same sign in all 3? |
|:--|--:|--:|--:|:--|
| Thumb force at release | 0.23 (15) | 0.41 (11) | 0.70 (15) | yes |
| Thumb peak force | 0.34 (15) | 0.43 (11) | 0.68 (15) | yes |
| Total peak force | 0.31 (15) | 0.48 (11) | 0.65 (15) | yes |
| Index force at release | 0.23 (15) | 0.28 (11) | 0.39 (15) | yes |

Per-pitcher estimates use that pitcher's own effort levels as the control and are badly underpowered on their own (P2 contributes 11 fastballs against 3 effort levels). They are reported to show the pooled estimate is not the product of a single pitcher, not as independent tests.


### Rank-based robustness — is the surviving result an artefact of the calibration curve?

Two channels were calibrated only to 19.6 N and the pitching peaks exceed that, so the top of the force scale is extrapolated. A rank-based partial correlation is invariant to any *monotonic* distortion of the force scale: if the surviving associations hold on ranks, no error in the shape of the calibration curve can have produced them. Ranks are taken within each pitcher × effort cell, which is the same control as Table A2.

| Feature | Pearson r (cell control) | Spearman r (cell control) | p | verdict |
|:--|--:|--:|--:|:--|
| Thumb force at release | 0.486 | 0.489 | 0.00391 | holds on ranks |
| Thumb peak force | 0.484 | 0.477 | 0.00498 | holds on ranks |
| Total peak force | 0.475 | 0.466 | 0.00628 | holds on ranks |
| Index force at release | 0.302 | 0.318 | 0.0711 | does not hold on ranks — treat as calibration-sensitive |
| Index impulse | 0.198 | 0.057 | 0.753 | does not hold on ranks — treat as calibration-sensitive |

## 3b. Why the thumb behaves differently from the fingers

The thumb is the only channel whose effort-controlled association is *stronger* than its raw one. That is a suppression pattern, and it has a direct explanation: how tightly each digit loads is not equally a readout of commanded effort. Each feature is correlated with commanded effort itself, within pitcher.

| Feature | r with commanded effort | p | r with velocity, effort fixed | p |
|:--|--:|--:|--:|--:|
| Index+middle impulse | 0.610 | 0.0000 | 0.275 | 0.121 |
| Index+middle force at release | 0.607 | 0.0000 | 0.326 | 0.0638 |
| Index impulse | 0.581 | 0.0001 | 0.198 | 0.269 |
| Index+middle peak force | 0.561 | 0.0002 | 0.381 | 0.0285 |
| Middle impulse | 0.560 | 0.0002 | 0.326 | 0.0644 |
| Index+middle RFD | 0.542 | 0.0004 | -0.158 | 0.381 |
| Middle force at release | 0.537 | 0.0004 | 0.218 | 0.222 |
| Index force at release | 0.528 | 0.0005 | 0.302 | 0.0881 |
| Index RFD | 0.507 | 0.0010 | -0.210 | 0.24 |
| Middle peak force | 0.490 | 0.0015 | 0.295 | 0.0951 |
| Middle RFD | 0.473 | 0.0024 | -0.014 | 0.94 |
| Index peak force | 0.458 | 0.0033 | 0.305 | 0.0847 |
| Thumb impulse | 0.445 | 0.0045 | 0.370 | 0.0339 |
| Total peak force | 0.400 | 0.0116 | 0.475 | 0.00526 |
| Thumb RFD | 0.395 | 0.0127 | -0.030 | 0.867 |
| Thumb force at release | 0.384 | 0.0159 | 0.486 | 0.00418 |
| Thumb peak force | 0.245 | 0.1326 | 0.484 | 0.00435 |
| Thumb release lead | 0.071 | 0.6675 | 0.138 | 0.442 |
| Thumb-to-finger force ratio | -0.053 | 0.7499 | 0.420 | 0.015 |
| Inter-finger discrepancy | -0.394 | 0.0130 | -0.008 | 0.963 |

Read the first column against the last. **The finger channels are largely a readout of commanded effort** — index force at release tracks effort at r = 0.528 — and once effort is held fixed they have little left to say about velocity. **Thumb peak force is the grip feature least coupled to commanded effort** (r = 0.245, not significant), and it is the one that retains an association with velocity once effort is fixed.

This reframes what the instrument is measuring. Index and middle loading is close to an intensity proxy: it says how hard the pitcher is trying, which the pitcher already knows. Thumb loading carries information that commanded effort does not, which is the only part of the grip signal that could be independently actionable. It is also the channel the closest prior work could not see at all, having instrumented only index and middle.

The claim this supports is narrower than the one the project set out to make, and it is about a different digit. It should be labelled exploratory: the thumb was not the pre-specified primary, it does not clear family-wise correction, and it emerged from the same 20-feature family that the multiplicity control exists to discipline. It is a hypothesis for the next study, not a result this one establishes.


## 4. Table A3. Mixed-effects models for the primary hypothesis

Outcome: release velocity (mph). Predictor: index force at release (z-scored within pitcher, so the coefficient is mph per within-pitcher SD). Random intercept for pitcher throughout. Models are nested and compared by likelihood-ratio test on ML fits.

Unconditional ICC = 0.000. The pitcher variance component is estimated at the boundary of its parameter space — effectively zero — because the effort ladder deliberately created within-pitcher velocity variance far larger than the differences between these three pitchers. A boundary estimate is not evidence that pitches are independent: with three clusters the component is barely identifiable, so every estimate in this report is a within-pitcher estimate regardless.

| Feature | β per within-pitcher SD (95 % CI) | p | χ²(1) vs effort-only | p | marginal R² effort-only → +grip |
|:--|:--|--:|--:|--:|:--|
| Index force at release | +0.27 [-0.50, +1.05] mph | 0.491 | 0.47 | 0.492 | 0.774 → 0.776 |
| Index peak force | +0.50 [-0.23, +1.22] mph | 0.177 | 1.78 | 0.182 | 0.774 → 0.779 |
| Index impulse | +0.27 [-0.54, +1.08] mph | 0.516 | 0.42 | 0.517 | 0.774 → 0.776 |
| Middle impulse | +0.52 [-0.25, +1.30] mph | 0.188 | 1.70 | 0.192 | 0.774 → 0.779 |
| **Thumb peak force** | +0.67 [+0.02, +1.32] mph | 0.043 | 3.89 | **0.0486** | 0.774 → 0.783 |
| Thumb force at release | +0.55 [-0.16, +1.26] mph | 0.129 | 2.24 | 0.134 | 0.774 → 0.780 |
| Total peak force | +0.52 [-0.20, +1.25] mph | 0.159 | 1.93 | 0.165 | 0.774 → 0.779 |
| Index RFD | -0.13 [-0.88, +0.62] mph | 0.733 | 0.12 | 0.733 | 0.774 → 0.774 |

The mixed model enters effort additively and pitcher as a random intercept, so it is a weaker control than the full cell centring in Table A2 and should agree with it in direction. It does.

Allowing the grip slope to vary by pitcher does not improve fit (χ²(2) = 3.04, p = 0.219), so a single common slope is retained. With three pitchers this test has very little power and is a check, not evidence of homogeneity.


## 5. Variance partitioning — how much does grip add over effort?

Velocity variance is decomposed into the part unique to grip, the part unique to commanded effort, and the part they share. The shared part is the confound made visible: variance neither predictor can be credited with alone. All increments are over a pitcher-only baseline, so between-pitcher variance is removed first and cannot inflate them. Effort enters as a three-level factor, matching the additive column of Table A2.

| Feature | R² effort | R² grip | R² both | unique grip | unique effort | shared |
|:--|--:|--:|--:|--:|--:|--:|
| Index force at release | 0.743 | 0.217 | 0.744 | **0.000** | 0.527 | 0.217 |
| Index peak force | 0.743 | 0.210 | 0.749 | **0.005** | 0.538 | 0.205 |
| Index impulse | 0.743 | 0.285 | 0.745 | **0.002** | 0.460 | 0.284 |
| Middle impulse | 0.743 | 0.296 | 0.749 | **0.005** | 0.453 | 0.291 |
| Thumb peak force | 0.743 | 0.103 | 0.756 | **0.013** | 0.654 | 0.090 |
| Thumb force at release | 0.743 | 0.169 | 0.751 | **0.008** | 0.583 | 0.161 |
| Total peak force | 0.743 | 0.193 | 0.754 | **0.010** | 0.561 | 0.182 |
| Index RFD | 0.743 | 0.191 | 0.743 | **0.000** | 0.553 | 0.191 |

Read the *unique grip* column against the *shared* column. Where unique is near zero and shared is large, the feature is carrying commanded effort and nothing else — it looks predictive only because the ladder moved both quantities together.


## 6. Cluster bootstrap

Resampling pitchers with replacement, then pitches within each resampled pitcher. This is the only interval here that propagates the uncertainty of *which three pitchers* were measured. Reported both for the raw association and, where estimable, for the association with effort held fixed.

| Feature | r_rm (raw) | analytic 95 % CI | cluster bootstrap 95 % CI | permutation p |
|:--|--:|:--|:--|--:|
| Index force at release | 0.511 | [0.23, 0.71] | [0.26, 0.72] | 0.0004 |
| Thumb force at release | 0.450 | [0.16, 0.67] | [0.17, 0.68] | 0.0044 |
| Thumb peak force | 0.351 | [0.04, 0.60] | [0.05, 0.61] | 0.0432 |
| Total peak force | 0.481 | [0.20, 0.69] | [0.22, 0.76] | 0.0044 |

Every bootstrap interval is wider than its analytic counterpart. That gap is the honest cost of three pitchers: resampling at the pitcher level admits that a different three pitchers could have produced a noticeably different estimate, and no number of pitches per pitcher repairs it.


## 7. Instrument stability across a session

Thin-film force sensors creep under sustained load and drift with temperature. If grip readings trended across a session, an apparent grip–velocity association could be a drift artefact aligned with fatigue. Each feature is regressed on pitch order within pitcher.

| Feature | r with pitch order | p | interpretation |
|:--|--:|--:|:--|
| Index force at release | -0.449 | 0.00417 | TRENDS — check |
| Index peak force | -0.243 | 0.136 | no detectable drift |
| Total peak force | -0.276 | 0.0889 | no detectable drift |
| velo_mph | -0.736 | 9.61e-08 | TRENDS — check |

Order is confounded with the protocol itself — the submaximal blocks were thrown last — so a trend here would not by itself prove drift. It is reported because its absence removes one alternative explanation.


### Within-condition repeatability

Coefficient of variation of each feature within a pitcher × effort cell, which bounds how much of the pitch-to-pitch spread is measurement noise rather than real variation.

| Feature | median within-cell CV | pooled within-cell SD |
|:--|--:|--:|
| Index force at release | 0.306 | 3.76 |
| Index peak force | 0.202 | 3.51 |
| Index impulse | 0.297 | 0.48 |
| Total peak force | 0.305 | 13.21 |
| Inter-finger discrepancy | 0.288 | 0.13 |

## 8. Bounding the negative results

A non-significant result is not evidence of no effect unless the interval excludes the effect that was expected. Each feature that failed is checked against the effect size the reference literature reports (Yeh et al. give r ≈ 0.53 to 0.58 for finger characteristics against velocity).

The features that matter here are the ones that fail *under effort control*, since that is the test the project's claim depends on. A Fisher interval is placed on each effort-controlled estimate and checked against r = 0.53.

| Feature | r (cell control) | 95 % CI | excludes r = 0.53? | verdict |
|:--|--:|:--|:--|:--|
| Index+middle force at release | 0.326 | [-0.03, 0.61] | no | underpowered — cannot be distinguished from it |
| Middle impulse | 0.326 | [-0.03, 0.61] | no | underpowered — cannot be distinguished from it |
| Index peak force | 0.305 | [-0.05, 0.59] | no | underpowered — cannot be distinguished from it |
| Index force at release | 0.302 | [-0.05, 0.59] | no | underpowered — cannot be distinguished from it |
| Middle peak force | 0.295 | [-0.06, 0.58] | no | underpowered — cannot be distinguished from it |
| Index+middle impulse | 0.275 | [-0.08, 0.57] | no | underpowered — cannot be distinguished from it |
| Middle force at release | 0.218 | [-0.14, 0.53] | yes | bounded below the literature value |
| Index RFD | -0.210 | [-0.52, 0.15] | yes | bounded below the literature value |
| Index impulse | 0.198 | [-0.16, 0.51] | yes | bounded below the literature value |
| Index+middle RFD | -0.158 | [-0.48, 0.20] | yes | bounded below the literature value |
| Thumb release lead | 0.138 | [-0.22, 0.46] | yes | bounded below the literature value |
| Thumb RFD | -0.030 | [-0.37, 0.32] | yes | bounded below the literature value |
| Middle RFD | -0.014 | [-0.36, 0.34] | yes | bounded below the literature value |
| Inter-finger discrepancy | -0.008 | [-0.36, 0.34] | yes | bounded below the literature value |

Minimum detectable within-pitcher correlation at α = 0.05 (two-sided) with df = 37 is r = 0.316. Any |r| below that could not have reached significance in this design regardless of the truth.


## 9. Fastball versus curveball, with pitcher as a blocking factor

Reported on force *shares* and timing rather than newtons, because a given finger is read by a different sensor on each pitch type and absolute values are therefore not comparable across types. Two-way model with pitcher as a blocking factor tests whether the grip contrast holds after every between-pitcher difference is removed.

| Feature | FB mean | CB mean | difference | F (pitch type) | p | partial η² | replicates in all 3? |
|:--|--:|--:|--:|--:|--:|--:|:--|
| thumb_share | 0.408 | 0.070 | +0.338 | 242.8 | 1.4e-22 | 0.805 | yes |
| middle_share | 0.184 | 0.515 | -0.331 | 258.1 | 3.25e-23 | 0.814 | yes |
| pointer_share | 0.408 | 0.415 | -0.007 | 0.1 | 0.743 | 0.002 | no |
| CV_peak | 0.464 | 0.753 | -0.289 | 60.7 | 1.23e-10 | 0.507 | yes |
| thumb_lead_ms | 12.825 | 4.885 | +7.940 | 33.5 | 2.93e-07 | 0.362 | yes |

## 10. Secondary ball-flight outcomes


**Spin rate**: captured for 1 of 63 analyzable pitches (P2: 1).
Too few observations for inference. Values are reported descriptively only, and no correlation with grip is computed — with n = 1 any estimate would be uninterpretable.

| Pitcher | pitch type | velocity (mph) | spin rate |
|:--|:--|--:|--:|
| P2 | curveball | 69.1 | 1676.0 |

**Induced vertical break**: captured for 4 of 63 analyzable pitches (P1: 2, P2: 1, P3: 1).
Too few observations for inference. Values are reported descriptively only, and no correlation with grip is computed — with n = 4 any estimate would be uninterpretable.

| Pitcher | pitch type | velocity (mph) | induced vertical break |
|:--|:--|--:|--:|
| P1 | fastball | 77.0 | 7.0 |
| P1 | curveball | 71.9 | 0.0 |
| P2 | curveball | 70.4 | -3.4 |
| P3 | curveball | 68.9 | -3.8 |

**Horizontal break**: captured for 4 of 63 analyzable pitches (P1: 2, P2: 1, P3: 1).
Too few observations for inference. Values are reported descriptively only, and no correlation with grip is computed — with n = 4 any estimate would be uninterpretable.

| Pitcher | pitch type | velocity (mph) | horizontal break |
|:--|:--|--:|--:|
| P1 | fastball | 77.0 | 18.9 |
| P1 | curveball | 71.9 | -11.6 |
| P2 | curveball | 70.4 | -13.3 |
| P3 | curveball | 68.9 | -11.8 |