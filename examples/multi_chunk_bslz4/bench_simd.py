#!/usr/bin/env python
"""SIMD variant benchmark: standard CSC vs 1D padded + quantization + error analysis.

Measures across 6 SIMD variants, 4 CSC dtypes (f32/u8/u16/u32),
standard CSC (f32 only) and 1D padded. Reports FPS, C time, and
quantization error.  Each measurement repeated 3 times.

Usage:
    HDF5_PLUGIN_PATH=... python3 bench_simd.py
"""

from __future__ import print_function
import os, sys, time, json, copy
import numpy as np
import c2ImageD11._cImageD11 as _m
from c2ImageD11.bslz4 import chunk2sparseCSC, chunk2sparseCSC_1d
from c2ImageD11.csc_convert import (
    generate_csc, to_1d_padded, quantize_weights, save_csc_1d, load_csc_1d)
import h5py

_HOME = os.environ.get("HOME", os.path.expanduser("~"))
EXDIR = os.path.dirname(os.path.abspath(__file__))
DATAFILE = os.path.join(EXDIR, "testdata_poisson.h5")
MASKFILE = os.path.join(_HOME, "test_data", "eiger_mask.npy")
PONIFILE = os.path.join(EXDIR, "example.poni")
CSCFILE  = os.path.join(EXDIR, "csc_2500_1d.h5")
NFRAMES = 32
NOUT = 2500
BS = 4
CUT = 50
MAX_SPARSE = 50000
NREPEAT = 3

# ---------------------------------------------------------------------------
# Load mask (1=active)
# ---------------------------------------------------------------------------
mask_2d = np.load(MASKFILE).astype(np.uint8)
mask_2d = (1 - mask_2d).astype(np.uint8)
flat_mask = mask_2d.ravel()
NIJ = len(flat_mask)
nactive = flat_mask.sum()
print("Mask: %d / %d active (%.1f%%)" % (nactive, NIJ, 100.0 * nactive / NIJ))

# ---------------------------------------------------------------------------
# Load or generate 1D padded CSC + quantized copies
# ---------------------------------------------------------------------------
csc_flat, csc_first_bin, _, epp, _, _ = load_csc_1d(CSCFILE)
if csc_flat is None:
    print("Generating CSC from PONI...", end=" "); sys.stdout.flush()
    data, indices, indptr, _, _ = generate_csc(PONIFILE, NOUT)
    csc_flat, csc_first_bin, epp = to_1d_padded(data, indices, indptr,
                                                  mask_2d, verify=False)
    save_csc_1d(CSCFILE, csc_flat, csc_first_bin, NOUT,
                description="2500-bin 1D padded from example.poni")
    print("saved.")

# Also need standard CSC arrays for comparison
data_s, indices_s, indptr_s, _, _ = generate_csc(PONIFILE, NOUT)

# Quantized copies
csc_u8  = quantize_weights(csc_flat, scale_factor=255,    dtype=np.uint8,
                           mask=flat_mask, entries_per_pixel=epp)
csc_u16 = quantize_weights(csc_flat, scale_factor=32768,  dtype=np.uint16,
                           mask=flat_mask, entries_per_pixel=epp)
csc_u32 = quantize_weights(csc_flat, scale_factor=1<<31,  dtype=np.uint32,
                           mask=flat_mask, entries_per_pixel=epp)

# Also quantize standard CSC arrays for comparison
nzi = data_s > 0
# For standard CSC, each pixel's entries sum to 1.0, and indices are sequential
# Quantization for standard CSC: per-pixel weights
# Use the same scale factors
csc_u8_s   = quantize_weights(data_s.astype(np.float32), scale_factor=255,
                               dtype=np.uint8, mask=flat_mask,
                               entries_per_pixel=None)
# For standard CSC quantize we pass the full data array and mask
# But quantize_weights expects padded format. Let's handle this differently.

print("CSC: epp=%d, f32=%.1f MB, u8=%.1f MB, u16=%.1f MB, u32=%.1f MB" % (
    epp, csc_flat.nbytes/1e6, csc_u8.nbytes/1e6,
    csc_u16.nbytes/1e6, csc_u32.nbytes/1e6))

