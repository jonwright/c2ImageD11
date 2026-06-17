"""bench1.py -- comprehensive bslz4/bszstd benchmark.

Tests all engine×backend×ISA variants across u8/u16/u32 dtypes,
basic and CSC modes, with saturated-pixel mask.

Data files expected in /home/worker/test_data/:
  eiger_lz4_u8.h5   eiger_zstd_u8.h5
  eiger_lz4_u16.h5  eiger_zstd_u16.h5
  eiger_lz4_u32.h5  eiger_zstd_u32.h5
  eiger_mask.npy
"""

import os, timeit
import numpy as np
import c2ImageD11._cImageD11 as _m


DATADIR = "/home/worker/test_data"
NFRAMES = 100
NREPEATS = 3
CUT = 0

ENGINES = {
    "lz4":  {"prefix": "bslz4",  "files": {"u8":"eiger_lz4_u8.h5", "u16":"eiger_lz4_u16.h5", "u32":"eiger_lz4_u32.h5"}},
    "zstd": {"prefix": "bszstd", "files": {"u8":"eiger_zstd_u8.h5", "u16":"eiger_zstd_u16.h5", "u32":"eiger_zstd_u32.h5"}},
}

BACKENDS = ["kcb", "bs"]
ISAS     = ["avx512", "avx2", "sse42"]


def bench_basic(engine, backend, isa, dtype_name, chunks, mask_flat, out_dtype):
    """Benchmark basic sparse decompress. Returns (fps, npx_total)."""
    prefix = ENGINES[engine]["prefix"]
    vname = "{}_{}".format(backend, isa)
    rebind = getattr(_m, "_rebind_" + prefix + "_" + dtype_name)
    rebind(vname)
    func = getattr(_m, prefix + "_" + dtype_name)

    N = mask_flat.size
    vals = np.empty(N, dtype=out_dtype)
    inds = np.empty(N, dtype=np.uint32)
    total_npx = 0

    t0 = timeit.default_timer()
    for _ in range(NREPEATS):
        for buf in chunks:
            chunk_buf = np.frombuffer(buf, dtype=np.uint8)
            npx = func(chunk_buf, mask_flat, vals, inds, CUT)
            total_npx += npx
    elapsed = timeit.default_timer() - t0
    fps = (NREPEATS * len(chunks)) / elapsed
    return fps, total_npx


def bench_csc(engine, backend, isa, dtype_name, chunks, mask_flat,
              out_dtype, csc_data, csc_indices, csc_indptr, powder):
    """Benchmark CSC sparse decompress. Returns (fps, npx_total)."""
    prefix = ENGINES[engine]["prefix"]
    vname = "{}_{}".format(backend, isa)
    csc_name = "csc_" + dtype_name
    rebind = getattr(_m, "_rebind_" + prefix + "_" + csc_name)
    rebind(vname)
    func = getattr(_m, prefix + "_" + csc_name)

    N = mask_flat.size
    outpx = np.empty(N, dtype=out_dtype)
    outP = np.empty(N, dtype=np.uint32)
    total_npx = 0

    t0 = timeit.default_timer()
    for _ in range(NREPEATS):
        powder[:] = 0.0
        for buf in chunks:
            chunk_buf = np.frombuffer(buf, dtype=np.uint8)
            npx = func(chunk_buf, mask_flat, outpx, outP, CUT,
                       powder, csc_data, csc_indices, csc_indptr)
            total_npx += npx
    elapsed = timeit.default_timer() - t0
    fps = (NREPEATS * len(chunks)) / elapsed
    return fps, total_npx


def make_fake_csc(mask):
    """Make a trivial CSC matrix (one bin covering all pixels)."""
    flat = mask.ravel()
    nz = int(flat.sum())
    data = np.ones(nz, dtype=np.float32)
    indices = np.where(flat)[0].astype(np.uint32)
    indptr = np.zeros(len(flat) + 1, dtype=np.uint32)
    indptr[:] = np.arange(len(flat) + 1) * (nz / len(flat))  # distribute
    # Actually simpler: indptr each pixel maps to bin 0 (identity-like)
    # Just make a 1-bin CSC: every non-zero pixel maps to bin 0
    data = np.ones(len(flat), dtype=np.float32)  # include masked pixels too (val=0 in indptr)
    indices = np.zeros(len(flat), dtype=np.uint32)  # all map to bin 0
    indptr = np.arange(len(flat) + 1, dtype=np.uint32)  # one pixel per column
    powder = np.zeros(1, dtype=np.float64)
    return data, indices, indptr, powder


def fmt(n):
    if n is None: return "   --"
    return "%6.1f" % n


