# c2ImageD11 Build System -- High Level Specification

## 1. Motivation

The original cImageD11 package (Jon Wright, 2005-) processes diffraction
data at synchrotron beamlines.  Columnfiles hold up to 1e9 peaks.  The
indexing, geometry, and reconstruction hot paths run in C.  Those C functions
use a single set of compiler flags.  On x86-64 this leaves substantial
throughput on the table:

| ISA level | Vector width (bits) | doubles per op | FMA |
|-----------|--------------------|-----------------|-----|
| SSE2      | 128                | 2               | no  |
| AVX2      | 256                | 4               | yes |
| AVX-512F  | 512                | 8               | yes |

A loop that runs at 4 doubles/cycle on SSE2 could process 8 doubles/cycle
on AVX2 (with FMA) and 16 doubles/cycle on AVX-512F.  The data is there;
the hardware is there; the compiled code is not.

The c2py23 project and this c2ImageD11 port exist to overcome these
limitations, as well as fragmentation of the Python C API and evolution of
the numpy package.  We use the PEP 3118 buffer interface to break the numpy
dependency.

This document specifies the architecture for building and distributing
c2ImageD11 so that:

- compute code can be compiled with any compiler (GCC, Clang, MSVC, ICC,
  ICX, mingw64, future compilers);

## 1a. Implemented Architecture (new_build_system branch, June 2026)

The `new_build_system` branch implements a single-build architecture:

```
meson (one compiler, one build):
  ├── Compile all C sources (compute + vendored + bridge)
  ├── c2py23 generate -> _cImageD11_wrapper.c
  ├── Compile wrapper
  └── shared_module('_cImageD11')
        -> build/libc2ImageD11/_cImageD11.so

setup.py (pure Python, zero compilation):
  └── Copies _cImageD11.so into c2ImageD11/ package
```

Key properties:
- **No Python.h**: c2py_runtime resolves CPython API at load time via
  `dlopen(NULL)` + `dlsym()`.  The `.so` is a plain C dynamic library.
  No `Python.h`, no `-I $(python3-config --includes)`.
- **Single compiler**: meson owns the entire toolchain.  No subprocess
  compiler calls.  No compiler mismatch between static lib and bridge.
- **Setuptools is pure Python**: finds the pre-built `.so`, copies it
  into the package, declares the wheel.  No `Extension()`, no `build_ext`.
- **One `.so` for all Python versions**: c2py_runtime resolves CPython ABI
  at module load, so the same `.so` binary works from Python 2.7 to 3.15+.

The two-tier architecture described below (Section 3) is the design
specification.  The current implementation simplifies it: no separate
static library, meson builds the `.so` directly.  When SIMD ISA variants
and multi-compiler support are re-added (P7), the static library split
may be revisited.
- any SIMD approach can be plugged in (compiler auto-vectorization,
  hand-written intrinsics, NASM/GAS assembly, ISPC);
- multiple implementations of each kernel can be benchmarked against each
  other to understand performance tradeoffs across different data patterns;
- the Python binding stays C99 and portable, working identically across
  Python 2.7 through 3.14+;
- third-party C libraries (KCB, LZ4, Zstd) build on Windows without
  modification;
- the result is distributable as a standard wheel.

The document does not describe implementation details (meson syntax, file locations,
directory layout).  Those belong in the companion document
`doc/build-system-implementation.md` that describes the technical choices we made now.
Any detailed step-by-step actions for an LLM system carrying out changes
will be discarded later. A third document, `doc/build-other-systems.md`,
describes how we expect to adapt the underlying C/C++ code to other build
systems or compilers or new computers when they come.

## 2. Principles

### 2.1 Historical standards

This project is based on the oldest historical standards still in active
use today: C99, Python 2.7-3.x language intersection subset, YAML, and
the PEP 3118 buffer protocol for doing computations from python.
These foundations are expected to remain stable into the future.
We do not follow the most recent standards as they will continue
to evolve, but instead we look for a core subset that is common across
all versions.

### 2.2 Strict C++ subset for compute

