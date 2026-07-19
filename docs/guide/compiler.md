# Compiler Selection

c2ImageD11 is built with GCC by default on Linux and MSVC on Windows.
Alternative compilers can be selected via `CC=` at meson configure time.

## Default compiler

GCC is the default. It provides:
- Consistently fast codegen across all functions
- Reliable OpenMP (`libgomp`) with low thread overhead
- `-march=native` support for auto-vectorization on non-ISA-variant functions

## Drag racing

A drag race compares the same C code compiled with different compilers.
The current results (single-threaded, `taskset -c 0`, this CPU):

| Compiler | `score` 200k (M gv/s) | `misori_cubic` (ns) | Notes |
|---|---|---|---|
| GCC 13 | 1,152 | 103 | Default |
| Zig cc 0.16.0 (Clang 21) | 1,156 | 98 | Needs LLVM `libomp` |

Codegen quality is essentially tied (within 5%). The main difference is
OpenMP runtime overhead: GCC's `libgomp` is faster for multi-threaded
workloads than LLVM's `libomp`.

## How to switch compilers

```bash
# Zig cc
CC="zig cc" CXX="zig c++" meson setup build-zig
CC="zig cc" ninja -C build-zig

# Clang
CC=clang CXX=clang++ meson setup build-clang

# Build with extra optimizations
CC=gcc CFLAGS="-march=native" meson setup build-native
```

## `-march=native`

Adding `-march=native` lets the compiler use all available instructions
on the build machine. This helps functions that don't have explicit ISA
variants (e.g. `compute_geometry` gets ~6% faster).

For functions with explicit ISA variants (`score`, `score_and_refine`),
the ISA variants already specify `-mavx2` / `-mavx512f` flags, so
`-march=native` provides minimal additional benefit there.

## Benchmarking

Each function has a `bench.py` that measures throughput:

```bash
python lib/functions/score/bench.py         # default variant
python lib/functions/score/bench.py --md    # markdown output for docs
```

To compare two compilers:
```bash
CC=gcc    meson setup build-gcc    && ninja -C build-gcc
CC=zig cc meson setup build-zig    && ninja -C build-zig
cp build-gcc/_cImageD11.so c2ImageD11/
python lib/functions/score/bench.py
cp build-zig/_cImageD11.so c2ImageD11/
python lib/functions/score/bench.py
```
