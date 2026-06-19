# c2ImageD11 - Agent Plan

## Project Goals

Port the ImageD11 C extensions from f2py to c2py23, creating a standalone
binary distribution `c2ImageD11`. The original ImageD11 repo is NOT modified.
After extensive testing, `ImageD11/cImageD11.py` will be updated to try
importing from `c2ImageD11` first, falling back to `ImageD11._cImageD11`.

## Current Status

- [x] Phase I: Repo structure created, C sources copied
- [x] Phase II: _cImageD11.c2py interface written
- [x] Phase III: Python package (c2ImageD11/) written
- [x] Phase IV: setup.py written
- [x] c2py23 features implemented (fixed-width types, optionals, constants, docstrings)
- [x] Phase V: Buffer-interface tests created
- [x] Phase VI: CI passing on all 8 Python versions (2.7-3.14)
- [x] Phase VII: Equivalence testing against ImageD11._cImageD11 (53/54 pass)
  - 1 test skipped: TestRefineAssigned (ImageD11 PyPI release < 2.1.4 has bug;
    git head has the fix but version string not yet bumped; skip remains until
    fix is released on PyPI)
- [x] Phase VIII: SIMD dispatch (SSE/AVX2/AVX-512) for hot-path functions
- [x] Phase IX: bslz4_to_sparse import with multi-backend SIMD dispatch
- [x] Phase IXb: Integer CSC data types (exact arithmetic with uint64 output)
- [ ] Phase X: Project layout refactoring (repo is ~90MB; split into manageable sub-packages)

## Remaining Tasks

All tracked in this file (AGENTS.md).  PLAN.md and c2py23_requests.md
contain historical context and deferred improvement requests.

| ID | Task | Where | Priority |
|----|------|-------|----------|
| T1 | Refactor project layout for manageability (repo too large) | AGENTS.md Phase X | Medium |
| T2 | ImageD11 cImageD11.py: try c2ImageD11 first, fallback to _cImageD11 | PLAN.md | High |
| T3 | KCB ifunc dispatch: port up one level or keep as-is | AGENTS.md Phase IX | Low |
| T4 | MSVC / Windows build support | AGENTS.md Phase IX | Low |
| T5 | Vector sparse masking with hand-written SIMD intrinsics | AGENTS.md Phase IX | Low |
| T6 | c2py23 publish to PyPI (eliminates --no-build-isolation) | c2py23_requests.md #9 | Medium |
| T7 | c2py23 features: default_raise, outputs, expand templates | c2py23 review | Low |
| T8 | Generate ZSTD test data and verify bit-perfect ZSTD decompress | tests/ | Medium |
| T9 | Debug and fix bslz4 / hdf5 chunk reading on Python 2.7 | bslz4.py, tests/ | High |
| T10 | [x] Integer CSC exact arithmetic (Phase IXb complete) | src/, c2ImageD11/, tests/ | High |

## Phase VIII: amd64 SIMD Dispatch (SSE, AVX2, AVX-512)

### Motivation

ImageD11 columnfiles hold up to 1e9 peaks. The indexing, geometry, and
reconstruction functions in `indexing.py`, `columnfile.py`, `refinegrains.py`,
and `transform.py` call C functions in hot loops over all peaks. Multi-flag
compilation with c2py23's grouped variant dispatch auto-vectorizes these
loops at the installed ISA level (SSE4.2 / AVX2 / AVX-512F).

### Which Functions Get SIMD

Based on call-frequency analysis across all ImageD11 Python files (202 calls,
44 files), prioritized by data volume and hot-path impact:

**Tier 1 -- Indexing hot path (columnfile/indexing core):**

| Function | .c2py name | Calls | Data per call | Source |
|----------|-----------|-------|---------------|--------|
| `score` | `score` | 10 | gv=`(ng,3)`, ubi=9 | `indexing.py:1095`, `unitcell.py:800` |
| `score_and_refine` | `score_and_refine` | 10 | gv=`(ng,3)`, ubi=9 | `indexing.py:825`, `refinegrains.py:389` |
| `score_and_assign` | `score_and_assign` | 6 | gv=`(ng,3)`, ubi=9 | `indexing.py:888,1080` |
| `compute_gv` | `compute_gv` | 5 | xyz=`(n,3)`, omega=`(n,)` | `refinegrains.py:721`, `transform.py:717` |
| `compute_geometry` | `compute_geometry` | 1 | xyz=`(n,3)`, out=`(n,6)` | `transform.py:764` |
| `compute_xlylzl` | `compute_xlylzl` | 1 | s/f=`(n,)`, out=`(n,3)` | `transform.py:705` |
| `compute_xlylzl_xpos_variable` | `compute_xlylzl_xpos_variable` | 1 | s/f/xpos=`(n,)`, out=`(n,3)` | `transform.py:748` |

