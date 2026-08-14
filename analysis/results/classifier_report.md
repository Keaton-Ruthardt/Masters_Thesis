# Pitch-type classification from grip force — instrument validation

n = 63 analyzable pitches (41 fastballs, 22 curveballs) from 3 pitchers. Features: pointer_share, middle_share, thumb_share, CV_peak, thumb_lead_ms. No ball-flight measurement enters the model.

Pitchers contributing curveballs: P1, P2, P3 (3 of 3). Leave-one-pitcher-out is therefore a 3-fold test, and every fold is trained without the tested pitcher entirely.


## Table B1. Classification accuracy

| Validation scheme | Accuracy | What it tests |
|:--|--:|:--|
| Majority-class baseline | 0.651 | — |
| Leave-one-pitch-out | 0.984 | generalization to an unseen pitch |
| **Leave-one-pitcher-out** | **0.986** | **generalization to an unseen pitcher** |

**Per-fold accuracy (leave-one-pitcher-out).** A single mean can hide one fold collapsing.

| Held-out pitcher | n pitches | FB / CB | accuracy |
|:--|--:|:--|--:|
| P1 | 23 | 15 / 8 | 1.000 |
| P2 | 17 | 11 / 6 | 1.000 |
| P3 | 23 | 15 / 8 | 0.957 |

Fold accuracies range 0.957 to 1.000.

**Permutation test.** Pitch-type labels were shuffled within pitcher and the entire leave-one-pitcher-out procedure re-run 5,000 times. Observed accuracy 0.986; permutation p = **0.0002**. The accuracy is not an artefact of class imbalance or of having few folds.


**Confusion matrix (leave-one-pitcher-out, pooled over folds).**

| | predicted FB | predicted CB |
|:--|--:|--:|
| **actual FB** | 40 | 1 |
| **actual CB** | 0 | 22 |

Sensitivity to curveballs 1.000, specificity 0.976.


## Table B2. Standardized coefficients

Fitted on all pitches. Sign is relative to the curveball class.

| Feature | standardized coefficient |
|:--|--:|
| middle_share | +1.48 |
| thumb_share | -1.40 |
| CV_peak | +0.67 |
| pointer_share | -0.12 |
| thumb_lead_ms | -0.10 |

The discriminating signal is a thumb-to-middle trade-off. Index share contributes least, which is exactly the point: an instrument reading only index and middle would be sampling the least informative channel and one of the two most informative, and would have no thumb channel at all.


## Interpretation

This validates the four-position design; it is not a biomechanical finding. The grip was deliberately changed between pitch types and the sensors are fixed to the ball, so a detectable difference in which channels load is the expected consequence of the protocol rather than a discovery about pitching. What is worth reporting is that the difference transfers to a pitcher the model has never seen, and that is what justifies four sensor positions over the two used in the closest prior work.