# ---------------------------------------------------------------------------
# Load test data
# ---------------------------------------------------------------------------
if not os.path.exists(DATAFILE):
    print("Generating test data..."); sys.stdout.flush()
    rng = np.random.RandomState(42)
    d3 = np.zeros((NFRAMES, 2162, 2068), dtype=np.uint16)
    active_idx = np.where(flat_mask)[0]
    npeaks = int(nactive * 0.001)
    nhot = int(NIJ * 0.0001)
    for fr in range(NFRAMES):
        f = np.zeros(NIJ, dtype=np.float64)
        f += rng.poisson(5, size=NIJ).astype(np.float64) * flat_mask
        pk = rng.choice(active_idx, size=npeaks, replace=False)
        f[pk] += rng.poisson(200, size=npeaks).astype(np.float64)
        hot = rng.choice(active_idx, size=nhot, replace=False)
        f[hot] = 65530.0
        d3[fr] = f.clip(0, 65535).astype(np.uint16).reshape(2162, 2068)
    with h5py.File(DATAFILE, "w") as hf:
        hf.create_dataset("data", data=d3, chunks=(1, 2162, 2068),
                          compression=32008, compression_opts=(0, 2))

offsets = np.full(NFRAMES, -1, dtype=np.int64)
lengths = np.full(NFRAMES, -1, dtype=np.int32)
with h5py.File(DATAFILE, "r") as hf:
    ds = hf["data"]
    def cb(si):
        lo, _, fl, sz = si
        if lo[0] < NFRAMES:
            offsets[lo[0]] = fl; lengths[lo[0]] = sz
    ds.id.chunk_iter(cb)
if (offsets < 0).any() or (lengths < 0).any():
    raise RuntimeError("Missing chunk offsets")
mmap = np.memmap(DATAFILE, dtype="B", mode="r")

# ---------------------------------------------------------------------------
# Pre-allocated buffers
# ---------------------------------------------------------------------------
outpx  = np.zeros(BS * NIJ, dtype=np.uint16)
outadr = np.zeros(BS * NIJ, dtype=np.uint32)
all_powder_f64 = np.zeros((NFRAMES, NOUT), dtype=np.float64)
all_powder_u64 = np.zeros((NFRAMES, NOUT), dtype=np.uint64)
all_vals = np.zeros((NFRAMES, MAX_SPARSE), dtype=np.uint16)
all_inds = np.zeros((NFRAMES, MAX_SPARSE), dtype=np.uint32)
all_nnz  = np.zeros(NFRAMES, dtype=np.int32)

# ---------------------------------------------------------------------------
# Warmup
# ---------------------------------------------------------------------------
print("Warming up...", end=" "); sys.stdout.flush()
for b in range(0, NFRAMES, BS):
    bn = min(BS, NFRAMES - b)
    npc = np.zeros(bn, np.int32)
    _m.bslz4_csc_u16(mmap, flat_mask, outpx, outadr, CUT,
                      all_powder_f64[b:b+bn].ravel(),
                      data_s, indices_s, indptr_s,
                      offsets[b:b+bn], lengths[b:b+bn], npc)
all_vals[:] = 0; all_inds[:] = 0
print("done.\n")

# ---------------------------------------------------------------------------
# Benchmark helper
# ---------------------------------------------------------------------------
def benchmark_csc(fn, pow_slice_f64, pow_slice_u64, name, nrepeat=NREPEAT):
    """Time fn() over NFRAMES frames, repeated nrepeat times.

    fn is a callable that processes NFRAMES frames using pre-allocated buffers.
    pow_slice_f64/pow_slice_u64 are callables returning the next powder buffer.

    Returns: (c_ms_best, copy_ms_best, fps_best, powder_results)
    """
    best = None
    powder_samples = []
    for rep in range(nrepeat):
        all_nnz[:] = 0
        t0 = time.perf_counter()
        fn()
        total = time.perf_counter() - t0
        fps = NFRAMES / total

        # Copy powder snapshot for error analysis
        powder_samples.append(all_powder_f64[:, :NOUT].copy())

        if best is None or fps > best["fps"]:
            best = {"total_ms": total * 1000, "fps": fps}
    print("  %-24s total=%5.0f ms  FPS=%6.1f  (best of %d)" % (
        name, best["total_ms"], best["fps"], nrepeat))
    return best["total_ms"], 0, best["fps"], powder_samples