Where C++ is used (Tier 1 static library), only a minimal subset
is permitted: templates, `extern "C"` wrappers, `__inline` extensions where
necessary.  No STL, no exceptions, no RTTI, no `new`/`delete`, no `class`.
There are several ways to enforce this and various strong opinions about how
to do it. The goal is keeping code C99-compatible and easy to compile
everywhere. We make the tradeoff that C++ templates are more convenient today
compared to a C99 template + dispatch system.  This keeps the library
compilable with the widest range of compilers and linkable into the widest
range of runtimes.

### 2.3 Assembly

Hand-written assembly is an eventual target for this project, inspired by the FFmpeg
and VLC projects (FFmpeg: The Incredible Technology Behind Video on the Internet | Lex Fridman Podcast #496).
Those projects credit hand-written assembly for their performance and portability.  Our
architecture must accommodate `.asm` / `.S` files in the future.
Today, no one is writing these kernels. In the near future, we suspect LLM
frameworks may be able to outperform current compilers.

## 3. Two-Tier Architecture

The build is split into two completely independent tiers:

```
  Tier 1: libc2ImageD11.a  (static library)
  -------------------------------------------------
  Build:        any build system that produces a static library
  Languages:    C, C++ (strict subset), assembly (NASM/GAS), ISPC
  Compilers:    any (GCC, Clang, ICC, MSVC, mingw64, ...)
  Output:       libc2ImageD11.a  +  c2ImageD11.h

  Contains ALL computation:
    - Reference implementations (C99, portable, no SIMD)
    - Auto-vectorized variants (same source, different -m flags)
    - Hand-written using intel style intrinsics variants (future)
    - Hand-written assembly variants (future)
    - BSLZ4 / KCB / LZ4 / Zstd (vendored dependencies)
    - Disjoint-set, blob moments, sparse image utilities

  Every kernel exposed as an extern "C" function:
    score_gvf64_sse42()
    score_gvf32_avx2()
    compute_gv_f64_avx2()
    compute_gv_f32_avx512()
    blobproperties_f64_avx512()
    bslz4_u16_kcb_avx2()
    ...

  Naming convention:
    <function>_<datatype>_<isalevel>[_<method>_<version>]

                      static link
                           |
                           v

  Tier 2: _cImageD11.cpython-*.so  (Python extension)
  -------------------------------------------------
  Build:        setuptools or any PEP 517 compatible backend
  Language:     C99 only
  Sources:      c2py23-generated wrapper  +  c2py_runtime.c
                +  _wrappers.c (flat/vec pointer adapters)
                +  c2py_amd64.h (CPU feature flags)
  Links:        libc2ImageD11.a (static)

  This is a thin bridge.  It does:
    - CPython buffer protocol acquisition / release
    - Argument parsing and type checking
    - CPU ISA feature check at module init (populates c2py_amd64_* flags)
    - Variant dispatch: select which extern "C" function to call,
      based on data type (per-call) and CPU features (init-time)
    - GIL release / re-acquisition during C calls
    - Performance timing instrumentation

  It does NOT do:
    - Any computation beyond pointer dereferencing
    - Any buffer allocation, copy, conversion, or transpose
    - Any SIMD compilation
    - Any invocation of external compilers (subprocess is banned)
```

### Why two tiers

| Concern | Single-tier (current) | Two-tier |
|---------|----------------------|----------|
| SIMD compilation | setup.py calls subprocess(gcc -mavx512f ...); breaks on MSVC | Meson handles it; setup.py never sees an ISA flag |
| New SIMD method | Rewrite setup.py build hooks | Add a build target; Python extension unchanged |
| Different compilers per source | Not possible (one compiler for the whole .so) | Each source compiled with its preferred compiler |
| KCB on Windows | `__attribute__((ifunc))` rejected by MSVC | mingw64-gcc compiles KCB; MSVC links the .o |
| Python ABI breakage | Whole .so rebuilt | Only thin bridge rebuilt |
| Testing across Python versions | Rebuild per version | Build libc2ImageD11.a once, test with all Pythons |
| Non-Python consumers | Impossible (bound to CPython) | libc2ImageD11.a is a plain C library; callable from any language |

## 4. The Static Library (Tier 1)

### 4.1 Contents

All computation.  Every C file currently in `src/` (geometry, imageproc,
bslz4 plus vendored lz4/kcb/zstd/bitshuffle) lives in the static library.
The only files that stay in the Python extension are:

- c2py_runtime.c / c2py_runtime.h / c2py_amd64.h (CPython API loader)
- The c2py23-generated wrapper (buffer protocol, dispatch, timing)
- _wrappers.c (flat-pointer-to-vec adapters -- pure casts, no computation)

We will re-visit the requirement for _wrappers.c later - it is
probably a design problem that needs to be fixed by an api cleanup.

### 4.2 Dispatch dimensions

c2py23 resolves the correct kernel to call at two levels: per-call
(Layer 1: buffer format, shape, and layout) and init-time (Layer 2:
CPU ISA features).  The total dispatch space is the product of
several independent dimensions:

| Dimension | Layer | Example values |
|-----------|-------|---------------|
| Scalar type (ubi) | 1 (per-call) | `f64`, `f32` |
| Scalar type (gv) | 1 (per-call) | `f64`, `f32` |
| gv layout | 1 (per-call) | `aos` (ng,3), `soa` (3,ng) |
| ISA level | 2 (init-time) | `sse42`, `avx2`, `avx512f` |
| Method | 2 (rebind-only) | `autovec`, `intrin_v1`, `intrin_v2` |

Not all combinations are implemented -- each function earns the
variants that profiling and error analysis justify.

**Type dispatch (f64 / f32)**

gv is a large array of noisy peak positions (centroid fits).  These
positions might not be more precise than the ~23 bits of meaningful
precision in f32.  Storing them as float can halve memory bandwidth
without accuracy loss.

UBI is a compact 3x3 matrix (9 doubles) refined to high precision,
typically kept as double.  Mixed-precision kernels (e.g. `score_gvf32`:
f64 ubi, f32 gv) are natural: the tolerance lives in ubi's type, and
the g-vectors are cast in the inner loop.

**Layout dispatch (AoS / SoA)**

ImageD11 produces g-vectors in AoS layout (shape `(ng,3)`, each row
is a 3-component vector).  Some callers may hold transposed data in
SoA layout (shape `(3,ng)`, each component contiguous).  The memory
access pattern differs -- different vectorization opportunities for
each layout.  The dispatch `when:` condition inspects the buffer shape
at call time:

```yaml
# AoS: (ng, 3)
- when: "gv.ndim == 2 and gv.shape[1] == 3"
  map: {ng: "gv.shape[0]", ...}
  group: score_aos
  variants: [...]

# SoA: (3, ng)
- when: "gv.ndim == 2 and gv.shape[0] == 3"
  map: {ng: "gv.shape[1]", ...}
  group: score_soa
  variants: [...]
```

Each layout requires a separate kernel implementation; the access
pattern within the inner loop differs fundamentally.  Both kernels
accept the same flat `const double* gv` pointer and stride through
the buffer according to their expected layout.

**C++ template implementation (optional)**

For functions with multiple type combinations, C++ templates can
eliminate source-code duplication of the inner loop:

```cpp
template <typename T_UBI, typename T_GV>
int score_aos_impl(const T_UBI* ubi, const T_GV* gv,
                   T_UBI tol, intptr_t ng) {
    T_UBI atol = tol * tol;
    int n = 0;
    #pragma omp parallel for reduction(+:n)
    for (intptr_t k = 0; k < ng; k++) {
        const T_GV* g = gv + k * 3;
        T_UBI h0 = (T_UBI)ubi[0] * (T_UBI)g[0]
                 + (T_UBI)ubi[1] * (T_UBI)g[1]
                 + (T_UBI)ubi[2] * (T_UBI)g[2];
        T_UBI h1 = h0 - floor(h0);
        if (h1 < atol || h1 > (T_UBI)1 - atol) n++;
    }
    return n;
}
```

Instantiated via `extern "C"` and compiled at each ISA level:

```cpp
extern "C" {
  int score_aos_f64_avx2(const double* ubi, const double* gv, double tol, intptr_t ng) {
      return score_aos_impl<double, double>(ubi, gv, tol, ng);
  }
  int score_aos_f32_avx2(const double* ubi, const float* gv, double tol, intptr_t ng) {
      return score_aos_impl<double, float>(ubi, gv, tol, ng);
  }
}
```

Naming convention: `<function>_<layout>_<datatype>_<isalevel>`.
Example: `score_aos_f64_avx2`, `score_soa_f64_avx2`.
Where layout is unambiguous or only one is implemented, the layout
tag may be omitted (defaults to AoS).

**Scope of f32 support:** Each function requires careful error analysis.
Peak assignment (score, compute_gv) has very different precision requirements
from strain refinement (misori, refine_assigned).  The former is a counting
problem where ~23 bits is ample; the latter accumulates small differences
over many peaks and demands higher precision.  f32 variants are added on a
case-by-case basis after benchmarking validates both performance and accuracy
against the f64 reference.

### 4.3 Memory allocation

Some kernels allocate memory internally:

- `blobs.c`: the disjoint-set (dset) uses `calloc`, `realloc`, and `free`.
  Callers (`connectedpixels.c`, `sparse_image.c`) are also inside the static
  library.  They allocate via `dset_initialise`, receive results via
  `dset_compress`, and free both sets.  All malloc/free pairs are internal
  to the static library.

- `connectedpixels.c`: allocates temporary `link` and `T` arrays, frees
  them before returning.  Outputs go into caller-provided buffers.

The contract is: **caller provides output buffers; callee writes into them.**
No pointer to allocated memory crosses the boundary to the Python bridge.
The Python bridge never receives a pointer it must free.  This works across
compiler boundaries on all platforms.

### 4.4 Third-party dependencies (KCB, LZ4, Zstd)

These are git submodules in `src/bslz4/vendor/`.  They are compiled as part
of the static library.

**KCB on Windows:** KCB's `bitshuffle.c` uses `__attribute__((ifunc))` for
internal SIMD dispatch (which already works well).  This is a GCC/Clang
extension; MSVC does not support it.  We compile KCB with **mingw64-gcc**
on Windows.  Clang (with `-target x86_64-windows-msvc`) and the Intel
compiler are also options.  The resulting `.o` file is a standard COFF
object that links into the static library alongside MSVC-compiled objects.
No KCB source changes are required.

## 5. The Python Extension (Tier 2)

### 5.1 Responsibilities

The Python extension is a thin, C99 bridge.  Its responsibilities:

1. Expose CPython module -- method table, module init, constants
2. Parse Python arguments -- extract buffer objects, validate types and
   dimensions
3. Acquire buffer protocol -- `PyObject_GetBuffer`, released after the call
4. Check CPU ISA features at module init -- `c2py_runtime_init()` probes
   cpuid on x86_64, sets `c2py_amd64_avx512f` etc.  These are the same
   globals used in the `.c2py` yaml `when:` conditions to dispatch variants
5. Dispatch to the correct kernel -- select which `extern "C"` function
   from libc2ImageD11.a to call, based on buffer format (per-call) and
   CPU features (pre-resolved at init time)
6. Release / re-acquire the GIL -- for long-running C calls
7. Record performance timing -- c2py23's `c2py_perf_t` instrumentation
8. Return results -- convert C return values to Python objects (int,
   float, None)
9. Provide `_rebind_<name>()` -- allow Python to override variant dispatch
   at runtime (force a specific named variant)

The bridge allocates only: `Py_buffer` structs and Python return value
objects.  It does not allocate, copy, convert, or transpose data buffers.

### 5.2 Compilation

Compiled once with the platform's default C99 compiler (whatever setuptools
or the PEP 517 backend selects).  No ISA flags.  No per-file
`extra_compile_args`.  Links `libc2ImageD11.a` via `extra_objects`.

