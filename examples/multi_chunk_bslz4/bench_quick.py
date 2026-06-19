#!/usr/bin/env python
"""Quick benchmark: both datasets, kcb/avx2/avx512, std/csc1d, f32/u16, bs 1/4/16."""

from __future__ import print_function
import os, sys, time, json
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
BATCH_SIZES = [1, 4, 16]

def get_chunk_offsets(h5path, ds_path, nframes):
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

def load_csc(nout):
    d, i, ip, _, _ = generate_csc(PONIFILE, nout)
    ma = np.load(os.path.join(_HOME, "test_data", "eiger_mask.npy"))
    ma = (1 - ma).astype(np.uint8)
    cf, fb, ep = to_1d_padded(d, i, ip, ma, verify=False)
    cu16 = quantize_weights(cf, 32768, np.uint16, mask=ma.ravel(), entries_per_pixel=ep)
    return cf, fb, ep, cu16, d, i, ip

def benchmark(h5path, ds_path, nframes, nout, label):
    print("\n=== %s (%d frames, %d bins) ===" % (label, nframes, nout))
    sys.stdout.flush()
    offs, lens = get_chunk_offsets(h5path, ds_path, nframes)
    mmap = np.memmap(h5path, dtype="B", mode="r")
    ma = np.load(os.path.join(_HOME, "test_data", "eiger_mask.npy"))
    flat = (1 - ma.ravel()).astype(np.uint8)
    NIJ = len(flat)

    cf, fb, ep, cu16, d_s, i_s, ip_s = load_csc(nout)
    max_bs = max(BATCH_SIZES)
    ox = np.zeros(max_bs * NIJ, np.uint16)
    oa = np.zeros(max_bs * NIJ, np.uint32)

    print("  warmup...", end=" "); sys.stdout.flush()
    for b in range(0, min(32, nframes), 4):
        bn = min(4, nframes - b)
        npc = np.zeros(bn, np.int32)
        _m.bslz4_csc_u16(mmap, flat, ox, oa, 50, np.zeros(bn * nout),
                          d_s, i_s, ip_s, offs[b:b+bn], lens[b:b+bn], npc)
    print("done"); sys.stdout.flush()

    rows = []
    for bs in BATCH_SIZES:
        # Standard CSC f32
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
            rows.append((label, "std_f32", bs, v, fps[0], fps[1] if len(fps) > 1 else 0))
        # CSC1D f32 and u16
        for qlabel, fn, reb, qarr in [
            ("f32", _m.bslz4_csc1d_u16, _m._rebind_bslz4_csc1d_u16, (cf, fb, ep)),
            ("u16", _m.bslz4_csc1d_u16_cu16, _m._rebind_bslz4_csc1d_u16_cu16, (cu16, fb, ep)),
        ]:
            for v in ["kcb_avx512", "kcb_avx2"]:
                reb(v)
                sf = None if qlabel == "f32" else 32768
                fps = []
                for _ in range(NREPEAT):
                    t0 = time.perf_counter()
                    for b in range(0, nframes, bs):
                        bn = min(bs, nframes - b)
                        npc = np.zeros(bn, np.int32)
                        pw = np.zeros(bn * nout, dtype=np.float64 if sf is None else np.uint64)
                        fn(mmap, flat, ox, oa, 50, pw, qarr[0], qarr[1], qarr[2],
                           offs[b:b+bn], lens[b:b+bn], npc)
                    fps.append(nframes / (time.perf_counter() - t0))
                fps.sort(reverse=True)
                rows.append((label, "csc1d_" + qlabel, bs, v, fps[0], fps[1] if len(fps) > 1 else 0))
    return rows

all_rows = []
all_rows.extend(benchmark(POISSON_H5, "data", 32, 2500, "poisson"))
all_rows.extend(benchmark(EIGER_H5, EIGER_DS, 100, 1500, "eiger"))

print("\n\n%-7s %-10s %2s %-12s %8s %8s %8s" % ("ds", "fmt", "bs", "variant", "best", "2nd", "ms/f"))
print("-" * 70)
all_rows.sort(key=lambda r: -r[4])
for r in all_rows:
    ms = 1000 / r[4] if r[4] > 0 else 0
    print("%-7s %-10s %2d %-12s %8.1f %8.1f %8.2f" % (r[0], r[1], r[2], r[3][:12], r[4], r[5], ms))
print("Done.")
