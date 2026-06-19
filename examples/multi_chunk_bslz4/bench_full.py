#!/usr/bin/env python
"""Comprehensive benchmark: test data × SIMD × quantization × batch size.

Runs 3 repeats per combination, reports best and 2nd-best FPS.
"""

from __future__ import print_function
import os, sys, time, json, itertools
import numpy as np
import c2ImageD11._cImageD11 as _m
from c2ImageD11.bslz4 import chunk2sparseCSC
from c2ImageD11.csc_convert import (
    generate_csc, to_1d_padded, quantize_weights, save_csc_1d, load_csc_1d)
import h5py

_HOME = os.environ.get("HOME", os.path.expanduser("~"))
EXDIR = os.path.dirname(os.path.abspath(__file__))
PONIFILE = os.path.join(EXDIR, "example.poni")
CSCFILE  = os.path.join(EXDIR, "csc_2500_1d.h5")

# ----- Datasets ------
datasets = {
    "poisson": {
        "h5": os.path.join(EXDIR, "testdata_poisson.h5"),
        "ds": "data",
        "nframes": 32,
        "nout": 2500,
    },
    "eiger": {
        "h5": os.path.join(_HOME, "test_data", "eiger_0000.h5"),
        "ds": "entry_0000/ESRF-ID11/eiger/data",
        "nframes": 100,
        "nout": 1500,
    },
}
NREPEAT = 3
BATCH_SIZES = [1, 2, 4, 8, 16]

SIMD_VARIANTS = ['kcb_avx512', 'kcb_avx2', 'kcb_sse42',
                 'bs_avx512', 'bs_avx2', 'bs_sse42']

# --------------------------------------------------------------------
# Build / load 1D padded CSC for each nout
# --------------------------------------------------------------------
def get_or_create_csc(nout):
    """Return (csc_flat, first_bin, entries_per_pixel, nout)."""
    cf, fb, nout_r, epp, _, _ = load_csc_1d(CSCFILE)
    if cf is not None and nout_r == nout:
        return cf, fb, epp, nout
    # Generate from PONI
    data, indices, indptr, mask, _ = generate_csc(PONIFILE, nout)
    mask_py = np.load(os.path.join(_HOME, "test_data", "eiger_mask.npy"))
    mask_py = (1 - mask_py).astype(np.uint8)
    cf, fb, epp = to_1d_padded(data, indices, indptr, mask_py)
    save_csc_1d(CSCFILE, cf, fb, nout, description="1D padded")
    return cf, fb, epp, nout

# Also build standard CSC (f32 only) for each nout
def get_standard_csc(nout):
    """Return (data, indices, indptr)."""
    return generate_csc(PONIFILE, nout)[:4]  # data, indices, indptr, mask

# ----- Load data -----
def load_data(dsname):
    info = datasets[dsname]
    N = info["nframes"]
    offs = np.full(N, -1, dtype=np.int64)
    lens = np.full(N, -1, dtype=np.int32)
    with h5py.File(info["h5"], "r") as hf:
        ds = hf[info["ds"]]
        def cb(si):
            lo,_,fl,sz=si
            if lo[0]<N: offs[lo[0]]=fl;lens[lo[0]]=sz
        ds.id.chunk_iter(cb)
    if (offs < 0).any() or (lens < 0).any():
        raise RuntimeError("Missing chunk offsets in %s" % info["h5"])
    # Also read raw data for reference
    mmap = np.memmap(info["h5"], dtype="B", mode="r")
    # Load mask (same for both datasets, from eiger_mask)
    mask_2d = np.load(os.path.join(_HOME, "test_data", "eiger_mask.npy")).astype(np.uint8)
    flat_mask = (1 - mask_2d.ravel()).astype(np.uint8)
    return mmap, offs, lens, flat_mask, len(flat_mask), info["nout"]

# ----- Warmup -----
def warmup(mmap, flat, N, nout, bs, offs, lens):
    ox = np.zeros(bs * len(flat), dtype=np.uint16)
    oa = np.zeros_like(ox, dtype=np.uint32)
    pw = np.zeros(bs * nout, dtype=np.float64)
    for b in range(0, min(bs, N), bs):
        bn = min(bs, N - b)
        npc = np.zeros(bn, np.int32)
        _m.bslz4_csc_u16(mmap, flat, ox, oa, 50,
                          pw[:bn*nout],
                          np.ones(100, np.float32),
                          np.zeros(100, np.uint32),
                          np.arange(len(flat)+1, dtype=np.uint32),
                          offs[b:b+bn], lens[b:b+bn], npc)