### 5.3 c2py23 variant dispatch

c2py23's dispatch mechanism is the core of the Python binding.  It is
specified declaratively in the `.c2py` yaml file and compiled into the
generated wrapper.  Two-level resolution:

**Level 1 -- per-call:** buffer format check (`data.format == 'f'` vs
`'d'`).  Evaluated on every call inside the `_impl` function.

**Level 2 -- init-time:** CPU feature check (`c2py_amd64_avx512f`).  A
`_resolve_*()` function runs once at module load, checks the ISA globals
in priority order, and stores the winning variant index.  The `_impl`
function dispatches through a `switch` on the pre-resolved index.

The `_rebind_<name>(variant_name)` mechanism allows Python to override the
resolved variant at runtime: `module._rebind_score('avx2')` forces the AVX2
variant; `module._rebind_score(None)` resets to auto-resolve.

**Open issue: multiple variants at the same ISA level.**  Currently c2py23
resolves by checking `when:` conditions in order and picking the first
match.  For benchmarking, we want multiple variants that all match the same
ISA level (e.g., `avx2_autovec`, `avx2_intrin_v1` both with
`when: "c2py_amd64_avx2"`) with the first one as the production default
and the others only reachable via `_rebind_*()`.  Additionally, there is
no API to enumerate available variant names (they should appear in the
function docstring since they come from the yaml, but there is no
programmatic `_variants_<name>()`).  These issues are tracked upstream at
https://github.com/jonwright/c2py23/issues/8.

