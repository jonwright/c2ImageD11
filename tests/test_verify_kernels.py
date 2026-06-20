#!/usr/bin/env python
"""test_verify_kernels.py - SIMD kernel equivalence against ImageD11 f2py.

For each SIMD-accelerated function, generates random test inputs, calls both
the ImageD11 f2py reference and the c2ImageD11 c2py23 build, and compares
outputs element-by-element.

Only the functions with SIMD dispatch are tested (score family, compute_*
geometry, darksub/darkflm, put_incr*, reorder*, blobproperties).
Non-SIMD functions are already covered by test_equivalence.py.
"""
from __future__ import print_function
import numpy as np

import pytest
OLD = pytest.importorskip("ImageD11._cImageD11")
import c2ImageD11._cImageD11 as NEW


def close(a, b, rtol=1e-5, atol=1e-8):
    if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        if not np.allclose(a, b, rtol=rtol, atol=atol):
            diff = np.max(np.abs(a - b.astype(a.dtype)))
            raise AssertionError(
                "max diff %g, shapes %s vs %s" % (diff, a.shape, b.shape))
    else:
        if abs(a - b) > max(rtol * abs(b), atol):
            raise AssertionError("%s != %s" % (a, b))


# ============================================================
# score family
# ============================================================

class TestScoreKernel:
    def test_random(self):
        rng = np.random.RandomState(42)
        for _ in range(3):
            ubi = rng.randn(3, 3)
            gv = rng.randn(50, 3)
            tol = 0.1 + 0.2 * rng.random()
            assert OLD.score(ubi, gv, tol) == NEW.score(ubi, gv, tol)


class TestScoreAndRefineKernel:
    def test_random(self):
        rng = np.random.RandomState(42)
        for _ in range(3):
            ubi_o = rng.randn(3, 3).copy()
            ubi_n = ubi_o.copy()
            gv = rng.randn(30, 3)
            tol = 0.15
            n_o, s_o = OLD.score_and_refine(ubi_o, gv, tol)
            s_n = np.zeros(1, dtype=np.float64)
            n_n = NEW.score_and_refine(ubi_n, gv, tol, s_n)
            assert n_o == n_n
            close(s_o, s_n[0])
            close(ubi_o, ubi_n)


class TestScoreAndAssignKernel:
    def test_random(self):
        rng = np.random.RandomState(42)
        for _ in range(3):
            ubi = rng.randn(3, 3).astype(np.float64)
            gv = rng.randn(30, 3).astype(np.float64)
            tol = 0.2
            drlv2_o = np.zeros(30, dtype=np.float64)
            labels_o = np.zeros(30, dtype=np.int32)
            drlv2_n = np.zeros(30, dtype=np.float64)
            labels_n = np.zeros(30, dtype=np.int32)
            n_o = OLD.score_and_assign(ubi, gv, tol, drlv2_o, labels_o, 1)
            n_n = NEW.score_and_assign(ubi, gv, tol, drlv2_n, labels_n, 1)
            assert n_o == n_n
            assert (labels_o == labels_n).all()


# ============================================================
# geometry
# ============================================================

class TestComputeGVKernel:
    def test_random(self):
        rng = np.random.RandomState(42)
        for ng in [1, 10, 50]:
            xl = rng.randn(ng, 3).astype(np.float64)
            w = rng.randn(ng).astype(np.float64)
            t_vec = np.array([0.1, 0.2, 0.3])
            gv_o = np.zeros((ng, 3), dtype=np.float64)
            gv_n = np.zeros((ng, 3), dtype=np.float64)
            OLD.compute_gv(xl, w, 1.0, 0.3, 5.0, 3.0, t_vec, gv_o)
            NEW.compute_gv(xl, w, 1.0, 0.3, 5.0, 3.0, t_vec, gv_n)
            close(gv_o, gv_n, atol=1e-6)


class TestComputeGeometryKernel:
    def test_random(self):
        rng = np.random.RandomState(42)
        for ng in [1, 10, 50]:
            xl = rng.randn(ng, 3).astype(np.float64)
            w = rng.randn(ng).astype(np.float64)
            t_vec = np.array([0.1, 0.2, 0.3])
            out_o = np.zeros((ng, 6), dtype=np.float64)
            out_n = np.zeros((ng, 6), dtype=np.float64)
            OLD.compute_geometry(xl, w, 1.0, 0.3, 5.0, 3.0, t_vec, out_o)
            NEW.compute_geometry(xl, w, 1.0, 0.3, 5.0, 3.0, t_vec, out_n)
            close(out_o, out_n, atol=1e-5)