**Tier 2 -- High-volume element-wise / gather-scatter:**

| Function | .c2py name | Calls | Data per call | Where |
|----------|-----------|-------|---------------|-------|
| `put_incr32` | `put_incr32` | 10+ | data=`(m,)`, ind/vals=`(n,)` | tomography, sinogram |
| `put_incr64` | `put_incr64` | 10+ | data=`(m,)`, ind/vals=`(n,)` | volume mapping |
| `reorder_f32_a32` | `reorder_f32_a32` | 3 | 4.2e6 floats | `fazit.py:281` |
| `reorder_f32_a32` (lut) | `reorderlut_f32_a32` | 3 | 4.2e6 floats | `fazit.py:290` |
| `reorder_u16_a32` | `reorder_u16_a32` | 3 | 4.2e6 uint16 | `fazit.py:261` |
| `reorder_u16_a32` (lut) | `reorderlut_u16_a32` | 3 | 4.2e6 uint16 | `fazit.py:270` |

**Tier 3 -- Dense per-frame image processing:**

| Function | .c2py name | Calls | Data per call | Where |
|----------|-----------|-------|---------------|-------|
| `blobproperties` | `blobproperties` | 7 | 4.2e6 pixels x 36 props | `frelon_peaksearch.py:366` |
| `uint16_to_float_darksub` | `uint16_to_float_darksub` | 2 | 4.2e6 pixels | `frelon_peaksearch.py` |
| `uint16_to_float_darkflm` | `uint16_to_float_darkflm` | 2 | 4.2e6 pixels | `frelon_peaksearch.py` |

**NOT SIMD-targeted** (tiny data, graph algorithms, or called <2x):
`misori_*`, `quickorient`, `closest`, `closest_vec`, `cluster1d`,
`count_shared`, `verify_rounding`, `connectedpixels`, `bloboverlaps`,
`blob_moments`, `clean_mask`, `make_clean_mask`, `sparse_*`,
`tosparse_*`, `coverlaps`, `compress_duplicates`, `bgcalc`,
`frelon_lines`, `array_*`, `localmaxlabel`, `mask_to_coo`, `splat`,
`sparse_is_sorted`, `splat`. These ~25 functions keep their existing
flat overloads unchanged.

### Architecture

```
Python caller
  -> _cImageD11.score(ubi, gv, tol)
    -> _wrapper: buffer acquire + checks
    -> _impl: outer when: (format check, per-call)
      -> inner switch: _score_group_variant (pre-resolved at init)
        -> score_avx512 / score_avx2 / score_sse42

Module init:
  c2py_runtime_init()
    -> cpuid probing -> sets c2py_amd64_avx2, c2py_amd64_avx512f
  _score_group_resolve()
    -> if (c2py_amd64_avx512f) _score_group_variant = 0
      else if (c2py_amd64_avx2) _score_group_variant = 1
      else _score_group_variant = 2
```

### Kernel File Structure

One `.c` file per function in `src_simd/`, each following the c2py23
`KERNEL_FN` pattern from `examples/simd_dispatch/`:

```c
// src_simd/score_kernel.c
#include "cImageD11.h"    // for restrict, stdint
#include <math.h>

#ifndef KERNEL_FN
#define KERNEL_FN score_sse42
#endif

// Magic constant for fast double-to-int rounding
#define MAGIC 6755399441055744.0
static inline double fast_round(double x) { return (x + MAGIC) - MAGIC; }

int KERNEL_FN(const double *restrict ubi, const double *restrict gv,
              double tol, int ng) {
    double atol = tol * tol;
    int n = 0, k;
    #pragma omp parallel for reduction(+:n)
    for (k = 0; k < ng; k++) {
        const double *g = gv + k * 3;
        double h0 = ubi[0]*g[0] + ubi[1]*g[1] + ubi[2]*g[2];
        // ... original score() inner loop ...
    }
    return n;
}
```

Key design choices:
- Kernels take **flat `double*`** (not `vec[3]`), matching c2py23 `.ptr` output
- This eliminates the wrapper layer for SIMD paths (speed: one fewer call)
- `conv_double_to_int_fast` is `static inline` in each kernel (DLL_LOCAL in original)
- `add_pixel` from blobs.c is duplicated as `static inline` in blobproperties kernel
- OMP pragmas preserved from original code

### Multi-Flag Compilation

Each kernel compiled 3 times by setup.py pre-build hook:

```bash
gcc -c -O3 -fPIC -fopenmp -Wall \
    -mavx512f -DKERNEL_FN=score_avx512 src_simd/score_kernel.c -o score_avx512.o
gcc -c -O3 -fPIC -fopenmp -Wall \
    -mavx2 -DKERNEL_FN=score_avx2    src_simd/score_kernel.c -o score_avx2.o
gcc -c -O3 -fPIC -fopenmp -Wall \
    -msse4.2 -DKERNEL_FN=score_sse42 src_simd/score_kernel.c -o score_sse42.o
```