### 5.4 Docstrings from C/C++ source

The c2py yaml file is to be built automatically from the C/C++ sources.
It then becomes the reference contract for the library to connect to
python via c2py23 (that does not parse C/C++/assembly, it trusts you).
This file also harvest documentation from the C/C++ sources.

Building this yaml file from the sources is a significant task for
the c2ImageD11 framework as it becomes the single source of truth for
function signatures and documentation.  In the current setup the yaml
lives in `interface/` and is inevitably out of sync with the code.
This is a design error in the early (still current now) implementation
that needs to be fixed.
The long-term direction is to embed yaml blocks into the C/C++ source files
themselves (similar to the f2py `!F2PY` comment convention used in original
cImageD11), then extract and assemble them automatically.  This ensures:

- One source of truth, no copy-paste
- Functional description lives on the generic (reference) implementation
- Variant-specific notes are appended to the generic description
- The reference implementation is the authoritative source for docstrings

A code generator extracts yaml blocks from C/C++ sources and produces the
assembled `.c2py` file.  The extraction format could be yaml blocks inside
C comments (with automatic indentation management) or a standard comment
convention like Doxygen `/** @c2py ... */` mapped to yaml.

## 6. Benchmarking: Understanding Implementation Tradeoffs

"Benchmarking" means: for a given function, compile N different
implementations, measure each one on representative data, verify correctness
against a reference, and understand which implementation performs best under
which conditions.

