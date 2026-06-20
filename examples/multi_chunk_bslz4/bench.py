#!/usr/bin/env python
"""Benchmark all retained bslz4/bszstd variants on both test images.

Parameters varied:
  engine:       LZ4 (bslz4) | ZSTD (bszstd)
  function:     basic (decompress to sparse) | csc (std CSC) | csc1d (1D-padded CSC)
  batch_size:   1 | 16 frames (loop-interchanged)
  dataset:      eiger_lz4 | eiger_zstd | poisson
  ISA:          auto-resolved: avx512 / avx2 / sse42 (not cycled here)
  pixel_type:   u16 only (all test data is uint16)
  backend:      KCB only (bitshuffle-core, integer CSC removed)

Usage:
  python3 examples/multi_chunk_bslz4/bench.py
"""

from __future__ import print_function
import os, sys, time
import numpy as np
import c2ImageD11._cImageD11 as _m
from c2ImageD11.csc_convert import generate_csc, to_1d_padded
import h5py

HOME = os.environ.get("HOME", "/home/worker")
EXDIR = os.path.dirname(os.path.abspath(__file__))
NREPEAT = 1

DATASETS = [
    # (label, h5path, ds_path, nframes, engine)  -- engine='lz4'|'zstd'
    ("eiger_lz4",  "/home/worker/test_data/eiger_lz4_u16.h5",
     "entry_0000/measurement/data", 1000, "lz4"),
    ("eiger_zstd", "/home/worker/test_data/eiger_zstd_u16.h5",
     "entry_0000/measurement/data", 1000, "zstd"),
    ("poisson",    os.path.join(EXDIR, "testdata_poisson.h5"),
     "data", 32, "lz4"),
]

BATCH_SIZES = [1, 16]
PONIFILE = os.path.join(EXDIR, "example.poni")
MASKFILE = os.path.join(HOME, "test_data", "eiger_mask.npy")
NOUT = 2500


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
        raise RuntimeError("Missing chunk offsets for %s" % h5path)
    return offs, lens


def bench_one(ds_label, h5path, ds_path, nframes, engine):
    sys.stdout.flush()
    offs, lens = get_offsets(h5path, ds_path, nframes)
    mm = np.memmap(h5path, dtype="B", mode="r")

    mask = np.load(MASKFILE)
    mask = (1 - mask.ravel()).astype(np.uint8)
    NIJ = mask.size

    # Generate CSC data from PONI
    csc_data, csc_idx, csc_ptr, _, _ = generate_csc(PONIFILE, NOUT)
    csc_flat, csc_first, epp = to_1d_padded(csc_data, csc_idx, csc_ptr, mask)

    max_batch = max(BATCH_SIZES)
    ox = np.zeros(max_batch * NIJ, dtype=np.uint16)
    oa = np.zeros(max_batch * NIJ, dtype=np.uint32)

    print("  warmup ...", end=" "); sys.stdout.flush()
    enc = 3 if engine == "zstd" else 2
    _m.bs_u16(mm, mask, ox[:NIJ], oa[:NIJ], 0, enc,
              offs[:1], lens[:1], np.zeros(1, np.int32))
    print("done"); sys.stdout.flush()

    # Results table header
    print("  %-10s %-5s %-6s %2s  %8s  %7s" %
          ("dataset", "type", "engine", "bs", "fps", "ms/frame"))
    print("  " + "-" * 48)

    rows = []
    VARIANTS = [
        ("basic", "bslz4", _m.bs_u16,      None, None, 2),
        ("basic", "bszstd", _m.bs_u16,     None, None, 3),
        ("csc",   "bslz4", None, _m.bs_csc_u16,   None, 2),
        ("csc",   "bszstd", None, _m.bs_csc_u16,  None, 3),
        ("csc1d", "bslz4", None, None, _m.bs_csc1d_u16, 2),
        ("csc1d", "bszstd", None, None, _m.bs_csc1d_u16, 3),
    ]
    for fun_type, eng_name, fn_basic, fn_csc, fn_csc1d, enc in VARIANTS:
        if (engine == "lz4" and eng_name != "bslz4") or (engine == "zstd" and eng_name != "bszstd"):
            continue
        for bs in BATCH_SIZES:
            actual = min(bs, nframes)
            npc = np.zeros(actual, dtype=np.int32)

            nerr = 0
            t0 = time.perf_counter()
            for _ in range(NREPEAT):
                for b in range(0, nframes, actual):
                    bn = min(actual, nframes - b)
                    ob = bn * NIJ
                    if fn_basic is not None:
                        npx = fn_basic(mm, mask, ox[:ob], oa[:ob], 0, enc,
                                       offs[b:b+bn], lens[b:b+bn], npc[:bn])
                    elif fn_csc is not None:
                        pw = np.zeros(bn * NOUT, dtype=np.float64)
                        npx = fn_csc(mm, mask, ox[:ob], oa[:ob], 0, enc,
                                     pw, csc_data, csc_idx, csc_ptr,
                                     offs[b:b+bn], lens[b:b+bn], npc[:bn])
                    else:
                        pw = np.zeros(bn * NOUT, dtype=np.float64)
                        npx = fn_csc1d(mm, mask, ox[:ob], oa[:ob], 0, enc,
                                       pw, csc_flat, csc_first, epp,
                                       offs[b:b+bn], lens[b:b+bn], npc[:bn])
                    if npx < 0:
                        nerr += 1

            elapsed = time.perf_counter() - t0
            fps = nframes * NREPEAT / elapsed
            rows.append((ds_label, fun_type, eng_name, bs, fps, nerr))
            warn = "  ERR=%d" % nerr if nerr else ""
            print("  %-10s %-5s %-6s %2d  %8.0f  %7.2f%s" %
                  (ds_label, fun_type, eng_name, bs, fps, 1000.0 / fps, warn))
            sys.stdout.flush()

    return rows


def main():
    print("=" * 72)
    print("  c2ImageD11 benchmark: retained variants")
    print("  Parameters:")
    print("    engine:    LZ4 | ZSTD")
    print("    function:  basic (decompress) | csc (std CSC) | csc1d (1D-padded CSC)")
    print("    batch:     1 | 16 frames")
    print("    dataset:   eiger_lz4 (LZ4) | eiger_zstd (ZSTD) | poisson (LZ4)")
    print("    pixel:     u16 only")
    print("    backend:   KCB only")
    print("    ISA:       auto-resolved (avx512/avx2/sse42)")
    print("    note:      each dataset uses its native engine only (no cross-engine tests)")
    print("=" * 72)
    print()

    all_rows = []
    for label, h5path, ds_path, nframes, engine in DATASETS:
        print("\n--- %s (%s, %d frames, %s) ---" %
              (label, os.path.basename(h5path), nframes, engine))
        sys.stdout.flush()
        rows = bench_one(label, h5path, ds_path, nframes, engine)
        all_rows.extend(rows)

    print("\n" + "=" * 72)
    print("  Summary")
    print("=" * 72)
    print("  %-10s %-5s %-6s %2s  %8s" %
          ("dataset", "type", "engine", "bs", "fps"))
    print("  " + "-" * 38)
    for row in all_rows:
        print("  %-10s %-5s %-6s %2d  %8.0f" % row)
    print("\nDone.")


if __name__ == "__main__":
    main()