On non-x86_64: compile only `_sse42` variant without `-m` flags (generic -O3).
cpuid globals resolve to 0, dispatch falls through to sse42 variant.

### .c2py Syntax (Grouped Variant Dispatch)

```yaml
- py_sig: "score(ubi: buffer, gv: buffer, tol: float) -> int"
  doc: "..."
  checks: [...]
  gil_release: true                                  # NEW
  c_overloads:
    - when: "ubi.format == 'd' and gv.format == 'd'" # per-call format check
      map: {ubi: "ubi.ptr", gv: "gv.ptr", tol: tol, ng: "gv.shape[0]"}
      group: score
      variants:
        - name: "avx512"
          sig: "int score_avx512(const double *ubi, const double *gv, double tol, int ng) -> int"
          when: "c2py_amd64_avx512f"
        - name: "avx2"
          sig: "int score_avx2(const double *ubi, const double *gv, double tol, int ng) -> int"
          when: "c2py_amd64_avx2"
        - name: "sse"
          sig: "int score_sse42(const double *ubi, const double *gv, double tol, int ng) -> int"
```

### Rebind API

Auto-generated per function:
```python
_cImageD11._rebind_score('avx2')   # force AVX2 variant
_cImageD11._rebind_score(None)     # back to auto-resolve
```

### New Features Adopted from Updated c2py23

- **`gil_release: true`**: Release GIL during heavy C calls (no Python API usage)
- **`c2py_amd64.h`**: CPU feature globals in headers block
- **`variants:` dispatch**: Two-level (buffer format + CPU feature) resolution
- **Free-threaded 3.14t support**: Transparent; no changes needed
- **Contiguity check**: Auto-applied by updated c2py23 runtime
- **Per-variant timing**: `read_perf()` returns `variant_name`, `variant`, `group_idx`

### File Changes

| File | Change |
|------|--------|
| `src_simd/score_kernel.c` | NEW |
| `src_simd/score_and_refine_kernel.c` | NEW |
| `src_simd/score_and_assign_kernel.c` | NEW |
| `src_simd/compute_gv_kernel.c` | NEW |
| `src_simd/compute_geometry_kernel.c` | NEW |
| `src_simd/compute_xlylzl_kernel.c` | NEW |
| `src_simd/compute_xlylzl_xpos_kernel.c` | NEW |
| `src_simd/put_incr32_kernel.c` | NEW |
| `src_simd/put_incr64_kernel.c` | NEW |
| `src_simd/blobproperties_kernel.c` | NEW |
| `src_simd/darksub_kernel.c` | NEW |
| `src_simd/darkflm_kernel.c` | NEW |
| `src_simd/reorder_f32_a32_kernel.c` | NEW |
| `src_simd/reorderlut_f32_a32_kernel.c` | NEW |
| `src_simd/reorder_u16_a32_kernel.c` | NEW |
| `src_simd/reorderlut_u16_a32_kernel.c` | NEW |
| `_cImageD11.c2py` | ~15 functions: flat->grouped variants; add `gil_release`; add `c2py_amd64.h` |
| `setup.py` | Add `_compile_simd_variants()` pre-build; link .o files |
| `c2py23_requests.md` | Mark #7 DONE |
| `AGENTS.md` | This Phase VIII section |

## c2py23 Features Now Available

All previously-requested c2py23 extensions have been implemented upstream
(see c2py23 commit 95a2076 and later). The .c2py interface file now uses:

  - Fixed-width integer format strings ('H', 'I', 'q', 'b', 'h', 'B') in checks
  - Optional parameter defaults with the `|O$` syntax in py_sig
  - Module-level `constants:` block for integer constant export
  - Custom `doc:` field for function docstrings
  - Per-function performance timing via `timing: true` module flag
  - METH_FASTCALL dispatch on Python 3.12+

The thin wrappers in src_wrapper/_wrappers.c are only needed for adapting
2D arrays (vec[3], double[][3], double[][6]) to flat pointers, since the
.c2py grammar cannot express multi-dimensional array parameters directly.
All fixed-width integer types (uint16_t*, int32_t*, etc.) are handled
natively by c2py23.

## Directory Structure