### 6.1 The goal is understanding, not selecting a single winner

There is no universally fastest implementation.  Like sorting algorithms,
different implementations win on different data patterns.  A sparse peak
image may favor one approach; a dense image another.  F32 may win on memory
bandwidth but lose on precision for some algorithms.  The benchmarking
framework must expose these tradeoffs so the user or the dispatch logic can
make informed choices.

### 6.2 Workflow

1. Compile all implementations into libc2ImageD11.a.  Register them in the
   `.c2py` yaml as variants (multiple per ISA level allowed, production
   default listed first).

2. In Python, benchmarking each variant can be done like this:
   ```
   for variant_name in available_variants("score"):
       module._rebind_score(variant_name)
       for _ in range(warmup): module.score(...)
       reset_perf(module._perf_score)
       for _ in range(N): module.score(...)
       stats = read_perf(module._perf_score)
       record(variant_name, stats.c_mean_ns)
   ```

3. Validate correctness: every variant is tested against the reference
   implementation on representative datasets.  The reference is the
   original C99 code compiled at `-O0` (no auto-vectorization, no fast-math
   that reorders operations).

4. Record tradeoffs: per-variant, per-dataset timing and accuracy, stored
   for analysis.  Tools like `py-spy` and `perf record` provide additional
   profiling depth.

Where to take the decision about what to supply as the default is at the
level of deciding which functions / isa variants are exposed to the user.
When the yaml is built from the sources, they are either included
or not in the build. We can have source in the project which does not
compile, or is known to segfault, so there needs to be a manifest with
function level about what to include, or not. That is the place to
define the order of which function is preferred. It should be a list
of C99 functions, sorted into order, and organised by the python
method they implement (so it is the skeleton for building the full yaml
from the C99 sources).


