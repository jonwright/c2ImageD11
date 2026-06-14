# c2ImageD11 - Migration & Refactoring Plan

## Status

- [x] Phase I-IV: Repo structure, C source copy, .c2py interface, Python wrapper, setup.py
- [x] Phase 1: Bug fixes (clean diffs for upstream submission)
- [ ] Phase 2: Type-generic refactoring (C preprocessor #include template pattern)
- [ ] Phase 3: SIMD versioning (per-ISA impl files, runtime dispatch via c2py23)
- [x] Phase 4: c2py23 integration and build
- [x] Phase 5: Testing vs ImageD11._cImageD11
- [x] Phase 6: CI

## Phase 1: Bug Fixes

Each fix is a standalone git commit with a clear message, suitable for
submission to ImageD11.

| ID | File | Line | Bug | Fix |
|----|------|------|-----|-----|
| F1 | closest.c | 425 | Inner loop increments `i` not `j`; R,H,UB partially uninitialized | `i++` → `j++` |
| F2 | sparse_image.c | 1015-1016 | AVX-512 row/col uses chunk start `p` instead of `(p+bit)` | Use `(p+bit)` |
| F3 | closest.c | 195 | `best = 99.` magic number; no match if all distances ≥ 99 | `best = DBL_MAX` |
| F4 | connectedpixels.c | 364 | `assert("I am not here!")` — string literal always truthy | `assert(0 && "unreachable")` |
| F5 | blobs.c | 239 | `S = realloc(S, ...)` clobbers S on failure | Use temp variable |
| F6 | darkflat.c | 416 | `ostep = nhist / (high - low)` — div by zero if high==low | Add guard |
| F7 | closest.c | 647,652,656 | `1.0/sqrt(0)` when g-vector is zero → NaN | Add zero-guard |
| F8 | sparse_image.c | 864-872 | Three `if` instead of `if/else if/else if` | Use else if |
| F9 | connectedpixels.c | 9-18 | `boundscheck` calls `exit(0)` | Change to `return` |

## Phase 2: Type-Generic Refactoring

Use C preprocessor `#include` template pattern (inspired by ffmpeg/BLAS).

Pattern: a `_tmpl.h` header is parameterized by `#define`d macros (PIXEL_TYPE,
FUNC_SUFFIX, etc.) and `#include`d from per-type `.c` files.

```c
// src/algo/connectedpixels_f32.c
#define PIXEL_TYPE float
#define FUNC_SUFFIX _f32
#include "connectedpixels_tmpl.h"
```

Type-generic targets:

| Function | Input types | Template | Per-type files |
|----------|-------------|----------|----------------|
| connectedpixels | f32, u8, u16, u32 | connectedpixels_tmpl.h | 4 |
| localmaxlabel | f32, u8, u16, u32 | localmaxlabel_tmpl.h | 4 |
| sparse_connectedpixels | f32, u8, u16, u32 | sparse_connectedpixels_tmpl.h | 4 |
| sparse_localmaxlabel | f32, u8, u16, u32 | sparse_localmaxlabel_tmpl.h | 4 |
| blobproperties | f32, u16 | blobproperties_tmpl.h | 2 |
| sparse_blob2Dproperties | f32, u16 | sparse_blob2Dproperties_tmpl.h | 2 |
| sparse_smooth | f32 | sparse_smooth_tmpl.h | 1 |
| tosparse_* | u16, u32, f32 | tosparse_tmpl.h | 3 |
| reorder_* | u16+f32 scatter/gather | reorder_tmpl.h | 4 |
| array_stats | f32, f64 | array_stats_tmpl.h | 2 |
| array_mean_var_* | f32, f64 | array_mean_var_tmpl.h | 2 |
| uint16_to_float_* | u16→f32 | convert_tmpl.h | 1 |

## Phase 3: SIMD Versioning

Per-ISA implementation files dispatched at runtime via c2py23 `when:` conditions.

```
src/algo/
  tosparse/
    tosparse_u16_scalar.c
    tosparse_u16_avx2.c
    tosparse_u16_avx512.c
  connectedpixels/
    connectedpixels_f32_scalar.c
    connectedpixels_f32_avx2.c
  uint16_to_float/
    darksub_scalar.c
    darksub_avx2.c
    darksub_avx512.c
```

Dispatch via c2py23:
```yaml
c_overloads:
  - sig: "int tosparse_u16_avx512(...)"
    when: "cpu_has_avx512"
  - sig: "int tosparse_u16_avx2(...)"
    when: "cpu_has_avx2"
  - sig: "int tosparse_u16_scalar(...)"
    when: "1"
```

## Target Directory Layout (end state)

```
src/
  algo/
    connectedpixels/
      connectedpixels_tmpl.h
      connectedpixels_f32_scalar.c
      connectedpixels_f32_avx2.c
      connectedpixels_u16_scalar.c
      connectedpixels_u8_scalar.c
    localmaxlabel/
      localmaxlabel_tmpl.h
      localmaxlabel_f32_scalar.c
      localmaxlabel_u16_scalar.c
    sparse/
      sparse_connectedpixels_tmpl.h
      sparse_connectedpixels_f32_scalar.c
      sparse_localmaxlabel_tmpl.h
      sparse_blob2Dproperties_tmpl.h
      sparse_smooth_tmpl.h
    convert/
      tosparse_tmpl.h
      tosparse_u16_scalar.c
      tosparse_u16_avx2.c
      tosparse_u16_avx512.c
      tosparse_u32_scalar.c
      tosparse_f32_scalar.c
      convert_tmpl.h
      darksub_scalar.c
      darksub_avx2.c
    reorder/
      reorder_tmpl.h
      reorder_u16_scalar.c
      reorder_f32_scalar.c
    stats/
      array_stats_tmpl.h
      array_stats_f32_scalar.c
      array_mean_var_tmpl.h
  core/
    cImageD11.h
    blobs.h / blobs.c
    closest.c
    cdiffraction.c / cdiffraction.h
    ImageD11_cmath.h
    splat.c
    cimaged11utils.c
```

## Blockers

- c2py23: Fixed-width types, optional params, docstrings, constants — COMMITTED
- c2py23: CPU feature detection for SIMD dispatch — NOT YET
- c2py23: Per-function timing — IMPLEMENTED (timing: true in .c2py)

## Recent Achievements

- 58 functions ported from f2py to c2py23, all producing identical results
- 9 bugs fixed with clean diffs (submittable to ImageD11 upstream)
- Optional parameter defaults for 6 functions
- c2py23 CLI extended with CC/CFLAGS/LDFLAGS/LIBS env vars
- setup.py with pip install -e . support
- Timing instrumentation enabled (c2py23.perf)
- Equivalence test suite covering 40+ functions
- GitHub Actions CI across Python 2.7-3.14
