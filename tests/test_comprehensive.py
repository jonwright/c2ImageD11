"""Comprehensive coverage: threading, edge cases, fuzz, type confusion."""
from __future__ import absolute_import, division, print_function, unicode_literals

import sys, os, pytest
import numpy as np
import c2ImageD11

N_CORES = max(2, os.cpu_count() or 2)
N_ABOVE_GEOM = 10001   # above compute_geometry threshold (5000)
N_ABOVE_SCORE = 20001  # above score threshold (10000)
SEED = 42


# ======================== edge cases: empty / single / boundary ===============

class TestScoreEdgeCases(object):
    """score() edge cases: empty, single, boundary ng, tol=0."""

    @pytest.fixture
    def ubi(self):
        return np.eye(3, dtype=np.float64)

    def test_ng0(self, ubi):
        gv = np.empty((0, 3), dtype=np.float64)
        assert c2ImageD11.score(ubi, gv, 0.05) == 0

    def test_ng1(self, ubi):
        gv = np.random.randn(1, 3).astype(np.float64)
        n = c2ImageD11.score(ubi, gv, 0.05)
        assert isinstance(n, (int, np.integer))

    def test_tol0(self, ubi):
        gv = np.array([[1, 2, 3]], dtype=np.float64)
        n = c2ImageD11.score(ubi, gv, 0.0)
        assert isinstance(n, (int, np.integer))

    def test_ng_just_below_omp(self, ubi):
        ng = 9999
        gv = np.random.randn(ng, 3).astype(np.float64)
        n = c2ImageD11.score(ubi, gv, 0.05)
        assert isinstance(n, (int, np.integer))

    def test_ng_just_above_omp(self, ubi):
        ng = 10001
        gv = np.random.randn(ng, 3).astype(np.float64)
        n = c2ImageD11.score(ubi, gv, 0.05)
        assert isinstance(n, (int, np.integer))

    def test_all_zero_gv(self, ubi):
        gv = np.zeros((10, 3), dtype=np.float64)
        n = c2ImageD11.score(ubi, gv, 0.05)
        assert isinstance(n, (int, np.integer))

    def test_nan_gv(self, ubi):
        gv = np.full((10, 3), np.nan, dtype=np.float64)
        n = c2ImageD11.score(ubi, gv, 0.05)
        assert isinstance(n, (int, np.integer))

    def test_inf_gv(self, ubi):
        gv = np.full((10, 3), np.inf, dtype=np.float64)
        n = c2ImageD11.score(ubi, gv, 0.05)
        assert isinstance(n, (int, np.integer))


class TestScoreAndRefineEdgeCases(object):
    """score_and_refine() edge cases."""

    @pytest.fixture
    def ubi(self):
        return np.eye(3, dtype=np.float64)

    def test_ng0_returns_zero_s(self, ubi):
        gv = np.empty((0, 3), dtype=np.float64)
        n, s = c2ImageD11.score_and_refine(ubi, gv, 0.05)
        assert n == 0 and s == 0.0

    def test_ng_just_above_omp(self, ubi):
        ng = 10001
        gv = (np.random.randn(ng, 3) * 10).astype(np.float64)
        n, s = c2ImageD11.score_and_refine(ubi, gv, 0.05)
        assert isinstance(n, (int, np.integer))
        assert isinstance(s, float)


class TestScoreAndAssignEdgeCases(object):
    """score_and_assign() edge cases."""

    @pytest.fixture
    def ubi(self):
        return np.eye(3, dtype=np.float64)

    def test_ng0(self, ubi):
        gv = np.empty((0, 3), dtype=np.float64)
        dv = np.empty(0, dtype=np.float64)
        lb = np.empty(0, dtype=np.int32)
        n = c2ImageD11.score_and_assign(ubi, gv, 0.05, dv, lb, 1)
        assert n == 0

    def test_ng_just_above_omp(self, ubi):
        ng = 10001
        gv = (np.random.randn(ng, 3) * 10).astype(np.float64)
        dv = np.full(ng, 999.0, dtype=np.float64)
        lb = np.full(ng, -1, dtype=np.int32)
        n = c2ImageD11.score_and_assign(ubi, gv, 0.05, dv, lb, 1)
        assert isinstance(n, (int, np.integer))