# ============================================================================
# Standard CSC (f32 only for SIMD comparison)
# ============================================================================
STD_FN = _m.bslz4_csc_u16
variants = ['kcb_avx512', 'kcb_avx2', 'kcb_sse42']

results = {}
std_powders = {}

for v in variants:
    _m._rebind_bslz4_csc_u16(v)
    def make_std():
        def call():
            for b in range(0, NFRAMES, BS):
                bn = min(BS, NFRAMES - b)
                npc = np.zeros(bn, np.int32)
                STD_FN(mmap, flat_mask, outpx, outadr, CUT,
                       all_powder_f64[b:b+bn].ravel(),
                       data_s, indices_s, indptr_s,
                       offsets[b:b+bn], lengths[b:b+bn], npc)
        return call

    ms, _, fps, pow_samples = benchmark_csc(
        make_std(), lambda: all_powder_f64, lambda: None,
        "std %s f32" % v)
    results[("std", v, "f32")] = {"ms": ms, "fps": fps}
    std_powders[v] = pow_samples[0]  # reference

# ============================================================================
# 1D CSC across all variants and dtypes
# ============================================================================
CSC1D_FN_F32 = _m.bslz4_csc1d_u16
CSC1D_FN_U8  = _m.bslz4_csc1d_u16_cu8
CSC1D_FN_U16 = _m.bslz4_csc1d_u16_cu16
CSC1D_FN_U32 = _m.bslz4_csc1d_u16_cu32

quant_configs = [
    ("f32", csc_flat, None, all_powder_f64, CSC1D_FN_F32),
    ("u8",  csc_u8,  255,  all_powder_u64, CSC1D_FN_U8),
    ("u16", csc_u16, 32768, all_powder_u64, CSC1D_FN_U16),
    ("u32", csc_u32, 1<<31, all_powder_u64, CSC1D_FN_U32),
]

for v in ['kcb_avx512', 'kcb_avx2', 'kcb_sse42',
          'bs_avx512', 'bs_avx2', 'bs_sse42']:
    for qlabel, qarr, sf, pow_dest, fn_q in quant_configs:
        # Rebind the appropriate function variant
        fname = "bslz4_csc1d_u16%s%s" % (
            "_cu" + qlabel[1:] if qlabel.startswith("u") else "", "")
        rebind_name = "_rebind_bslz4_csc1d" + ("_u16" if qlabel == "f32" else "_u16_cu" + qlabel[1:])
        rebind_fn = getattr(_m, rebind_name)
        rebind_fn(v)

        def make_csc1d(fn=fn_q, sf_=sf, qlabel_=qlabel):
            def call():
                for b in range(0, NFRAMES, BS):
                    bn = min(BS, NFRAMES - b)
                    npc = np.zeros(bn, np.int32)
                    if sf_ is None:
                        pw = all_powder_f64[b:b+bn].ravel()
                    else:
                        pw = all_powder_u64[b:b+bn].ravel()
                        pw[:] = 0
                    fn(mmap, flat_mask, outpx, outadr, CUT,
                       pw, qarr, csc_first_bin, epp,
                       offsets[b:b+bn], lengths[b:b+bn], npc)
                    if sf_ is not None:
                        pw_f64 = all_powder_f64[b:b+bn].ravel()
                        pw_f64[:] = pw.astype(np.float64) * (1.0 / sf_)
            return call

        ms, _, fps, _ = benchmark_csc(
            make_csc1d(), lambda: None, lambda: None,
            "csc1d %s %s" % (v[:10], qlabel))
        results[("csc1d", v, qlabel)] = {"ms": ms, "fps": fps}

