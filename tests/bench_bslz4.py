"""Benchmark bslz4_uint16 variants on real Eiger data.

Forces each variant via _rebind API and measures wall-clock throughput.
3 repeats per variant to average out noise.

Requires: h5py + a bitshuffle-lz4 compressed HDF5 file.
Default path: /home/worker/test_data/eiger_0000.h5
Override:   BSLZ4_BENCH_FILE=/path/to/file.h5 python3 tests/bench_bslz4.py

Compile flags:
  c2py23 bslz4:   -O3 -fopenmp -mavx512f / -mavx2 / -msse4.2  (multi-ISA dispatch)
  original f2py:  -O2  (no ISA flags, no OpenMP)
"""

import os
import sys
import timeit

import numpy as np
import c2ImageD11._cImageD11 as _m
from c2ImageD11.bslz4 import chunk2sparse

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
H5FILE = os.environ.get("BSLZ4_BENCH_FILE", "/home/worker/test_data/eiger_0000.h5")
DSPATH = "/entry_0000/measurement/data"
NFRAMES = 100
NREPEATS = 3
CUT = 0

VARIANTS = [
    "kcb_avx512",
    "kcb_avx2",
    "kcb_sse42",
    "bs_avx512",
    "bs_avx2",
    "bs_sse42",
]


def _cpu_has(flag):
    try:
        with open("/proc/cpuinfo") as f:
            return flag in f.read()
    except IOError:
        return False


def bench_variant(vname, chunks, mask):
    """Run *NREPEATS* passes through all *chunks* using *vname* variant."""
    _m._rebind_bslz4_uint16(vname)
    fun = chunk2sparse(mask, dtype=np.uint16)

    total_npx = 0
    t0 = timeit.default_timer()
    for _ in range(NREPEATS):
        for buf in chunks:
            npx, _ = fun(buf, CUT)
            total_npx += npx
    elapsed = timeit.default_timer() - t0
    nframes_total = NREPEATS * len(chunks)
    return nframes_total / elapsed, total_npx, elapsed


def main():
    # Check for test data
    if not os.path.isfile(H5FILE):
        print("=" * 72)
        print("  bslz4_uint16 benchmark: SKIPPED")
        print("  data file not found: %s" % H5FILE)
        print("  set BSLZ4_BENCH_FILE to a bitshuffle-lz4 .h5 file")
        print("=" * 72)
        return

    import h5py

    print("=" * 72)
    print("  bslz4_uint16 benchmark: %d frames x %d repeats" %
          (NFRAMES, NREPEATS))
    print("  c2py23: -O3 -fopenmp   f2py: -O2  (both use KCB)")
    print("=" * 72)

    f = h5py.File(H5FILE, "r")
    ds = f[DSPATH]
    mask = np.ones(ds.shape[1:], dtype=np.uint8)
    print("  file:  %s" % H5FILE)
    print("  shape: %s  dtype=%s  chunks=%s" % (ds.shape, ds.dtype, ds.chunks))
    print("  filters: %s" % ds._filters)

    # Pre-read chunks (amortise h5py overhead)
    chunks = []
    for i in range(NFRAMES):
        _, buf = ds.id.read_direct_chunk((i, 0, 0))
        chunks.append(buf)
    mb_per_frame = ds.shape[1] * ds.shape[2] * 2 / 1e6
    print("  pre-read %d chunks (%.1f MB uncompressed each)" %
          (len(chunks), mb_per_frame))
    print()

    # -- Reference: original f2py (C layer, no Python wrapper) --
    ref_fps = None
    try:
        from bslz4_to_sparse import bslz4_uint16_t as f2py_fn

        t0 = timeit.default_timer()
        for _ in range(NREPEATS):
            for buf in chunks:
                chunk_buf = np.frombuffer(buf, dtype=np.uint8)
                vals = np.zeros(mask.size, dtype=np.uint16)
                inds = np.zeros(mask.size, dtype=np.uint32)
                f2py_fn(chunk_buf, mask.ravel(), vals, inds, CUT)
        ref_fps = (NREPEATS * len(chunks)) / (timeit.default_timer() - t0)
    except ImportError:
        pass

    if ref_fps:
        print("  %-22s  %8.1f fps  %7.2f ms  (reference f2py, -O2 KCB)" %
              ("[original f2py]", ref_fps, 1000.0 / ref_fps))
    else:
        print("  %-22s  %8s  (not installed)" % ("[original f2py]", "--"))

    # -- c2py23 variants --
    results = []
    ref_npx = None
    print("  %-22s  %8s  %9s  %s" %
          ("variant", "fps", "ms/frame", "vs f2py"))
    print("  " + "-" * 65)

    for vname in VARIANTS:
        fps, npx, elapsed = bench_variant(vname, chunks, mask)
        if ref_npx is None:
            ref_npx = npx
        ok = " " if npx == ref_npx else " MISMATCH!"
        ms_frame = 1000.0 / fps
        vs_ref = " %.2fx" % (fps / ref_fps) if ref_fps else ""
        results.append((vname, fps, npx, elapsed))
        print("  %-22s  %8.1f fps  %7.2f ms  %s%s" %
              (vname, fps, ms_frame, vs_ref, ok))
        if npx != ref_npx:
            print("    *** npx mismatch: %d != %d ***" % (npx, ref_npx))

    print()

    # -- Summary --
    cpu = "(avx2=%s avx512f=%s)" % (_cpu_has("avx2"), _cpu_has("avx512f"))
    print("  CPU features: %s" % cpu)
    print("  Compiled ISA levels: sse42 avx2 avx512")
    print("  Compile flags: c2py23=-O3  f2py=-O2")

    for backend in ("kcb", "bs"):
        backend_results = [r for r in results if r[0].startswith(backend)]
        if len(backend_results) >= 2:
            best = max(r[1] for r in backend_results)
            worst = min(r[1] for r in backend_results)
            names = [r[0] for r in sorted(backend_results, key=lambda x: -x[1])]
            print("  %s:  %s  (best=%.1f, range=%.1f)" %
                  (backend, " > ".join(names), best, best - worst))

    if ref_fps:
        print()
        print("  Speedup vs original f2py (-O2 KCB):")
        for backend in ("kcb", "bs"):
            best = max(r[1] for r in results if r[0].startswith(backend))
            print("    %s best: %.2fx (%s)" % (
                backend, best / ref_fps,
                [r[0] for r in results if r[0].startswith(backend) and r[1] == best][0]))

    f.close()


if __name__ == "__main__":
    main()
