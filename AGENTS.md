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
- [ ] BLOCKED: c2py23 needs extensions before build will succeed
- [ ] Phase V: Testing (needs build to work)
- [ ] Phase VI: CI (needs build + tests)

## BLOCKERS: c2py23 Extensions Needed

See `/home/worker/C2PY23_REQUESTS.md` for the detailed list.

The .c2py file and thin C wrappers in src_wrapper/_wrappers.c are written to
use ONLY c2py23's current type set ({int, float, double, char}). However,
c2py23's parser currently rejects format strings like 'H', 'I', 'q', 'b' in
checks (the `arr.format == 'H'` pattern) and may not handle all expression
combinations. The c2py23 code generator also needs:
  - Support for format strings beyond 'd', 'f', 'i', 'B'
  - Optional parameter defaults
  - Module-level constant export
  - Docstring support

Once c2py23 is extended, come back and:
1. Run `c2py23 build _cImageD11.c2py` to verify it generates wrapper C
2. Fix any parse errors in the .c2py file
3. Build and install with `pip install -e .`
4. Run equivalence tests

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
    test_equivalence.py       # Test against ImageD11._cImageD11
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

1. Build c2ImageD11 with `pip install -e .`
2. Import both old and new: `from ImageD11._cImageD11 import * as old`
   and `from c2ImageD11._cImageD11 import * as new`
3. For each function F:
   - Generate random, valid inputs matching expected types/shapes
   - Call `old.F(inputs)` and `new.F(inputs)`
   - Compare outputs (arrays: np.allclose; scalars: ==)
4. Also test with real data from ImageD11/test/

## Notes

- The c2py23 runtime (c2py_runtime.h/.c) must be built alongside.
  The `c2py23 build` command handles this.
- OpenMP: compile with `-fopenmp`. The GIL is held during calls
  (c2py23 doesn't release it yet). OpenMP threading within a single
  call still works.
- malloc/free: The restriction in c2py23 docs is relaxed for this project.
  blobs.c, sparse_image.c, connectedpixels.c allocate/free internally.
- Python 2.7: The ImageD11 GitHub Actions test 2.7-3.14. c2ImageD11
  targets 3.8+ for now (ctypes buffer protocol works on 2.7 but
  memoryview.cast(shape) is 3.3+).
