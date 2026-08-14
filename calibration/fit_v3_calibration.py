"""Fit v3 calibration — reads the weight sequence from each capture's header.

Supersedes fit_v2_calibration.py, which hardcoded six weights (300..2000 g) and
kept the six LARGEST plateaus. On the 7-step BK/RM captures that pairs the
600..2900 g plateaus with 300..2000 g labels — every point mislabeled low, which
biases calFactor down. This version parses the "300g,600g,..." header line per
file, so 6- and 7-step captures both fit correctly.

Level extraction: each test is a monotonic staircase held ~5 s per level at
10 Hz, with no return to zero between levels, so gap-splitting doesn't work.
Instead we 1-D k-means the loaded samples into k = n_levels clusters and take
each cluster's median. That tolerates uneven hold durations and the transition
samples between levels.

Model:  F(N) = k * G,   G = ADC/(4095-ADC),   k fit through the origin.

Run from this directory:  python fit_v3_calibration.py
"""
import glob
import os
import re

import numpy as np

G_ACCEL = 9.81
ADC_MAX = 4095
LOAD_THR = 15        # avg ADC above this counts as loaded
MIN_LOADED = 40      # a test needs at least this many loaded samples
DEFAULT_GRAMS = [300, 600, 900, 1200, 1500, 2000]   # pre-header captures


def parse_header_grams(path):
    """Pull the '300g,600g,...' weight line out of the first few lines.

    Accepts grams and kilograms in the same line — captures have been written
    both ways ('2000g' and '2kg'), and a missed level silently mis-fits the
    whole sensor, so both forms are parsed explicitly.
    """
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for _ in range(6):
            line = fh.readline()
            if not line:
                break
            found = re.findall(r"(\d+(?:\.\d+)?)\s*(kg|g)\b", line, re.I)
            if len(found) >= 3:
                return [int(round(float(v) * (1000 if u.lower() == "kg" else 1)))
                        for v, u in found]
    return list(DEFAULT_GRAMS)


def parse_tests(path):
    """Split a capture into per-test lists of the 'avg' column."""
    tests, cur = [], []
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if re.match(r"\s*test\s*\d", line, re.I):
                if cur:
                    tests.append(cur)
                cur = []
                continue
            m = re.match(r"\s*\d+\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", line)
            if m:
                cur.append(int(m.group(1)))
    if cur:
        tests.append(cur)
    return tests


def kmeans_1d(values, k, iters=60):
    """Lloyd's algorithm on 1-D data, seeded at evenly spaced quantiles."""
    v = np.asarray(values, dtype=float)
    centers = np.quantile(v, np.linspace(0.08, 0.92, k))
    for _ in range(iters):
        assign = np.argmin(np.abs(v[:, None] - centers[None, :]), axis=1)
        moved = False
        for c in range(k):
            members = v[assign == c]
            if len(members):
                new = float(np.median(members))
                if abs(new - centers[c]) > 1e-9:
                    centers[c] = new
                    moved = True
        centers.sort()
        if not moved:
            break
    assign = np.argmin(np.abs(v[:, None] - centers[None, :]), axis=1)
    levels, counts = [], []
    for c in range(k):
        members = v[assign == c]
        if len(members):
            levels.append(float(np.median(members)))
            counts.append(int(len(members)))
    return levels, counts


def fit_sensor(path):
    grams = parse_header_grams(path)
    forces = [g / 1000.0 * G_ACCEL for g in grams]
    k_levels = len(grams)
    tests = parse_tests(path)

    Gs, Fs, per_test_k, used = [], [], [], 0
    for t in tests:
        loaded = [v for v in t if v > LOAD_THR]
        if len(loaded) < MIN_LOADED:
            continue
        levels, _ = kmeans_1d(loaded, k_levels)
        if len(levels) < k_levels:
            continue
        used += 1

        g_test, f_test = [], []
        for adc, F in zip(levels, forces):
            if 0 < adc < ADC_MAX:
                g_test.append(adc / (ADC_MAX - adc))
                f_test.append(F)
        if not g_test:
            continue
        g_arr, f_arr = np.array(g_test), np.array(f_test)
        Gs.extend(g_test)
        Fs.extend(f_test)
        per_test_k.append(float(np.sum(g_arr * f_arr) / np.sum(g_arr * g_arr)))

    G, F = np.array(Gs), np.array(Fs)
    k = float(np.sum(G * F) / np.sum(G * G))
    pred = k * G
    r2 = 1 - np.sum((F - pred) ** 2) / np.sum((F - F.mean()) ** 2)
    kt = np.array(per_test_k)
    cv = float(kt.std(ddof=1) / kt.mean() * 100) if len(kt) > 1 else float("nan")
    return {
        "k": k, "r2": r2, "cv": cv, "tests_used": used, "tests_total": len(tests),
        "max_force": max(forces), "grams": grams,
    }


def main():
    paths = sorted(set(glob.glob("Sensor*.txt") + glob.glob("sensor*.txt")),
                   key=lambda p: os.path.basename(p).lower())
    rows = []
    for path in paths:
        name = os.path.basename(path).replace(".txt", "")
        name = re.sub(r"(?i)^sensor\s*", "", name).strip()
        r = fit_sensor(path)
        rows.append((name, r))
        print(f"{name:>4}: calFactor {r['k']:6.1f} N | R2 {r['r2']:.3f} | "
              f"CV {r['cv']:4.1f}% | {r['tests_used']}/{r['tests_total']} tests | "
              f"to {r['max_force']:.1f} N ({len(r['grams'])} levels)")

    with open("calfactors_v3.csv", "w", encoding="utf-8") as fh:
        fh.write("# SmartBall v2 calibration — fit_v3_calibration.py\n")
        fh.write("# Model: F(N) = calFactor * ADC/(4095-ADC), through origin.\n")
        fh.write("# Weight sequence read per-file from the capture header.\n")
        fh.write("sensor,calFactor_N,R2,repeatability_cv_pct,tests,max_force_N\n")
        for name, r in rows:
            fh.write(f"{name},{r['k']:.0f},{r['r2']:.3f},{r['cv']:.1f},"
                     f"{r['tests_used']},{r['max_force']:.1f}\n")
    print("\nwrote calfactors_v3.csv")


if __name__ == "__main__":
    main()