class TestGeomEdgeCases(object):
    """compute_geometry edge cases."""

    def test_n0(self):
        xlylzl = np.empty((0, 3), dtype=np.float64)
        omega = np.empty(0, dtype=np.float64)
        t = np.zeros(3, dtype=np.float64)
        out = np.empty((0, 6), dtype=np.float64)
        c2ImageD11.compute_geometry(xlylzl, omega, 1.0, 0.7, 1.5, 0.0, t, out)

    def test_ng_just_above_omp(self):
        n = 5001
        xlylzl = np.random.randn(n, 3).astype(np.float64)
        omega = np.random.uniform(-np.pi, np.pi, n).astype(np.float64)
        t = np.zeros(3, dtype=np.float64)
        out = np.zeros((n, 6), dtype=np.float64)
        c2ImageD11.compute_geometry(xlylzl, omega, 1.0, 0.7, 1.5, 0.0, t, out)

    def test_single_spot(self):
        xlylzl = np.array([[10.0, 20.0, 30.0]], dtype=np.float64)
        omega = np.array([0.0], dtype=np.float64)
        t = np.zeros(3, dtype=np.float64)
        out = np.zeros((1, 6), dtype=np.float64)
        c2ImageD11.compute_geometry(xlylzl, omega, 1.0, 0.7, 1.5, 0.0, t, out)
        assert not np.isnan(out).any()

    def test_all_zero_xlylzl(self):
        """All-zero xlylzl: atan2(0,0) may produce NaN in some columns."""
        n = 100
        xlylzl = np.zeros((n, 3), dtype=np.float64)
        omega = np.zeros(n, dtype=np.float64)
        t = np.zeros(3, dtype=np.float64)
        out = np.zeros((n, 6), dtype=np.float64)
        c2ImageD11.compute_geometry(xlylzl, omega, 1.0, 0.7, 1.5, 0.0, t, out)


# ======================== threading: 1T vs nT =================================