```
c2ImageD11/
  AGENTS.md                   # This file
  c2py23_requests.md          # c2py23 improvement requests (9 items)
  PLAN.md                     # Migration & refactoring roadmap (some sections superseded)
  _cImageD11.c2py             # c2py23 interface definition (64 functions)
  setup.py                    # Build with c2py23 (SIMD + bslz4 multi-flag compilation)
  pyproject.toml              # Build config (setuptools, numpy dependency)
  MANIFEST.in                 # sdist file list
  run_ci.sh                   # Single-version local CI
  run_ci_all.sh               # Multi-version CI via Apptainer containers
  src/                        # Original C sources from ImageD11/src + bslz4
    cImageD11.h               # Platform macros, DLL visibility
    blobs.h                   # Disjoint set, NPROPERTY enums
    blobs.c                   # Disjoint set, blob moments
    cdiffraction.h            # Vector/matrix macros
    cdiffraction.c            # compute_geometry, compute_gv, compute_xlylzl*, quickorient
    cimaged11utils.c          # omp_set_num_threads, my_get_time
    closest.c                 # verify_rounding, closest, score, score_and_refine,
                              #   score_and_assign, refine_assigned, put_incr*, cluster1d,
                              #   misori_*, count_shared
    connectedpixels.c         # connectedpixels, blobproperties, bloboverlaps, blob_moments,
                              #   clean_mask, make_clean_mask
    darkflat.c                # uint16_to_float_darksub/darkflm, frelon_lines, array_stats,
                              #   array_histogram, reorder*, bgcalc
    localmaxlabel.c           # localmaxlabel
    sparse_image.c            # mask_to_coo, sparse_*, tosparse_*, coverlaps, compress_duplicates
    splat.c                   # splat
    ImageD11_cmath.h          # Alternative math macros
    bs_master.c               # Master compilation unit (includes template files)
    bs_sparse_tmpl.c          # Basic sparse decompress template
    bs_sparse_csc_tmpl.c      # CSC sparse decompress template (CSC_DATA_T/CSC_SUM_T)
    bs_functions.h            # Forward declarations for c2py23 (auto-generated)
  src_wrapper/
    _wrappers.c               # 2D-array-to-flat-pointer wrappers (6 functions)
  src_simd/                   # SIMD kernel files (16 functions, 3x ISA compiled)
    score_kernel.c
    score_and_refine_kernel.c
    score_and_assign_kernel.c
    compute_gv_kernel.c
    compute_geometry_kernel.c
    compute_xlylzl_kernel.c
    compute_xlylzl_xpos_kernel.c
    put_incr32_kernel.c
    put_incr64_kernel.c
    blobproperties_kernel.c
    darksub_kernel.c
    darkflm_kernel.c
    reorder_f32_a32_kernel.c
    reorderlut_f32_a32_kernel.c
    reorder_u16_a32_kernel.c
    reorderlut_u16_a32_kernel.c
  lz4/                        # Git submodule: LZ4 compression library
  kcb/                        # Git submodule: KCB bitshuffle (priority backend)
  bitshuffle/                 # Git submodule: original bitshuffle (fallback)
  c2ImageD11/
    __init__.py               # Pure Python: imports .so, exports constants, bslz4
    _constants.py             # Blob property enum values (hardcoded)
    bslz4.py                  # bslz4 Python API: chunk2sparse, chunk2sparseCSC
  tests/
    test_buffer.py            # Lightweight numpy buffer-interface tests
    test_equivalence.py       # Equivalence tests vs ImageD11._cImageD11 (53/54 pass)
    test_bslz4.py             # bslz4 buffer tests + equivalence vs original f2py
    benchmark_timing.py       # c2py23 vs f2py timing comparison
    benchmark_simd.py         # SIMD variant comparison (SSE/AVX2/AVX512)
    bench_bslz4.py            # bslz4 throughput benchmark (KCB vs BS backends)
    test_all.py               # Multi-version orchestrator (Apptainer)
    run_multiversion.sh       # Build + test script for inside containers
    conftest.py               # Pytest configuration (empty)
  .github/workflows/
    test.yml                  # CI: Python 2.7-3.14, timeout-minutes: 10
```

## 2D-Array-to-Flat-Pointer Wrappers

c2py23 handles flat buffers via `.ptr`, but the .c2py grammar cannot express
multi-dimensional array parameters (vec[3], double[][3], double[][6]).
src_wrapper/_wrappers.c provides thin adapters that cast flat `double*` to
`vec*` or `double(*)[N]`:

```c
// Original: double misori_cubic(vec u1[3], vec u2[3])
// Wrapper:
double misori_cubic_wrapper(const double *u1_ptr, const double *u2_ptr) {
    return misori_cubic((vec *)u1_ptr, (vec *)u2_ptr);
}
```

All wrapper names end in `_wrapper` to distinguish them from original C
functions. The .c2py file references these wrapper names in `c_overloads`.
The 6 remaining wrappers cover misori_*, refine_assigned, and splat.

## Functions with Output Scalars

Functions returning values via pointer arguments use 1-element Python buffers.
The C function writes into `buf->buf[0]`. No wrapper needed for these
(except score_and_refine which returns n as the Python int return value).

Example Python call:
```python
mean = np.zeros(1, dtype=np.float32)
var  = np.zeros(1, dtype=np.float32)
array_stats(img, minval, maxval, mean, var)
# results in mean[0], var[0]
```

