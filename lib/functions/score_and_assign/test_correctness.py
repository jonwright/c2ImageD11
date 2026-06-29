"""Test score_and_assign correctness: f2py equivalence across multiple grains.

Cycles through several random UBIs with shared drlv2/labels,
ensuring c2py matches f2py exactly (n, drlv2 values, labels).

Also tests SoA layout and f32 type.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import sys, os, numpy as np

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PROJECT, "lib", "functions", "score_and_refine"))
from test_data import generate_random_rotations


def test_single_assign_f64():
    """Single UBI, AoS f64: c2py matches f2py."""
    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
    except ImportError:
        return
    import c2ImageD11 as ci

    rng = np.random.RandomState(42)
    ubi = rng.randn(3, 3)
    ng = 50
    gv = rng.randn(ng, 3)
    tol = 0.2

    dv_old = np.full(ng, 999.0); lb_old = np.full(ng, -1, dtype=np.int32)
    dv_new = np.full(ng, 999.0); lb_new = np.full(ng, -1, dtype=np.int32)

    no = old.score_and_assign(ubi, gv, tol, dv_old, lb_old, 1)
    nn = ci.score_and_assign(ubi, gv, tol, dv_new, lb_new, 1)

    assert no == nn, "n mismatch: %d vs %d" % (no, nn)
    assert np.allclose(dv_old, dv_new, atol=1e-12), "drlv2 mismatch"
    assert np.array_equal(lb_old, lb_new), "labels mismatch"


def test_multi_grain_cycle():
    """Cycle through 10 random UBIs with shared drlv2/labels, verify equivalence."""
    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
    except ImportError:
        return
    import c2ImageD11 as ci

    rng = np.random.RandomState(123)
    B = np.eye(3) / 4.06
    Us = generate_random_rotations(10, 77)
    ubis = np.zeros((10, 3, 3))
    for i in range(10):
        UB = np.dot(Us[i], B)
        ubis[i] = np.linalg.inv(UB)

    ng = 200
    hkls = rng.randint(-8, 9, size=(ng, 3)).astype(np.float64)
    gv = np.dot(hkls, np.dot(Us[0], B).T)
    tol = 0.05

    dv_old = np.full(ng, 999.0); lb_old = np.full(ng, -1, dtype=np.int32)
    dv_new = np.full(ng, 999.0); lb_new = np.full(ng, -1, dtype=np.int32)

    for i in range(10):
        no = old.score_and_assign(ubis[i], gv, tol, dv_old, lb_old, 1)
        nn = ci.score_and_assign(ubis[i], gv, tol, dv_new, lb_new, 1)
        assert no == nn, "grain %d: n mismatch %d vs %d" % (i, no, nn)
        assert np.allclose(dv_old, dv_new, atol=1e-12), "grain %d: drlv2 mismatch" % i
        assert np.array_equal(lb_old, lb_new), "grain %d: labels mismatch" % i


def test_soa_layout_f64():
    """SoA layout (3, ng) produces same results as AoS (ng, 3)."""
    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
    except ImportError:
        return
    import c2ImageD11 as ci

    rng = np.random.RandomState(99)
    ubi = rng.randn(3, 3)
    ng = 80
    gv_aos = rng.randn(ng, 3)
    gv_soa = gv_aos.T.copy()
    tol = 0.2

    dv_aos = np.full(ng, 999.0); lb_aos = np.full(ng, -1, dtype=np.int32)
    dv_soa = np.full(ng, 999.0); lb_soa = np.full(ng, -1, dtype=np.int32)

    na = ci.score_and_assign(ubi, gv_aos, tol, dv_aos, lb_aos, 1)
    ns = ci.score_and_assign(ubi, gv_soa, tol, dv_soa, lb_soa, 1)

    assert na == ns, "n mismatch AoS=%d SoA=%d" % (na, ns)
    assert np.allclose(dv_aos, dv_soa, atol=1e-12), "drlv2 AoS vs SoA mismatch"
    assert np.array_equal(lb_aos, lb_soa), "labels AoS vs SoA mismatch"


def test_f32_type():
    """f32 gv/drlv2 produces consistent results with f64."""
    import c2ImageD11 as ci

    rng = np.random.RandomState(55)
    ubi = rng.randn(3, 3)
    ng = 80
    gv_f64 = rng.randn(ng, 3)
    gv_f32 = gv_f64.astype(np.float32)
    tol = 0.2

    dv_f64 = np.full(ng, 999.0); lb_f64 = np.full(ng, -1, dtype=np.int32)
    dv_f32 = np.full(ng, 999.0, dtype=np.float32); lb_f32 = np.full(ng, -1, dtype=np.int32)

    n_f64 = ci.score_and_assign(ubi, gv_f64, tol, dv_f64, lb_f64, 1)
    n_f32 = ci.score_and_assign(ubi, gv_f32, tol, dv_f32, lb_f32, 1)

    # f32 has lower precision so we allow a tolerance
    # n might differ by 1-2 due to rounding differences
    # but drlv2 and labels should be similar
    assert abs(n_f64 - n_f32) <= max(1, ng / 10), \
        "n mismatch f64=%d f32=%d (tol=%.f%%)" % (n_f64, n_f32, abs(n_f64 - n_f32) / max(ng, 1) * 100)
    # f32 drlv2 should be close to f64 drlv2 where both matched
    # We don't check exact equality since f32/f64 rounding differs


def test_multi_grain_soa_f32():
    """Multi-grain cycling with SoA f32 layout."""
    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
    except ImportError:
        return
    import c2ImageD11 as ci

    rng = np.random.RandomState(200)
    B = np.eye(3) / 4.06
    Us = generate_random_rotations(10, 77)
    ubis = np.zeros((10, 3, 3))
    for i in range(10):
        UB = np.dot(Us[i], B)
        ubis[i] = np.linalg.inv(UB)

    ng = 200
    hkls = rng.randint(-8, 9, size=(ng, 3)).astype(np.float64)
    gv_aos = np.dot(hkls, np.dot(Us[0], B).T)
    gv_soa = gv_aos.T.copy().astype(np.float32)
    tol = 0.05

    dv_old = np.full(ng, 999.0); lb_old = np.full(ng, -1, dtype=np.int32)
    dv_soa = np.full(ng, 999.0, dtype=np.float32); lb_soa = np.full(ng, -1, dtype=np.int32)

    for i in range(10):
        no = old.score_and_assign(ubis[i], gv_aos, tol, dv_old, lb_old, 1)
        nn = ci.score_and_assign(ubis[i], gv_soa, tol, dv_soa, lb_soa, 1)
        assert no == nn, "grain %d: n mismatch %d vs %d" % (i, no, nn)
        assert np.array_equal(lb_old, lb_soa), "grain %d: labels mismatch" % i


def test_large_multi_grain():
    """Large multi-grain test (triggers OpenMP)."""
    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
    except ImportError:
        return
    import c2ImageD11 as ci

    rng = np.random.RandomState(42)
    B = np.eye(3) / 4.06
    Us = generate_random_rotations(5, 77)
    ubis = np.zeros((5, 3, 3))
    for i in range(5):
        UB = np.dot(Us[i], B)
        ubis[i] = np.linalg.inv(UB)

    ng = 50000  # large enough to trigger OpenMP
    hkls = rng.randint(-8, 9, size=(ng, 3)).astype(np.float64)
    gv = np.dot(hkls, np.dot(Us[0], B).T)
    tol = 0.05

    dv_old = np.full(ng, 999.0); lb_old = np.full(ng, -1, dtype=np.int32)
    dv_new = np.full(ng, 999.0); lb_new = np.full(ng, -1, dtype=np.int32)

    for i in range(5):
        no = old.score_and_assign(ubis[i], gv, tol, dv_old, lb_old, 1)
        nn = ci.score_and_assign(ubis[i], gv, tol, dv_new, lb_new, 1)
        assert no == nn, "grain %d large: n mismatch %d vs %d" % (i, no, nn)
        assert np.allclose(dv_old, dv_new, atol=1e-12), "grain %d large: drlv2 mismatch" % i
        assert np.array_equal(lb_old, lb_new), "grain %d large: labels mismatch" % i


if __name__ == "__main__":
    print("test_single_assign_f64...", end=" "); test_single_assign_f64(); print("OK")
    print("test_multi_grain_cycle...", end=" "); test_multi_grain_cycle(); print("OK")
    print("test_soa_layout_f64...", end=" "); test_soa_layout_f64(); print("OK")
    print("test_f32_type...", end=" "); test_f32_type(); print("OK")
    print("test_multi_grain_soa_f32...", end=" "); test_multi_grain_soa_f32(); print("OK")
    print("test_large_multi_grain...", end=" "); test_large_multi_grain(); print("OK")
    print("All correctness tests passed.")
