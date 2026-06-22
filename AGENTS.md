# c2ImageD11 — Agent Guide

## Project Purpose

Port ImageD11's C extensions from f2py to **c2py23**, producing a standalone
shared library `_cImageD11.so` that can be distributed like a ctypes library
(copy the `.so` into the Python package directory).

All C functions are exposed directly by c2py23's generated wrapper — no
hand-written adapter code.

## Current Status

- Meson (in `lib/`) builds `_cImageD11.so` directly via `shared_module()`
- c2py23 v0.2.0 handles fixed-width integer types and multi-dimensional
  arrays (`double[3][3]`, `double[][3]`) natively
- 56 tests pass (7 buffer + 49 equivalence including ImageD11 f2py comparison)
- Tested on Python 3.12; targets Python 2.7–3.14

## Language Choices

- **C**: C99, compiled with `-O3 -ffast-math -msse4.2 -fopenmp`
- **c2py23**: Code generator for CPython C extensions from YAML interface files
- **Python**: Must parse on Python 2.7 **and** 3.x — no f-strings, no type
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
    interface/           # GENERATED — checked into git to break
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

Build the `.so` with meson (see Build), then:

```bash
# Build once, run under each Python version
python3 setup.py bdist_wheel
python2 setup.py bdist_wheel   # if Python 2.7 available
```

Output is in `dist/` — e.g. `c2imaged11-0.2.0-py3-none-manylinux2014_x86_64.whl`.

The `.so` is the same binary for both Python versions (c2py23 emits both
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
placed in `c2ImageD11/` — the same pattern as a ctypes library.

A two-tier build (meson produces `.a` + setuptools links `.so` for `pip install`)
is deferred.

## Deferred Work

- **Two-tier build** (meson `.a` + setuptools `.so` bridge)
- **SIMD dispatch** (SSE4.2/AVX2/AVX-512) for hot-path functions
- **bslz4** bitshuffle-lz4 sparse decompress (was present, removed for clean slate)
- **YAML-in-C comments** single-source-of-truth for c2py metadata
- **Integer CSC types** (uint8/16/32 with uint64 exact arithmetic)
- **CI** (GitHub Actions, multi-version)

All deferred work is tracked in git history on the `new_build_system` branch.
