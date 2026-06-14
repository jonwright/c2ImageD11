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
- [x] Phase VI: CI passing
- [ ] Phase VII: Equivalence testing against ImageD11._cImageD11

## c2py23 Features Now Available

All previously-requested c2py23 extensions have been implemented upstream
(see c2py23 commit 95a2076 and later). The .c2py interface file now uses:

  - Fixed-width integer format strings ('H', 'I', 'q', 'b', 'h', 'B') in checks
  - Optional parameter defaults with the `|O$` syntax in py_sig
  - Module-level `constants:` block for integer constant export
  - Custom `doc:` field for function docstrings
  - Per-function performance timing via `timing: true` module flag
  - METH_FASTCALL dispatch on Python 3.12+

The thin wrappers in src_wrapper/_wrappers.c remain necessary for adapting
fixed-size C types to c2py23-compatible buffer handles, but the parser and
generator now handle all expression forms used in _cImageD11.c2py.

## Directory Structure

```
c2ImageD11/
  AGENTS.md                   # This file
  _cImageD11.c2py             # c2py23 interface definition (~40 functions)
  setup.py                    # Build with c2py23
  pyproject.toml              # Minimal
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
    _wrappers.c               # Thin C wrappers adapting fixed-size types
  c2ImageD11/
    __init__.py               # Pure Python: imports .so, exports constants
    _constants.py             # Blob property enum values (hardcoded)
  tests/
    test_buffer.py            # Lightweight numpy buffer-interface tests
    test_equivalence.py       # Equivalence tests vs ImageD11._cImageD11
    test_all.py               # Multi-version orchestrator (Apptainer)
    benchmark_timing.py       # c2py23 vs f2py timing comparison
    conftest.py               # Pytest configuration (empty)
  .github/workflows/
    test.yml                  # CI adapted from ImageD11
```

## Thin Wrapper Pattern

All fixed-size integer types (uint16_t*, int32_t*, etc.) are adapted via
thin C wrappers that use c2py23-compatible types (char*, int*):

```c
// Original: int mask_to_coo(int8_t msk[], ..., uint16_t i[], ...)
// Wrapper:
int mask_to_coo_wrapper(const char *msk_buf, ..., char *i_buf, ...) {
    return mask_to_coo((int8_t *)msk_buf, ..., (uint16_t *)i_buf, ...);
}
```

The Python caller provides a buffer with the correct PEP 3118 format
('H' for uint16, 'B' for uint8, etc.) and the wrapper casts `char*` → the
actual type. All type-punning through `char*` is valid C (strict aliasing
exception).

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

1. Build c2ImageD11 with `pip install --no-build-isolation -e .` (requires c2py23
   already installed in the environment, since c2py23 is not on PyPI).
2. Run lightweight buffer tests: `python -m pytest tests/ -v -k "TestBuffer"`
3. These verify the build succeeded and numpy buffer protocol calls work
   for a representative subset of functions.
4. For equivalence testing, import both old and new:
   `from ImageD11._cImageD11 import * as old` and
   `from c2ImageD11._cImageD11 import * as new`, then compare outputs.

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