## Testing Strategy

**Benchmark memory hygiene**: All benchmarks must use pre-allocated,
pre-touched numpy buffers. The c2py23 wrapper maps Python buffers to C
pointers without copy, but `np.zeros()` adds page-fault+zeroing overhead
(20-33% on large arrays). Use `np.empty()` + touch (`[:] = 0`) or
recycle arrays across frames to measure C throughput, not Python alloc.

### Local CI (pre-push)
```bash
bash run_ci.sh          # Single Python version, ~30s
bash run_ci_all.sh      # All 8 Python versions via Apptainer, ~5min
```

Both scripts must pass before pushing. `run_ci.sh` creates a clean venv,
installs c2py23 from a sibling directory, builds c2ImageD11, installs
ImageD11 from git head with `--no-deps`, and runs the full test suite.

**Pre-push checklist**: Before pushing, also verify:
  - `.github/workflows/test.yml` includes `submodules: true` for all
    checkout steps (otherwise CI fails on missing lz4/kcb/etc.)
  - `README.md` status line and test counts are up to date
  - `MANIFEST.in` includes any new source files added to submodules

### Test Files
1. `test_buffer.py`: Lightweight numpy buffer-interface tests. No ImageD11
   dependency. Verifies the build succeeded and buffer protocol calls work.
2. `test_equivalence.py`: Compares c2ImageD11 output against ImageD11._cImageD11
   for every function. Skips if ImageD11 is not importable. All 53 tests pass;
   TestRefineAssigned skipped (PyPI ImageD11 < 2.1.4 has infinite-loop bug).
3. `benchmark_timing.py`: Timing comparison using c2py23.perf module.

### GitHub Actions CI
Mirrors the local scripts. Checks out c2py23 from `jonwright/c2py23`,
installs ImageD11 from git head with `--no-deps`, runs both test files
across Python 2.7-3.14. `timeout-minutes: 10` prevents infinite-loop hangs.
`fail-fast: true` stops other jobs on first failure.

## Submodule Reference (agents: do NOT read these sources)

These are large third-party libraries. Minimise token usage by treating them
as opaque dependencies. Only the listed API functions are called.

