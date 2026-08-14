# Release-window study — how narrowly should 'force at release' be defined?

Fastballs with a paired velocity: n = 41. Sampling interval at 480 Hz is 2.083 ms, so a 5 ms window spans about 2.4 samples and a 10 ms window about 4.8. Cell control removes the mean of each of the 9 pitcher × commanded-effort combinations.


## Index + middle combined

| Definition | r (pitcher-centred) | p | r (pitcher × effort cell-centred) | p | n |
|:--|--:|--:|--:|--:|--:|
| Peak force, anywhere in the pitch | 0.566 | 0.000173 | 0.337 | 0.0551 | 41 |
| Mean force, final 5 ms | 0.596 | 7.79e-05 | 0.249 | 0.169 | 40 |
| Mean force, final 10 ms | 0.582 | 0.000103 | 0.307 | 0.0825 | 41 |
| Mean force, final 25 ms | 0.547 | 0.000317 | 0.305 | 0.0839 | 41 |
| Mean force, final 50 ms | 0.496 | 0.00131 | 0.303 | 0.0861 | 41 |
| Mean force, final 100 ms | 0.555 | 0.000249 | 0.288 | 0.104 | 41 |
| Impulse over final 5 ms | 0.560 | 0.000254 | 0.205 | 0.259 | 40 |
| Impulse over final 10 ms | 0.545 | 0.00033 | 0.314 | 0.0749 | 41 |
| Impulse over final 25 ms | 0.523 | 0.000627 | 0.243 | 0.173 | 41 |
| Impulse over final 50 ms | 0.510 | 0.000916 | 0.292 | 0.0997 | 41 |
| Impulse over final 100 ms | 0.556 | 0.000235 | 0.286 | 0.107 | 41 |
| Peak within final 40 ms | 0.492 | 0.00146 | 0.307 | 0.0822 | 41 |
| Unloading rate at release | 0.124 | 0.47 | -0.339 | 0.0672 | 38 |

## Index finger alone

| Definition | r (pitcher-centred) | p | r (pitcher × effort cell-centred) | p | n |
|:--|--:|--:|--:|--:|--:|
| Peak force, anywhere in the pitch | 0.503 | 0.0011 | 0.305 | 0.0847 | 41 |
| Mean force, final 5 ms | 0.499 | 0.00141 | 0.278 | 0.124 | 40 |
| Mean force, final 10 ms | 0.511 | 0.000892 | 0.302 | 0.0881 | 41 |
| Mean force, final 25 ms | 0.512 | 0.000871 | 0.283 | 0.111 | 41 |
| Mean force, final 50 ms | 0.465 | 0.00284 | 0.294 | 0.0962 | 41 |
| Mean force, final 100 ms | 0.527 | 0.000569 | 0.253 | 0.155 | 41 |
| Impulse over final 5 ms | 0.488 | 0.0019 | 0.287 | 0.112 | 40 |
| Impulse over final 10 ms | 0.471 | 0.0025 | 0.290 | 0.101 | 41 |
| Impulse over final 25 ms | 0.494 | 0.00141 | 0.230 | 0.197 | 41 |
| Impulse over final 50 ms | 0.486 | 0.00169 | 0.286 | 0.107 | 41 |
| Impulse over final 100 ms | 0.530 | 0.000513 | 0.258 | 0.148 | 41 |
| Peak within final 40 ms | 0.463 | 0.00302 | 0.329 | 0.0615 | 41 |
| Unloading rate at release | 0.199 | 0.252 | -0.202 | 0.292 | 37 |

## Thumb

| Definition | r (pitcher-centred) | p | r (pitcher × effort cell-centred) | p | n |
|:--|--:|--:|--:|--:|--:|
| **Peak force, anywhere in the pitch** | 0.351 | 0.0284 | **0.484** | 0.00435 | 41 |
| **Mean force, final 5 ms** | 0.449 | 0.00528 | **0.505** | 0.00376 | 39 |
| **Mean force, final 10 ms** | 0.450 | 0.00401 | **0.486** | 0.00418 | 41 |
| **Mean force, final 25 ms** | 0.401 | 0.0115 | **0.468** | 0.00606 | 41 |
| **Mean force, final 50 ms** | 0.388 | 0.0148 | **0.469** | 0.00594 | 41 |
| **Mean force, final 100 ms** | 0.402 | 0.0111 | **0.447** | 0.00919 | 41 |
| **Impulse over final 5 ms** | 0.469 | 0.00342 | **0.512** | 0.00324 | 39 |
| **Impulse over final 10 ms** | 0.453 | 0.00375 | **0.488** | 0.00401 | 41 |
| **Impulse over final 25 ms** | 0.422 | 0.00738 | **0.477** | 0.00505 | 41 |
| **Impulse over final 50 ms** | 0.399 | 0.012 | **0.477** | 0.00502 | 41 |
| **Impulse over final 100 ms** | 0.403 | 0.011 | **0.445** | 0.00943 | 41 |
| **Peak within final 40 ms** | 0.363 | 0.0233 | **0.477** | 0.00498 | 41 |
| Unloading rate at release | 0.336 | 0.0365 | 0.175 | 0.329 | 41 |

## Reading this table

The left pair of columns removes only between-pitcher differences and is confounded by the effort ladder, which moved grip force and velocity together by design. The right pair holds commanded effort exactly fixed. A window definition earns its place only if it survives on the right.

Windows narrower than about 10 ms are averaging fewer than five samples and are correspondingly noisy; any apparent advantage at 5 ms should be read with that in mind rather than as a real gain in resolution.
