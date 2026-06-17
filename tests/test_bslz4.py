"""Tests for bslz4_to_sparse C functions in c2ImageD11.

Buffer-level tests (no h5py needed) verify the C bridge works.
Equivalence tests compare against the original bslz4_to_sparse package.
"""

import numpy as np
import pytest
import c2ImageD11._cImageD11 as m


# ---------------------------------------------------------------------------
# Buffer-level smoke tests
# ---------------------------------------------------------------------------

class TestBslz4Buffer:
    """Test that bslz4 C functions accept buffers and return int."""

    def _check_basic(self, func, dtype):
        """Call a basic bslz4 function with zeroed data. Should return 0 npx."""
        compressed = np.zeros(100, dtype=np.uint8)
        mask = np.ones(4, dtype=np.uint8)
        out = np.zeros(4, dtype=dtype)
        outP = np.zeros(4, dtype=np.uint32)
        npx = func(compressed, mask, out, outP, 0)
        assert isinstance(npx, int)
        return npx

    def _check_csc(self, func, dtype):
        """Call a CSC bslz4 function with zeroed data."""
        compressed = np.zeros(100, dtype=np.uint8)
        mask = np.ones(4, dtype=np.uint8)
        outpx = np.zeros(4, dtype=dtype)
        outP = np.zeros(4, dtype=np.uint32)
        out = np.zeros(8, dtype=np.float64)
        data = np.ones(4, dtype=np.float32)
        indices = np.zeros(4, dtype=np.uint32)
        indptr = np.arange(5, dtype=np.uint32)
        npx = func(compressed, mask, outpx, outP, 0, out, data, indices, indptr)
        assert isinstance(npx, int)
        return npx

    def test_bslz4_uint8(self):
        self._check_basic(m.bslz4_uint8, np.uint8)

    def test_bslz4_uint16(self):
        self._check_basic(m.bslz4_uint16, np.uint16)

    def test_bslz4_uint32(self):
        self._check_basic(m.bslz4_uint32, np.uint32)

    def test_bslz4_csc_uint8(self):
        self._check_csc(m.bslz4_csc_uint8, np.uint8)

    def test_bslz4_csc_uint16(self):
        self._check_csc(m.bslz4_csc_uint16, np.uint16)

    def test_bslz4_csc_uint32(self):
        self._check_csc(m.bslz4_csc_uint32, np.uint32)


# ---------------------------------------------------------------------------
# Equivalence tests
# ---------------------------------------------------------------------------

def _make_compressed_data(shape=(4, 8), dtype=np.uint16, seed=42, cut=0):
    """Create synthetic compressed+mask data for comparison."""
    import h5py
    import hdf5plugin  # noqa: registers filter 32008
    import tempfile
    import os

    rng = np.random.RandomState(seed)
    frames = (rng.randint(0, 100, size=(1,) + shape)).astype(dtype)

    path = os.path.join(tempfile.mkdtemp(), "test.h5")
    with h5py.File(path, "w") as f:
        ds = f.create_dataset(
            "data", data=frames, chunks=(1,) + shape,
            compression=32008, compression_opts=(0, 2),
        )
    return path, frames[0]


class TestEquivalence:
    """Compare c2ImageD11 bslz4 C output against original bslz4_to_sparse."""

    def test_equivalence_c_layer(self):
        """Compare our bslz4_uint16 C function against original f2py."""
        try:
            from bslz4_to_sparse import bslz4_uint16_t as f2py_fn
        except ImportError:
            pytest.skip("original bslz4_uint16_t not available")

        path, ref_frame = _make_compressed_data()
        import h5py
        mask = np.ones(ref_frame.shape, dtype=np.uint8)
        N = ref_frame.size

        with h5py.File(path, "r") as f:
            ds = f["data"]
            filtinfo, chunk = ds.id.read_direct_chunk((0, 0, 0))
            chunk_buf = np.frombuffer(chunk, dtype=np.uint8)

            # Original: f2py bslz4_uint16_t(compressed, mask, values, indices, cut)
            vals_orig = np.zeros(N, dtype=np.uint16)
            inds_orig = np.zeros(N, dtype=np.uint32)
            npx_orig = f2py_fn(chunk_buf, mask.ravel(), vals_orig, inds_orig, 0)

            # Ours: c2py23 bslz4_uint16(compressed, mask, out, outP, thresh)
            vals_new = np.zeros(N, dtype=np.uint16)
            inds_new = np.zeros(N, dtype=np.uint32)
            npx_new = m.bslz4_uint16(
                chunk_buf, mask.ravel(), vals_new, inds_new, 0)

        assert npx_orig == npx_new
        np.testing.assert_array_equal(
            vals_orig[:npx_orig], vals_new[:npx_new])
        np.testing.assert_array_equal(
            inds_orig[:npx_orig], inds_new[:npx_new])
