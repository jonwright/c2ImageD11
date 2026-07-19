# ISA Variants

`score`, `score_and_refine`, and `score_and_assign` have multiple compiled
kernels targeting different ISA levels. At runtime, c2py23 reads the CPU
feature flags and dispatches to the best available kernel.

## Dispatch logic

c2py23 probes the CPU at module init and sets C globals:

```c
int c2py_amd64_sse4_1 = 1;   // SSE4.1 detected
int c2py_amd64_avx2    = 1;   // AVX2 detected
int c2py_amd64_avx512f = 1;   // AVX-512F detected
```

Each variant overload has a `when:` condition in the C2PY_BEGIN block:

```json
{
  "sig": "... score_f64_avx512 ...",
  "when": "... c2py_amd64_avx512f",
  ...
}
```

The wrapper checks conditions in order. The first matching overload wins.
ISA-sorted overloads (highest tier first) ensure the best kernel is chosen.

## Which functions have variants

| Function | AoS | SoA | f64 | f32 | SSE4.1 | AVX2 | AVX-512 |
|---|---|---|---|---|---|---|---|
| `score` | yes | yes | yes | yes | - | yes | yes |
| `score_and_refine` | yes | yes | yes | yes | yes | yes | yes |
| `score_and_assign` | yes | yes | yes | yes | - | yes | yes |

## Compiler flags per variant

Each variant is compiled as a separate `static_library` in meson with
its own `c_args`:

| Tier | Flags |
|---|---|
| SSE4.1 | `-O2 -fopenmp -fPIC -msse4.1` |
| AVX2 | `-O3 -ffast-math -fopenmp -fPIC -mavx2 -mfma` |
| AVX-512 | `-O3 -ffast-math -fopenmp -fPIC -mavx512f -mavx2 -mfma` |
| Baseline (non-x86) | `-O2 -fopenmp -fPIC` |

On non-x86_64 platforms (aarch64, ppc64le), all ISA variants compile
with baseline flags and use stub symbols that delegate to scalar loops.

## SoA vs AoS dispatch

g-vectors can be passed in either layout:

- **AoS** (Array of Structures): shape `(ng, 3)` -- row-major, slow_axis=0
- **SoA** (Structure of Arrays): shape `(3, ng)` -- column-major, slow_axis=0

The wrapper detects the layout from shape at call time and dispatches to
the appropriate kernel. No `.T.copy()` needed -- pass the buffer as-is.

## Runtime ISA introspection

Python-callable functions on `c2ImageD11._cImageD11`:

```python
>>> c2ImageD11._c2py_has_avx512f()
1
>>> c2ImageD11._c2py_has_avx2()
1
>>> c2ImageD11._c2py_set_avx2(0)   # temporarily force off for benchmarking
1
```

See the [CPU Features](../api/cpu.md) page for the full list across x86_64,
arm64, and ppc64.