# ----- Benchmark a single combination -----
def time_one(fn, mmap, flat, N, nout, bs, offs, lens, ox, oa,
             csc_format, csc_data, extra_args, nrepeat=NREPEAT):
    """Run 3 repeats, return (best_ms, best_fps, second_fps, fps_list)."""
    all_nnz = np.zeros(N, np.int32)
    fps_list = []
    for rep in range(nrepeat):
        t0 = time.perf_counter()
        for b in range(0, N, bs):
            bn = min(bs, N - b)
            npc = np.zeros(bn, np.int32)
            pw = np.zeros(bn * nout, dtype=np.float64 if csc_format == 'std' or (
                csc_format == 'csc1d' and extra_args[-1] is None) else np.uint64)
            if csc_format == 'std':
                fn(mmap, flat, ox, oa, 50, pw,
                   csc_data[0], csc_data[1], csc_data[2],
                   offs[b:b+bn], lens[b:b+bn], npc)
            else:
                csc_arr, first_bin, epp, sf = extra_args
                if sf is None:
                    fn(mmap, flat, ox, oa, 50, pw,
                       csc_arr, first_bin, epp,
                       offs[b:b+bn], lens[b:b+bn], npc)
                else:
                    pw_u64 = pw.view(np.uint64)
                    fn(mmap, flat, ox, oa, 50, pw_u64,
                       csc_arr, first_bin, epp,
                       offs[b:b+bn], lens[b:b+bn], npc)
        total = time.perf_counter() - t0
        fps_list.append(N / total)
    fps_list.sort(reverse=True)
    return fps_list[0], fps_list[1] if len(fps_list) > 1 else 0, fps_list

# ====================================================================
# Main
# ====================================================================
print("Loading CSC matrices...", end=" "); sys.stdout.flush()
# For each dataset, we need CSC with appropriate nout
csc_cache = {}  # nout -> (csc_flat, first_bin, epp)
std_cache = {}  # nout -> (data, indices, indptr)
for dsname in datasets:
    nout = datasets[dsname]["nout"]
    csc_f, fb, epp, _ = get_or_create_csc(nout)
    csc_cache[nout] = (csc_f, fb, epp)
    std_cache[nout] = get_standard_csc(nout)
print("done.")
sys.stdout.flush()

results = []

for dsname in ['poisson', 'eiger']:
    print("\n# ===== Dataset: %s =====\n" % dsname.upper())
    sys.stdout.flush()
    mmap, offs, lens, flat, NIJ, nout = load_data(dsname)
    N = datasets[dsname]["nframes"]
    max_bs = max(BATCH_SIZES)
    nout = datasets[dsname]["nout"]

    # Pre-allocate reused buffers
    ox = np.zeros(max_bs * NIJ, dtype=np.uint16)
    oa = np.zeros(max_bs * NIJ, dtype=np.uint32)

    # Warmup
    print("  Warming up...", end=" "); sys.stdout.flush()
    warmup(mmap, flat, N, nout, max_bs, offs, lens)
    print("done."); sys.stdout.flush()

    # Get CSC arrays
    csc_f, fb, epp = csc_cache[nout]
    csc_u8  = quantize_weights(csc_f, 255,   np.uint8,  mask=flat, entries_per_pixel=epp)
    csc_u16 = quantize_weights(csc_f, 32768, np.uint16, mask=flat, entries_per_pixel=epp)
    csc_u32 = quantize_weights(csc_f, 1<<31, np.uint32, mask=flat, entries_per_pixel=epp)
    std_data, std_indices, std_indptr = std_cache[nout]

    for bs in BATCH_SIZES:
        # ----- Standard CSC (f32 only) -----
        for v in ['kcb_avx512', 'kcb_avx2', 'kcb_sse42']:
            _m._rebind_bslz4_csc_u16(v)
            best, second, all_fps = time_one(
                _m.bslz4_csc_u16, mmap, flat, N, nout, bs, offs, lens,
                ox, oa, 'std', (std_data, std_indices, std_indptr), None)
            results.append((dsname, 'std', v, 'f32', bs, best, second, all_fps))

        # ----- 1D CSC (f32 + u8 + u16 + u32) -----
        for qlabel, qarr, sf in [
            ('f32', csc_f, None),
            ('u8',  csc_u8, 255),
            ('u16', csc_u16, 32768),
            ('u32', csc_u32, 1<<31),
        ]:
            for v in SIMD_VARIANTS:
                fn_name = 'bslz4_csc1d_u16'
                reb_name = '_rebind_bslz4_csc1d_u16'
                if qlabel != 'f32':
                    fn_name += '_cu' + qlabel[1:]
                    reb_name += '_cu' + qlabel[1:]
                getattr(_m, reb_name)(v)
                fn = getattr(_m, fn_name)
                best, second, all_fps = time_one(
                    fn, mmap, flat, N, nout, bs, offs, lens,
                    ox, oa, 'csc1d', None,
                    (qarr, fb, epp, sf))
                results.append((dsname, 'csc1d', v, qlabel, bs, best, second, all_fps))

# ====================================================================
# Print results
# ====================================================================
print("\n\n" + "=" * 110)
print("%-8s %-7s %-12s %-4s %2s %10s %10s %10s" % (
    "dataset", "format", "variant", "dtype", "bs", "best_FPS",
    "2nd_FPS", "ms/frame"))
print("-" * 110)

# Group by dataset, sort by FPS descending
ds_order = ['poisson', 'eiger']
for dsname in ds_order:
    print("\n--- %s ---" % dsname.upper())
    ds_rows = [r for r in results if r[0] == dsname]
    ds_rows.sort(key=lambda r: -r[5])  # sort by best FPS descending
    for row in ds_rows:
        _, fmt, v, qlabel, bs, best, second, fps_list = row
        ms = (1.0 / best) * 1000
        print("%-8s %-7s %-12s %-4s %2d %10.1f %10.1f %10.2f" % (
            dsname, fmt, v[:12], qlabel, bs, best, second, ms))
print("=" * 110)
print("\nDone.")