# ============================================================
# dark/flat
# ============================================================

class TestDarksubKernel:
    def test_random(self):
        rng = np.random.RandomState(42)
        for npx in [1, 100, 1000]:
            data = rng.randint(0, 65535, npx).astype(np.uint16)
            drk = rng.randn(npx).astype(np.float32)
            img_o = np.zeros(npx, dtype=np.float32)
            img_n = np.zeros(npx, dtype=np.float32)
            OLD.uint16_to_float_darksub(img_o, drk, data)
            NEW.uint16_to_float_darksub(img_n, drk, data)
            close(img_o, img_n)


class TestDarkflmKernel:
    def test_random(self):
        rng = np.random.RandomState(42)
        for npx in [1, 100, 1000]:
            data = rng.randint(0, 65535, npx).astype(np.uint16)
            drk = rng.randn(npx).astype(np.float32)
            flm = rng.randn(npx).astype(np.float32) + 0.1
            img_o = np.zeros(npx, dtype=np.float32)
            img_n = np.zeros(npx, dtype=np.float32)
            OLD.uint16_to_float_darkflm(img_o, drk, flm, data)
            NEW.uint16_to_float_darkflm(img_n, drk, flm, data)
            close(img_o, img_n)


# ============================================================
# put_incr race test
# ============================================================

class TestPutIncrKernel:
    def test_put_incr32(self):
        data = np.zeros(5, dtype=np.float32)
        ind = np.array([1, 1, 1, 1, 1], dtype=np.int32)
        vals = np.ones(5, dtype=np.float32)
        NEW.put_incr32(data, ind, vals)
        assert data[1] == 5.0, "put_incr32: expected 5, got %g" % data[1]

    def test_put_incr64(self):
        data = np.zeros(5, dtype=np.float32)
        ind = np.array([1, 1, 1, 1, 1], dtype=np.int64)
        vals = np.ones(5, dtype=np.float32)
        NEW.put_incr64(data, ind, vals)
        assert data[1] == 5.0, "put_incr64: expected 5, got %g" % data[1]


# ============================================================
# reorder
# ============================================================

class TestReorderKernel:
    def test_reorder_u16(self):
        rng = np.random.RandomState(42)
        N = 100
        data = rng.randint(0, 100, N).astype(np.uint16)
        adr = rng.permutation(N).astype(np.uint32)
        out_o = np.zeros(N, dtype=np.uint16)
        out_n = np.zeros(N, dtype=np.uint16)
        OLD.reorder_u16_a32(data, adr, out_o)
        NEW.reorder_u16_a32(data, adr, out_n)
        assert (out_o == out_n).all()

    def test_reorder_f32(self):
        rng = np.random.RandomState(42)
        N = 100
        data = rng.randn(N).astype(np.float32)
        adr = rng.permutation(N).astype(np.uint32)
        out_o = np.zeros(N, dtype=np.float32)
        out_n = np.zeros(N, dtype=np.float32)
        OLD.reorder_f32_a32(data, adr, out_o)
        NEW.reorder_f32_a32(data, adr, out_n)
        close(out_o, out_n)


# ============================================================
# blobproperties (SIMD path verification, not full equivalence)
# ============================================================

class TestBlobpropertiesKernel:
    def test_smoke(self):
        rng = np.random.RandomState(42)
        ns, nf = 16, 16
        data = (rng.rand(ns * nf).astype(np.float32) * 10).reshape(ns, nf)
        labels = rng.randint(0, 5, (ns, nf)).astype(np.int32)
        # OLD: f2py returns result array from (data, labels, npk)
        res_o = OLD.blobproperties(data, labels, 5)
        # NEW: c2py23 writes into pre-allocated buffer
        res_n = np.zeros((5, 36), dtype=np.float64)
        NEW.blobproperties(data, labels, 5, res_n)
        assert res_o.shape == res_n.shape
        close(res_o, res_n)
