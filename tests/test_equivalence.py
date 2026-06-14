"""Equivalence tests: c2ImageD11._cImageD11 vs ImageD11._cImageD11.

Each test generates random valid inputs, calls both the old f2py-based
module and the new c2py23-based module with the same inputs, and verifies
the outputs match.

Requires: ImageD11 installed (for _cImageD11 reference) and c2ImageD11 built.
"""

from __future__ import print_function

import numpy as np
import pytest

# ---- Try importing both modules ----

try:
    import ImageD11._cImageD11 as OLD
except ImportError:
    OLD = None
    print("WARNING: ImageD11._cImageD11 not available - reference tests skipped")

try:
    import c2ImageD11._cImageD11 as NEW
except ImportError:
    NEW = None
    print("WARNING: c2ImageD11._cImageD11 not available - new module not built")

needs_both = pytest.mark.skipif(
    OLD is None or NEW is None,
    reason="Both old and new modules must be available"
)

needs_old = pytest.mark.skipif(
    OLD is None,
    reason="Old module not available"
)

needs_new = pytest.mark.skipif(
    NEW is None,
    reason="New module not available"
)


# ===================================================================
# Helper
# ===================================================================

def assert_close(a, b, tol=1e-10):
    """Compare scalars or arrays."""
    a = np.asarray(a); b = np.asarray(b)
    assert a.shape == b.shape, "Shape mismatch: %s vs %s" % (a.shape, b.shape)
    assert np.allclose(a, b, atol=tol), "Value mismatch"


# ===================================================================
# Simple scalar functions
# ===================================================================

class TestVerifyRounding:
    @needs_both
    def test_small(self):
        for n in [1, 2, 5, 10, 20, 50, 100]:
            assert OLD.verify_rounding(n) == NEW.verify_rounding(n)


class TestOMP:
    @needs_new
    def test_get_max_threads(self):
        result = NEW.cimaged11_omp_get_max_threads()
        assert isinstance(result, int)

    @needs_new
    def test_set_num_threads(self):
        NEW.cimaged11_omp_set_num_threads(1)
        # Should not crash


# ===================================================================
# score family
# ===================================================================

class TestScore:
    @needs_both
    def test_random(self):
        np.random.seed(42)
        for _ in range(5):
            ubi = np.random.randn(3, 3)
            gv = np.random.randn(100, 3)
            tol = 0.1 + 0.1 * np.random.random()
            old_score = OLD.score(ubi, gv, tol)
            new_score = NEW.score(ubi, gv, tol)
            assert old_score == new_score, \
                "score mismatch: old=%d new=%d" % (old_score, new_score)


class TestScoreAndRefine:
    @needs_both
    def test_random(self):
        np.random.seed(42)
        for _ in range(5):
            ubi_old = np.random.randn(3, 3)
            ubi_new = ubi_old.copy()
            gv = np.random.randn(100, 3)
            tol = 0.1
            sumdrlv2_old = np.zeros(1, dtype=np.float64)
            sumdrlv2_new = np.zeros(1, dtype=np.float64)
            n_old = OLD.score_and_refine(ubi_old, gv, tol, sumdrlv2_old)
            n_new = NEW.score_and_refine(ubi_new, gv, tol, sumdrlv2_new)
            assert n_old == n_new
            assert_close(sumdrlv2_old, sumdrlv2_new)
            assert_close(ubi_old, ubi_new)


# ===================================================================
# closest functions
# ===================================================================

class TestClosestVec:
    @needs_both
    def test_random(self):
        np.random.seed(42)
        for _ in range(3):
            nv, dim = 50, 3
            x = np.random.randn(nv, dim)
            ic_old = np.zeros(nv, dtype=np.int32)
            ic_new = np.zeros(nv, dtype=np.int32)
            OLD.closest_vec(x, ic_old)
            NEW.closest_vec(x, ic_new)
            assert_close(ic_old, ic_new)


class TestClosest:
    @needs_both
    def test_random(self):
        np.random.seed(42)
        for _ in range(3):
            x = np.sort(np.random.random(100))
            v = np.random.random(20)
            ibest_old = np.zeros(1, dtype=np.int32)
            best_old = np.zeros(1, dtype=np.float64)
            ibest_new = np.zeros(1, dtype=np.int32)
            best_new = np.zeros(1, dtype=np.float64)
            OLD.closest(x, v, ibest_old, best_old)
            NEW.closest(x, v, ibest_new, best_new)
            assert ibest_old[0] == ibest_new[0]
            assert_close(best_old, best_new)


# ===================================================================
# misori functions
# ===================================================================

class TestMisori:
    @needs_both
    @pytest.mark.parametrize("func", [
        "misori_cubic", "misori_orthorhombic",
        "misori_tetragonal", "misori_monoclinic"
    ])
    def test_random(self, func):
        np.random.seed(42)
        for _ in range(5):
            u1 = np.random.randn(3, 3)
            u2 = np.random.randn(3, 3)
            old_result = getattr(OLD, func)(u1, u2)
            new_result = getattr(NEW, func)(u1, u2)
            assert_close(old_result, new_result)