### 6.3 What c2py23 provides

- `_rebind_<name>(variant_name)` -- force a specific variant
- `read_perf(ptr)` -- call count, min/mean/max C execution time
  (ns precision via `clock_gettime` or `rdtsc` on x86)
- `set_enabled(ptr, 0/1)` -- toggle timing (zero overhead when disabled)
- Per-function GIL release flags exposed as module attributes
- Module level free threading compatibility (or not if code is not thread safe)

In general, the code here is expected to run as thread safe, and
document expectations. Things like "please don't write in a buffer that I am using"
are not enforced.

### 6.4 What c2py23 may need added

- Multiple variants at the same ISA level, with first-one-listed as the
  production default and others reachable only via `_rebind_*()`
- `_variants_<name>()` returning available variant names (variants are
  already declared in the yaml; they should appear in docstrings and be
  enumerable at runtime)
- Per-variant performance stats populated in the generated code (the
  `c2py_perf_t` struct already has `variant` and `variant_name` fields)

## 7. Distribution

### 7.1 Build once, test on many Python versions

`libc2ImageD11.a` is Python-version-independent.  It links against libc, not
libpython.  c2py_runtime resolves all CPython API at module load time via
`dlopen(NULL)` / `dlsym()`, so the same `.so` binary works from Python 2.7
through 3.14+.

CI workflow:
```
1. Build libc2ImageD11.a  (once)
2. Build _cImageD11.cpython-*.so  (once, links the .a)
3. For each Python version (2.7, ..., 3.14):
     pip install c2ImageD11
     pytest tests/
```

Steps 1-2 run once.  Step 3 runs in parallel.  This replaces the current CI
which rebuilt from source for every Python version.

### 7.2 Wheels

Wheels would like to be tagged as semantically: `py3-none-manylinux2014_x86_64`
(and equivalents for other platforms).
The `py3` tag covers all Python 3 interpreters; a separate
wheel is needed for Python 2.7 due to the `py2` tag.  Platform-specific
wheels encode the architecture (x86_64, aarch64, ppc64le).  This is a
standard cibuildwheel pattern; the details are worked out in the
implementation document. We follow the methods expected for ctypes, nimporter,
and cffi based projects, with the use of c2py23 as our ffi bridge.

The goal is getting a much smaller list of wheels that all ship
the same code inside, with recompilation to match to a C ABI target rather
than the CPython ABI (that needs a lot more versioning). It is closer
to the Java JNI practice than the current CPython approach.

### 7.3 Source distribution

An sdist includes the C/C++ sources, vendored submodules, the pre-generated
c2py23 wrappers and yaml, and the c2py_runtime.  The user needs a C99 compiler and
(optionally) a C++ compiler for the static library.  If they lack a compiler
with ifunc support, they get the baseline ISA level only.  Since GCC and
Clang are universally available on platforms that run Python, this covers
the vast majority of cases.

## 8. Architecture for Growth

The two-tier architecture is designed to accommodate future needs without
restructuring.

**Today:** compiler auto-vectorization at 3 ISA levels (SSE4.2, AVX2,
AVX-512F).  C++ templates for f32/f64 where validated.  Production default
dispatch selects the best available ISA level.

**Tomorrow:** an LLM generates AVX2 intrinsics for `score` (cf. DeepMind
AlphaTensor, "Discovering faster matrix multiplication algorithms with
reinforcement learning", Nature 610, 2022 -- an example of automated
discovery of high-performance kernels).  The new implementation is added as
one  `.c` or `.cpp` file to the static library and one variant entry to the yaml.
Benchmarked against auto-vec AVX2.  If it wins, it can become the released
default for that ISA level.

**Next year:** hand-written AVX-512 assembly for `compute_gv` inspired by
FFmpeg's approach (Lex Fridman Podcast #496).  Add one `.asm` file.  Same
dispatch table.  Same benchmark workflow.  Same artificial intelligence LLM
based author for the assembly code, although humans may have fun here.