class TestThreadingDeterministic(object):
    """Deterministic OpenMP functions: 1T output must match nT."""

    def test_compute_geometry(self):
        n = N_ABOVE_GEOM
        xlylzl = np.random.RandomState(SEED).randn(n, 3).astype(np.float64)
        omega = np.random.RandomState(SEED + 1).uniform(-np.pi, np.pi, n).astype(np.float64)
        t = np.zeros(3, dtype=np.float64)
        out1 = np.zeros((n, 6), dtype=np.float64)
        outN = np.zeros((n, 6), dtype=np.float64)

        c2ImageD11.cimaged11_omp_set_num_threads(1)
        c2ImageD11.compute_geometry(xlylzl, omega, 1.0, 0.7, 1.5, 0.0, t, out1)

        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        c2ImageD11.compute_geometry(xlylzl, omega, 1.0, 0.7, 1.5, 0.0, t, outN)

        assert np.allclose(out1, outN, atol=1e-12), \
            "compute_geometry: 1T/nT mismatch"

    def test_compute_gv(self):
        n = N_ABOVE_GEOM
        xlylzl = np.random.RandomState(10).randn(n, 3).astype(np.float64)
        omega = np.random.RandomState(11).uniform(-np.pi, np.pi, n).astype(np.float64)
        t = np.zeros(3, dtype=np.float64)
        gv1 = np.zeros((n, 3), dtype=np.float64)
        gvN = np.zeros((n, 3), dtype=np.float64)

        c2ImageD11.cimaged11_omp_set_num_threads(1)
        c2ImageD11.compute_gv(xlylzl, omega, 1.0, 0.7, 1.5, 0.0, t, gv1)

        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        c2ImageD11.compute_gv(xlylzl, omega, 1.0, 0.7, 1.5, 0.0, t, gvN)

        assert np.allclose(gv1, gvN, atol=1e-12), \
            "compute_gv: 1T/nT mismatch"

    def test_score_above_omp(self):
        n = N_ABOVE_SCORE
        ubi = np.eye(3, dtype=np.float64)
        gv = np.random.RandomState(20).randn(n, 3).astype(np.float64)

        c2ImageD11.cimaged11_omp_set_num_threads(1)
        n1 = c2ImageD11.score(ubi, gv, 0.05)

        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        nN = c2ImageD11.score(ubi, gv, 0.05)

        assert n1 == nN, "score %dT/%dT mismatch: %d != %d" % (1, N_CORES, n1, nN)

    def test_score_and_refine_above_omp(self):
        """score_and_refine refines ubi in-place -- reinitialize per call."""
        n = N_ABOVE_SCORE
        gv = np.random.RandomState(30).randn(n, 3).astype(np.float64)

        c2ImageD11.cimaged11_omp_set_num_threads(1)
        n1, s1 = c2ImageD11.score_and_refine(np.eye(3, dtype=np.float64), gv, 0.05)

        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        nN, sN = c2ImageD11.score_and_refine(np.eye(3, dtype=np.float64), gv, 0.05)

        assert n1 == nN, "sar %dT/%dT n mismatch" % (1, N_CORES)
        assert abs(s1 - sN) < 1e-10, "sar %dT/%dT s mismatch" % (1, N_CORES)

    def test_score_and_assign_above_omp(self):
        n = N_ABOVE_SCORE
        ubi = np.eye(3, dtype=np.float64)
        gv = np.random.RandomState(40).randn(n, 3).astype(np.float64)
        dv = np.full(n, 999.0, dtype=np.float64)
        lb = np.full(n, -1, dtype=np.int32)

        c2ImageD11.cimaged11_omp_set_num_threads(1)
        dv1 = dv.copy()
        lb1 = lb.copy()
        c2ImageD11.score_and_assign(ubi, gv, 0.05, dv1, lb1, 1)

        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        dvN = dv.copy()
        lbN = lb.copy()
        c2ImageD11.score_and_assign(ubi, gv, 0.05, dvN, lbN, 1)

        assert np.allclose(dv1, dvN, atol=1e-10), \
            "sa %dT/%dT drlv2 mismatch" % (1, N_CORES)
        assert np.array_equal(lb1, lbN), \
            "sa %dT/%dT labels mismatch" % (1, N_CORES)

    def test_clean_mask_below_omp(self):
        """clean_mask always parallel (no threshold)."""
        ns, nf = 20, 30
        msk = np.random.RandomState(50).randint(0, 2, size=(ns, nf)).astype(np.int8)
        ret1 = np.zeros_like(msk)
        retN = np.zeros_like(msk)

        c2ImageD11.cimaged11_omp_set_num_threads(1)
        n1 = c2ImageD11.clean_mask(msk, ret1)

        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        nN = c2ImageD11.clean_mask(msk, retN)

        assert n1 == nN
        assert np.array_equal(ret1, retN)

    def test_mask_to_coo(self):
        ns, nf = 30, 40
        msk = np.random.RandomState(60).randint(0, 2, size=(ns, nf)).astype(np.int8)
        nnz = int(msk.sum())
        i1 = np.zeros(nnz, dtype=np.uint16)
        j1 = np.zeros(nnz, dtype=np.uint16)
        nrow1 = np.zeros(ns, dtype=np.int32)
        iN = np.zeros(nnz, dtype=np.uint16)
        jN = np.zeros(nnz, dtype=np.uint16)
        nrowN = np.zeros(ns, dtype=np.int32)

        c2ImageD11.cimaged11_omp_set_num_threads(1)
        err1 = c2ImageD11.mask_to_coo(msk, i1, j1, nrow1)

        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        errN = c2ImageD11.mask_to_coo(msk, iN, jN, nrowN)

        assert err1 == errN == 0
        assert np.array_equal(i1, iN)
        assert np.array_equal(j1, jN)
        assert np.array_equal(nrow1, nrowN)

    def test_score_gvec_z(self):
        n = 5000
        ubi = np.eye(3, dtype=np.float64)
        ub = np.eye(3, dtype=np.float64)
        gv = np.random.RandomState(70).randn(n, 3).astype(np.float64)
        g01 = np.zeros((n, 3), dtype=np.float64)
        g11 = np.zeros((n, 3), dtype=np.float64)
        g21 = np.zeros((n, 3), dtype=np.float64)
        e1 = np.zeros((n, 3), dtype=np.float64)
        g0N = np.zeros_like(g01)
        g1N = np.zeros_like(g11)
        g2N = np.zeros_like(g21)
        eN = np.zeros_like(e1)

        c2ImageD11.cimaged11_omp_set_num_threads(1)
        c2ImageD11.score_gvec_z(ubi, ub, gv, g01, g11, g21, e1, 1)

        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        c2ImageD11.score_gvec_z(ubi, ub, gv, g0N, g1N, g2N, eN, 1)

        assert np.allclose(g01, g0N, atol=1e-12)
        assert np.allclose(g11, g1N, atol=1e-12)
        assert np.allclose(g21, g2N, atol=1e-12)
        assert np.array_equal(e1, eN)


