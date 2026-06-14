"""Lightweight buffer-interface tests for c2ImageD11.

Verifies the compiled C module works via numpy's PEP 3118 buffer protocol.
No dependency on ImageD11. Runs on Python 2.7 through 3.14.

All tests use only numpy arrays (buffer protocol) -- no ctypes, no f2py.
"""
from __future__ import print_function

import sys
import numpy as np
import pytest

import c2ImageD11 as ci

IS_PY3 = sys.version_info[0] >= 3


# ============================================================
# Scalar in / scalar out
# ============================================================

class TestScalar:
    def test_verify_rounding(self):
        assert ci.verify_rounding(20) == 0
        assert ci.verify_rounding(5) == 0

    def test_omp_threads(self):
        n = ci.cimaged11_omp_get_max_threads()
        assert n >= 0


# ============================================================
# Buffer in / buffer out (1D float32)
# ============================================================

class TestArrayStats:
    def test_output(self):
        np.random.seed(42)
        img = (np.random.randn(200).astype(np.float32) * 3 + 7)
        mn = np.zeros(1, dtype=np.float32)
        mx = np.zeros(1, dtype=np.float32)
        me = np.zeros(1, dtype=np.float32)
        va = np.zeros(1, dtype=np.float32)
        ci.array_stats(img, mn, mx, me, va)
        assert np.isfinite(mn[0])
        assert np.isfinite(mx[0])
        assert np.isfinite(me[0])
        assert np.isfinite(va[0])
        assert mn[0] <= me[0] <= mx[0]
        assert va[0] >= 0.0


# ============================================================
# Buffer in / buffer out (uint16 -> float32)
# ============================================================

class TestUint16ToFloat:
    def test_darksub(self):
        np.random.seed(42)
        n = 250
        data = np.random.randint(0, 65535, n, dtype=np.uint16)
        dark = (np.random.randn(n).astype(np.float32) * 20 + 100)
        out = np.zeros(n, dtype=np.float32)
        ci.uint16_to_float_darksub(out, dark, data)
        assert np.isfinite(out).all()
        assert out.dtype == np.float32
        assert out.shape == (n,)


# ============================================================
# Buffer in / buffer out (2D float64 -> 1D int32)
# ============================================================

class TestClosestVec:
    def test_random(self):
        np.random.seed(42)
        nv, dim = 30, 3
        x = np.random.randn(nv, dim)
        ic = np.zeros(nv, dtype=np.int32)
        ci.closest_vec(x, ic)
        assert (ic >= 0).all()
        assert (ic < nv).all()


# ============================================================
# Buffer in / buffer out (2D float64 -> 2D float64)
# ============================================================

class TestComputeGV:
    def test_random(self):
        np.random.seed(42)
        n = 15
        xl = (np.random.randn(n, 3) * 0.1).astype(np.float64)
        w = np.random.random(n).astype(np.float64) * 360.0
        t_vec = np.random.randn(3).astype(np.float64) * 10
        gv = np.zeros((n, 3), dtype=np.float64)
        ci.compute_gv(xl, w, 1.0, 0.3, 5.0, 3.0, t_vec, gv)
        assert np.isfinite(gv).all()
        assert gv.dtype == np.float64
        assert gv.shape == (n, 3)


# ============================================================
# Buffer in / void out (in-place)
# ============================================================

class TestQuickorient:
    def test_inplace(self):
        np.random.seed(42)
        ubi = np.random.randn(9).astype(np.float64)
        bt = np.random.randn(9).astype(np.float64)
        ubi_copy = ubi.copy()
        ci.quickorient(ubi, bt)
        assert np.isfinite(ubi).all()
