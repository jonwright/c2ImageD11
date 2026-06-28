#!/usr/bin/env python3
"""Accuracy comparison: f32 vs f64 for score_and_refine.

Compares n (count) and sumdrlv2 between float32 and float64
g-vector paths, with small angular perturbations.

Usage:
    python check_accuracy.py
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from test_data import generate_random_rotations


def rotation_matrix_x(angle_deg):
    c = np.cos(np.radians(angle_deg))
    s = np.sin(np.radians(angle_deg))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rotation_matrix_y(angle_deg):
    c = np.cos(np.radians(angle_deg))
    s = np.sin(np.radians(angle_deg))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rotation_matrix_z(angle_deg):
    c = np.cos(np.radians(angle_deg))
    s = np.sin(np.radians(angle_deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def random_perturbation(angle_deg):
    """Random 3D rotation of given angle (degrees)."""
    axis = np.random.randn(3)
    axis = axis / np.linalg.norm(axis)
    c = np.cos(np.radians(angle_deg))
    s = np.sin(np.radians(angle_deg))
    K = np.array([[0, -axis[2], axis[1]],
                  [axis[2], 0, -axis[0]],
                  [-axis[1], axis[0], 0]])
    return np.eye(3) + s * K + (1 - c) * np.dot(K, K)


def test_single_peak_set():
    """Single UBI with known hkls, perturbed by small rotations."""
    import c2ImageD11
    fn = c2ImageD11.score_and_refine

    B = np.eye(3) / 4.06
    rng = np.random.RandomState(42)

    # Generate one UBI from a random rotation
    U = generate_random_rotations(1, 42)[0]
    UB_ideal = np.dot(U, B)
    ubi_ideal = np.linalg.inv(UB_ideal)

    # Generate hkl grid
    hmax = 8
    r = np.arange(-hmax, hmax + 1)
    hkls = np.array(np.meshgrid(r, r, r)).T.reshape(-1, 3)
    mask = ~((hkls[:, 0] == 0) & (hkls[:, 1] == 0) & (hkls[:, 2] == 0))
    hkls = hkls[mask]  # 4912 hkls (excl 0,0,0)

    # Compute ground truth g-vectors (float64)
    gv_f64 = np.dot(hkls, UB_ideal.T)  # shape (4912, 3)

    print("=" * 70)
    print("ACCURACY TEST 1: Single peak set (4912 peaks)")
    print("=" * 70)

    for angle_deg in [0.1, 0.5, 1.0, 5.0]:
        print("\n--- Perturbation: %.1f degrees ---" % angle_deg)

        # Perturb the UBI
        dR = random_perturbation(angle_deg)
        ubi_pert = np.dot(dR, ubi_ideal)

        # Run with float64 gv
        ubi_f64 = ubi_pert.copy()
        n_f64, s_f64 = fn(ubi_f64, gv_f64, 0.02)

        # Run with float32 gv
        gv_f32 = gv_f64.astype(np.float32)
        ubi_f32 = ubi_pert.copy()
        n_f32, s_f32 = fn(ubi_f32, gv_f32, 0.02)

        # Same test with tol=0.05
        ubi_f64_2 = ubi_pert.copy()
        n_f64b, s_f64b = fn(ubi_f64_2, gv_f64, 0.05)
        ubi_f32_2 = ubi_pert.copy()
        n_f32b, s_f32b = fn(ubi_f32_2, gv_f32, 0.05)

        print("  tol=0.02:  f64 n=%5d s=%.6f | f32 n=%5d s=%.6f | n_diff=%d s_diff=%.2e" %
              (n_f64, s_f64, n_f32, s_f32, n_f64 - n_f32, s_f64 - s_f32))
        print("  tol=0.05:  f64 n=%5d s=%.6f | f32 n=%5d s=%.6f | n_diff=%d s_diff=%.2e" %
              (n_f64b, s_f64b, n_f32b, s_f32b, n_f64b - n_f32b, s_f64b - s_f32b))

        # Check refined UBI difference
        ubi_diff = np.linalg.norm(ubi_f64 - ubi_ideal)  # f64 refined
        ubi_diff_f32 = np.linalg.norm(ubi_f32 - ubi_ideal)  # f32 refined
        print("  |ubi_refined - ubi_ideal|: f64=%.2e  f32=%.2e  ratio=%.2f" %
              (ubi_diff, ubi_diff_f32, ubi_diff_f32 / ubi_diff if ubi_diff > 0 else 0))


def test_overlapping_grains():
    """1000 grains with overlapping peaks, tol=0.02."""
    import c2ImageD11
    fn = c2ImageD11.score_and_refine

    B = np.eye(3) / 4.06
    rng = np.random.RandomState(123)

    n_grains = 1000
    peaks_per_grain = 100
    tol = 0.02

    # Pre-generate random hkls (same set for all grains)
    all_hkls = rng.randint(-8, 9, size=(peaks_per_grain, 3)).astype(np.float64)

    # Generate random rotations for all grains
    Us = generate_random_rotations(n_grains, 123)

    print("\n" + "=" * 70)
    print("ACCURACY TEST 2: %d overlapping grains, %d peaks each, tol=%.2f" %
          (n_grains, peaks_per_grain, tol))
    print("=" * 70)

    n_diff_total = 0
    s_diff_total = 0.0
    n_match_64 = 0
    n_match_32 = 0
    ubi_errors_64 = []
    ubi_errors_32 = []

    for gi in range(n_grains):
        U = Us[gi]
        UB = np.dot(U, B)
        ubi_ideal = np.linalg.inv(UB)

        # Perturb by 0.5 degree
        dR = random_perturbation(0.5)
        ubi_pert = np.dot(dR, ubi_ideal)

        # g-vectors (same hkls, different UB)
        gv_f64 = np.dot(all_hkls, UB.T)

        # Run f64
        ubi_64 = ubi_pert.copy()
        n64, s64 = fn(ubi_64, gv_f64, tol)

        # Run f32
        gv_f32 = gv_f64.astype(np.float32)
        ubi_32 = ubi_pert.copy()
        n32, s32 = fn(ubi_32, gv_f32, tol)

        n_diff = n64 - n32
        s_diff = s64 - s32
        n_diff_total += n_diff
        s_diff_total += abs(s_diff)

        if n64 > 0:
            n_match_64 += 1
        if n32 > 0:
            n_match_32 += 1

        ubi_errors_64.append(np.linalg.norm(ubi_64 - ubi_ideal))
        ubi_errors_32.append(np.linalg.norm(ubi_32 - ubi_ideal))

    ubi_errors_64 = np.array(ubi_errors_64)
    ubi_errors_32 = np.array(ubi_errors_32)

    print("  Grains with any match: f64=%d f32=%d" % (n_match_64, n_match_32))
    print("  Total n_diff (f64-f32): %d" % n_diff_total)
    print("  Mean |s_diff|: %.2e" % (s_diff_total / n_grains))
    print("  UBI error |refined - ideal|:")
    print("    f64: mean=%.2e  median=%.2e  max=%.2e" %
          (ubi_errors_64.mean(), np.median(ubi_errors_64), ubi_errors_64.max()))
    print("    f32: mean=%.2e  median=%.2e  max=%.2e" %
          (ubi_errors_32.mean(), np.median(ubi_errors_32), ubi_errors_32.max()))
    print("    ratio (f32/f64): mean=%.2f" %
          (ubi_errors_32.mean() / ubi_errors_64.mean() if ubi_errors_64.mean() > 0 else 0))

    # Show worst cases
    worst = np.argsort(ubi_errors_32 - ubi_errors_64)[-5:]
    print("\n  5 worst f32 vs f64 UBI error cases:")
    for idx in reversed(worst):
        print("    grain %d: f64=%.2e  f32=%.2e  ratio=%.2f" %
              (idx, ubi_errors_64[idx], ubi_errors_32[idx],
               ubi_errors_32[idx] / ubi_errors_64[idx] if ubi_errors_64[idx] > 0 else 0))


if __name__ == "__main__":
    test_single_peak_set()
    test_overlapping_grains()