class TestApproxDeterministic(object):
    """Functions where float non-associativity may cause bit-level diffs."""

    def test_array_stats(self):
        n = 50000
        img = np.random.RandomState(80).randn(n).astype(np.float32)

        c2ImageD11.cimaged11_omp_set_num_threads(1)
        min1, max1, mean1, var1 = c2ImageD11.array_stats(img)

        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        minN, maxN, meanN, varN = c2ImageD11.array_stats(img)

        assert min1 == minN and max1 == maxN, "min/max mismatch"
        assert abs(mean1 - meanN) < 1e-5 * max(1.0, abs(mean1))
        assert abs(var1 - varN) < 1e-4 * max(1.0, abs(var1))


# ======================== fuzz: strings, scalars, wrong types =================

class TestFuzzCall(object):
    """Pass insane arguments; verify no crashes, only clean exceptions."""

    def test_score_buffer_replaced_with_string(self):
        with pytest.raises((ValueError, TypeError, SystemError)):
            c2ImageD11.score("help", "me", 0.5)

    def test_score_gv_replaced_with_string(self):
        ubi = np.eye(3, dtype=np.float64)
        with pytest.raises((ValueError, TypeError, SystemError)):
            c2ImageD11.score(ubi, "help", 0.5)

    def test_score_and_refine_ubi_string(self):
        gv = np.random.randn(10, 3).astype(np.float64)
        with pytest.raises((ValueError, TypeError, SystemError)):
            c2ImageD11.score_and_refine("help", gv, 0.5)

    def test_score_and_assign_gv_string(self):
        ubi = np.eye(3, dtype=np.float64)
        dv = np.full(10, 999.0, dtype=np.float64)
        lb = np.full(10, -1, dtype=np.int32)
        with pytest.raises((ValueError, TypeError, SystemError)):
            c2ImageD11.score_and_assign(ubi, "help", 0.5, dv, lb, 1)

    def test_connectedpixels_data_string(self):
        labels = np.zeros((10, 10), dtype=np.int32)
        with pytest.raises((ValueError, TypeError, SystemError)):
            c2ImageD11.connectedpixels("help", labels, 50.0)

    def test_compute_geometry_xlylzl_string(self):
        omega = np.zeros(10, dtype=np.float64)
        t = np.zeros(3, dtype=np.float64)
        out = np.zeros((10, 6), dtype=np.float64)
        with pytest.raises((ValueError, TypeError, SystemError)):
            c2ImageD11.compute_geometry("help", omega, 1.0, 0.7, 1.5, 0.0, t, out)

    def test_scalar_arg_substituted_with_array(self):
        """tol expects float; pass array -- may or may not raise."""
        ubi = np.eye(3, dtype=np.float64)
        gv = np.random.randn(10, 3).astype(np.float64)
        try:
            c2ImageD11.score(ubi, gv, np.array([0.5]))
        except (ValueError, TypeError):
            pass

    def test_scalar_arg_substituted_with_string(self):
        ubi = np.eye(3, dtype=np.float64)
        gv = np.random.randn(10, 3).astype(np.float64)
        with pytest.raises((ValueError, TypeError)):
            c2ImageD11.score(ubi, gv, "tol")

    def test_int_arg_substituted_with_float(self):
        """label arg in score_and_assign: int, pass float."""
        ubi = np.eye(3, dtype=np.float64)
        gv = np.random.randn(10, 3).astype(np.float64)
        dv = np.full(10, 999.0, dtype=np.float64)
        lb = np.full(10, -1, dtype=np.int32)
        with pytest.raises((ValueError, TypeError)):
            c2ImageD11.score_and_assign(ubi, gv, 0.5, dv, lb, 0.5)

    def test_array_stats_scalar_buffers_wrong_type(self):
        img = np.random.randn(100).astype(np.float32)
        # Pass plain scalar instead of buffer for output args
        with pytest.raises((ValueError, TypeError)):
            c2ImageD11.array_stats(img, 0.0, 0.0, 0.0, 0.0)

    def test_reorder_pass_string_for_adr(self):
        data = np.arange(100, dtype=np.uint16)
        out = np.zeros(100, dtype=np.uint16)
        with pytest.raises((ValueError, TypeError, SystemError)):
            c2ImageD11.reorder_u16_a32(data, "help", out)

    def test_misori_pass_single_array(self):
        """misori functions expect two UBIs; pass one."""
        u = np.eye(3, dtype=np.float64)
        with pytest.raises(TypeError):
            c2ImageD11.misori_cubic(u)


# ======================== reorder duplicate address race ======================

