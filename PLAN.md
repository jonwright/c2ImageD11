# c2ImageD11 - Migration & Refactoring Plan

## Status

- [x] Phase I-IV: Repo structure, C source copy, .c2py interface, Python wrapper, setup.py
- [x] Phase V-VII: Testing, bug fixes, CI
- [x] Phase VIII: SIMD dispatch (SSE/AVX2/AVX-512) for hot-path functions
  (implemented via multi-flag compilation in src_simd/, supersedes Phase 2-3 below)
- [x] Phase IX: bslz4_to_sparse import with multi-backend SIMD dispatch

Superseded proposals (not implemented in this form):
- [x] Phase 2 (type-generic refactoring): superseded by SIMD kernel approach
- [x] Phase 3 (SIMD versioning): superseded by multi-flag compilation in src_simd/

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

## Phase 2-3: Superseded by Phase VIII

The original Phase 2 (type-generic C preprocessor #include template) and
Phase 3 (hand-written per-ISA SIMD files in src/algo/) were superseded by
the AGENTS.md Phase VIII approach: multi-flag compilation of single kernel
files in src_simd/ with auto-vectorization at the compiler level.

## Phase VIII (Actual): SIMD Dispatch

Implemented via multi-flag compilation in src_simd/:
- 16 kernel files, each compiled 3x with -msse4.2/-mavx2/-mavx512f
- Grouped variant dispatch in _cImageD11.c2py with c2py_amd64_* flags
- Rebind API: _rebind_score('avx2') to force a variant
- See AGENTS.md Phase VIII section for full architecture details

## Phase IX (Actual): bslz4_to_sparse Import

bslz4 C extension with KCB/bitshuffle backend dispatch:
- 3 git submodules: lz4, kcb, bitshuffle
- bslz4_to_sparse.c compiled 6x (2 backends x 3 ISAs)
- 6 functions in _cImageD11.c2py with 36 variant signatures
- Python API: chunk2sparse, chunk2sparseCSC, bslz4_to_sparse()
- See AGENTS.md Phase IX section for full architecture details

## Recent Achievements

- 64 Python-callable functions (58 original + 6 bslz4 groups)
- SIMD dispatch for 16 hot-path functions (SSE4.2/AVX2/AVX-512)
- bslz4 import with KCB/bitshuffle dual-backend dispatch
- 53/54 equivalence tests pass vs ImageD11._cImageD11
- 7 buffer-level + 1 equivalence bslz4 tests pass
- 9 bugs fixed with clean diffs (submittable to ImageD11 upstream)
- Optional parameter defaults for 6 functions
- c2py23 CLI extended with CC/CFLAGS/LDFLAGS/LIBS env vars
- setup.py with pip install -e . support
- Timing instrumentation enabled (c2py23.perf)
- GitHub Actions CI across Python 2.7-3.14

## Blockers

- ~~c2py23: CPU feature detection for SIMD dispatch~~ — DONE (commit 645356d)
- ~~c2py23: Fixed-width types, optional params, docstrings, constants~~ — DONE
- c2py23: not on PyPI (requires --no-build-isolation, see c2py23_requests.md #9)
- ImageD11 cImageD11.py: not yet updated to try c2ImageD11 first (planned post-testing)