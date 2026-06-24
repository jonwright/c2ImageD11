# c2ImageD11 -- Agent Guide

## Project Purpose

Port ImageD11's C extensions from f2py to **c2py23**, producing a standalone
shared library `_cImageD11.so` that can be distributed like a ctypes library
(copy the `.so` into the Python package directory).

All C functions are exposed directly by c2py23's generated wrapper -- no
hand-written adapter code.

## Current Status

- Meson (in `lib/`) builds `_cImageD11.so` directly via `shared_module()`
- c2py23 v0.2.0 handles fixed-width integer types and multi-dimensional
  arrays (`double[3][3]`, `double[][3]`) natively
- 56 tests pass (7 buffer + 49 equivalence including ImageD11 f2py comparison)
- Performance at parity with ImageD11 (e.g. `compute_geometry` 0.97x of f2py at n=200)
- Tested on Python 3.12; targets Python 2.7-3.14

## Language Choices

- **C**: C99, compiled with `-O3 -ffast-math -fopenmp`
- **c2py23**: Code generator for CPython C extensions from YAML interface files
- **Python**: Must parse on Python 2.7 **and** 3.x -- no f-strings, no type
  annotations, no `async`/`await`, no keyword-only arguments

### Python 2.7 polyglot rules

Every `.py` file starts with:
```python
from __future__ import absolute_import, division, print_function, unicode_literals
```

Avoid (Python 3-only):
- f-strings (`f"hello {name}"`)
- Type annotations (`def foo(x: int) -> str:`)
- `async` / `await`
- `nonlocal`, `yield from`
- Keyword-only arguments (`def foo(*, bar):`)
- `{**d}`, `[*l]` unpacking syntax
- `pathlib`, `concurrent.futures`, `unittest.mock`

Use `.format()` or `%` for string formatting.

Strings: prefer `u"unicode"` for text (no-op on 3.x), `b"bytes"` for raw bytes.

File I/O: `import io; io.open("file.txt", "r", encoding="utf-8")`.

`class Foo(object):` (explicit `object` base for new-style classes on 2.7).

## Directory Structure

```
c2ImageD11/
  AGENTS.md              # This file
  README.md
  pyproject.toml
  setup.py               # Stub (two-tier build deferred)
  MANIFEST.in            # Needs update (deferred)
  .gitignore

  lib/                   # Meson build root
    meson.build          # Builds _cImageD11.so; single source of truth
                         # for C source/header lists
    interface/           # GENERATED -- checked into git to break
      _cImageD11.c2py      # c2py23 dependency on normal builds.
      _cImageD11_wrapper.c # Regenerate with: ninja -C build/libc2ImageD11 regenerate
      c2py_runtime.c
      c2py_runtime.h
      c2py_amd64.h
      c2py_arm64.h
      c2py_ppc64.h
    src/                 # All C source files
      core/              # cImageD11.h, cimaged11utils.c, ImageD11_cmath.h
      geometry/          # cdiffraction.c, closest.c
      imageproc/         # blobs.c, connectedpixels.c, darkflat.c,
                         #   localmaxlabel.c, sparse_image.c, splat.c

  c2ImageD11/            # Python package
    __init__.py          # Re-exports C functions, OpenMP safety, constants
    _constants.py        # Blob property enum values from blobs.h
    _cImageD11.so        # Built .so (copied from build/)
    csc_convert.py       # pyFAI CSC conversion utility

  tests/
    test_buffer.py       # Lightweight numpy buffer protocol tests
    test_equivalence.py  # Equivalence vs ImageD11._cImageD11
    benchmark_timing.py  # c2py23 vs f2py timing comparison
    conftest.py          # Pytest config (empty)

  tools/
    harvester.py         # Regenerates lib/interface/ from C sources + c2py23
    strip_c2py.py        # Removes C2PY_BLOCKs to verify C code unchanged
    test_build_once.sh   # Legacy CI helper (needs apptainer)
```

## Interface regeneration: CI vs Release

The `lib/interface/` files (`_cImageD11.c2py`, `_cImageD11_wrapper.c`,
c2py_runtime.*, c2py_amd64.h) are GENERATED from C2PY_BEGIN blocks in
C sources by `tools/harvester.py`.  They are **checked into git** so
that release/sdist builds do NOT need c2py23.

**Release / sdist build**: uses pre-generated files in `lib/interface/`.
No c2py23 needed.  `meson setup && ninja` -> `_cImageD11.so`.

**CI build**: regenerates from C sources to catch upstream breakage.
Requires c2py23.  The CI runs `python3 tools/harvester.py --output-dir lib/interface`
BEFORE `meson setup`, overwriting the pre-generated files.  If c2py23
changes break generation, CI catches it at build time.

**Local development**: to regenerate after editing C2PY_BEGIN blocks:
```bash
python3 tools/harvester.py --output-dir lib/interface
# or: cd build/libc2ImageD11 && ninja regenerate-interface
```

This is confusing because the same files are both checked in (for release)
and overwritten (for CI).  Think of the git-checked-in files as the
"known good" baseline for release builds, and the CI overwrites them
to validate that the C2PY_BEGIN blocks are correct and c2py23 still
generates from them.

## Build

A normal build needs only meson + ninja + a C compiler.  The generated
files in `lib/interface/` are checked into git, so c2py23 is **not**
required to build from a released source tree.

```bash
# Configure once, build many times
mkdir -p build/libc2ImageD11
cd build/libc2ImageD11
meson setup ../../lib
ninja
cp _cImageD11.so ../../c2ImageD11/
```