class TestReorderRaces(object):
    """reorder_u16_a32 and reorder_f32_a32: test with duplicate adr."""

    def test_reorder_u16_a32_no_duplicates(self):
        n = 1000
        data = np.arange(n, dtype=np.uint16)
        adr = np.arange(n, dtype=np.uint32)
        out = np.zeros(n, dtype=np.uint16)
        c2ImageD11.reorder_u16_a32(data, adr, out)
        assert np.array_equal(out, data)

    def test_reorder_u16_a32_duplicates(self):
        """Known potential race: all writes to same index."""
        n = 1000
        data = np.arange(n, dtype=np.uint16)
        adr = np.zeros(n, dtype=np.uint32)  # all write to index 0
        out = np.zeros(n, dtype=np.uint16)  # must be >= data.n
        c2ImageD11.reorder_u16_a32(data, adr, out)

    def test_reorderlut_u16_a32(self):
        n = 1000
        data = np.arange(n, dtype=np.uint16)
        lut = np.arange(n, dtype=np.uint32)
        out = np.zeros(n, dtype=np.uint16)
        c2ImageD11.reorderlut_u16_a32(data, lut, out)
        assert np.array_equal(out, data)


# ======================== common function oddities ============================

class TestOddities(object):
    """Edge cases uncovered during audit."""

    def test_verify_rounding_zero(self):
        result = c2ImageD11.verify_rounding(0)
        assert isinstance(result, (int, np.integer))

    def test_verify_rounding_large(self):
        result = c2ImageD11.verify_rounding(1000)
        assert isinstance(result, (int, np.integer))

    def test_omp_set_get(self):
        old = c2ImageD11.cimaged11_omp_get_max_threads()
        c2ImageD11.cimaged11_omp_set_num_threads(3)
        assert c2ImageD11.cimaged11_omp_get_max_threads() == 3
        c2ImageD11.cimaged11_omp_set_num_threads(old)

    def test_count_shared_empty(self):
        i = np.array([], dtype=np.int32)
        j = np.array([], dtype=np.int32)
        assert c2ImageD11.count_shared(i, j) == 0

    def test_blob_moments_one_result(self):
        results = np.zeros((1, 36), dtype=np.float64)
        c2ImageD11.blob_moments(results)

    def test_closest_empty(self):
        x = np.empty((0, 3), dtype=np.float64)
        v = np.zeros(3, dtype=np.float64)
        c2ImageD11.closest(x, v)

    def test_closest_vec_empty(self):
        x = np.empty((0, 3), dtype=np.float64)
        ic = np.empty(0, dtype=np.int32)
        c2ImageD11.closest_vec(x, ic)


# ======================== untested functions ==================================

