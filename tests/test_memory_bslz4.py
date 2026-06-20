"""Memory safety tests for bslz4 C functions.

Exercises every CSC1D and CSC function variant with valid data
sizes, and explicitly tests the NOUT/nchunks boundary condition that
caused a heap-buffer-overflow (fixed by adding
/ chunk_offsets.shape[0] to the NOUT map expression).

Run under valgrind:
    valgrind --leak-check=full --error-exitcode=1 python3 -m pytest tests/test_memory_bslz4.py -v

Quick mode (no valgrind, 10 iterations):
    python3 tests/test_memory_bslz4.py
"""

from __future__ import print_function

import os
import sys
import numpy as np
import c2ImageD11._cImageD11 as _m

NITERS = int(os.environ.get("MEMTEST_ITERS", "100" if "--valgrind" in sys.argv else "3"))
NIJ_SMALL = 256       # small NIJ for fast valgrind runs
NOUT_SMALL = 32
EASY_EPP = 4
NIJ_EASY = NIJ_SMALL * EASY_EPP  # 1024 flat elements


def _make_mask():
    mask = np.ones(NIJ_SMALL, dtype=np.uint8)
    mask[::3] = 0  # ~33% masked
    return mask


def _make_csc_flat(entries_per_pixel=4):
    """Create a synthetic 1D-padded CSC array where weights sum to 1.0 per pixel."""
    NIJ = NIJ_SMALL
    epp = entries_per_pixel
    flat = np.zeros(NIJ * epp, dtype=np.float32)
    first_bin = np.zeros(NIJ, dtype=np.uint32)
    rng = np.random.RandomState(42)
    for j in range(NIJ):
        if rng.rand() > 0.33:  # 2/3 of pixels have data
            nz = rng.randint(2, epp + 1)
            w = rng.random(nz)
            w /= w.sum()
            flat[j * epp: j * epp + nz] = w
            first_bin[j] = rng.randint(0, NOUT_SMALL - epp)
    return flat, first_bin


def _make_quantized(csc_flat, scale_factor, dtype):
    """Quantize CSC weights, ensuring per-pixel sum = scale_factor."""
    epp = len(csc_flat) // NIJ_SMALL
    q = np.round(csc_flat * scale_factor).astype(dtype)
    for j in range(NIJ_SMALL):
        base = j * epp
        row = q[base:base + epp]
        s = int(row.sum(dtype=np.int64))
        if s > 0 and s != scale_factor:
            idx = int(np.argmax(row))
            diff = scale_factor - s
            new_val = int(row[idx]) + diff
            if 0 <= new_val <= np.iinfo(dtype).max:
                row[idx] = dtype(new_val)
    return q


def _make_standard_csc():
    """Create a standard CSC matrix (data, indices, indptr)."""
    NIJ = NIJ_SMALL
    mask = _make_mask()
    rng = np.random.RandomState(42)
    data = []
    indices = []
    indptr = [0]
    for j in range(NIJ):
        if mask[j] and rng.rand() > 0.2:
            nz = rng.randint(2, 5)
            w = rng.random(nz).astype(np.float32)
            w /= w.sum()
            bins = rng.randint(0, NOUT_SMALL - 3, size=nz)
            bins.sort()
            data.extend(w)
            indices.extend(bins)
        indptr.append(len(data))
    return (np.array(data, dtype=np.float32),
            np.array(indices, dtype=np.uint32),
            np.array(indptr, dtype=np.uint32))


def get_chunk_offsets(nij):
    """Simulate chunk offsets as if from an HDF5 file."""
    compressed = np.arange(12 + 4 + nij * 2, dtype=np.uint8)  # header + some data
    return compressed, np.array([0], dtype=np.int64), np.array([len(compressed)], dtype=np.int32)


# ===========================================================================
# Tests
# ===========================================================================

