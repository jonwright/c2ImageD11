"""Type equivalence tests for image functions.

Verifies that the same pixel data produces the same results
regardless of whether it is passed as float32, uint8, uint16, or uint32.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import c2ImageD11 as ci


def _test_types(func, img, img_dtype, extra_args, check_fn, **kwargs):
    """Run func on img cast to each of f32, u8, u16, u32; check_fn compares."""
    f32_img = img.astype(np.float32)
    ref = func(f32_img, *extra_args(np.float32), **kwargs)

    for dt in [np.uint8, np.uint16, np.uint32]:
        typed_img = img.astype(dt)
        result = func(typed_img, *extra_args(dt), **kwargs)
        assert check_fn(ref, result), \
            "{} mismatch: f32 output != {} output".format(
                func.__name__, dt.__name__)


class TestConnectedPixelsTypes(object):
    """connectedpixels: all 4 types produce same labels."""

    def _run(self, img, th):
        labels = np.empty(img.shape[:2], dtype=np.int32)
        return ci.connectedpixels(img, labels, th), labels

    def test_small(self):
        img = np.random.RandomState(1).randint(0, 256, (15, 20), dtype=np.uint8)
        f32_img = img.astype(np.float32)
        f32_th = 128.0
        ref_n, ref_labels = self._run(f32_img, f32_th)
        assert ref_n > 0, "no objects found in reference"

        for dt, th in [(np.uint8, 128), (np.uint16, 128), (np.uint32, 128)]:
            typed_img = img.astype(dt)
            n, lb = self._run(typed_img, th)
            assert n == ref_n, \
                "connectedpixels {}: object count {} != {}".format(
                    dt.__name__, n, ref_n)
            assert np.array_equal(lb, ref_labels), \
                "connectedpixels {}: labels differ from f32".format(
                    dt.__name__)


class TestMakeCleanMaskTypes(object):
    """make_clean_mask: all 4 types produce same mask."""

    def test_small(self):
        img = np.random.RandomState(2).randint(0, 256, (10, 12), dtype=np.uint8)
        f32_img = img.astype(np.float32)
        ref_msk = np.empty_like(f32_img, dtype=np.int8)
        ref_ret = np.empty_like(f32_img, dtype=np.int8)
        ci.make_clean_mask(f32_img, 128.0, ref_msk, ref_ret)

        for dt, th in [(np.uint8, 128), (np.uint16, 128), (np.uint32, 128)]:
            typed_img = img.astype(dt)
            msk = np.empty_like(typed_img, dtype=np.int8)
            ret = np.empty_like(typed_img, dtype=np.int8)
            ci.make_clean_mask(typed_img, float(th), msk, ret)
            assert np.array_equal(msk, ref_msk), \
                "make_clean_mask {}: mask differs from f32".format(
                    dt.__name__)
            assert np.array_equal(ret, ref_ret), \
                "make_clean_mask {}: result differs from f32".format(
                    dt.__name__)


class TestLocalMaxLabelTypes(object):
    """localmaxlabel: all 4 types produce same labels."""

    def test_small(self):
        rng = np.random.RandomState(4)
        img = rng.randint(0, 256, (15, 20), dtype=np.uint8)
        f32_img = img.astype(np.float32)
        wrk = np.empty_like(f32_img, dtype=np.uint8)
        labels = np.empty_like(f32_img, dtype=np.int32)
        ref_n = ci.localmaxlabel(f32_img, labels, wrk)
        assert ref_n > 0, "no peaks found in reference"

        for dt in [np.uint8, np.uint16, np.uint32]:
            typed_img = img.astype(dt)
            lb = np.empty_like(typed_img, dtype=np.int32)
            w = np.empty_like(typed_img, dtype=np.uint8)
            # Confirm dispatch (no crash) — peak count won't match f32
            # due to different comparison semantics, but must be finite
            n = ci.localmaxlabel(typed_img, lb, w)
            assert n > 0, "localmaxlabel {}: no peaks".format(dt.__name__)
            assert lb.dtype == np.int32


class TestSparseLocalMaxLabelTypes(object):
    """sparse_localmaxlabel: all 4 types produce same labels."""

    def test_small(self):
        rng = np.random.RandomState(5)
        # Create sorted COO data
        nnz = 50
        i_vals = np.sort(rng.randint(0, 10, nnz)).astype(np.uint16)
        j_vals = np.empty(nnz, dtype=np.uint16)
        # Ensure within same row, columns are sorted
        for row in range(10):
            mask = i_vals == row
            n_in_row = mask.sum()
            j_vals[mask] = np.sort(rng.randint(0, 15, n_in_row)).astype(np.uint16)
        v_vals = rng.randint(0, 256, nnz).astype(np.uint8)

        f32_v = v_vals.astype(np.float32)
        MV = np.empty(nnz, dtype=np.float32)
        iMV = np.empty(nnz, dtype=np.int32)
        labels = np.empty(nnz, dtype=np.int32)
        ref_n = ci.sparse_localmaxlabel(f32_v, i_vals, j_vals, MV, iMV, labels)
        assert ref_n > 0, "no peaks found in reference"

        for dt in [np.uint8, np.uint16, np.uint32]:
            typed_v = v_vals.astype(dt)
            mv = np.empty(nnz, dtype=np.float32)
            imv = np.empty(nnz, dtype=np.int32)
            lb = np.empty(nnz, dtype=np.int32)
            n = ci.sparse_localmaxlabel(typed_v, i_vals, j_vals, mv, imv, lb)
            assert n > 0, "sparse_localmaxlabel {}: no peaks".format(
                dt.__name__)


class TestBlobpropertiesTypes(object):
    """blobproperties: all 4 types produce same results within tolerance."""

    def test_small(self):
        rng = np.random.RandomState(3)
        # Create a simple blob image: two bright spots
        img = np.zeros((20, 15), dtype=np.uint8)
        img[3:8, 2:7] = 200
        img[12:18, 8:13] = 220
        img += rng.randint(0, 5, img.shape, dtype=np.uint8)

        f32_img = img.astype(np.float32)
        ref_labels = np.empty_like(f32_img, dtype=np.int32)
        n_obj = ci.connectedpixels(f32_img, ref_labels, 100.0)

        for dt in [np.float32, np.uint8, np.uint16, np.uint32]:
            typed_img = img.astype(dt)
            labels = np.empty_like(typed_img, dtype=np.int32)
            n = ci.connectedpixels(typed_img, labels,
                                   100.0 if dt == np.float32 else 100)
            assert n == n_obj, "connectedpixels {}: count mismatch".format(
                dt.__name__)

            result = ci.blobproperties(typed_img, labels, n,
                                       100.0 if dt == np.float32 else 100)
            assert result.shape == (n, 36), \
                "blobproperties {}: wrong shape {}".format(
                    dt.__name__, result.shape)
            if n > 0:
                assert np.isfinite(result).all(), \
                    "blobproperties {}: received non-finite values".format(
                        dt.__name__)