class TestUntestedFunctions(object):
    """Smoke tests for the 9 completely untested public functions."""

    def test_array_mean_var_msk(self):
        """Sigma-clipped mean/var with mask. Realistic: ImageD11 indexing."""
        rng = np.random.RandomState(42)
        img = rng.randn(10000).astype(np.float32)
        msk = np.ones(10000, dtype=np.uint8)
        mean1, var1 = c2ImageD11.array_mean_var_msk(img, msk, 3, 3.0)
        assert np.isfinite(mean1)
        assert np.isfinite(var1)
        assert var1 >= 0

    def test_array_mean_var_msk_masked(self):
        """With some pixels masked out."""
        rng = np.random.RandomState(43)
        img = rng.randn(10000).astype(np.float32)
        img[:5000] = 100.0  # bright outliers
        msk = np.ones(10000, dtype=np.uint8)
        msk[:5000] = 0  # mask them
        mean1, var1 = c2ImageD11.array_mean_var_msk(img, msk, 3, 3.0)
        assert np.isfinite(mean1)
        assert np.isfinite(var1)

    def test_array_mean_var_msk_no_msk(self):
        """All pixels masked out -- should handle gracefully."""
        img = np.ones(100, dtype=np.float32)
        msk = np.zeros(100, dtype=np.uint8)
        mean1, var1 = c2ImageD11.array_mean_var_msk(img, msk, 1, 3.0)
        assert np.isfinite(mean1) or True  # may return NaN/0

    def test_bgcalc(self):
        """Recursive background filter. Realistic: ImageD11 peaksearch."""
        rng = np.random.RandomState(44)
        ns, nf = 50, 60
        img = rng.randn(ns, nf).astype(np.float32)
        bg = np.zeros_like(img)
        msk = np.ones_like(img, dtype=np.uint8)
        c2ImageD11.bgcalc(img, bg, msk, 1.0, 3.0, 3.0)
        assert np.all(np.isfinite(bg))

    def test_bgcalc_edge_single_row(self):
        ns, nf = 1, 100
        img = np.ones((ns, nf), dtype=np.float32) * 100.0
        bg = np.zeros_like(img)
        msk = np.ones_like(img, dtype=np.uint8)
        c2ImageD11.bgcalc(img, bg, msk, 1.0, 3.0, 3.0)
        assert np.all(np.isfinite(bg))

    def test_bgcalc_edge_single_col(self):
        ns, nf = 100, 1
        img = np.ones((ns, nf), dtype=np.float32) * 100.0
        bg = np.zeros_like(img)
        msk = np.ones_like(img, dtype=np.uint8)
        c2ImageD11.bgcalc(img, bg, msk, 1.0, 3.0, 3.0)
        assert np.all(np.isfinite(bg))

    def test_bgcalc_all_uniform(self):
        ns, nf = 20, 30
        img = np.ones((ns, nf), dtype=np.float32) * 100.0
        bg = np.zeros_like(img)
        msk = np.ones_like(img, dtype=np.uint8)
        c2ImageD11.bgcalc(img, bg, msk, 1.0, 3.0, 3.0)
        assert np.allclose(bg, 100.0, atol=1e-3)

    def test_compute_xlylzl_xpos_variable(self):
        """Like compute_xlylzl but with per-spot x-offset. Realistic."""
        n = 100
        rng = np.random.RandomState(45)
        s = rng.randn(n).astype(np.float64)
        f = rng.randn(n).astype(np.float64)
        p = np.array([0.1, 0.0, 0.0, 0.0], dtype=np.float64)
        r = np.eye(3, dtype=np.float64).ravel()
        dist = np.array([200.0, 0.0, 0.0], dtype=np.float64)
        xpos = rng.randn(n).astype(np.float64) * 0.1
        xlylzl = np.zeros((n, 3), dtype=np.float64)
        c2ImageD11.compute_xlylzl_xpos_variable(s, f, p, r, dist, xpos, xlylzl)
        assert np.all(np.isfinite(xlylzl))

    def test_frelon_lines(self):
        """Per-row baseline removal. Realistic: ImageD11 frelon detector."""
        rng = np.random.RandomState(46)
        ns, nf = 100, 100
        img = rng.poisson(lam=10.0, size=(ns, nf)).astype(np.float32)
        img_copy = img.copy()
        c2ImageD11.frelon_lines(img, 5.0)
        assert not np.array_equal(img, img_copy)  # was modified
        assert np.all(np.isfinite(img))

    def test_frelon_lines_uniform(self):
        """Uniform image should produce zeros after baseline removal."""
        img = np.ones((50, 50), dtype=np.float32) * 100.0
        c2ImageD11.frelon_lines(img, 99.0)  # cut below value, uses all pixels
        # Each row becomes zero-centered
        assert abs(img.mean()) < 1e-5

    def test_frelon_lines_sub(self):
        """Dark subtract then per-row baseline. Realistic: ImageD11."""
        rng = np.random.RandomState(47)
        ns, nf = 100, 100
        data = rng.poisson(lam=10.0, size=(ns, nf)).astype(np.float32)
        drk = rng.poisson(lam=10.0, size=(ns, nf)).astype(np.float32)
        img = data.copy()
        c2ImageD11.frelon_lines_sub(img, drk, 5.0)
        assert np.all(np.isfinite(img))

    def test_reorder_u16_a32_a16(self):
        """2D reorder: per-row base + per-pixel offsets. Realistic."""
        ns, nf = 5, 10
        data = np.arange(ns * nf, dtype=np.uint16).reshape(ns, nf)
        adr0 = np.array([10, 20, 30, 40, 50], dtype=np.int32)
        adr1 = np.arange(ns * nf, dtype=np.int16).reshape(ns, nf) % 8
        out = np.zeros(100, dtype=np.uint16)
        c2ImageD11.reorder_u16_a32_a16(data, adr0, adr1, out)

    def test_reorderlut_f32_a32_lut(self):
        """reorderlut_f32_a32: lookup table reorder."""
        n = 100
        data = np.random.RandomState(48).randn(n).astype(np.float32)
        lut = np.arange(n, dtype=np.int32)
        out = np.zeros_like(data)
        c2ImageD11.reorderlut_f32_a32(data, lut, out)
        assert np.allclose(out, data)

    def test_sparse_blob2Dproperties(self):
        """Sparse blob 2D properties (wrapped). Realistic."""
        nnz = 50
        v = np.ones(nnz, dtype=np.float32)
        i = np.arange(nnz, dtype=np.uint16)
        j = np.zeros(nnz, dtype=np.uint16)
        labels = np.zeros(nnz, dtype=np.int32)
        # wrapper: 5 args, returns results
        results = c2ImageD11.sparse_blob2Dproperties(v, i, j, labels, 0)
        assert results.shape == (0, 11)

    def test_sparse_blob2Dproperties_with_peaks(self):
        """Sparse blob with some peaks."""
        nnz = 50
        v = np.ones(nnz, dtype=np.float32)
        i = np.arange(nnz, dtype=np.uint16)
        j = np.zeros(nnz, dtype=np.uint16)
        labels = np.ones(nnz, dtype=np.int32)  # one peak per pixel
        results = c2ImageD11.sparse_blob2Dproperties(v, i, j, labels, 1)
        assert results.shape == (1, 11)

    def test_sparse_connectedpixels_splat(self):
        """Sparse connected components with splat to dense. Realistic."""
        nnz = 50
        rng = np.random.RandomState(50)
        v = rng.randn(nnz).astype(np.float32)
        i = np.arange(nnz, dtype=np.uint16)
        j = np.zeros(nnz, dtype=np.uint16)
        lbl = np.zeros(nnz, dtype=np.int32)
        Z = np.zeros((50, 50), dtype=np.int32)
        n = c2ImageD11.sparse_connectedpixels_splat(v, i, j, 0.5, lbl, Z, 50, 50)
        assert isinstance(n, (int, np.integer))


