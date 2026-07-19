# c2ImageD11

Standalone C extensions for [ImageD11](https://github.com/jonwright/ImageD11),
ported from f2py to **[c2py23](https://github.com/jonwright/c2py23)**.

## What this is

A shared library (`_cImageD11.so`) that exposes the same 58 C functions as
`ImageD11._cImageD11`, with no ctypes, no f2py, no Python.h dependency.

One `.so` file works on Python 2.7 through 3.14 — just copy it into the
Python package directory.

## Key improvements over ImageD11.cImageD11

- **SoA without copies**: `score` and `score_and_refine` accept g-vectors
  in both row-major (N,3) and column-major (3,N) layouts. No `.T.copy()`
  needed — the C dispatch detects the shape and selects the right kernel.

- **Automatic ISA dispatch**: AVX-512, AVX2, and SSE4.1 variants are
  compiled with per-ISA compiler flags and selected at runtime based on
  CPU features. No manual tuning needed.

- **f32/f64 templating**: `score_and_refine` has both float32 and
  float64 kernels. Indexing uses f32 for throughput; strain refinement
  uses f64 for precision. C++ templates generate both from one source.

- **OpenMP threading**: `score`, `score_and_refine`, `score_and_assign`,
  `compute_geometry`, `compute_gv`, and other expensive functions use
  `#pragma omp parallel for if(n > threshold)` guards.

- **No build-time Python dependency**: The generated wrapper + `c2py.h`
  runtime are checked into git. `meson setup && ninja` is all you need.

## Quickstart

```bash
# Build
mkdir -p build && cd build
meson setup ../lib
ninja
cp _cImageD11.so ../c2ImageD11/

# Test
cd ..
python -m pytest tests/
```

## API Reference

The full API reference (58 C functions + CPU feature probes) is at the
[API Reference](api/index.md) page.

## Documentation

- [API Reference](api/index.md) — auto-generated from C2PY_BEGIN blocks
- [ISA Variants](guide/variants.md) — CPU dispatch, compiler flags, tier selection
- [Compiler Selection](guide/compiler.md) — GCC vs Clang/zig cc drag race

## Links

- [GitHub](https://github.com/jonwright/c2ImageD11)
- [c2py23](https://github.com/jonwright/c2py23)
- [ImageD11](https://github.com/jonwright/ImageD11)
