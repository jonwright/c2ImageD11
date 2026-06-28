# score_and_refine — ISA-dispatched C++ template variants

## What it is

A c2py23-dispatched implementation of `score_and_refine`, the most-used
function in ImageD11 (refinegrains.py, indexing.py).  Replaces the original
f2py-compiled C code with type-and-ISA-dispatched C++ template variants.

## How it works

### Dispatch chain (c2py23 wrapper → C)

On every call, the c2py23-generated C wrapper checks conditions in order
(first-match-wins):

```
AoS path (score_and_refine):
  1. f64 AVX-512   ← if cpu has avx512f and gv is float64
  2. f32 AVX-512   ← if cpu has avx512f and gv is float32
  3. f64 AVX2      ← if cpu has avx2
  4. f32 AVX2
  5. f64 SSE4.1    ← if cpu has sse4.1
  6. f32 SSE4.1
  7. f32 baseline  ← C++ template, any CPU
  8. f64 baseline  ← C++ template, any CPU (was orig C)

SoA path (score_and_refine_soa):
  Same order, separate functions for gvx,gvy,gvz component arrays.
```

### Python layer (c2ImageD11/__init__.py)

Detects layout from gv shape:
- `(N,3)` with N≠3 → AoS (interleaved x/y/z)
- `(3,N)` with N≠3 → SoA (component rows)
- `(3,3)` → uses strides to disambiguate

Then delegates to the c2py23 dispatch wrapper.

### OpenMP threading

Active automatically when `ng > 50000` (OMP_MIN_NG) and thread count > 1.
Controlled via `cimaged11_omp_set_num_threads(n)`.
Speedup: ~2x at ng ≥ 75000 on 4C x86_64.

### C++ template (score_and_refine.hpp)

Single template supporting both AoS (interleaved) and SoA (separate arrays)
layouts.  Each ISA variant is compiled with flags tuned to that ISA level
(see meson.build for exact flags).

Rounding:
- SSE4.1+ (all ISA variants): `nearbyint()` → roundsd/roundss instruction
- Baseline (no ISA): magic integer trick `(x + MAGIC) - MAGIC`
  **Must not use -ffast-math** — it would simplify the trick away.

### Variant files (16 total)

| File | AoS/SoA | ISA level | In dispatch? |
|------|---------|-----------|:---:|
| score_and_refine_f64.cpp | AoS f64 | baseline | yes |
| score_and_refine_f32.cpp | AoS f32 | baseline | yes |
| score_and_refine_f64_soa.cpp | SoA f64 | baseline | yes |
| score_and_refine_f32_soa.cpp | SoA f32 | baseline | yes |
| score_and_refine_f64_sse41.cpp | AoS f64 | SSE4.1 | yes |
| score_and_refine_f32_sse41.cpp | AoS f32 | SSE4.1 | yes |
| score_and_refine_f64_soa_sse41.cpp | SoA f64 | SSE4.1 | yes |
| score_and_refine_f32_soa_sse41.cpp | SoA f32 | SSE4.1 | yes |
| score_and_refine_f64_avx2.cpp | AoS f64 | AVX2 | yes |
| score_and_refine_f32_avx2.cpp | AoS f32 | AVX2 | yes |
| score_and_refine_f64_soa_avx2.cpp | SoA f64 | AVX2 | yes |
| score_and_refine_f32_soa_avx2.cpp | SoA f32 | AVX2 | yes |
| score_and_refine_f64_avx512.cpp | AoS f64 | AVX-512 | yes |
| score_and_refine_f32_avx512.cpp | AoS f32 | AVX-512 | yes |
| score_and_refine_f64_soa_avx512.cpp | SoA f64 | AVX-512 | yes |
| score_and_refine_f32_soa_avx512.cpp | SoA f32 | AVX-512 | yes |

All 16 have C2PY_BEGIN blocks and participate in dispatch.

### Compiler flags

Variants are compiled as separate static libraries with per-ISA flags:

| Variant | Flags |
|---------|-------|
| Baseline (all 4) | `-O2 -fopenmp` (no -ffast-math) |
| f64 SSE4.1 | `-O2 -fopenmp -msse4.1` |
| f32 SSE4.1 | `-O3 -ffast-math -fopenmp -msse4.1` |
| AVX2 (all 4) | `-O3 -ffast-math -fopenmp -mavx2 -mfma` |
| AVX-512 (all 4) | `-O3 -ffast-math -fopenmp -mavx512f -mavx2 -mfma` |

Flags were determined by reproducible measurement (see measure_flags.py).

## How to build

```bash
cd build/libc2ImageD11 && ninja
cp _cImageD11.so ../../c2ImageD11/_cImageD11.so
cp _cImageD11.so ../../c2ImageD11/_cImageD11_x86_64.so
```

If C2PY_BEGIN blocks were edited:
```bash
python3 tools/harvester.py --output-dir lib/interface
cd build/libc2ImageD11 && ninja
```

## How to test

```bash
python3 -m pytest tests/test_variants.py tests/test_equivalence.py -v
```

## Benchmarks

```bash
python3 lib/functions/score_and_refine/bench.py              # throughput
python3 lib/functions/score_and_refine/bench.py --threads    # threading scaling
python3 lib/functions/score_and_refine/bench.py --overhead   # vs f2py
```

### Compiler-flag measurement (research)

```bash
python3 lib/functions/score_and_refine/measure_flags.py
```

Reproducibly measures O2/O3 × fm/no-fm × ISA across both dtypes.
Generates standalone .cpp compilations, builds a temp .so, measures via ctypes.
Artifacts in `/tmp/sar_flag_measure/`.

## Performance (x86_64, 4C Zen3)

| Mode | f64 | f32 |
|------|-----|-----|
| c2py vs f2py (10k gvs) | 1.9x | — |
| 100k gvs, 4T | 852M/s | 2893M/s |
| Threading 200k, 4T | 2.0x | 1.6x |

## Design decisions

- OpenMP is at the C level (pragma in the template), not Python-layer dispatch.
  The `if(ng > 50000)` guard prevents threading overhead on small arrays.
- f64 SSE4.1 variants are slower than AVX2 but faster than the original C at
  scale due to OpenMP threading. f32 variants are faster due to narrower types.
- Baseline is compiled without `-ffast-math` because the magic-integer rounding
  trick `(x + MAGIC) - MAGIC` would be optimized away.