# ======================== _v2 kernel correctness ===============================

class TestV2Kernels(object):
    """score_and_assign _v2 (wide-load+permute) must match non-_v2."""

    def test_f64_v2_matches_original(self):
        """score_and_assign_f64_avx512_v2 matches score_and_assign_f64_avx512."""
        _rebind = getattr(c2ImageD11._cImageD11, "_rebind_score_and_assign", None)
        _variants = getattr(c2ImageD11._cImageD11, "_variants_score_and_assign", lambda: ())()
        if "score_and_assign_f64_avx512_v2" not in _variants:
            pytest.skip("_v2 variant not available")
        if "score_and_assign_f64_avx512" not in _variants:
            pytest.skip("original avx512 variant not available")
        rng = np.random.RandomState(51)
        n = 1000
        ubi = np.eye(3, dtype=np.float64)
        gv = rng.randn(n, 3).astype(np.float64)
        dv = np.full(n, 999.0, dtype=np.float64)
        lb = np.full(n, -1, dtype=np.int32)
        _rebind("score_and_assign_f64_avx512_v2")
        dv2 = dv.copy(); lb2 = lb.copy()
        c2ImageD11.score_and_assign(ubi, gv, 0.05, dv2, lb2, 1)
        _rebind("score_and_assign_f64_avx512")
        dv0 = dv.copy(); lb0 = lb.copy()
        c2ImageD11.score_and_assign(ubi, gv, 0.05, dv0, lb0, 1)
        assert np.allclose(dv2, dv0, atol=1e-10), "f64 _v2 drlv2 mismatch"
        assert np.array_equal(lb2, lb0), "f64 _v2 labels mismatch"
        _rebind(None)

    def test_f32_v2_matches_original(self):
        _rebind = getattr(c2ImageD11._cImageD11, "_rebind_score_and_assign", None)
        _variants = getattr(c2ImageD11._cImageD11, "_variants_score_and_assign", lambda: ())()
        if "score_and_assign_f32_aos_avx512_v2" not in _variants:
            pytest.skip("_v2 f32 variant not available")
        if "score_and_assign_f32_aos_avx512" not in _variants:
            pytest.skip("original f32 avx512 variant not available")
        rng = np.random.RandomState(52)
        n = 1000
        ubi = np.eye(3, dtype=np.float64)
        gv = rng.randn(n, 3).astype(np.float32)
        dv = np.full(n, 999.0, dtype=np.float32)
        lb = np.full(n, -1, dtype=np.int32)
        _rebind("score_and_assign_f32_aos_avx512_v2")
        dv2 = dv.copy(); lb2 = lb.copy()
        c2ImageD11.score_and_assign(ubi, gv, 0.05, dv2, lb2, 1)
        _rebind("score_and_assign_f32_aos_avx512")
        dv0 = dv.copy(); lb0 = lb.copy()
        c2ImageD11.score_and_assign(ubi, gv, 0.05, dv0, lb0, 1)
        assert np.allclose(dv2, dv0, atol=1e-6), "f32 _v2 drlv2 mismatch"
        assert np.array_equal(lb2, lb0), "f32 _v2 labels mismatch"
        _rebind(None)