| Submodule | URL | C functions used | Files linked |
|-----------|-----|-----------------|-------------|
| lz4 | github.com/lz4/lz4 | `LZ4_decompress_safe` | lib/lz4.c |
| kcb | github.com/kalcutter/bitshuffle | `bitshuf_decode_block` | src/bitshuffle.c |
| bitshuffle | github.com/kiyo-masui/bitshuffle | `bshuf_untrans_bit_elem` | src/bitshuffle_core.c, src/iochain.c |
| zstd | github.com/facebook/zstd | `ZSTD_decompress`, `ZSTD_compressBound` | lib/decompress/*.c, lib/common/*.c |

## Notes

- **Do not invent root causes**: When you do not know what is wrong,
  stop and ask. Never fabricate theories about bugs in third-party
  libraries (h5py, numpy, etc.) or write invented commentary into code
  or commit messages. State only what you know to be true.
- **Virtualenv convention**: create venvs as `venv/py<major><minor>/<arch>/`
  (e.g. `venv/py312/x86_64/`). This directory is gitignore'd. Always reuse
  the same venv; re-create only if the Python version or arch changes.
  Never put venvs in /tmp or tests/.
- **HDF5 for binary data**: Prefer HDF5 (.h5) over .npz for binary
  persistence (CSC matrices, test data).  All .h5 files are gitignored
  and must be regenerated by the scripts that use them.
- **Memory safety**: Run `tests/test_memory_bslz4.py` under valgrind before
  pushing:
  ```
  valgrind --leak-check=full --error-exitcode=1 python3 -m pytest tests/test_memory_bslz4.py -v
  ```
  A pre-push hook (`.githooks/pre-push`) does this automatically on master.
  Install it: `ln -sf ../../.githooks/pre-push .git/hooks/pre-push`
- **ASCII only**: This repo must contain only 7-bit ASCII characters.
  Non-ASCII (Unicode arrows, em dashes, multiplication signs, etc.)
  break Python 2.7 CI. A pre-commit hook in `.githooks/pre-commit`
  enforces this. Install it: `ln -sf ../../.githooks/pre-commit .git/hooks/pre-commit`

- The c2py23 runtime (c2py_runtime.h/.c) must be built alongside.
  The `c2py23 build` command handles this.
- OpenMP: compile with `-fopenmp`. `gil_release: true` is used for
  hot-path SIMD functions (score, score_and_refine, put_incr*, bslz4_*,
  compute_*, blobproperties, darksub/darkflm, reorder*). The GIL is
  held for remaining functions.
- malloc/free: The restriction in c2py23 docs is relaxed for this project.
  blobs.c, sparse_image.c, connectedpixels.c allocate/free internally.
- CI uses `--no-build-isolation` because c2py23 is not on PyPI.
  c2py23 must be installed before building c2ImageD11.
- Python compatibility: targets 2.7-3.14. The c2py_runtime uses dlopen
  to resolve CPython API, so one .so binary works across versions.
  Build on the oldest target OS for maximum portability.
  **Python 2.7 syntax subset**: all .py files must parse on Python 2.7.
  Do NOT use: f-strings, type annotations, async/await, nonlocal,
  yield from, `{**d}`, `[*l]`, `@` matrix multiply, keyword-only args
  (def f(*, kw)), `utf-8` source encoding needed by non-ASCII.
  Use `from __future__ import print_function` in every .py file.
  Use `%` or `.format()` for string formatting.
- numpy is used for testing; its buffer protocol (PEP 3118) is supported
  on Python 2.7-3.14 via `PyObject_GetBuffer` / c2py_acquire_buffer.
- ImageD11 is installed from git head with `--no-deps` to avoid pulling
  500MB+ of heavy runtime deps (numba, scikit-image, etc.). Only numpy
  and setuptools are needed at build time since we only test against
  the C code in `ImageD11._cImageD11`.
- Snakepit Apptainer containers (ubuntu20.04.sif, ubuntu24.04.sif) provide
  all 8 Python versions. Run `bash run_ci_all.sh` for multi-version testing.
- c2py23 improvement requests from this migration are documented in
  `c2py23_requests.md` (9 items covering safety, usability, and features).

## Phase IX: bslz4_to_sparse Import (bslz4_import)

Import the bslz4_to_sparse C extension (bitshuffle-lz4 decompress->sparse)
into c2ImageD11.  ImageD11/sinograms/ uses `chunk2sparse` and `chunk2sparseCSC`
for fast frame decoding from Dectris HDF5 files (bitshuffle-lz4 filter 32008).

### API Surface (users depend on)

From `ImageD11/sinograms/lima_segmenter.py`:
```python
from bslz4_to_sparse import chunk2sparse       # optional, falls back to numpy
fun = chunk2sparse(mask, dtype=frms.dtype)
npx, row, col, val = fun.coo(chunk, cut)         # -> (npx, row, col, val)
```

From `ImageD11/sinograms/sinogram2crysalis.py`:
```python
import bslz4_to_sparse
dc = bslz4_to_sparse.chunk2sparse(image_mask, dt)
npx, (vals, inds) = dc(b, 0)                     # -> (npx, (vals, inds))
```

Also: `chunk2sparseCSC` (CSC powder integration) and `bslz4_to_sparse()` (HDF5
dataset convenience function).

### Submodules (git)

| Submodule | URL | Purpose |
|-----------|-----|---------|
| lz4       | https://github.com/lz4/lz4 | LZ4 decompression (lz4/lz4.c) |
| kcb       | https://github.com/kalcutter/bitshuffle | KCB bitshuffle backend (priority) |
| bitshuffle | https://github.com/kiyo-masui/bitshuffle | Original bitshuffle backend (fallback) |

### C Source Files

| File | Origin | Changes |
|------|--------|---------|
| `src/bs_master.c` | master compilation unit | Generated by `generate_bslz4.py`; includes path+engine+backend selection |
| `src/bs_sparse_tmpl.c` | template for basic sparse decompress | Uses `DATATYPE`, `KERNEL_FN` macros |
| `src/bs_sparse_csc_tmpl.c` | template for CSC sparse decompress | Uses `DATATYPE`, `CSC_DATA_T`, `CSC_SUM_T`, `KERNEL_CSC_FN` macros |
| `src/bs_functions.h` | NEW, generated | Forward declarations for c2py23 to see template-generated functions |

### Multi-ISA Compilation

`bs_master.c` compiled 12x with `-DKERNEL_SUFFIX=_<backend>_<isa>`:

```
gcc -DKERNEL_SUFFIX=_kcb_avx512 -mavx512f -DUSE_KCB   -> bslz4_u16_kcb_avx512()
gcc -DKERNEL_SUFFIX=_kcb_avx2   -mavx2    -DUSE_KCB   -> bslz4_u16_kcb_avx2()
gcc -DKERNEL_SUFFIX=_kcb_sse42  -msse4.2  -DUSE_KCB   -> bslz4_u16_kcb_sse42()
... plus BS backend, ZSTD engine variants
```

The mask/loop in bshuf.c auto-vectorizes at the given ISA level.
KCB's `bitshuffle.c` and LZ4's `lz4.c` are compiled once each.
KCB has internal `ifunc` dispatch for its own SIMD selection.

### c2py23 Variant Dispatch

Two-level dispatch per function (6 functions x 2 backends):

Level 1: bit-width (uint8, uint16, uint32) -- per-call buffer check
Level 2: ISA + backend -- resolved at init time

```yaml
- py_sig: "bslz4_uint16(compressed: buffer, mask: buffer,
             out: buffer, outP: buffer, thresh: int) -> int"
  c_overloads:
    - when: "compressed.format == 'B' and mask.format == 'B' and out.format == 'H' and outP.format == 'I'"
      map: {compressed: "compressed.ptr", cmpN: "compressed.shape[0]", ...}
      group: bslz4_uint16
      variants:
        - name: "kcb_avx512"
          sig: "int bslz4_uint16_t_kcb_avx512(...)"
          when: "c2py_amd64_avx512f"
        - name: "kcb_avx2"
          sig: "int bslz4_uint16_t_kcb_avx2(...)"
          when: "c2py_amd64_avx2"
        - name: "kcb_sse42"
          sig: "int bslz4_uint16_t_kcb_sse42(...)"
        - name: "bs_avx512"
          sig: "int bslz4_uint16_t_bs_avx512(...)"
          when: "c2py_amd64_avx512f"
        - name: "bs_avx2"
          sig: "int bslz4_uint16_t_bs_avx2(...)"
          when: "c2py_amd64_avx2"
        - name: "bs_sse42"
          sig: "int bslz4_uint16_t_bs_sse42(...)"
```

### KCB ifunc Discussion (open)

KCB's `bitshuffle.c` uses `__attribute__((ifunc))` for internal dispatch
(SSE2/AVX2/AVX-512) across 11 internal functions. Options:
1. Keep KCB's ifunc as-is; compile bitshuffle.c once; our dispatch at bslz4 level
2. Port KCB's ifunc up one level: compile bitshuffle.c 3x with ISA flags,
   removing ifunc and using `KERNEL_FN`-style renaming

Option 1 is implemented first for simplicity. Option 2 gives explicit control
and consistent architecture with the rest of the codebase.

### Python API (c2ImageD11/bslz4.py)

Port of `src/__init__.py` from bslz4_to_sparse. Functions import from
`_cImageD11` instead of f2py module. h5py imported lazily.

### Build System Changes

- Add `lz4/lib/lz4.c`, `kcb/src/bitshuffle.c`, `bitshuffle/src/bitshuffle_core.c`,
  `bitshuffle/src/iochain.c` to SOURCES
- Add include dirs for submodule headers
- Compile `bslz4_to_sparse.c` 3x for ISA variants (like SIMD kernels)
- Add `-DUSE_KCB` to KCB compilation, `-DBSLZ4_BACKEND=bs` to bitshuffle
- Rename KCB functions via `-DKERNEL_SUFFIX=_kcb` when compiling with KCB,
  and bitshuffle functions via `-DKERNEL_SUFFIX=_bs` when compiling with bitshuffle

### Tests

- `tests/test_bslz4.py`: buffer-level tests (no h5py needed) + equivalence
  tests against original bslz4_to_sparse (with h5py/hdf5plugin skip markers)
- Port `test_vs_hdf5plugin.py` and `test_dot.py` with pytest.importorskip

### Remaining Open Questions

- MSVC / Windows: KCB's ifunc won't work; need `-DBITSHUF_USE_IFUNC=0` on MSVC.
  Original bslz4_to_sparse already supports this.
- ImageD11 `cImageD11.py` update: after extensive testing, add `try: from
  c2ImageD11.bslz4 import chunk2sparse; except ImportError: ...` pattern
- Vector sparse masking: the mask loop in bshuf.c can be further optimized
  with hand-written SIMD intrinsics (post-MVP)

### Generated Files

All auto-generated by `generate_bslz4.py`:

| File | Contents |
|------|----------|
| `src/bs_master.c` | Template instantiation blocks for all type/engine/backend/ISA combos |
| `src/bs_functions.h` | 180 forward declarations |
| `_cImageD11_bslz4.c2py` | 30 function definitions spliced into main `.c2py` |

### Build Process

The `.c2py` interface file is assembled at build time from two pieces:

| File | Source | Contents |
|------|--------|----------|
| `_cImageD11_base.c2py` | Hand-written | All function definitions except bslz4 |
| `_cImageD11_bslz4.c2py` | Generated by `generate_bslz4.py` | bslz4/bszstd function definitions |

`setup.py` concatenates them before invoking the c2py23 parser:

```python
# In c2py23_build_ext.build_extensions():
with open(C2PY_BASE_FILE) as fb: base = fb.read()
with open(C2PY_BSLZ4_FILE) as fb: bslz4 = fb.read()
with open(C2PY_FILE, 'w') as fout:
    fout.write(base)
    fout.write(bslz4)
module_def = load_c2py(C2PY_FILE)   # parses the assembled file
```

The assembled `_cImageD11.c2py` is gitignored.  Both source files are
checked in, so a fresh clone can build without running the generator.

The generator produces three derived files.  build is triggered via setup.py:

```bash
# 1. Regenerate derived C and .c2py boilerplate (only needed when
#    pixel types or CSC data types change)
python3 generate_bslz4.py

# 2. Build -- setup.py assembles .c2py, then compiles bs_master.c 12x
#    with different -DKERNEL_SUFFIX= / -DUSE_KCB / -DUSE_ZSTD flags
python setup.py build_ext
```

`setup.py:_compile_bslz4_variants()` handles the multi-flag compilation.
No changes to `setup.py` are needed when adding new CSC data types --
only `generate_bslz4.py` needs a line added to the `CSC_TYPES` table.

## Phase IXb: Integer CSC Data Types (Exact Arithmetic)

### Motivation

CSC powder integration uses float32 CSC matrix data and float64 output.
When the CSC matrix is stored as integer weights (uint8/uint16/uint32),
the float multiply-accumulate introduces roundoff error. Using uint64
output and integer arithmetic throughout gives exact results.

### Architecture

The CSC template `bs_sparse_csc_tmpl.c` takes two new preprocessor parameters:

| Macro | Purpose | Float path | Integer path |
|-------|---------|-----------|-------------|
| `CSC_DATA_T` | CSC matrix element type | `float` | `uint8/16/32_t` |
| `CSC_SUM_T` | Histogram accumulation type | `double` | `uint64_t` |

The inner accumulation loop becomes:
```c
output[indices[k]] += ((CSC_SUM_T)data[k]) * (CSC_SUM_T)tmp2[j];
```

Zero-init uses `(CSC_SUM_T)0` which works for both double and uint64.

### Function Naming

| Pixel | CSC data | CSC output | Function name | Python name |
|-------|----------|-----------|---------------|-------------|
| u8 | float | double | `bslz4_csc_u8_kcb_sse42` | `bslz4_csc_u8` |
| u8 | uint8 | uint64 | `bslz4_csc_u8_cu8_kcb_sse42` | `bslz4_csc_u8_cu8` |
| u8 | uint16 | uint64 | `bslz4_csc_u8_cu16_kcb_sse42` | `bslz4_csc_u8_cu16` |
| u8 | uint32 | uint64 | `bslz4_csc_u8_cu32_kcb_sse42` | `bslz4_csc_u8_cu32` |
| u16 | float | double | `bslz4_csc_u16_kcb_sse42` | `bslz4_csc_u16` |
| u16 | uint8 | uint64 | `bslz4_csc_u16_cu8_kcb_sse42` | `bslz4_csc_u16_cu8` |
| u16 | uint16 | uint64 | `bslz4_csc_u16_cu16_kcb_sse42` | `bslz4_csc_u16_cu16` |
| u16 | uint32 | uint64 | `bslz4_csc_u16_cu32_kcb_sse42` | `bslz4_csc_u16_cu32` |
| ... and so on for u32 pixel type and ZSTD engine |

Legacy float CSC functions (`bslz4_csc_u16`, etc.) are unchanged.

### Python Auto-Dispatch

`c2ImageD11/bslz4.py:chunk2sparseCSC` inspects `csc.data.dtype` at
construction time:
- `np.issubdtype(csc.data.dtype, np.integer)` → integer path: u64 powder
- Otherwise → legacy float path: f64 powder

```python
self.fun, powder_dtype = _get_csc_function(dtype, csc.data.dtype)
self.powder = np.empty(nbins, dtype=powder_dtype)
```

All function lookup is via `getattr(_m, fn_name)` — no manual import list.

### Code Generator

`generate_bslz4.py` produces three files from a single configuration table:

| Output | Purpose | Est. lines |
|--------|---------|-----------|
| `src/bs_master.c` | C template include blocks (12 CSC includes per pixel type) | ~196 |
| `src/bs_functions.h` | Forward declarations (180 functions) | ~578 |
| `_cImageD11_bslz4.c2py` | c2py23 function definitions (30 Python funcs) | ~1066 |

Run `python3 generate_bslz4.py` to regenerate. `_cImageD11.c2py` is then
built by concatenating: `head -n 1415 _cImageD11.c2py + _cImageD11_bslz4.c2py`.

Generator configuration: 3 pixel types × 4 CSC data types × 2 engines ×
2 backends × 3 ISAs. All loops are data-driven; adding a new CSC data type
requires one line in the `CSC_TYPES` table.

### Tests

39 tests in `tests/test_bslz4.py`:
- `TestIntegerCSCSmoke` (36): smoke + wrong-type rejection for all 18 combos
- `TestIntegerCSCExact` (3): u16 pixel data with u8/u16/u32 CSC, verified
  against uint64 Python reference
- `TestChunk2sparseCSCInt` (2): auto-dispatch yields correct powder dtype