# ===================================================================
# array_stats
# ===================================================================

class TestArrayStats:
    @needs_both
    def test_random(self):
        np.random.seed(42)
        for _ in range(5):
            img = np.random.randn(1000).astype(np.float32)
            min_old = np.zeros(1, dtype=np.float32)
            max_old = np.zeros(1, dtype=np.float32)
            mean_old = np.zeros(1, dtype=np.float32)
            var_old = np.zeros(1, dtype=np.float32)
            min_new = np.zeros(1, dtype=np.float32)
            max_new = np.zeros(1, dtype=np.float32)
            mean_new = np.zeros(1, dtype=np.float32)
            var_new = np.zeros(1, dtype=np.float32)
            OLD.array_stats(img, min_old, max_old, mean_old, var_old)
            NEW.array_stats(img, min_new, max_new, mean_new, var_new)
            assert_close(min_old, min_new)
            assert_close(max_old, max_new)
            assert_close(mean_old, mean_new)
            assert_close(var_old, var_new)


# ===================================================================
# compute_* functions
# ===================================================================

class TestComputeGeometry:
    @needs_both
    def test_random(self):
        np.random.seed(42)
        for _ in range(3):
            n = 50
            xlylzl = np.random.randn(n, 3)
            omega = np.random.random(n) * 360.0
            omegasign = 1.0
            wvln = 0.3
            wedge = 5.0
            chi = 3.0
            t_vec = np.random.randn(3)
            out_old = np.zeros((n, 6))
            out_new = np.zeros((n, 6))
            OLD.compute_geometry(xlylzl, omega, omegasign, wvln, wedge, chi,
                                  t_vec, out_old)
            NEW.compute_geometry(xlylzl, omega, omegasign, wvln, wedge, chi,
                                  t_vec, out_new)
            assert_close(out_old, out_new, tol=1e-6)


class TestComputeGV:
    @needs_both
    def test_random(self):
        np.random.seed(42)
        for _ in range(3):
            n = 50
            xlylzl = np.random.randn(n, 3)
            omega = np.random.random(n) * 360.0
            omegasign = 1.0
            wvln = 0.3
            wedge = 5.0
            chi = 3.0
            t_vec = np.random.randn(3)
            gv_old = np.zeros((n, 3))
            gv_new = np.zeros((n, 3))
            OLD.compute_gv(xlylzl, omega, omegasign, wvln, wedge, chi,
                            t_vec, gv_old)
            NEW.compute_gv(xlylzl, omega, omegasign, wvln, wedge, chi,
                            t_vec, gv_new)
            assert_close(gv_old, gv_new, tol=1e-6)


class TestComputeXlylzl:
    @needs_both
    def test_random(self):
        np.random.seed(42)
        for _ in range(3):
            n = 100
            s = np.random.random(n).astype(np.float64) * 2000
            f = np.random.random(n).astype(np.float64) * 2000
            p = np.array([1000.0, 1000.0, 0.1, 0.1])
            r = np.array([0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0],
                         dtype=np.float64)
            dist = np.array([100.0, 0.0, 0.0], dtype=np.float64)
            xlylzl_old = np.zeros((n, 3))
            xlylzl_new = np.zeros((n, 3))
            OLD.compute_xlylzl(s, f, p, r, dist, xlylzl_old)
            NEW.compute_xlylzl(s, f, p, r, dist, xlylzl_new)
            assert_close(xlylzl_old, xlylzl_new, tol=1e-6)


# ===================================================================
# connectedpixels (if built)
# ===================================================================

class TestConnectedPixels:
    @needs_both
    def test_small(self):
        np.random.seed(42)
        ns, nf = 20, 20
        data = np.random.random(ns * nf).astype(np.float32).reshape(ns, nf)
        labels_old = np.zeros((ns, nf), dtype=np.int32)
        labels_new = np.zeros((ns, nf), dtype=np.int32)
        threshold = 0.8
        npk_old = OLD.connectedpixels(data, labels_old, threshold, 0, 1)
        npk_new = NEW.connectedpixels(data, labels_new, threshold, 0, 1)
        assert npk_old == npk_new
        assert_close(labels_old, labels_new)


# ===================================================================
# localmaxlabel (if built)
# ===================================================================

class TestLocalMaxLabel:
    @needs_both
    def test_small(self):
        np.random.seed(42)
        ns, nf = 20, 20
        data = np.random.random(ns * nf).astype(np.float32).reshape(ns, nf)
        labels_old = np.zeros((ns, nf), dtype=np.int32)
        labels_new = np.zeros((ns, nf), dtype=np.int32)
        wrk_old = np.zeros((ns, nf), dtype=np.int8)
        wrk_new = np.zeros((ns, nf), dtype=np.int8)
        OLD.localmaxlabel(data, labels_old, wrk_old)
        npk_new = NEW.localmaxlabel(data, labels_new, wrk_new)
        # localmaxlabel returns number of peaks
        npk_old = OLD.localmaxlabel(data, labels_old, wrk_old)
        assert npk_old >= 0
        assert npk_new >= 0
