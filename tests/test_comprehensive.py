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
