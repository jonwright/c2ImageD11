"""Test score_and_refine variants: dispatch, correctness, shape detection, threading."""

from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import os
import numpy as np

sys.path.insert(0,
    os.path.join(os.path.dirname(__file__), "..", "lib", "functions",
                 "score_and_refine"))
from test_data import generate_single_ubi_data

from c2ImageD11 import score_and_refine, OMP_MIN_NG
from c2ImageD11 import cimaged11_omp_set_num_threads


def test_basic():
    """score_and_refine works via Python dispatch."""
    ubi, gv, tol = generate_single_ubi_data(100)
    n, s = score_and_refine(ubi.copy(), gv, tol)
    assert isinstance(n, (int, np.integer))
    assert isinstance(s, float)
    assert n >= 0 and s >= 0


def test_aos_vs_soa_shape():
    """AoS (N,3) and SoA (3,N) produce identical results."""
    B = np.eye(3) / 4.06
    rng = np.random.RandomState(42)
    U, _ = np.linalg.qr(rng.randn(3, 3))
    UB = np.dot(U, B)
    ubi = np.linalg.inv(UB)
    hkls = rng.randint(-8, 9, size=(500, 3)).astype(np.float64)
    gv = np.dot(hkls, UB.T)

    na, sa = score_and_refine(ubi.copy(), gv, 0.05)        # AoS (N,3)
    ns, ss = score_and_refine(ubi.copy(), gv.T.copy(), 0.05)  # SoA (3,N)

    assert na == ns, "n mismatch: %d %d" % (na, ns)
    assert abs(sa - ss) < 1e-12, "s mismatch AoS vs SoA"


def test_aos_vs_soa_f32():
    """f32 AoS and f32 SoA produce identical n via Python dispatch."""
    B = np.eye(3) / 4.06
    rng = np.random.RandomState(42)
    U, _ = np.linalg.qr(rng.randn(3, 3))
    UB = np.dot(U, B)
    ubi = np.linalg.inv(UB)
    hkls = rng.randint(-8, 9, size=(500, 3)).astype(np.float64)
    gv = (np.dot(hkls, UB.T)).astype(np.float32)

    na, sa = score_and_refine(ubi.copy(), gv, 0.05)
    ns, ss = score_and_refine(ubi.copy(), gv.T.copy(), 0.05)
    assert na == ns, "f32 n mismatch: %d %d" % (na, ns)


def test_ambiguous_33():
    """Ambiguous (3,3): c2py dispatch routes to AoS via shape[1]==3 check."""
    B = np.eye(3) / 4.06
    rng = np.random.RandomState(42)
    U, _ = np.linalg.qr(rng.randn(3, 3))
    UB = np.dot(U, B)
    ubi = np.linalg.inv(UB)
    hkls = rng.randint(-8, 9, size=(3, 3)).astype(np.float64)
    gv = np.dot(hkls, UB.T)

    n, s = score_and_refine(ubi.copy(), gv, 0.05)
    assert isinstance(n, (int, np.integer))
    assert n >= 0


def test_f64_f32_consistent():
    """f64 and f32 paths produce consistent results via Python dispatch."""
    B = np.eye(3) / 4.06
    rng = np.random.RandomState(42)
    U, _ = np.linalg.qr(rng.randn(3, 3))
    UB = np.dot(U, B)
    ubi = np.linalg.inv(UB)
    hkls = rng.randint(-8, 9, size=(200, 3)).astype(np.float64)
    gv_f64 = np.dot(hkls, UB.T)
    gv_f32 = gv_f64.astype(np.float32)

    n_f64, s_f64 = score_and_refine(ubi.copy(), gv_f64, 0.05)
    n_f32, s_f32 = score_and_refine(ubi.copy(), gv_f32, 0.05)

    # f32 may find +/- a few peaks due to rounding, but should be close
    assert abs(n_f64 - n_f32) <= 2, \
        "f64/f32 n too far: %d vs %d" % (n_f64, n_f32)
    # sumdrlv2 should be very close
    assert abs(s_f64 - s_f32) < 1e-4, \
        "f64/f32 s mismatch: %.6f vs %.6f" % (s_f64, s_f32)


def test_dispatch_f32_without_sse41():
    """f32 path works — exercises the f32 fallback in the overload chain."""
    B = np.eye(3) / 4.06
    rng = np.random.RandomState(999)
    U, _ = np.linalg.qr(rng.randn(3, 3))
    UB = np.dot(U, B)
    ubi = np.linalg.inv(UB)
    hkls = rng.randint(-8, 9, size=(100, 3)).astype(np.float64)
    gv = (np.dot(hkls, UB.T)).astype(np.float32)

    n, s = score_and_refine(ubi.copy(), gv, 0.05)
    assert isinstance(n, (int, np.integer))
    assert n > 0, "f32 path should find peaks"
    assert s > 0


def test_omp_min_ng():
    """OMP_MIN_NG is accessible and matches threading cutoff."""
    assert isinstance(OMP_MIN_NG, int)
    assert OMP_MIN_NG > 0
    assert OMP_MIN_NG == 50000


def test_threading_correctness():
    """Threaded path (ng > OMP_MIN_NG) produces correct results, 1T and nT."""
    ng = OMP_MIN_NG + 10000  # ~60k, above cutoff
    rng = np.random.RandomState(42)
    B = np.eye(3) / 4.06
    U, _ = np.linalg.qr(rng.randn(3, 3))
    UB = np.dot(U, B)
    ubi = np.linalg.inv(UB)
    hkls = rng.randint(-8, 9, size=(ng, 3)).astype(np.float64)
    gv = np.dot(hkls, UB.T)

    # Single thread
    cimaged11_omp_set_num_threads(1)
    ubi_1t = ubi.copy()
    n_1t, s_1t = score_and_refine(ubi_1t, gv, 0.05)

    # Multi thread
    n_cores = os.cpu_count() or 2
    cimaged11_omp_set_num_threads(n_cores)
    ubi_nt = ubi.copy()
    n_nt, s_nt = score_and_refine(ubi_nt, gv, 0.05)

    assert n_1t == n_nt, \
        "threading n mismatch: 1T=%d nT=%d" % (n_1t, n_nt)
    assert abs(s_1t - s_nt) < 1e-12, \
        "threading s mismatch: %.15e vs %.15e" % (s_1t, s_nt)


def test_soa_direct_api():
    """SoA layout (3,N) C-contiguous works via single entry point."""
    B = np.eye(3) / 4.06
    rng = np.random.RandomState(42)
    U, _ = np.linalg.qr(rng.randn(3, 3))
    UB = np.dot(U, B)
    ubi = np.linalg.inv(UB)
    hkls = rng.randint(-8, 9, size=(200, 3)).astype(np.float64)
    gv = np.dot(hkls, UB.T)

    # AoS (N,3)
    na, sa = score_and_refine(ubi.copy(), gv, 0.05)
    # SoA (3,N) C-contiguous copy
    gv_soa = np.ascontiguousarray(gv.T)
    ns, ss = score_and_refine(ubi.copy(), gv_soa, 0.05)
    assert na == ns
    assert abs(sa - ss) < 1e-12