**Later:** a new compiler or a new ISA (RISC-V V, ARM SVE2).  The static
library build adds new variants.  The C99 bridge does not change.  The C/C++
code, being a strict historical subset, compiles on future toolchains.

**Python ABI breakage:** If CPython 4.0 changes the C API, only Tier 2 is
rebuilt.  `libc2ImageD11.a` is unaffected. The c2py23 project is shipping
a stable C-ABI for us and we expect them to deal with it for us.

**Non-Python bindings:** `libc2ImageD11.a` is a plain C library callable
from Julia (`ccall`), Nim (`{.importc.}`), Zig (`@cImport`), Mojo (C interop),
or any language with a C FFI. Hypothetically at least.

## 9. Portability

The project targets these platforms initially:
- Linux x86_64 (GCC)
- Windows x86_64 (MSVC + mingw64 for KCB)

Expected to run on:
- ppc64le
- aarch64 (ARM64)

macOS is deferred (not yet investigated).

The portability infrastructure rests on three universal foundations:
- C99 (the bridge)
- Python 2.7 language subset (all `.py` files)
- YAML (the `.c2py` interface definition)

For the C++ compute code, a small subset needs to be enforced: templates
and `extern "C"` wrappers only; no STL, exceptions, RTTI, or heap allocation
operators.  This ensures the library compiles and links everywhere. Anything
making it binary incompatible with C99, or non portable, is not suitable
for our goals.

## 10. Idealized Goals

### Build

- [ ] Multi-ISA compilation works on Linux (GCC) and Windows (MSVC + mingw64)
      without compiler-specific code paths in the Python extension build
- [ ] Adding a new kernel implementation requires one source file and one
      build-system entry; no changes to the Python extension
- [ ] The Python extension compiles with the platform's default C99 compiler
      with zero ISA flags and zero subprocess calls
- [ ] Third-party C libraries (KCB, LZ4, Zstd) build on all platforms without
      source modifications
- [ ] Incremental builds: changing one kernel recompiles only that kernel

### Distribution

- [ ] `python -m build --wheel` produces a standard wheel that runs on all
      Python versions within its ABI tag
- [ ] The wheel contains all ISA variants; dispatch selects at import time;
      no runtime compilation
- [ ] CI builds the static library once, links once, then tests on all
      supported Python versions in parallel
- [ ] Source distribution builds with `pip install .` using only a C99
      compiler (C++ optional for extra ISA levels)

### Benchmarking

- [ ] Every kernel implementation has per-call timing instrumentation
      (c2py23 `read_perf`) with sub-microsecond precision
- [ ] Variant dispatch can be overridden at runtime to measure specific
      implementations (`_rebind_*()`)
- [ ] A benchmark suite validates correctness of every implementation against
      the reference, then measures performance across representative datasets
- [ ] The production default for each function is validated as correct for
      all use cases; it is a compromise that gives good performance for the
      majority

### Cross-platform

- [ ] KCB (with `__attribute__((ifunc))`) compiles and runs correctly on
      Windows via mingw64-gcc, producing bit-identical results to Linux
      [risk: mingw64 COFF object compatibility with MSVC linker must be
       tested; test suite verifies this]
- [ ] The disjoint-set allocator in blobs.c works correctly when compiled
      into the static library -- no heap cross-contamination with the
      Python bridge [risk: test suite verifies this under valgrind]
- [ ] The `score` function demonstrates f32 gv with f64 ubi as a template
      instantiation, validated against the f64 reference
- [ ] The `.c2py` yaml is a single source of truth for signatures and
      docstrings; variant documentation is discoverable

### Maintainability

- [ ] The Python bridge contains no computation, no SIMD, and no
      compiler-specific code -- it is pure C99 buffer protocol glue
- [ ] The static library contains no Python C API calls -- it is a pure
      C/C++ compute library
- [ ] Both tiers can have separate CI: the static library tested as a C library;
      the bridge tested with Python. Today, the static library is tested from python.
- [ ] A new developer can add an optimized implementation for one function
      on one ISA level without understanding the Python binding or the
      build system
- [ ] Docstrings live in the C/C++ source code; the `.c2py` yaml is
      generated from the sources, not maintained by hand