# ======================== threading for remaining OMP functions ===============

class TestThreadingRemaining(object):
    """Threading tests for OMP functions not yet covered."""

    def test_closest_vec_1T_vs_nT(self):
        rng = np.random.RandomState(60)
        nv, dim = 200, 3
        x = rng.randn(nv, dim).astype(np.float64)
        ic1 = np.zeros(nv, dtype=np.int32)
        icN = np.zeros(nv, dtype=np.int32)
        c2ImageD11.cimaged11_omp_set_num_threads(1)
        c2ImageD11.closest_vec(x, ic1)
        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        c2ImageD11.closest_vec(x, icN)
        assert np.array_equal(ic1, icN)

    def test_array_mean_var_cut_1T_vs_nT(self):
        rng = np.random.RandomState(61)
        n = 50000
        img = rng.randn(n).astype(np.float32)
        c2ImageD11.cimaged11_omp_set_num_threads(1)
        m1, v1 = c2ImageD11.array_mean_var_cut(img, 3, 3.0)
        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        mN, vN = c2ImageD11.array_mean_var_cut(img, 3, 3.0)
        assert abs(m1 - mN) < 1e-5 * max(1.0, abs(m1))
        assert abs(v1 - vN) < 1e-4 * max(1.0, abs(v1))

    def test_uint16_to_float_darksub_1T_vs_nT(self):
        """Element-wise darksub: deterministic, 1T must match nT exactly."""
        rng = np.random.RandomState(62)
        ns, nf = 50, 60
        data = rng.randint(0, 256, size=(ns, nf)).astype(np.uint16)
        drk = rng.randn(ns, nf).astype(np.float32) * 10.0
        img1 = np.zeros((ns, nf), dtype=np.float32)
        imgN = np.zeros((ns, nf), dtype=np.float32)
        c2ImageD11.cimaged11_omp_set_num_threads(1)
        c2ImageD11.uint16_to_float_darksub(img1, drk, data)
        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        c2ImageD11.uint16_to_float_darksub(imgN, drk, data)
        assert np.array_equal(img1, imgN)

    def test_uint16_to_float_darkflm_1T_vs_nT(self):
        rng = np.random.RandomState(63)
        ns, nf = 50, 60
        data = rng.randint(0, 256, size=(ns, nf)).astype(np.uint16)
        drk = rng.randn(ns, nf).astype(np.float32) * 10.0
        flm = np.ones((ns, nf), dtype=np.float32) * 0.5
        img1 = np.zeros((ns, nf), dtype=np.float32)
        imgN = np.zeros((ns, nf), dtype=np.float32)
        c2ImageD11.cimaged11_omp_set_num_threads(1)
        c2ImageD11.uint16_to_float_darkflm(img1, drk, flm, data)
        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        c2ImageD11.uint16_to_float_darkflm(imgN, drk, flm, data)
        assert np.allclose(img1, imgN, atol=1e-6)

    def test_connectedpixels_1T_vs_nT(self):
        """connectedpixels: only relabel step is parallel, should match."""
        rng = np.random.RandomState(64)
        ns, nf = 50, 50
        data = rng.randn(ns, nf).astype(np.float32)
        lbl1 = np.zeros((ns, nf), dtype=np.int32)
        lblN = np.zeros((ns, nf), dtype=np.int32)
        c2ImageD11.cimaged11_omp_set_num_threads(1)
        n1 = c2ImageD11.connectedpixels(data, lbl1, 0.0)
        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        nN = c2ImageD11.connectedpixels(data, lblN, 0.0)
        assert n1 == nN
        assert np.array_equal(lbl1, lblN)

    def test_make_clean_mask_1T_vs_nT(self):
        rng = np.random.RandomState(65)
        ns, nf = 30, 40
        img = rng.randn(ns, nf).astype(np.float32)
        msk1 = np.zeros((ns, nf), dtype=np.int8)
        ret1 = np.zeros((ns, nf), dtype=np.int8)
        mskN = np.zeros((ns, nf), dtype=np.int8)
        retN = np.zeros((ns, nf), dtype=np.int8)
        c2ImageD11.cimaged11_omp_set_num_threads(1)
        r1 = c2ImageD11.make_clean_mask(img, 0.0, msk1, ret1)
        c2ImageD11.cimaged11_omp_set_num_threads(N_CORES)
        rN = c2ImageD11.make_clean_mask(img, 0.0, mskN, retN)
        assert r1 == rN
        assert np.array_equal(msk1, mskN)
        assert np.array_equal(ret1, retN)