def main():
    mask = np.load(os.path.join(DATADIR, "eiger_mask.npy"))
    print("=" * 80)
    print("  bench1.py: bslz4/bszstd variants — %d frames x %d repeats" %
          (NFRAMES, NREPEATS))
    print("  mask: %d saturated pixels of %d (%.1f%%)" %
          (mask.sum(), mask.size, 100.*mask.sum()/mask.size))
    print("  c2py23: -O3 -Wall  (no -fopenmp for bslz4/bszstd)")
    print("=" * 80)

    # Fake CSC for CSC benchmarks
    csc_data, csc_indices, csc_indptr, powder = make_fake_csc(mask)

    # Per-dtype benchmark
    DTYPE_INFO = [
        ("u8",  np.uint8,  ["kcb", "bs"]),
        ("u16", np.uint16, ["kcb", "bs"]),
        ("u32", np.uint32, ["kcb", "bs"]),
    ]

    for dtype_name, out_dtype, backends in DTYPE_INFO:
        print("\n--- %s ---" % dtype_name)
        header = "  %-22s" % "variant"
        for eng in ["lz4", "zstd"]:
            header += " | %8s" % eng
        header += " | %8s" % "CSC lz4"
        print(header)
        print("  " + "-" * 70)

        # Pre-read chunks for this dtype
        engine_chunks = {}
        for eng in ["lz4", "zstd"]:
            h5path = os.path.join(DATADIR, ENGINES[eng]["files"][dtype_name])
            if not os.path.isfile(h5path):
                engine_chunks[eng] = None
                continue
            import h5py
            with h5py.File(h5path, "r") as f:
                ds = f["/entry_0000/measurement/data"]
                engine_chunks[eng] = [ds.id.read_direct_chunk((i,0,0))[1]
                                       for i in range(NFRAMES)]

        mask_flat = mask.ravel()

        for backend in ["kcb", "bs"]:
            for isa in ISAS:
                label = "%s/%s" % (backend, isa)
                row = "  %-22s" % label

                for eng in ["lz4", "zstd"]:
                    chunks = engine_chunks.get(eng)
                    if chunks is None:
                        row += " | %8s" % "--"
                        continue
                    fps, npx = bench_basic(eng, backend, isa, dtype_name,
                                           chunks, mask_flat, out_dtype)
                    row += " | %7.1f" % fps

                # CSC benchmark (all dtypes, lz4 only; zstd CSC omitted)
                chunks = engine_chunks.get("lz4")
                if chunks is not None:
                    fps_csc, _ = bench_csc("lz4", backend, isa, dtype_name,
                                           chunks, mask_flat, out_dtype,
                                           csc_data, csc_indices, csc_indptr, powder)
                    row += " | %7.1f" % fps_csc
                else:
                    row += " | %8s" % "--"

                print(row)

    # Summary
    print("\n" + "=" * 80)
    print("  Best fps per backend×dtype (KCB backend, basic sparse)")
    print("=" * 80)
    print("  %-4s  %6s  %6s  %6s  %s" % ("", "u8", "u16", "u32", "(best ISA)"))
    print("  " + "-" * 55)

    # Re-read the highest-perf engine chunks once more for summary
    sum_chunks = {}
    for eng in ["lz4", "zstd"]:
        sum_chunks[eng] = {}
        for dtype_name, out_dtype, _ in DTYPE_INFO:
            h5path = os.path.join(DATADIR, ENGINES[eng]["files"][dtype_name])
            if os.path.isfile(h5path):
                import h5py
                with h5py.File(h5path, "r") as f:
                    ds = f["/entry_0000/measurement/data"]
                    sum_chunks[eng][dtype_name] = [ds.id.read_direct_chunk((i,0,0))[1]
                                                     for i in range(NFRAMES)]

    for eng in ["lz4", "zstd"]:
        for backend in ["kcb", "bs"]:
            row_data = []
            for dtype_name, out_dtype, _ in DTYPE_INFO:
                chunks = sum_chunks.get(eng, {}).get(dtype_name)
                if chunks is None:
                    row_data.append("   --")
                    continue
                best_fps, best_isa = 0, ""
                for isa in ISAS:
                    fps, _ = bench_basic(eng, backend, isa, dtype_name,
                                         chunks, mask.ravel(), out_dtype)
                    if fps > best_fps:
                        best_fps, best_isa = fps, isa
                row_data.append("%5.0f %s" % (best_fps, best_isa))
            print("  %s/%-3s  %15s  %15s  %15s" %
                  (eng, backend, row_data[0], row_data[1], row_data[2]))

    # CSC summary (all dtypes, lz4 only)
    print()
    print("  CSC (lz4 only):")
    for dtype_name, out_dtype, _ in DTYPE_INFO:
        chunks = sum_chunks["lz4"][dtype_name]
        for backend in ["kcb", "bs"]:
            best_csc, best_isa = 0, ""
            for isa in ISAS:
                fps_csc, _ = bench_csc("lz4", backend, isa, dtype_name,
                                        chunks, mask.ravel(), out_dtype,
                                        csc_data, csc_indices, csc_indptr, powder)
                if fps_csc > best_csc:
                    best_csc, best_isa = fps_csc, isa
            print("    %-3s %3s: %6.1f fps (%s)" % (backend, dtype_name, best_csc, best_isa))


if __name__ == "__main__":
    main()
