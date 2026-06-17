"""CI-friendly bslz4/bszstd regression tests.

Generates synthetic Poisson test data (prime×prime image, 5 frames,
>5 bslz4 blocks of 8kB) in u8/u16/u32, compressed with LZ4 and ZSTD.
Decompresses all 12 Python-facing functions and verifies output
matches the original uncompressed data.

Requires: h5py, hdf5plugin  (skipped gracefully if not available)
"""

import os
import pytest
import numpy as np
import c2ImageD11._cImageD11 as _m

h5py = pytest.importorskip("h5py")
hdf5plugin = pytest.importorskip("hdf5plugin")  # noqa: registers filter 32008

# Two primes, >5 blocks of 8192 bytes for all dtypes
# 251 × 331 = 83,081 pixels
#   u8:  83,081 bytes = 10.1 blocks
#   u16: 166,162 bytes = 20.3 blocks
#   u32: 332,324 bytes = 40.6 blocks
ROWS, COLS = 251, 331
NFRAMES = 5
NPIX = ROWS * COLS  # 83,081

# ---- Test data generation (fixtures) ----

@pytest.fixture(scope="module")
def test_data():
    """Generate Poisson random data in all three dtypes, plus LZ4+ZSTD chunks."""
    rng = np.random.RandomState(42)

    data = {}
    for dt_name, dt, clip_max in [
        ("u8",  np.uint8,  200),
        ("u16", np.uint16, 50000),
        ("u32", np.uint32, 50000),
    ]:
        raw = rng.poisson(10, size=(NFRAMES, ROWS, COLS)).clip(0, clip_max).astype(dt)
        data[dt_name + "_raw"] = raw

        # Generate LZ4 and ZSTD compressed chunks
        for engine, copts in [
            ("lz4",  (0, 2, 0, 0, 2)),
            ("zstd", (0, 3, 2, 0, 2)),
        ]:
            import tempfile
            path = os.path.join(tempfile.mkdtemp(), "tmp.h5")
            h5f = h5py.File(path, "w")
            ds = h5f.create_dataset(
                "data", data=raw,
                chunks=(1, ROWS, COLS),
                compression=32008, compression_opts=copts,
            )
            chunks = [ds.id.read_direct_chunk((i, 0, 0))[1]
                      for i in range(NFRAMES)]
            h5f.close()
            data["%s_%s" % (engine, dt_name)] = chunks

    return data


# ---- The tests ----

def _check(func, chunks, raw, mask):
    """Decompress all frames, compare against raw data."""
    N = mask.size
    vals = np.empty(N, dtype=raw.dtype)
    inds = np.empty(N, dtype=np.uint32)
    for i in range(NFRAMES):
        npx = func(chunks[i], mask.ravel(), vals, inds, 0)
        ref_vals, ref_inds = _pysparse(raw[i], mask, 0)
        assert npx == len(ref_vals), f"frame {i}: npx {npx} != {len(ref_vals)}"
        np.testing.assert_array_equal(vals[:npx], ref_vals,
            err_msg=f"frame {i}: values mismatch")
        np.testing.assert_array_equal(inds[:npx], ref_inds,
            err_msg=f"frame {i}: indices mismatch")


def _check_csc(func, chunks, raw, mask):
    """Decompress CSC all frames, compare against raw data."""
    N = mask.size
    outpx = np.empty(N, dtype=raw.dtype)
    outP = np.empty(N, dtype=np.uint32)
    powder = np.zeros(1, dtype=np.float64)
    powder_ref = np.zeros(1, dtype=np.float64)
    data = np.ones(N, dtype=np.float32)
    indices = np.zeros(N, dtype=np.uint32)
    indptr = np.arange(N + 1, dtype=np.uint32)

    for i in range(NFRAMES):
        npx = func(chunks[i], mask.ravel(), outpx, outP, 0,
                   powder, data, indices, indptr)
        ref_vals, ref_inds = _pysparse(raw[i], mask, 0)
        assert npx == len(ref_vals), f"frame {i}: npx {npx} != {len(ref_vals)}"
        np.testing.assert_array_equal(outpx[:npx], ref_vals)
        np.testing.assert_array_equal(outP[:npx], ref_inds)
        powder_ref[:] = 0
        for k in range(N):
            v = raw[i].ravel()[k] * mask.ravel()[k]
            if v > 0:
                powder_ref[0] += v
        np.testing.assert_allclose(powder, powder_ref, rtol=1e-10)


def _pysparse(frame, mask, cut):
    """Pure-numpy reference: apply mask, threshold."""
    masked = frame * mask
    pixels = masked > cut
    return masked[pixels], np.where(pixels.ravel())[0].astype(np.uint32)


# ---- u8 tests ----

DTYPE_MAP = {
    np.uint8:  (_m.bslz4_u8,  _m.bslz4_csc_u8,  _m.bszstd_u8,  _m.bszstd_csc_u8),
    np.uint16: (_m.bslz4_u16, _m.bslz4_csc_u16, _m.bszstd_u16, _m.bszstd_csc_u16),
    np.uint32: (_m.bslz4_u32, _m.bslz4_csc_u32, _m.bszstd_u32, _m.bszstd_csc_u32),
}


@pytest.mark.parametrize("dtype_name,dt", [("u8", np.uint8), ("u16", np.uint16), ("u32", np.uint32)])
class TestBslz4CI:

    def test_bslz4_basic(self, dtype_name, dt, test_data):
        func = DTYPE_MAP[dt][0]
        mask = np.ones((ROWS, COLS), dtype=np.uint8)
        _check(func, test_data["lz4_" + dtype_name], test_data[dtype_name + "_raw"], mask)

    def test_bslz4_csc(self, dtype_name, dt, test_data):
        func = DTYPE_MAP[dt][1]
        mask = np.ones((ROWS, COLS), dtype=np.uint8)
        _check_csc(func, test_data["lz4_" + dtype_name], test_data[dtype_name + "_raw"], mask)

    def test_bszstd_basic(self, dtype_name, dt, test_data):
        func = DTYPE_MAP[dt][2]
        mask = np.ones((ROWS, COLS), dtype=np.uint8)
        _check(func, test_data["zstd_" + dtype_name], test_data[dtype_name + "_raw"], mask)

    def test_bszstd_csc(self, dtype_name, dt, test_data):
        func = DTYPE_MAP[dt][3]
        mask = np.ones((ROWS, COLS), dtype=np.uint8)
        _check_csc(func, test_data["zstd_" + dtype_name], test_data[dtype_name + "_raw"], mask)


# ---- Mask test ----

def test_bslz4_u16_with_mask(test_data):
    """Test with a sparse mask (10% active)."""
    mask = np.zeros((ROWS, COLS), dtype=np.uint8)
    rng = np.random.RandomState(99)
    mask.ravel()[rng.choice(NPIX, NPIX // 10, replace=False)] = 1

    func = _m.bslz4_u16
    chunks = test_data["lz4_u16"]
    raw = test_data["u16_raw"]
    N = mask.size
    vals = np.empty(N, dtype=np.uint16)
    inds = np.empty(N, dtype=np.uint32)
    for i in range(NFRAMES):
        npx = func(chunks[i], mask.ravel(), vals, inds, 0)
        ref_vals, ref_inds = _pysparse(raw[i], mask, 0)
        assert npx == len(ref_vals)
        np.testing.assert_array_equal(vals[:npx], ref_vals)
        np.testing.assert_array_equal(inds[:npx], ref_inds)
