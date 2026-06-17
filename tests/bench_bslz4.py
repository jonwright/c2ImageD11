"""Benchmark all bslz4/bszstd_u16 variants on real Eiger data.

Forces each of 12 variants (2 engines × 2 backends × 3 ISAs) via
_rebind API and measures wall-clock throughput. 3 repeats each.

Usage: python3 tests/bench_bslz4.py
Env:   BSLZ4_BENCH_FILE=/path/to/file.h5  (default: /home/worker/test_data/eiger_0000.h5)
"""

import os
import timeit
import numpy as np
import c2ImageD11._cImageD11 as _m

H5FILE = os.environ.get("BSLZ4_BENCH_FILE", "/home/worker/test_data/eiger_0000.h5")
DSPATH = "/entry_0000/measurement/data"
NFRAMES = 100
NREPEATS = 3
CUT = 0

VARIANTS = [
    # LZ4 engine, KCB backend
    ("kcb_avx512", "bslz4"),
    ("kcb_avx2",   "bslz4"),
    ("kcb_sse42",  "bslz4"),
    # LZ4 engine, bitshuffle-core backend
    ("bs_avx512",  "bslz4"),
    ("bs_avx2",    "bslz4"),
    ("bs_sse42",   "bslz4"),
    # ZSTD engine, KCB backend
    ("kcb_avx512", "bszstd"),
    ("kcb_avx2",   "bszstd"),
    ("kcb_sse42",  "bszstd"),
    # ZSTD engine, bitshuffle-core backend
    ("bs_avx512",  "bszstd"),
    ("bs_avx2",    "bszstd"),
    ("bs_sse42",   "bszstd"),
]


def _cpu_has(flag):
    try:
        with open("/proc/cpuinfo") as f:
            return flag in f.read()
    except IOError:
        return False


def bench_variant(vname, engine, chunks, mask):
    """Run NREPEATS passes using variant *vname* from *engine* family."""
    rebind = getattr(_m, "_rebind_" + engine + "_u16")
    rebind(vname)
    func = getattr(_m, engine + "_u16")

    mask_flat = mask.ravel()
    N = mask_flat.size
    total_npx = 0
    t0 = timeit.default_timer()
    for _ in range(NREPEATS):
        for buf in chunks:
            npx = func(buf, mask_flat, vals, inds, CUT)
            total_npx += npx
    elapsed = timeit.default_timer() - t0
    nframes_total = NREPEATS * len(chunks)
    return nframes_total / elapsed, total_npx, elapsed


def main():
    if not os.path.isfile(H5FILE):
        print("SKIPPED: data file not found:", H5FILE)
        print("set BSLZ4_BENCH_FILE to a bitshuffle-lz4 .h5 file")
        return

    import h5py
    print("=" * 72)
    print("  bslz4/bszstd_u16 benchmark: %d frames x %d repeats" %
          (NFRAMES, NREPEATS))
    print("  c2py23 -O3 (no -fopenmp for bslz4/bszstd). CPU: avx2=%s avx512f=%s" %
          (_cpu_has("avx2"), _cpu_has("avx512f")))
    print("=" * 72)

    f = h5py.File(H5FILE, "r")
    ds = f[DSPATH]
    mask = np.ones(ds.shape[1:], dtype=np.uint8)

    chunks = []
    for i in range(NFRAMES):
        _, buf = ds.id.read_direct_chunk((i, 0, 0))
        chunks.append(buf)

    print("  file: %s  shape=%s  dtype=%s  filters=%s" %
          (H5FILE, ds.shape, ds.dtype, ds._filters))
    print("  pre-read %d chunks (%.1f MB each)" %
          (len(chunks), ds.shape[1] * ds.shape[2] * 2 / 1e6))
    print()

    # Reference: original f2py
    ref_fps = None
    try:
        from bslz4_to_sparse import bslz4_uint16_t as f2py_fn
        vo = np.empty(mask.size, dtype=np.uint16)
        io = np.empty(mask.size, dtype=np.uint32)
        t0 = timeit.default_timer()
        for _ in range(NREPEATS):
            for buf in chunks:
                f2py_fn(np.frombuffer(buf, np.uint8), mask.ravel(), vo, io, CUT)
        ref_fps = (NREPEATS * len(chunks)) / (timeit.default_timer() - t0)
    except ImportError:
        pass

    print("  %-22s  %8s  %9s  %s" % ("variant", "fps", "ms/frame", "vs ref"))
    print("  " + "-" * 55)
    if ref_fps:
        print("  %-22s  %8.1f fps  %7.2f ms  (ref f2py -O2)" %
              ("[original f2py]", ref_fps, 1000.0 / ref_fps))

    results = []
    ref_npx = None
    engine_labels = {}  # (engine, vname) -> label for display
    for vname, engine in VARIANTS:
        label = engine + "_" + vname
        fps, npx, elapsed = bench_variant(vname, engine, chunks, mask)
        if ref_npx is None:
            ref_npx = npx
        ok = " " if npx == ref_npx else " MISMATCH"
        ms_frame = 1000.0 / fps
        vs = " %.2fx" % (fps / ref_fps) if ref_fps else ""
        results.append((label, fps, npx))
        print("  %-22s  %8.1f fps  %7.2f ms %s%s" %
              (label, fps, ms_frame, vs, ok))

    print()

    # Summary per backend within each engine
    for engine in ("bslz4", "bszstd"):
        for backend in ("kcb", "bs"):
            vrs = [r for r in results if r[0].startswith(engine + "_" + backend)]
            if vrs:
                best = max(r[1] for r in vrs)
                best_name = [r[0] for r in vrs if r[1] == best][0]
                print("  %s/%-3s  best: %s  %.1f fps" %
                      (engine, backend, best_name, best))

    if ref_fps:
        print()
        print("  Speedup vs original f2py (-O2):")
        for engine in ("bslz4", "bszstd"):
            for backend in ("kcb", "bs"):
                vrs = [r for r in results if r[0].startswith(engine + "_" + backend)]
                if vrs:
                    best = max(r[1] for r in vrs)
                    print("    %s/%-3s: %.2fx" % (engine, backend, best / ref_fps))

    f.close()


if __name__ == "__main__":
    main()
