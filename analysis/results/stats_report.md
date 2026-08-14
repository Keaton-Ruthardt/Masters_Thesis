# Data Analysis and Results — computed output

Generated from 3 sessions. 83 pitch events detected, 70 paired with an outcome, 7 of those warm-ups, 63 analyzable. Force at release is the mean over the final 10 ms of contact.


## Table 8. Participant characteristics and pitch counts

| Pitcher | Age (y) | Height (cm) | Mass (kg) | Fastballs | Curveballs | Warm-ups | Paired | Unpaired | Analyzable |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| P1 | 23 | 190.5 | 83.9 | 16 | 8 | 0 | 23 | 1 | 23 |
| P2 | 20 | 182.9 | 77.1 | 20 | 14 | 7 | 24 | 10 | 17 |
| P3 | 21 | 188.0 | 93.0 | 17 | 8 | 0 | 23 | 2 | 23 |
| **All / mean** | 21.3 | 187.1 | 84.7 | 53 | 30 | 7 | 70 | 13 | 63 |

Anthropometrics are reported to describe the sample. With three pitchers they cannot enter any model: a between-pitcher covariate is perfectly confounded with pitcher identity at n = 3.


## Effort labelling audit

Every analyzable pitch carries an effort label from exactly one source. An explicit `NN%` prefix outranks an active `effort=NN` state marker, which outranks the maximum-effort default. Effort is never inferred from velocity.

| Pitcher | explicit prefix | state marker | default (max) | warm-up (excluded) |
|:--|--:|--:|--:|--:|
| P1 | 0 | 8 | 15 | 0 |
| P2 | 11 | 0 | 6 | 7 |
| P3 | 8 | 0 | 15 | 0 |
| **All** | 19 | 8 | 36 | 7 |

| Pitcher | commanded effort levels present (analyzable) |
|:--|:--|
| P1 | 60 % (n = 4), 80 % (n = 4), 100 % (n = 15) |
| P2 | 60 % (n = 4), 80 % (n = 4), 100 % (n = 9) |
| P3 | 60 % (n = 4), 80 % (n = 4), 100 % (n = 15) |

## Descriptive statistics — peak and release force by finger

| Pitcher | Pitch | Finger | n | peak mean±SD (N) | F_rel mean±SD (N) |
|:--|:--|:--|--:|:--|:--|
| P1 | curveball | pointer | 8 | 17.6 ± 4.7 | 10.9 ± 2.8 |
| P1 | curveball | middle | 8 | 25.8 ± 8.2 | 20.5 ± 5.7 |
| P1 | curveball | thumb | 8 | 4.2 ± 2.5 | 2.5 ± 2.2 |
| P1 | fastball | pointer | 16 | 19.7 ± 3.6 | 12.1 ± 5.2 |
| P1 | fastball | middle | 16 | 9.9 ± 3.4 | 6.5 ± 3.5 |
| P1 | fastball | thumb | 16 | 20.7 ± 5.4 | 10.7 ± 5.4 |
| P2 | curveball | pointer | 14 | 10.8 ± 8.9 | 8.1 ± 6.7 |
| P2 | curveball | middle | 14 | 15.9 ± 12.3 | 11.5 ± 9.8 |
| P2 | curveball | thumb | 14 | 2.5 ± 1.2 | 1.4 ± 1.2 |
| P2 | fastball | pointer | 20 | 23.4 ± 3.8 | 14.2 ± 3.0 |
| P2 | fastball | middle | 20 | 12.9 ± 5.0 | 10.2 ± 4.8 |
| P2 | fastball | thumb | 20 | 22.8 ± 9.8 | 12.0 ± 5.8 |
| P3 | curveball | pointer | 8 | 19.4 ± 2.5 | 14.8 ± 2.4 |
| P3 | curveball | middle | 8 | 20.2 ± 6.1 | 16.4 ± 4.8 |
| P3 | curveball | thumb | 8 | 2.5 ± 0.7 | 1.4 ± 0.9 |
| P3 | fastball | pointer | 17 | 15.9 ± 5.3 | 8.9 ± 4.4 |
| P3 | fastball | middle | 17 | 6.5 ± 3.2 | 4.1 ± 2.4 |
| P3 | fastball | thumb | 17 | 18.9 ± 11.6 | 9.3 ± 7.6 |

## Release ordering

Thumb lead over the first finger to release, n = 83 pitches.

| Group | n | mean (ms) | SD | median | % thumb first | % above 4.17 ms floor |
|:--|--:|--:|--:|--:|--:|--:|
| ALL | 83 | 9.8 | 6.9 | 10.5 | 84% | 71% |
| P1 curveball | 8 | 4.3 | 2.5 | 4.2 | 88% | 50% |
| P1 fastball | 16 | 13.9 | 3.5 | 14.5 | 100% | 100% |
| P2 curveball | 14 | 1.8 | 3.4 | 0.0 | 43% | 14% |
| P2 fastball | 20 | 12.5 | 4.6 | 12.5 | 100% | 90% |
| P3 curveball | 8 | 6.0 | 3.5 | 6.2 | 88% | 62% |
| P3 fastball | 17 | 13.8 | 7.8 | 14.6 | 82% | 82% |

One-sample tests against zero lead: t = 12.95, p = 1.6e-21; Wilcoxon W = 6, p = 3.1e-13.

