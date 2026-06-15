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
  PLAN.md                     # Migration & refactoring roadmap
  _cImageD11.c2py             # c2py23 interface definition (~40 functions)
  setup.py                    # Build with c2py23
  pyproject.toml              # Minimal
  run_ci.sh                   # Single-version local CI (mirrors GHA steps)
  run_ci_all.sh               # Multi-version CI via snakepit Apptainer containers
  src/                        # Copied C sources from ImageD11/src
    cImageD11.h               # Platform macros, DLL visibility
    blobs.h                   # Disjoint set, NPROPERTY enums
    blobs.c                   # Disjoint set, blob moments
    cdiffraction.h            # Vector/matrix macros
    cdiffraction.c            # compute_geometry, compute_gv, etc.
    cimaged11utils.c          # omp_set_num_threads, my_get_time
    closest.c                 # verify_rounding, closest, score, etc.
    connectedpixels.c         # connectedpixels, blobproperties
    darkflat.c                # uint16_to_float, frelon_lines, reorder, bgcalc
    localmaxlabel.c           # localmaxlabel
    sparse_image.c            # mask_to_coo, sparse_*, tosparse_*
    splat.c                   # splat
    ImageD11_cmath.h          # Alternative math macros
  src_wrapper/
    _wrappers.c               # 2D-array-to-flat-pointer wrappers (vec[3], double[][N])
  c2ImageD11/
    __init__.py               # Pure Python: imports .so, exports constants
    _constants.py             # Blob property enum values (hardcoded)
  tests/
    test_buffer.py            # Lightweight numpy buffer-interface tests
    test_equivalence.py       # Equivalence tests vs ImageD11._cImageD11
    test_all.py               # Multi-version orchestrator (Apptainer)
    benchmark_timing.py       # c2py23 vs f2py timing comparison
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
The ~15 remaining wrappers cover score, misori_*, compute_*, and splat.

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

### Local CI (pre-push)
```bash
bash run_ci.sh          # Single Python version, ~30s
bash run_ci_all.sh      # All 8 Python versions via Apptainer, ~5min
```

Both scripts must pass before pushing. `run_ci.sh` creates a clean venv,
installs c2py23 from a sibling directory, builds c2ImageD11, installs
ImageD11 from git head with `--no-deps`, and runs the full test suite.

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

## Notes

- The c2py23 runtime (c2py_runtime.h/.c) must be built alongside.
  The `c2py23 build` command handles this.
- OpenMP: compile with `-fopenmp`. The GIL is held during calls
  (c2py23 doesn't release it yet). OpenMP threading within a single
  call still works.
- malloc/free: The restriction in c2py23 docs is relaxed for this project.
  blobs.c, sparse_image.c, connectedpixels.c allocate/free internally.
- CI uses `--no-build-isolation` because c2py23 is not on PyPI.
  c2py23 must be installed before building c2ImageD11.
- Python compatibility: targets 2.7-3.14. The c2py_runtime uses dlopen
  to resolve CPython API, so one .so binary works across versions.
  Build on the oldest target OS for maximum portability.
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
