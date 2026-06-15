# c2py23 Improvement Requests

Feedback from porting ImageD11's 58 C functions from f2py to c2py23.
Covering safety, usability, and features needed for Phase 2/3 of the migration.

**Status:** 7 of 9 implemented. 2 items remain: SIMD dispatch (#7), build-isolation (#9).

---

## Safety

### 1. Parameter count validation at codegen time — DONE

**Severity: Critical**  |  Real bug hit

The .c2py C signature and the actual C function signature can diverge silently.
The `bloboverlaps` C function takes 9 parameters but the .c2py C sig had 8
(missing `verbose`). The generated wrapper compiled fine and produced undefined
behavior at runtime — `ns` landed in `verbose`'s slot, `nf` became `ns`, and
`nf` was garbage from the stack.

**Request:** Compare the parameter count in the .c2py C signature against the
actual C function declaration (from the header or .c file). Emit a hard error
at codegen time if they don't match. At minimum, emit a warning.

**Resolution:** Done. c2py23 parser.py `_validate_module()` parses C source
files, extracts function param counts, and raises `ValueError` on mismatch.

### 2. Compile-time validation of buffer format vs C type — DONE

**Severity: High**

The `checks:` section in .c2py verifies buffer formats at runtime
(e.g. `labels1.format == 'i'`). If the check doesn't match the C type,
there's no compile-time warning. The generated code passes `int32_t *b1`
through an `int *` cast, which works on platforms where `int` == `int32_t`
but is not portable.

**Request:** Map buffer format checks to corresponding C types and warn if the
C function prototype uses a different-width type (e.g. `int32_t*` vs `int*`).

**Resolution:** Done. c2py23 `_validate_module()` maps format chars to C types
via `_FORMAT_TO_CTYPE` and raises `ValueError` on type-width mismatches.

---

## Usability

### 3. Direct support for fixed-width integer types — DONE

**Severity: High**  |  43 thin wrappers removed, ~300 LOC deleted

c2py23 now natively supports `uint16_t*`, `int32_t*`, `uint8_t*`, `int8_t*`,
`int64_t*`, `uint32_t*`, `int16_t*`, `uint64_t*` directly in C signatures.
Removed all thin type-adapting wrappers from `_wrappers.c` (~300 lines).
The .c2py interface now calls original C functions directly with correct types.

### 4. Handle integer literal map values — DONE

**Severity: Medium**

c2py23 now accepts bare integer literals in map values (e.g. `verbose: 0`).
No more quoting workaround needed.

### 5. Better buffer check error messages — DONE

**Severity: Medium**

When a buffer format check fails, the error is:
```
ValueError: check failed: labels1.format == 'i'
```
This doesn't tell the user what format was actually found, making debugging
difficult. The user has to add debug prints to discover the actual format.

**Request:** Include the actual value in check failure messages:
```
ValueError: check failed: labels1.format == 'i' (got 'l')
```

**Resolution:** Done. Generator now includes actual runtime values in check
failure messages (e.g. `got format='l'`, `got 5 vs 3`).

### 6. Output scalar convention option — DONE

**Severity: Low**  |  Useful for migration

f2py returns output scalars as tuple elements:
```python
minval, maxval, mean, var = old.array_stats(img)
```

c2py23 writes into 1-element buffers:
```python
mn = np.zeros(1, dtype=np.float32)
mx = np.zeros(1, dtype=np.float32)
new.array_stats(img, mn, mx, me, va)
```

The equivalence tests need ~20 lines of boilerplate per function to bridge
this gap. A c2py23 mode that auto-allocates and returns 1-element buffers as
scalar return values would simplify testing and migration.

**Request:** Option to annotate `intent(out)` scalar parameters in the C sig
so c2py23 returns them as Python return values, matching f2py behavior.

**Resolution:** Done. `outputs:` key on C overloads. c2py23 auto-allocates
1-element variables, passes pointers to C, returns tuple. See
`tests/cases/scalar_output/`.

---

## Features

### 7. CPU feature detection for SIMD dispatch

**Severity: Medium**  |  Phase 3 blocker (PLAN.md)

PLAN.md Phase 3 requires runtime dispatch to per-ISA implementations
(scalar, AVX2, AVX-512). The proposed syntax:
```yaml
c_overloads:
  - sig: "int tosparse_u16_avx512(...)"
    when: "cpu_has_avx512"
  - sig: "int tosparse_u16_avx2(...)"
    when: "cpu_has_avx2"
  - sig: "int tosparse_u16_scalar(...)"
    when: "1"
```

**Request:** Support `when:` conditions in `c_overloads` with a set of
built-in CPU feature predicates: `cpu_has_avx2`, `cpu_has_avx512`,
`cpu_has_neon`, etc. The condition is evaluated once at module load time.

### 8. Preprocessor template pattern support — DONE

**Severity: Low**  |  Phase 2 nice-to-have (PLAN.md)

PLAN.md Phase 2 uses C preprocessor `#include` templates to generate
type-generic variants. The pattern:
```c
// tosparse_u16.c
#define PIXEL_TYPE uint16_t
#define FUNC_SUFFIX _u16
#include "tosparse_tmpl.h"
```

Each variant needs its own .c2py entry with a different C symbol name.

**Request:** Support for parameterized .c2py function definitions that expand
to multiple variants, similar to a YAML loop/macro. Alternatively, document
the recommended approach for template-based code generation with c2py23.

**Resolution:** Done. `expand:` key with `${VAR}` substitution in c2py23.
Documented in `docs/specification.md`. Tested in `tests/cases/template/`.

---

## Documentation

### 9. Clarify --no-build-isolation interactions

**Severity: Low**

c2py23 currently requires `--no-build-isolation` for pip install because it's
not on PyPI. This flag prevents pip from creating an isolated build
environment, which causes problems when the same environment also needs to
build f2py-based projects (like ImageD11 itself) — the f2py build picks up
absolute paths from the venv numpy install and fails.

**Request:** Document the tradeoffs of `--no-build-isolation`. Consider
publishing c2py23 to PyPI (even as a dev release) so build isolation works
normally, or provide a `pip install c2py23` command that handles this
transparently.

---

## Summary

| # | Request | Severity | Status |
|---|---------|----------|--------|
| 1 | Parameter count validation | Critical | DONE |
| 2 | Buffer format vs C type validation | High | DONE |
| 3 | Direct fixed-width integer types | High | DONE |
| 4 | Integer literal map values | Medium | DONE |
| 5 | Better check failure messages | Medium | DONE |
| 6 | Output scalar convention option | Low | DONE |
| 7 | CPU feature detection (SIMD dispatch) | Medium | OPEN |
| 8 | Template pattern support | Low | DONE |
| 9 | --no-build-isolation docs | Low | DEFERRED |

#7 is the main blocker for Phase 3 SIMD dispatch.
#9 deferred: plan is binary wheels to PyPI (one per platform/arch,
Python-version-independent), eliminating need for build isolation.
