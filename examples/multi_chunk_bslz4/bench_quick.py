#!/usr/bin/env python
"""Benchmark: dataset x SIMD x quantization x batch_size x [csc_fmt + stride].

Prints each line as measured (no sorting at end).  Tests:
  - std_f32 (no stride)
  - csc1d_f32 with stride = auto(0), 64, 128, 256
  - csc1d_u8/u16/u32 with stride = 0 (auto)
"""

from __future__ import print_function
import os, sys, time
import numpy as np
import c2ImageD11._cImageD11 as _m
from c2ImageD11.csc_convert import generate_csc, to_1d_padded, quantize_weights
import h5py

_HOME = os.environ.get("HOME", "/home/worker")
EXDIR = os.path.dirname(os.path.abspath(__file__))
PONIFILE = os.path.join(EXDIR, "example.poni")
POISSON_H5 = os.path.join(EXDIR, "testdata_poisson.h5")
EIGER_H5 = os.path.join(_HOME, "test_data", "eiger_0000.h5")
EIGER_DS = "entry_0000/ESRF-ID11/eiger/data"
NREPEAT = 3
BATCH_SIZES = [1, 2, 4, 8, 16, 32]
STRIDES = [0, 64, 128, 256]

def get_offsets(h5path, ds_path, nframes):
    offs = np.full(nframes, -1, dtype=np.int64)
    lens = np.full(nframes, -1, dtype=np.int32)
    with h5py.File(h5path, "r") as hf:
        ds = hf[ds_path]
        def cb(si):
            lo, _, fl, sz = si
            if lo[0] < nframes:
                offs[lo[0]] = fl
                lens[lo[0]] = sz
        ds.id.chunk_iter(cb)
    if (offs < 0).any() or (lens < 0).any():
        raise RuntimeError("Missing chunk offsets")
    return offs, lens

def q(cf, flat, epp, sf, dt):
    return quantize_weights(cf, sf, dt, mask=flat, entries_per_pixel=epp)

def load_csc(nout):
    d, i, ip, _, _ = generate_csc(PONIFILE, nout)
    ma = np.load(os.path.join(_HOME, "test_data", "eiger_mask.npy"))
    ma = (1 - ma).astype(np.uint8); flat_m = ma.ravel()
    cf, fb, ep = to_1d_padded(d, i, ip, ma)
    return (cf, fb, ep, q(cf, flat_m, ep, 255, np.uint8),
            q(cf, flat_m, ep, 32768, np.uint16),
            q(cf, flat_m, ep, 1<<31, np.uint32), d, i, ip)

