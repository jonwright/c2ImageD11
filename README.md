# c2ImageD11

Standalone binary distribution of ImageD11 C extensions, ported from
f2py to c2py23.  Provides 64 C functions (closest-vec, score, compute_gv,
connectedpixels, sparse operations, bslz4 decompress, etc.) with SIMD
dispatch (SSE4.2/AVX2/AVX-512) for hot-path functions.

**Status:** All 53 equivalence tests pass (1 expected skip). 38 bslz4/bszstd
tests pass (CI micro + bit-perfect + CSC + f2py equivalence). CI green
on Python 2.7–3.14.

## Quick start

```bash
git clone --recurse-submodules https://github.com/jonwright/c2ImageD11
cd c2ImageD11
pip install --no-build-isolation -e .
pytest tests/
```

The `--recurse-submodules` (or `git submodule update --init`) is required
to fetch `lz4/`, `kcb/`, and `bitshuffle/` dependencies needed for
`bslz4_to_sparse` support.

If you do not need bslz4 support, the submodules can be skipped and
the build will still work for the core ImageD11 C functions.

Requires GCC with `-fopenmp` and a c2py23 installation.

## Features

- **SIMD dispatch**: Hot-path functions (score, compute_gv, put_incr,
  blobproperties, etc.) auto-select AVX-512 / AVX2 / SSE4.2 at runtime.
  Use `_rebind_score('avx2')` to force a specific variant.

- **bslz4_to_sparse**: Bitshuffle-lz4+zstd compressed frame decoding directly
  to sparse (indices, values) arrays, with dual compression engine +
  dual unshuffle backend support:
  - Engines: LZ4 (default), ZSTD (better compression ratio)
  - Backends: KCB (kalcutter, priority), bitshuffle-core (kiyo-masui, fallback)
  - Python API: `chunk2sparse`, `chunk2sparseCSC`, `bslz4_to_sparse()`

- **Per-function timing**: `c2py23.perf.read_perf()` for C-level
  microbenchmarks without Python overhead.

- **Equivalence tested**: 53/54 tests produce identical results to
  ImageD11._cImageD11. 7 bslz4 tests verify the C bridge and equivalence
  against the original f2py extension.

## See also

- `AGENTS.md` — full project plan, architecture, conventions
- `PLAN.md` — migration roadmap and bug fix details
- `tests/bench_bslz4.py` — throughput benchmark for bslz4 variants
- `tests/benchmark_simd.py` — ISA-level SIMD variant comparison