Pointer-to-middle gap: mean -0.75 ms, SD 1.28, |gap| < 4.17 ms in 98% of pitches (n = 83). Sign split: 0% middle last.


## Table 9. Grip features vs release velocity (fastballs)

Within-pitcher centred, pooled. Per-pitcher r shown for consistency.

| Feature | pooled r | 95% CI | p | n | P1 r (n) | P2 r (n) | P3 r (n) |
|:--|--:|:--|--:|--:|:--|:--|:--|
| pointer_F_rel_N | 0.511 | [0.24, 0.71] | 0.000644 | 41 | 0.66 (15) | 0.39 (11) | 0.54 (15) |
| pointer_peak_N | 0.503 | [0.23, 0.70] | 0.0008 | 41 | 0.52 (15) | 0.40 (11) | 0.58 (15) |
| pointer_RFD_Ns | 0.479 | [0.20, 0.69] | 0.00153 | 41 | 0.26 (15) | 0.74 (11) | 0.33 (15) |
| pointer_impulse_Ns | 0.586 | [0.34, 0.76] | 5.72e-05 | 41 | 0.69 (15) | 0.49 (11) | 0.61 (15) |
| middle_F_rel_N | 0.526 | [0.26, 0.72] | 0.000416 | 41 | 0.60 (15) | 0.61 (11) | 0.40 (15) |
| middle_peak_N | 0.496 | [0.22, 0.70] | 0.000974 | 41 | 0.66 (15) | 0.50 (11) | 0.39 (15) |
| middle_RFD_Ns | 0.479 | [0.20, 0.69] | 0.00152 | 41 | 0.51 (15) | 0.55 (11) | 0.48 (15) |
| middle_impulse_Ns | 0.597 | [0.35, 0.76] | 3.77e-05 | 41 | 0.73 (15) | 0.59 (11) | 0.53 (15) |
| thumb_F_rel_N | 0.450 | [0.17, 0.67] | 0.00312 | 41 | 0.60 (15) | 0.39 (11) | 0.44 (15) |
| thumb_peak_N | 0.351 | [0.05, 0.59] | 0.0244 | 41 | 0.49 (15) | 0.28 (11) | 0.37 (15) |
| thumb_RFD_Ns | 0.360 | [0.06, 0.60] | 0.0206 | 41 | 0.32 (15) | 0.67 (11) | 0.31 (15) |
| thumb_impulse_Ns | 0.514 | [0.25, 0.71] | 0.000581 | 41 | 0.62 (15) | 0.45 (11) | 0.53 (15) |
| total_peak_N | 0.481 | [0.20, 0.69] | 0.00144 | 41 | 0.76 (15) | 0.39 (11) | 0.47 (15) |
| CV_peak | -0.356 | [-0.60, -0.05] | 0.0221 | 41 | -0.34 (15) | -0.48 (11) | -0.33 (15) |
| thumb_lead_ms | 0.134 | [-0.18, 0.42] | 0.402 | 41 | -0.41 (15) | -0.15 (11) | 0.44 (15) |

## Fastball vs curveball grip contrast (within pitcher, paired)

| Pitcher | Feature | FB mean | CB mean | diff | t | p |
|:--|:--|--:|--:|--:|--:|--:|
| P1 | thumb_lead_ms | 13.87 | 4.32 | +9.55 | 7.38 | 6.05e-07 |
| P1 | total_peak_N | 50.18 | 47.60 | +2.58 | 0.61 | 0.552 |
| P1 | CV_peak | 0.38 | 0.75 | -0.37 | -6.06 | 1.39e-05 |
| P1 | thumb_share | 0.41 | 0.09 | +0.32 | 16.07 | 4.61e-13 |
| P1 | pointer_share | 0.40 | 0.38 | +0.02 | 0.34 | 0.739 |
| P1 | middle_share | 0.20 | 0.53 | -0.34 | -7.73 | 3.03e-05 |
| P2 | thumb_lead_ms | 12.47 | 1.78 | +10.69 | 7.53 | 1.48e-08 |
| P2 | total_peak_N | 59.12 | 29.16 | +29.96 | 4.62 | 0.000114 |
| P2 | CV_peak | 0.38 | 0.69 | -0.30 | -5.42 | 2.29e-05 |
| P2 | thumb_share | 0.37 | 0.20 | +0.17 | 3.10 | 0.00688 |
| P2 | pointer_share | 0.41 | 0.30 | +0.11 | 2.86 | 0.0102 |
| P2 | middle_share | 0.22 | 0.50 | -0.29 | -9.22 | 2.16e-08 |
| P3 | thumb_lead_ms | 13.83 | 6.00 | +7.83 | 3.31 | 0.00307 |
| P3 | total_peak_N | 41.35 | 42.08 | -0.73 | -0.14 | 0.888 |
| P3 | CV_peak | 0.56 | 0.73 | -0.17 | -4.12 | 0.000465 |
| P3 | thumb_share | 0.42 | 0.06 | +0.35 | 10.78 | 1.4e-09 |
| P3 | pointer_share | 0.41 | 0.47 | -0.05 | -1.66 | 0.111 |
| P3 | middle_share | 0.17 | 0.47 | -0.30 | -8.73 | 3.04e-07 |