def run_one(h5path, ds_path, nframes, nout, label):
    print("\n====== %s (%d frames, %d bins) ======" % (label, nframes, nout))
    sys.stdout.flush()
    offs, lens = get_offsets(h5path, ds_path, nframes)
    mmap = np.memmap(h5path, dtype="B", mode="r")
    ma = np.load(os.path.join(_HOME, "test_data", "eiger_mask.npy"))
    flat = (1 - ma.ravel()).astype(np.uint8); NIJ = len(flat)
    cf, fb, ep, cu8, cu16, cu32, d_s, i_s, ip_s = load_csc(nout)
    max_bs = max(BATCH_SIZES)
    ox = np.zeros(max_bs * NIJ, np.uint16)
    oa = np.zeros(max_bs * NIJ, np.uint32)

    print("  warmup...", end=" "); sys.stdout.flush()
    for b in range(0, min(32, nframes), 4):
        bn = min(4, nframes - b)
        npc = np.zeros(bn, np.int32)
        _m.bslz4_csc_u16(mmap, flat, ox, oa, 50, np.zeros(bn * nout),
                          d_s, i_s, ip_s, offs[b:b+bn], lens[b:b+bn], npc)
    print("done\n"); sys.stdout.flush()

    print("%-7s %-12s %-4s %2s %-12s %6s %8s %8s" % (
        "ds", "fmt", "dtype", "bs", "variant", "stride", "best", "2nd"))
    print("-" * 75)

    for bs in BATCH_SIZES:
        # ---- Standard CSC f32 (no stride) ----
        for v in ["kcb_avx512", "kcb_avx2"]:
            _m._rebind_bslz4_csc_u16(v)
            fps = []
            for _ in range(NREPEAT):
                t0 = time.perf_counter()
                for b in range(0, nframes, bs):
                    bn = min(bs, nframes - b)
                    npc = np.zeros(bn, np.int32)
                    _m.bslz4_csc_u16(mmap, flat, ox, oa, 50, np.zeros(bn * nout),
                                      d_s, i_s, ip_s, offs[b:b+bn], lens[b:b+bn], npc)
                fps.append(nframes / (time.perf_counter() - t0))
            fps.sort(reverse=True)
            s = fps[1] if len(fps) > 1 else 0
            print("%-7s %-12s %-4s %2d %-12s %6s %8.1f %8.1f" % (
                label, "std_f32", "f32", bs, v[:12], "-", fps[0], s))
            sys.stdout.flush()

        # ---- CSC1D f32 with stride sweep ----
        for stride in STRIDES:
            _m._rebind_bslz4_csc1d_u16(v)
            for v in ["kcb_avx512", "kcb_avx2"]:
                _m._rebind_bslz4_csc1d_u16(v)
                fps = []
                for _ in range(NREPEAT):
                    t0 = time.perf_counter()
                    for b in range(0, nframes, bs):
                        bn = min(bs, nframes - b)
                        npc = np.zeros(bn, np.int32)
                        _m.bslz4_csc1d_u16(mmap, flat, ox, oa, 50,
                            np.zeros(bn * nout), cf, fb, ep, stride,
                            offs[b:b+bn], lens[b:b+bn], npc)
                    fps.append(nframes / (time.perf_counter() - t0))
                fps.sort(reverse=True)
                s = fps[1] if len(fps) > 1 else 0
                lbl = "auto" if stride == 0 else str(stride)
                print("%-7s %-12s %-4s %2d %-12s %6s %8.1f %8.1f" % (
                    label, "csc1d_f32", "f32", bs, v[:12], lbl, fps[0], s))
                sys.stdout.flush()

        # ---- CSC1D quantized (stride=0 auto) ----
        for qlabel, fn, reb, qarr, sf in [
            ("u8", _m.bslz4_csc1d_u16_cu8, _m._rebind_bslz4_csc1d_u16_cu8, cu8, 255),
            ("u16", _m.bslz4_csc1d_u16_cu16, _m._rebind_bslz4_csc1d_u16_cu16, cu16, 32768),
            ("u32", _m.bslz4_csc1d_u16_cu32, _m._rebind_bslz4_csc1d_u16_cu32, cu32, 1<<31),
        ]:
            for v in ["kcb_avx512", "kcb_avx2"]:
                reb(v)
                fps = []
                for _ in range(NREPEAT):
                    t0 = time.perf_counter()
                    for b in range(0, nframes, bs):
                        bn = min(bs, nframes - b)
                        npc = np.zeros(bn, np.int32)
                        pw = np.zeros(bn * nout, dtype=np.float64 if sf is None else np.uint64)
                        fn(mmap, flat, ox, oa, 50, pw, qarr, fb, ep, 0,
                           offs[b:b+bn], lens[b:b+bn], npc)
                    fps.append(nframes / (time.perf_counter() - t0))
                fps.sort(reverse=True)
                s = fps[1] if len(fps) > 1 else 0
                print("%-7s %-12s %-4s %2d %-12s %6s %8.1f %8.1f" % (
                    label, "csc1d_" + qlabel, qlabel, bs, v[:12], "auto", fps[0], s))
                sys.stdout.flush()

run_one(POISSON_H5, "data", 32, 2500, "poisson")
run_one(EIGER_H5, EIGER_DS, 100, 1500, "eiger")
print("\nDone.")
