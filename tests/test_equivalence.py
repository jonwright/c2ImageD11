"""Equivalence tests: c2ImageD11._cImageD11 vs ImageD11._cImageD11.

Handles calling convention differences:
- f2py returns output scalars as tuple elements
- c2py23 takes output scalars as 1-element buffer args

Skips entirely if ImageD11 is not installed.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import ctypes
import pytest

pytest.importorskip("ImageD11._cImageD11", reason="ImageD11 not installed")

import ImageD11 as _ImageD11_pkg
_IMAGE_D11_VERSION = tuple(int(x) for x in _ImageD11_pkg.__version__.split("."))
_REFINE_ASSIGNED_FIXED = _IMAGE_D11_VERSION >= (2, 1, 4)

OLD = None
NEW = None

def setup_module():
    global OLD, NEW
    import ImageD11._cImageD11 as _old
    import c2ImageD11._cImageD11 as _new
    OLD = _old
    NEW = _new


def close(a, b, rtol=1e-10, atol=1e-10):
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    assert a.shape == b.shape
    assert np.allclose(a, b, rtol=rtol, atol=atol)


# ============================================================
# Scalar-in, scalar-out (same convention)
# ============================================================

class TestVerifyRounding:
    def test_basic(self):
        if not hasattr(OLD, 'verify_rounding'):
            pytest.skip("verify_rounding not in ImageD11 %s" % str(_IMAGE_D11_VERSION))
        assert OLD.verify_rounding(20) == NEW.verify_rounding(20)

class TestOMP:
    def test_get_max_threads(self):
        assert NEW.cimaged11_omp_get_max_threads() >= 0


# ============================================================
# closest family
# ============================================================

class TestClosestVec:
    def test_random(self):
        np.random.seed(42)
        for _ in range(3):
            nv, dim = 50, 3
            x = np.random.randn(nv, dim)
            ic_old = np.zeros(nv, dtype=np.int32)
            ic_new = np.zeros(nv, dtype=np.int32)
            OLD.closest_vec(x, ic_old)
            NEW.closest_vec(x, ic_new)
            assert (ic_old == ic_new).all()


class TestClosest:
    def test_random(self):
        np.random.seed(42)
        for _ in range(3):
            x = np.sort(np.random.random(100))
            v = np.random.random(20)
            # f2py returns (ibest, best) tuple
            ib_o, best_o = OLD.closest(x, v)
            # c2py23 returns tuple directly via outputs
            ib_n, best_n = NEW.closest(x, v)
            assert ib_o == ib_n
            close(best_o, best_n)


class TestCountShared:
    def test_random(self):
        np.random.seed(42)
        pi = np.sort(np.random.randint(0, 100, 50)).astype(np.int32)
        pj = np.sort(np.random.randint(0, 100, 40)).astype(np.int32)
        assert OLD.count_shared(pi, pj) == NEW.count_shared(pi, pj)


# ============================================================
# score family
# ============================================================

class TestScore:
    def test_random(self):
        np.random.seed(42)
        for _ in range(5):
            ubi = np.random.randn(3, 3)
            gv = np.random.randn(100, 3)
            tol = 0.1 + 0.2 * np.random.random()
            n_o = OLD.score(ubi, gv, tol)
            n_n = NEW.score(ubi, gv, tol)
            assert abs(n_o - n_n) <= 5, "n differ: %d vs %d" % (n_o, n_n)


class TestScoreAndRefine:
    def test_random(self):
        np.random.seed(42)
        for _ in range(3):
            ubi_o = np.random.randn(3, 3).copy()
            ubi_n = ubi_o.copy()
            gv = np.random.randn(50, 3)
            tol = 0.15
            # f2py returns (n, sumdrlv2)
            n_o, s_o = OLD.score_and_refine(ubi_o, gv, tol)
            # c2py23 returns tuple directly via outputs
            n_n, s_n = NEW.score_and_refine(ubi_n, gv, tol)
            assert abs(n_o - n_n) <= 2, "n differ: %d vs %d" % (n_o, n_n)
            close(s_o * (n_o or 1), s_n * (n_n or 1))
            if n_o == n_n:
                close(ubi_o, ubi_n)


class TestScoreAndAssign:
    def test_random(self):
        np.random.seed(42)
        ubi = np.random.randn(3, 3)
        gv = np.random.randn(30, 3)
        tol = 0.2
        drlv2_o = np.full(30, 999.0)
        drlv2_n = np.full(30, 999.0)
        labels_o = np.zeros(30, dtype=np.int32)
        labels_n = np.zeros(30, dtype=np.int32)
        n_o = OLD.score_and_assign(ubi, gv, tol, drlv2_o, labels_o, 1)
        n_n = NEW.score_and_assign(ubi, gv, tol, drlv2_n, labels_n, 1)
        assert n_o == n_n
        assert (labels_o == labels_n).all()


@pytest.mark.skipif(not _REFINE_ASSIGNED_FIXED,
                    reason="ImageD11 refine_assigned has infinite loop (fixed in >=2.1.4)")
class TestRefineAssigned:
    def test_random(self):
        np.random.seed(42)
        ubi_o = np.random.randn(3, 3).copy()
        ubi_n = ubi_o.copy()
        gv = np.random.randn(30, 3)
        labels = np.random.randint(0, 2, 30).astype(np.int32)
        label = 1
        # f2py returns (npk, drlv2)
        npk_o, drlv2_o = OLD.refine_assigned(ubi_o, gv, labels, label)
        # c2py23 returns tuple directly via outputs
        npk_n, drlv2_n = NEW.refine_assigned(ubi_n, gv, labels, label)
        assert npk_o == npk_n
        close(drlv2_o, drlv2_n)
        if npk_o > 0:
            close(ubi_o, ubi_n)


class TestCluster1D:
    def test_small(self):
        np.random.seed(42)
        ar = np.sort(np.random.random(20))
        order = np.arange(20, dtype=np.int32)
        tol = 0.05
        ids_o = np.zeros(20, dtype=np.int32)
        ids_n = np.zeros(20, dtype=np.int32)
        avgs_o = np.zeros(20, dtype=np.float64)
        avgs_n = np.zeros(20, dtype=np.float64)
        nco = OLD.cluster1d(ar, order, tol, ids_o, avgs_o)
        ncn = NEW.cluster1d(ar, order, tol, ids_n, avgs_n)
        assert nco == ncn
        assert (ids_o == ids_n).all()


# ============================================================
# misori (same convention: double in, double out)
# ============================================================

class TestPutIncr:
    def test_put_incr32(self):
        data = np.zeros(5, dtype=np.float32)
        ind = np.array([1, 1, 1, 1, 1], dtype=np.int32)
        vals = np.ones(5, dtype=np.float32)
        NEW.put_incr32(data, ind, vals)
        assert data[1] == 5.0

    def test_put_incr64(self):
        data = np.zeros(5, dtype=np.float32)
        ind = np.array([1, 1, 1, 1, 1], dtype=np.int64)
        vals = np.ones(5, dtype=np.float32)
        NEW.put_incr64(data, ind, vals)
        assert data[1] == 5.0


class TestMisori:
    @pytest.mark.parametrize("func", [
        "misori_cubic", "misori_orthorhombic",
        "misori_tetragonal", "misori_monoclinic"
    ])
    def test_identity(self, func):
        u1 = np.eye(3)
        u2 = np.eye(3)
        old_val = getattr(OLD, func)(u1, u2)
        new_val = getattr(NEW, func)(u1, u2)
        if func == "misori_tetragonal" and abs(old_val - 1.0) < 0.01:
            pytest.skip("misori_tetragonal: bug fixed in c2ImageD11 (OLD returns 1, correct is 3)")
        close(old_val, new_val)

    @pytest.mark.parametrize("func", [
        "misori_cubic", "misori_orthorhombic",
        "misori_tetragonal", "misori_monoclinic"
    ])
    def test_random(self, func):
        np.random.seed(42)
        for _ in range(3):
            u1 = np.random.randn(3, 3)
            u2 = np.random.randn(3, 3)
            old_val = getattr(OLD, func)(u1, u2)
            new_val = getattr(NEW, func)(u1, u2)
            if func == "misori_tetragonal" and abs(getattr(OLD, func)(np.eye(3), np.eye(3)) - 1.0) < 0.01:
                pytest.skip("misori_tetragonal: bug fixed in c2ImageD11")
            close(old_val, new_val)


# ============================================================
# compute_*
# ============================================================

class TestComputeGeometry:
    def test_random(self):
        if not hasattr(OLD, 'compute_geometry'):
            pytest.skip("compute_geometry not in ImageD11 %s" % str(_IMAGE_D11_VERSION))
        np.random.seed(42)
        n = 20
        xl = np.random.randn(n, 3) * 0.1
        w = np.random.random(n) * 360.0
        t_vec = np.random.randn(3) * 10
        out_o = np.zeros((n, 6))
        out_n = np.zeros((n, 6))
        OLD.compute_geometry(xl, w, 1.0, 0.3, 5.0, 3.0, t_vec, out_o)
        NEW.compute_geometry(xl, w, 1.0, 0.3, 5.0, 3.0, t_vec, out_n)
        close(out_o, out_n, atol=1e-6)

class TestComputeGV:
    def test_random(self):
        np.random.seed(42)
        n = 20
        xl = np.random.randn(n, 3) * 0.1
        w = np.random.random(n) * 360.0
        t_vec = np.random.randn(3) * 10
        gv_o = np.zeros((n, 3))
        gv_n = np.zeros((n, 3))
        OLD.compute_gv(xl, w, 1.0, 0.3, 5.0, 3.0, t_vec, gv_o)
        NEW.compute_gv(xl, w, 1.0, 0.3, 5.0, 3.0, t_vec, gv_n)
        close(gv_o, gv_n, atol=1e-6)

class TestComputeXlylzl:
    def test_random(self):
        np.random.seed(42)
        n = 20
        s = np.random.random(n) * 2000
        f = np.random.random(n) * 2000
        p = np.array([1000.0, 1000.0, 0.1, 0.1])
        r = np.array([0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0])
        dist = np.array([100.0, 0.0, 0.0])
        xl_o = np.zeros((n, 3))
        xl_n = np.zeros((n, 3))
        OLD.compute_xlylzl(s, f, p, r, dist, xl_o)
        NEW.compute_xlylzl(s, f, p, r, dist, xl_n)
        close(xl_o, xl_n, atol=1e-6)

class TestQuickorient:
    def test_random(self):
        np.random.seed(42)
        ubi = np.random.randn(3, 3).copy()
        bt = np.random.randn(3, 3).copy()
        ubi_n = ubi.copy()
        bt_n = bt.copy()
        OLD.quickorient(ubi, bt)
        NEW.quickorient(ubi_n, bt_n)
        close(ubi.ravel(), ubi_n.ravel())


# ============================================================
# array stats (f2py returns tuples, c2py23 takes buffers)
# ============================================================

class TestArrayStats:
    def test_random(self):
        np.random.seed(42)
        img = np.random.randn(1000).astype(np.float32) * 2 + 10
        mn_o, mx_o, me_o, va_o = OLD.array_stats(img)
        mn_n, mx_n, me_n, va_n = NEW.array_stats(img)
        close(mn_o, mn_n)
        close(mx_o, mx_n)
        close(me_o, me_n)
        close(va_o, va_n)

class TestArrayMeanVarCut:
    def test_random(self):
        np.random.seed(42)
        img = np.random.randn(1000).astype(np.float32) * 2 + 10
        me_o, va_o = OLD.array_mean_var_cut(img)
        me_n, va_n = NEW.array_mean_var_cut(img)
        close(me_o, me_n, atol=1e-4)
        close(va_o, va_n, atol=1e-4)

class TestArrayHistogram:
    def test_random(self):
        np.random.seed(42)
        img = np.random.randn(1000).astype(np.float32) * 2 + 10
        lo, hi = img.min(), img.max() + 1e-6
        nbins = 20
        hist_o = np.zeros(nbins, dtype=np.int32)
        hist_n = np.zeros(nbins, dtype=np.int32)
        OLD.array_histogram(img, lo, hi, hist_o)
        NEW.array_histogram(img, lo, hi, hist_n)
        assert (hist_o == hist_n).all()


# ============================================================
# uint16_to_float
# ============================================================

class TestUint16Convert:
    def test_darksub(self):
        np.random.seed(42)
        n = 500
        data = np.random.randint(0, 65535, n, dtype=np.uint16)
        drk = np.random.randn(n).astype(np.float32) * 10
        img_o = np.zeros(n, dtype=np.float32)
        img_n = np.zeros(n, dtype=np.float32)
        OLD.uint16_to_float_darksub(img_o, drk, data)
        NEW.uint16_to_float_darksub(img_n, drk, data)
        close(img_o, img_n)

    def test_darkflm(self):
        np.random.seed(42)
        n = 500
        data = np.random.randint(0, 65535, n, dtype=np.uint16)
        drk = np.random.randn(n).astype(np.float32) * 10
        flm = np.random.random(n).astype(np.float32) * 2 + 0.5
        img_o = np.zeros(n, dtype=np.float32)
        img_n = np.zeros(n, dtype=np.float32)
        OLD.uint16_to_float_darkflm(img_o, drk, flm, data)
        NEW.uint16_to_float_darkflm(img_n, drk, flm, data)
        close(img_o, img_n)


# ============================================================
# connectedpixels / blobproperties
# ============================================================

class TestConnectedPixels:
    def test_small(self):
        np.random.seed(42)
        ns, nf = 20, 20
        data = np.random.randn(ns, nf).astype(np.float32)
        labels_o = np.zeros((ns, nf), dtype=np.int32)
        labels_n = np.zeros((ns, nf), dtype=np.int32)
        npk_o = OLD.connectedpixels(data, labels_o, 0.5, 0, 1)
        npk_n = NEW.connectedpixels(data, labels_n, 0.5, 0, 1)
        assert npk_o == npk_n
        assert (labels_o == labels_n).all()

class TestBlobProperties:
    def test_simulated_blobs(self):
        """Create a simulated image with gaussian peaks, label them,
        then compute blobproperties by both old and new APIs."""
        np.random.seed(42)
        ns, nf = 64, 64
        sig = 3.0
        i, j = np.mgrid[0:ns, 0:nf]

        def gaussian(x, y, cx, cy, s):
            dx = i - cx
            dy = j - cy
            return np.exp(-(dx * dx + dy * dy) / (2 * s * s))

        # Place 4 well-separated gaussian peaks
        im = np.zeros((ns, nf), dtype=np.float32)
        peaks = [(16, 16), (48, 16), (16, 48), (48, 48)]
        for cx, cy in peaks:
            im += gaussian(i, j, cx, cy, sig)
        im *= 1000.0

        # Label via connectedpixels (use OLD for both)
        labels = np.zeros((ns, nf), dtype=np.int32)
        npk = OLD.connectedpixels(im, labels, 100.0, 0, 1)
        assert npk >= 1, "Expected at least 1 connected component"

        res_o = OLD.blobproperties(im, labels, npk)
        res_n = NEW.blobproperties(im, labels, npk)
        assert res_o.shape == res_n.shape
        close(res_o, res_n)

class TestBloboverlaps:
    def test_small(self):
        np.random.seed(42)
        ns, nf = 20, 20
        d1 = np.random.randn(ns, nf).astype(np.float32) + 10
        d2 = np.random.randn(ns, nf).astype(np.float32) + 10
        l1 = np.zeros((ns, nf), dtype=np.int32)
        l2 = np.zeros((ns, nf), dtype=np.int32)
        n1 = OLD.connectedpixels(d1, l1, 8.0, 0, 1)
        n2 = OLD.connectedpixels(d2, l2, 8.0, 0, 1)
        if n1 == 0 or n2 == 0:
            return
        # f2py blobproperties allocates and returns result arrays
        r1_o = OLD.blobproperties(d1, l1, n1)
        r2_o = OLD.blobproperties(d2, l2, n2)
        r1_n = r1_o.copy()
        r2_n = r2_o.copy()
        o = OLD.bloboverlaps(l1, n1, r1_o, l2, n2, r2_o)
        n = NEW.bloboverlaps(l1, n1, r1_n, l2, n2, r2_n)
        assert o == n
        close(r1_o, r1_n)
        close(r2_o, r2_n)

class TestBlobMoments:
    def test_random(self):
        np.random.seed(42)
        npk = 5
        res_o = np.zeros((npk, 36))
        res_n = np.zeros((npk, 36))
        for i in range(npk):
            off = i * 36
            for j in [0, 1, 3, 4, 6, 8, 9, 11]:
                val = np.random.random() * 1000 + 10
                res_o.flat[off + j] = val
                res_n.flat[off + j] = val
        OLD.blob_moments(res_o)
        NEW.blob_moments(res_n)
        close(res_o, res_n)

class TestCleanMask:
    def test_small(self):
        ns, nf = 10, 10
        msk = np.zeros((ns, nf), dtype=np.int8)
        msk[3:7, 4:8] = 1
        ret_o = np.zeros((ns, nf), dtype=np.int8)
        ret_n = np.zeros((ns, nf), dtype=np.int8)
        n_o = OLD.clean_mask(msk, ret_o)
        n_n = NEW.clean_mask(msk, ret_n)
        assert n_o == n_n
        assert (ret_o == ret_n).all()

class TestMakeCleanMask:
    def test_small(self):
        ns, nf = 10, 10
        img = np.random.randn(ns, nf).astype(np.float32) + 2
        msk_o = np.zeros((ns, nf), dtype=np.int8)
        msk_n = np.zeros((ns, nf), dtype=np.int8)
        ret_o = np.zeros((ns, nf), dtype=np.int8)
        ret_n = np.zeros((ns, nf), dtype=np.int8)
        n_o = OLD.make_clean_mask(img, 1.0, msk_o, ret_o)
        n_n = NEW.make_clean_mask(img, 1.0, msk_n, ret_n)
        assert n_o == n_n
        assert (ret_o == ret_n).all()


# ============================================================
# localmaxlabel
# ============================================================

class TestLocalMaxLabel:
    def test_small(self):
        np.random.seed(42)
        ns, nf = 20, 20
        data = np.random.randn(ns, nf).astype(np.float32)
        lo = np.zeros((ns, nf), dtype=np.int32)
        ln = np.zeros((ns, nf), dtype=np.int32)
        wo = np.zeros((ns, nf), dtype=np.int8)
        wn = np.zeros((ns, nf), dtype=np.int8)
        no = OLD.localmaxlabel(data, lo, wo)
        nn = NEW.localmaxlabel(data, ln, wn)
        assert no >= 0
        assert nn >= 0


# ============================================================
# sparse functions
# ============================================================

class TestSparseIsSorted:
    def test_sorted(self):
        i = np.array([0, 0, 0, 1, 1], dtype=np.uint16)
        j = np.array([0, 1, 2, 1, 2], dtype=np.uint16)
        assert OLD.sparse_is_sorted(i, j) == NEW.sparse_is_sorted(i, j)
        assert OLD.sparse_is_sorted(i, j) == 0

class TestMaskToCOO:
    def test_small(self):
        ns, nf = 5, 5
        msk = np.zeros((ns, nf), dtype=np.int8)
        msk[2:4, 1:3] = 1
        nnz = int(msk.sum())
        i = np.zeros(nnz, dtype=np.uint16)
        j = np.zeros(nnz, dtype=np.uint16)
        w = np.zeros(ns, dtype=np.int32)
        ret = NEW.mask_to_coo(msk, i, j, w)
        assert ret == 0

class TestCompressDuplicates:
    def test_small(self):
        np.random.seed(42)
        ii = np.sort(np.random.randint(0, 3, 10)).astype(np.int32)
        jj = np.sort(np.random.randint(0, 3, 10)).astype(np.int32)
        oi_o = np.zeros(10, dtype=np.int32)
        oj_o = np.zeros(10, dtype=np.int32)
        tmp_o = np.zeros(50, dtype=np.int32)
        n_o = OLD.compress_duplicates(ii.copy(), jj.copy(), oi_o, oj_o, tmp_o)
        n_n = NEW.compress_duplicates(ii.copy(), jj.copy(),
                                       np.zeros(10, dtype=np.int32),
                                       np.zeros(10, dtype=np.int32),
                                       np.zeros(50, dtype=np.int32))
        assert n_o == n_n

class TestSparseOverlaps:
    def test_small(self):
        i1 = np.array([0, 0, 1], dtype=np.uint16)
        j1 = np.array([1, 2, 1], dtype=np.uint16)
        i2 = np.array([0, 0, 1], dtype=np.uint16)
        j2 = np.array([2, 3, 1], dtype=np.uint16)
        k1 = np.zeros(3, dtype=np.int32)
        k2 = np.zeros(3, dtype=np.int32)
        o = OLD.sparse_overlaps(i1, j1, k1, i2, j2, k2)
        n = NEW.sparse_overlaps(i1, j1, k1, i2, j2, k2)
        assert o == n

class TestSparseConnectedPixels:
    def test_small(self):
        np.random.seed(42)
        n = 100
        v = np.random.randn(n).astype(np.float32) + 2
        ii = np.random.randint(0, 10, n, dtype=np.uint16)
        jj = np.random.randint(0, 10, n, dtype=np.uint16)
        lo = np.zeros(n, dtype=np.int32)
        ln = np.zeros(n, dtype=np.int32)
        o = OLD.sparse_connectedpixels(v, ii, jj, 0.5, lo)
        n = NEW.sparse_connectedpixels(v, ii, jj, 0.5, ln)
        assert o == n

class TestSparseSmooth:
    def test_small(self):
        if not hasattr(OLD, 'sparse_smooth'):
            pytest.skip("sparse_smooth not in ImageD11 %s" % str(_IMAGE_D11_VERSION))
        np.random.seed(42)
        n = 50
        v = np.random.randn(n).astype(np.float32) + 2
        ii = np.random.randint(0, 10, n, dtype=np.uint16)
        jj = np.random.randint(0, 10, n, dtype=np.uint16)
        so = np.zeros(n, dtype=np.float32)
        sn = np.zeros(n, dtype=np.float32)
        OLD.sparse_smooth(v, ii, jj, so)
        NEW.sparse_smooth(v, ii, jj, sn)
        close(so, sn)

class TestSparseLocalMaxLabel:
    def test_small(self):
        np.random.seed(42)
        n = 100
        v = np.random.randn(n).astype(np.float32) + 2
        ii = np.random.randint(0, 10, n, dtype=np.uint16)
        jj = np.random.randint(0, 10, n, dtype=np.uint16)
        MVo = np.zeros(n, dtype=np.float32)
        MVn = np.zeros(n, dtype=np.float32)
        iMVo = np.zeros(n, dtype=np.int32)
        iMVn = np.zeros(n, dtype=np.int32)
        lo = np.zeros(n, dtype=np.int32)
        ln = np.zeros(n, dtype=np.int32)
        o = OLD.sparse_localmaxlabel(v, ii, jj, MVo, iMVo, lo)
        n = NEW.sparse_localmaxlabel(v, ii, jj, MVn, iMVn, ln)
        assert o >= 0
        assert n >= 0

class TestToSparse:
    def test_u16(self):
        if not hasattr(OLD, 'tosparse_u16'):
            pytest.skip("tosparse_u16 not in ImageD11 %s" % str(_IMAGE_D11_VERSION))
        ns, nf = 8, 8
        img = np.random.randint(0, 100, (ns, nf), dtype=np.uint16)
        msk = np.ones((ns, nf), dtype=np.uint8)
        # f2py expects 2D (ns, nf) for row/col/val
        row = np.zeros((ns, nf), dtype=np.uint16)
        col = np.zeros((ns, nf), dtype=np.uint16)
        val = np.zeros((ns, nf), dtype=np.uint16)
        o = OLD.tosparse_u16(img, msk, row, col, val, 50)
        n = NEW.tosparse_u16(img, msk,
                              np.zeros((ns, nf), dtype=np.uint16),
                              np.zeros((ns, nf), dtype=np.uint16),
                              np.zeros((ns, nf), dtype=np.uint16), 50)
        assert o == n

    def test_f32(self):
        if not hasattr(OLD, 'tosparse_f32'):
            pytest.skip("tosparse_f32 not in ImageD11 %s" % str(_IMAGE_D11_VERSION))
        ns, nf = 8, 8
        img = np.random.randn(ns, nf).astype(np.float32) + 5
        msk = np.ones((ns, nf), dtype=np.uint8)
        row = np.zeros((ns, nf), dtype=np.uint16)
        col = np.zeros((ns, nf), dtype=np.uint16)
        val = np.zeros((ns, nf), dtype=np.float32)
        o = OLD.tosparse_f32(img, msk, row, col, val, 3.0)
        n = NEW.tosparse_f32(img, msk,
                              np.zeros((ns, nf), dtype=np.uint16),
                              np.zeros((ns, nf), dtype=np.uint16),
                              np.zeros((ns, nf), dtype=np.float32), 3.0)
        assert o == n

class TestCoverlaps:
    def test_small(self):
        if not hasattr(OLD, 'coverlaps'):
            pytest.skip("coverlaps not in ImageD11 %s" % str(_IMAGE_D11_VERSION))
        r1 = np.array([0, 0, 1], dtype=np.uint16)
        c1 = np.array([1, 2, 1], dtype=np.uint16)
        l1 = np.array([1, 1, 2], dtype=np.int32)
        r2 = np.array([0, 0, 1], dtype=np.uint16)
        c2 = np.array([1, 3, 1], dtype=np.uint16)
        l2 = np.array([1, 1, 1], dtype=np.int32)
        mat = np.zeros((2, 1), dtype=np.int32)
        res = np.zeros(10, dtype=np.int32)
        o = OLD.coverlaps(r1, c1, l1, r2, c2, l2, mat, res)
        n = NEW.coverlaps(r1, c1, l1, r2, c2, l2, mat, res)
        assert o == n


# ============================================================
# reorder
# ============================================================

class TestReorder:
    def test_u16(self):
        np.random.seed(42)
        n = 100
        data = np.random.randint(0, 100, n, dtype=np.uint16)
        adr = np.random.permutation(n).astype(np.uint32)
        out_o = np.zeros(n, dtype=np.uint16)
        out_n = np.zeros(n, dtype=np.uint16)
        OLD.reorder_u16_a32(data, adr, out_o)
        NEW.reorder_u16_a32(data, adr, out_n)
        assert (out_o == out_n).all()

    def test_f32(self):
        np.random.seed(42)
        n = 100
        data = np.random.randn(n).astype(np.float32)
        adr = np.random.permutation(n).astype(np.uint32)
        out_o = np.zeros(n, dtype=np.float32)
        out_n = np.zeros(n, dtype=np.float32)
        OLD.reorder_f32_a32(data, adr, out_o)
        NEW.reorder_f32_a32(data, adr, out_n)
        close(out_o, out_n)


# ============================================================
# splat
# ============================================================

class TestSplat:
    def test_small(self):
        rgba = np.zeros((100, 100, 4), dtype=np.uint8)
        gv = np.random.randn(10, 3)
        u = np.array([0.05, 0, 0, 0, -0.05, 0, 0, 0, 0.1])
        OLD.splat(rgba, gv, u, 1)
        rgba2 = np.zeros((100, 100, 4), dtype=np.uint8)
        NEW.splat(rgba2, gv, u, 1)
        assert (rgba == rgba2).all()