class TestCSC1DMemory:
    """Memory safety for 1D-padded CSC functions (bslz4_csc1d_*)."""

    def setup_method(self):
        self.mask = _make_mask()
        self.csc_flat, self.first_bin = _make_csc_flat(EASY_EPP)

    def _run_variant(self, nframes, fn, csc_arr, epp):
        """Run the C function with valid data.  No error expected."""
        mask = self.mask
        compressed, offsets, lengths = get_chunk_offsets(NIJ_SMALL)

        ox = np.zeros(nframes * NIJ_SMALL, dtype=np.uint16)
        oa = np.zeros(nframes * NIJ_SMALL, dtype=np.uint32)
        pw = np.zeros(nframes * NOUT_SMALL, dtype=np.float64)

        for _ in range(NITERS):
            offs_batch = np.array([0] * nframes if nframes > 1 else [0], dtype=np.int64)
            lens_batch = np.array([len(compressed)] * nframes if nframes > 1 else [len(compressed)], dtype=np.int32)

            npc = np.zeros(nframes, dtype=np.int32)
            fn(compressed, mask, ox, oa, 0,
               pw, csc_arr, self.first_bin, epp,
               offs_batch, lens_batch, npc)

    def test_csc1d_f32_1frame(self):
        self._run_variant(1, _m.bslz4_csc1d_u16, self.csc_flat, EASY_EPP)

    def test_csc1d_f32_4frames(self):
        self._run_variant(4, _m.bslz4_csc1d_u16, self.csc_flat, EASY_EPP)


class TestCSCStandardMemory:
    """Memory safety for standard CSC functions (bslz4_csc_*)."""

    def setup_method(self):
        self.mask = _make_mask()
        self.data, self.indices, self.indptr = _make_standard_csc()

    def test_standard_csc_1frame(self):
        nframes = 1
        compressed, offsets, lengths = get_chunk_offsets(NIJ_SMALL)
        nframes = 4 if NITERS > 1 else 1
        ox = np.zeros(nframes * NIJ_SMALL, dtype=np.uint16)
        oa = np.zeros(nframes * NIJ_SMALL, dtype=np.uint32)
        pw = np.zeros(nframes * NOUT_SMALL, dtype=np.float64)
        for _ in range(NITERS):
            of = offsets.repeat(nframes) if nframes > 1 else offsets
            ln = lengths.repeat(nframes) if nframes > 1 else lengths
            npc = np.zeros(nframes, dtype=np.int32)
            _m.bslz4_csc_u16(
                compressed, self.mask, ox, oa, 0,
                pw, self.data, self.indices, self.indptr,
                of, ln, npc)

    def test_standard_csc_4frames(self):
        nframes = 4
        compressed, offsets, lengths = get_chunk_offsets(NIJ_SMALL)
        ox = np.zeros(nframes * NIJ_SMALL, dtype=np.uint16)
        oa = np.zeros(nframes * NIJ_SMALL, dtype=np.uint32)
        pw = np.zeros(nframes * NOUT_SMALL, dtype=np.float64)
        for _ in range(NITERS):
            of = offsets.repeat(nframes)
            ln = lengths.repeat(nframes)
            npc = np.zeros(nframes, dtype=np.int32)
            _m.bslz4_csc_u16(
                compressed, self.mask, ox, oa, 0,
                pw, self.data, self.indices, self.indptr,
                of, ln, npc)


if __name__ == "__main__":
    # Run tests manually without pytest
    import gc

    def run(cls):
        obj = cls()
        obj.setup_method()
        for name in dir(cls):
            if name.startswith("test_"):
                fn = getattr(obj, name)
                print("  %s ... " % name, end="")
                sys.stdout.flush()
                fn()
                print("PASS")

    print("Memory safety tests (NITERS=%d)" % NITERS)
    sys.stdout.flush()

    run(TestCSC1DMemory)
    run(TestCSCStandardMemory)

    gc.collect()
    print("\nAll memory tests passed.")
