#!/usr/bin/env python
"""SIMD variant benchmark with synthetic Poisson test data (32 frames, 94% active).

Measures CSC and basic decompress across all 6 SIMD variants.
Uses Python time.perf_counter() for wall-clock timing.

Usage:
    python3 bench_simd.py
    HDF5_PLUGIN_PATH=... python3 bench_simd.py
"""

from __future__ import print_function
import os, sys, time, json
import numpy as np
import c2ImageD11._cImageD11 as _m
from c2ImageD11.bslz4 import chunk2sparseCSC
import h5py

_HOME = os.environ.get("HOME", os.path.expanduser("~"))
DATAFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "testdata_poisson.h5")
MASKFILE = os.path.join(_HOME, "test_data", "eiger_mask.npy")
NFRAMES = 32
NOUT = 1500
BS = 4
CUT = 50
MAX_SPARSE = 50000  # plenty for cut=50 (only ~4650 pixels above cut per frame)

# ---------------------------------------------------------------------------
# Load mask (file: 1=masked, 0=active; C code: 1=active)
# ---------------------------------------------------------------------------
mask_2d = np.load(MASKFILE).astype(np.uint8)
flat_mask = (1 - mask_2d.ravel()).astype(np.uint8)
NIJ = len(flat_mask)
nactive = flat_mask.sum()
print("Mask: %d / %d active (%.1f%%)" % (nactive, NIJ, 100.0 * nactive / NIJ))

# ---------------------------------------------------------------------------
# Get chunk offsets from HDF5
# ---------------------------------------------------------------------------
offsets = np.full(NFRAMES, -1, dtype=np.int64)
lengths = np.full(NFRAMES, -1, dtype=np.int32)

with h5py.File(DATAFILE, "r") as hf:
    ds = hf["data"]
    print("Dataset: shape=%s dtype=%s chunks=%s" % (
        ds.shape, ds.dtype, ds.chunks))
    def cb(si):
        lo, _, floc, sz = si
        if lo[0] < NFRAMES:
            offsets[lo[0]] = floc; lengths[lo[0]] = sz
    ds.id.chunk_iter(cb)
    raw = ds[:]

if (offsets < 0).any() or (lengths < 0).any():
    raise RuntimeError("Missing chunk offsets")

mmap = np.memmap(DATAFILE, dtype="B", mode="r")

# ---------------------------------------------------------------------------
# Build CSC matrix covering ALL NIJ pixels.
# Active pixels contribute to 6 random bins; inactive pixels contribute 0.
# ---------------------------------------------------------------------------
np.random.seed(123)
entries_per_pixel = 6
nnz = nactive * entries_per_pixel

csc_data = np.ones(nnz, dtype=np.float32)
csc_indices = np.random.randint(0, NOUT, size=nnz, dtype=np.uint32)

csc_indptr = np.zeros(NIJ + 1, dtype=np.uint32)
csc_indptr[1:] = np.cumsum(flat_mask.astype(np.uint32) * entries_per_pixel)

class CSCObj:
    pass
cobj = CSCObj()
cobj.data = csc_data; cobj.indices = csc_indices
cobj.indptr = csc_indptr; cobj.shape = (NOUT,); cobj.bins = NOUT
dc = chunk2sparseCSC(mask_2d, cobj, dtype=np.uint16)

# ---------------------------------------------------------------------------
# Pre-allocate buffers
# ---------------------------------------------------------------------------
outpx  = np.zeros(BS * NIJ, dtype=np.uint16)
outadr = np.zeros(BS * NIJ, dtype=np.uint32)
all_powder = np.zeros((NFRAMES, NOUT), dtype=np.float64)
all_vals = np.zeros((NFRAMES, MAX_SPARSE), dtype=np.uint16)
all_inds = np.zeros((NFRAMES, MAX_SPARSE), dtype=np.uint32)
all_nnz = np.zeros(NFRAMES, dtype=np.int32)

# ---------------------------------------------------------------------------
# Warmup
# ---------------------------------------------------------------------------
print("Warming up...", end=" "); sys.stdout.flush()
for b in range(0, NFRAMES, BS):
    bn = min(BS, NFRAMES - b)
    npc = np.zeros(bn, np.int32)
    dc.fun(mmap, flat_mask, outpx, outadr, CUT,
           all_powder[b:b+bn].ravel(), csc_data, csc_indices, csc_indptr,
           offsets[b:b+bn], lengths[b:b+bn], npc)
all_vals[:] = 0; all_inds[:] = 0
print("done.\n")

# ---------------------------------------------------------------------------
# SIMD variants
# ---------------------------------------------------------------------------
variants = ['kcb_avx512', 'kcb_avx2', 'kcb_sse42',
            'bs_avx512', 'bs_avx2', 'bs_sse42']