# ============================================================================
# Results table
# ============================================================================
print("\n" + "=" * 60)
print("%-10s %-6s %-4s %8s %8s" % ("variant", "fmt", "dtype", "ms", "FPS"))
print("-" * 60)
best_fps = 0; best_key = None
for key in sorted(results.keys()):
    fmt, v, q = key
    r = results[key]
    print("%-10s %-6s %-4s %8.0f %8.1f" % (v[:10], fmt, q, r["ms"], r["fps"]))
    if r["fps"] > best_fps:
        best_fps = r["fps"]
        best_key = key
print("-" * 60)
print("Best: %s FPS=%.1f" % (str(best_key), best_fps))

# ============================================================================
# Quantization error analysis
# ============================================================================
print("\n" + "=" * 60)
print("Quantization Error Analysis  (vs f32 reference, kcb_avx512)")
print("-" * 60)

ref = std_powders.get("kcb_avx512")
if ref is None:
    # Get f32 reference from csc1d
    ref = results.get(("csc1d", "kcb_avx512", "f32"), {})

# Compare csc1d f32 (reference) vs quantized
# We need powder data from the benchmark. Let's run one more time for error data.
print("  Running error analysis...", end=" "); sys.stdout.flush()

# Gather reference powder from csc1d f32 and quantized for kcb_avx512
ref_csc1d = None
quant_powders = {}

for v in ['kcb_avx512']:
    _m._rebind_bslz4_csc1d_u16(v)
    for qlabel, qarr, sf in [("f32", csc_flat, None),
                              ("u8", csc_u8, 255),
                              ("u16", csc_u16, 32768),
                              ("u32", csc_u32, 1<<31)]:
        all_powder_f64[:] = 0.0; all_powder_u64[:] = 0
        for b in range(0, NFRAMES, BS):
            bn = min(BS, NFRAMES - b)
            npc = np.zeros(bn, np.int32)
            if sf is None:
                pw = all_powder_f64[b:b+bn].ravel()
            else:
                pw = all_powder_u64[b:b+bn].ravel()
            CSC1D_FN(mmap, flat_mask, outpx, outadr, CUT,
                     pw, qarr, csc_first_bin, epp,
                     offsets[b:b+bn], lengths[b:b+bn], npc)
        if sf is None:
            ref_csc1d = all_powder_f64.copy()
        else:
            p64 = all_powder_u64.copy()
            quant_powders[qlabel] = p64
            # Print error
            ref_f = ref_csc1d.ravel()
            q_f = p64.ravel().astype(np.float64) * (1.0 / sf)
            err = np.abs(ref_f - q_f)
            nz = ref_f > 0
            rel = np.zeros_like(err)
            if nz.any():
                rel[nz] = err[nz] / ref_f[nz]
            print()
            print("  %-4s: max_abs_err=%.6g  max_rel_err=%.6g  rms_err=%.6g" % (
                qlabel, err.max(), rel.max() if len(rel) else 0,
                np.sqrt(np.mean(err**2))))

# Also run for standard CSC f32
_m._rebind_bslz4_csc_u16("kcb_avx512")
all_powder_f64[:] = 0.0
for b in range(0, NFRAMES, BS):
    bn = min(BS, NFRAMES - b)
    npc = np.zeros(bn, np.int32)
    STD_FN(mmap, flat_mask, outpx, outadr, CUT,
           all_powder_f64[b:b+bn].ravel(),
           data_s, indices_s, indptr_s,
           offsets[b:b+bn], lengths[b:b+bn], npc)
std_ref = all_powder_f64.copy()

if ref_csc1d is not None:
    err = np.abs(ref_csc1d.ravel() - std_ref.ravel())
    nz = std_ref.ravel() > 0
    rel = np.zeros_like(err)
    if nz.any():
        rel[nz] = err[nz] / std_ref.ravel()[nz]
    print("  std vs csc1d f32: max_abs_err=%.6g  max_rel_err=%.6g" % (
        err.max(), rel.max() if len(rel) else 0))

print("\nDone.")