## Wheel

Build the `.so` with meson (see Build), then run inside a manylinux container:

```bash
python3 setup.py bdist_wheel
pip install auditwheel
auditwheel repair --plat manylinux2014_x86_64 dist/*.whl -w wheelhouse/
```

Output is in `wheelhouse/` -- e.g. `c2imaged11-0.2.0-py3-none-manylinux2014_x86_64.whl`.

The manylinux container sets the platform tag; `auditwheel repair` applies it.
The `.so` binary works across Python 2.7-3.14 (c2py23 emits both
`init_cImageD11` and `PyInit__cImageD11`). The `__init__.py` loader detects
the Python version and uses `imp.load_dynamic` (Py2) or `importlib` (Py3).

The wheel includes an arch-named `.so` (e.g. `_cImageD11_x86_64.so`).
The loader picks the right one via `platform.machine()` at import time.

## Regenerate `lib/interface/`

Run this whenever a C2PY_BLOCK is added/changed in a C source file, or
when c2py23 is updated with new runtime/features (requires c2py23):

```bash
python3 tools/harvester.py --output-dir lib/interface
```

This runs `tools/harvester.py` which:
1. Walks `lib/src/`, finds all `.c` files
2. Extracts `/* C2PY_BEGIN ... C2PY_END */` blocks from each
   and assembles `lib/interface/_cImageD11.c2py`
3. Copies `c2py_runtime.c`, runtime headers from the installed
   c2py23 package into `lib/interface/`
4. Runs `c2py23.cli generate` to produce `lib/interface/_cImageD11_wrapper.c`

After regeneration, rebuild:

```bash
cd build/libc2ImageD11 && ninja && cp _cImageD11.so ../../c2ImageD11/
```

## Test

```bash
python3 -m pytest tests/
```

## Distribution Model (future)

The `.so` is a CPython extension built without Python.h (c2py23's runtime
uses dlopen internally). It will be distributed as a single `.so` file
placed in `c2ImageD11/` -- the same pattern as a ctypes library.

A two-tier build (meson produces `.a` + setuptools links `.so` for `pip install`)
is deferred.

## Deferred Work

### SIMD / Type Dispatch Architecture

**Design decisions (not yet implemented):**

- **Three dispatch axes:** type (f32 vs f64), ISA (SSE4.2/AVX2/AVX-512), kernel variant.
  Type dispatch is the first axis to solve. ISA dispatch comes after.
- **Functions as a tree:** each function is a directory. Context lives at the leaf.
  `C2PY_BEGIN` blocks in `.c` files (current pattern) remain the single source of truth
  for the interface -- when you change C code, the YAML is right above it.
- **Variants are leaves:** each variant directory has `.h` (ABI declaration) + `.c` or `.S`.
  The reference implementation lives alongside its `C2PY_BEGIN` block. Variants carry
  the same ABI.
- **ISA from binary scan, not manual tag:** the build scans each `.o`/`.S` for
  instruction encoding bytes and infers the required ISA level (e.g. `c2py_amd64_avx2`).
  No human writes `-mavx2` in a manifest. This prevents illegal instruction crashes
  from mismatched human-entered tags.
- **Assembly format:** Intel syntax (NASM, or gcc `-masm=intel`) for LLM readability.
  NASM assembles to `.o` which links into the same `.so` regardless of source language.
- **C++ templates for type dispatch:** one C++ template per algorithm instantiated
  for float32/float64, exposed via `extern "C"` wrappers. c2py23 only sees the extern
  C ABI -- type dispatch happens at the c2py23 `when: "format == 'd'"` / `"format == 'f'"`
  level (already supported).
- **LLM agent driven compiler workflow:** compile kernels with multiple compilers/flags,
  capture assembly, measure performance, have LLM read and analyze the assembly, select
  winning variants. Winners are checked in as `.o` files.
- **Pilot function:** `score_and_refine` -- most used function (refinegrains.py, indexing.py).
  Always has a float32 vs float64 question (indexing vs strain refinement) and a SIMD question.
- **Infrastructure:** c2py23 already supports grouped variant dispatch (`polysimd.c2py`
  example), CPU feature detection (cpuid in `c2py_runtime.c`), `_rebind_` / `_variants_`
  for runtime introspection, and per-variant perf counters. Build system needs multi-flag
  compilation support (compile same `.c` with different `-m` flags), which meson supports.
- **Context locality:** functions live in `functions/<name>/` directories with their own
  YAML, reference source, variant kernels, tests, and benchmarks. LLM sessions focus on
  one function's local context, not the whole project.

### Completed (since last AGENTS update)

- **OpenMP `if()` thresholds:** `compute_geometry` and `compute_gv` in `lib/src/geometry/cdiffraction.c`
  use `#pragma omp parallel for if(n > 5000)` to avoid thread-pool overhead on small workloads
  while still parallelizing large arrays.
- **Perf counter reset:** `c2py_perf_reset()` added to `c2py_runtime.h`, `reset_perf()` added to
  `c2py23.perf`. Benchmark uses it for clean per-batch measurements.
- **Benchmark warmup fixed:** timing disabled during warmup, `reset_perf()` called before timed
  batch. No contamination from cold-start thread pool creation or previous runs.
- **Compute geometry parity:** at n=200, c2py at 0.97x of f2py. With `if(n > 5000)` the
  overhead-free serial path matches ImageD11 performance.

### Remaining Deferred