print("%-16s %10s %10s %10s %10s %10s" % (
    "variant", "csc_ms", "basic_ms", "csc_add", "copy_ms", "FPS"))
print("-" * 72)

for v in variants:
    _m._rebind_bslz4_csc_u16(v)
    _m._rebind_bslz4_u16(v)

    # Reset storage
    all_powder[:] = 0.0; all_nnz[:] = 0

    # ---- CSC timed run ----
    copy_total = 0.0
    t0 = time.perf_counter()
    for batch_start in range(0, NFRAMES, BS):
        bn = min(BS, NFRAMES - batch_start)
        npc = np.zeros(bn, np.int32)
        dc.fun(mmap, flat_mask, outpx, outadr, CUT,
               all_powder[batch_start:batch_start+bn].ravel(),
               csc_data, csc_indices, csc_indptr,
               offsets[batch_start:batch_start+bn],
               lengths[batch_start:batch_start+bn], npc)
        t1 = time.perf_counter()
        for f in range(bn):
            frame = batch_start + f
            npx = int(npc[f])
            all_nnz[frame] = npx
            all_vals[frame, :npx] = outpx[f * NIJ : f * NIJ + npx]
            all_inds[frame, :npx] = outadr[f * NIJ : f * NIJ + npx]
        copy_total += time.perf_counter() - t1
    t1 = time.perf_counter()
    csc_total = t1 - t0

    # ---- Basic (no CSC) timed run ----
    t0 = time.perf_counter()
    for batch_start in range(0, NFRAMES, BS):
        bn = min(BS, NFRAMES - batch_start)
        npc = np.zeros(bn, np.int32)
        _m.bslz4_u16(mmap, flat_mask, outpx, outadr, CUT,
                      offsets[batch_start:batch_start+bn],
                      lengths[batch_start:batch_start+bn], npc)
    t1 = time.perf_counter()
    basic_total = t1 - t0

    csc_ms = csc_total * 1000
    basic_ms = basic_total * 1000
    overhead = csc_ms - basic_ms
    fps = NFRAMES / csc_total

    print("%-16s %10.2f %10.2f %10.2f %10.2f %10.1f" % (
        v, csc_ms, basic_ms, overhead, copy_total * 1000, fps))

_m._rebind_bslz4_csc_u16(None)

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("Verification  (using kcb variant data from last warmup run)")
frame0 = raw[0]
total_counts = frame0.sum(dtype=np.float64)
powder_sum = all_powder[0].sum()
sparse_sum = all_vals[0, :all_nnz[0]].sum(dtype=np.float64)
above_cut = frame0[frame0 > CUT].sum(dtype=np.float64)

print("  Frame 0:")
print("    Total image counts:   %.0f" % total_counts)
print("    Powder histogram sum: %.0f" % powder_sum)
print("    Sparse output sum:    %.0f  (cut=%d)" % (sparse_sum, CUT))
print("    Image > cut sum:      %.0f" % above_cut)
print()
for strict in [True, False]:
    ok_pow = abs(powder_sum - total_counts * entries_per_pixel) / max(total_counts, 1) < 0.01
    ok_spr = abs(sparse_sum - above_cut) / max(above_cut, 1) < 0.01
    label = "STRICT" if strict else "relaxed"
    if strict:
        print("    sum(powder) == sum(image)*%d:            %s" % (
            entries_per_pixel, "PASS" if ok_pow else "FAIL"))
        print("    sum(sparse) == sum(image > %d):           %s" % (CUT, "PASS" if ok_spr else "FAIL"))
    else:
        chk_pow = powder_sum / entries_per_pixel
        print("    sum(powder)/%d == sum(image):              %s (%.0f vs %.0f)" % (
            entries_per_pixel,
            "PASS" if abs(chk_pow - total_counts) / max(total_counts, 1) < 0.01 else "FAIL",
            chk_pow, total_counts))

print()
print("  All frames:")
failures = 0
for fr in range(NFRAMES):
    tc = raw[fr].sum()
    ps = all_powder[fr].sum()
    ss = all_vals[fr, :all_nnz[fr]].sum()
    ac = raw[fr][raw[fr] > CUT].sum()
    if abs(ps - tc * entries_per_pixel) / max(tc, 1) > 0.01:
        failures += 1
    if abs(ss - ac) / max(ac, 1) > 0.01:
        failures += 1
if failures:
    print("    %d failures (first at frame %d)" % (failures, next(
        fr for fr in range(NFRAMES) if
        abs(all_powder[fr].sum() - raw[fr].sum() * entries_per_pixel) / max(raw[fr].sum(),1) > 0.01
    )))
else:
    print("    All %d frames PASS" % NFRAMES)
print("    NNZ/frame: %.0f (min %.0f, max %.0f)" % (
    all_nnz.sum()/NFRAMES, all_nnz.min(), all_nnz.max()))
