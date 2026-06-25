# const review: parameters missing read-only annotation

## Notes

- `const` in the C2PY_BEGIN overload sig tells c2py23 to acquire the buffer
  read-only, accepting read-only numpy arrays and allowing aliasing.
- The C definition should also have `const` for correctness (matching what
  the C code actually does) and to avoid -Werror on discarding qualifier.
- "Already OK" means `const` is present in both C def and C2PY sig.
- **All 66 parameters fixed.** Compiler -Wall -Werror catches any
  over-constrained const (writes to const pointer). The build failed once
  on bloboverlaps (wrongly marked b2/res2 as const) and was corrected.

## Correctness verified

- `compute_xlylzl` accepts read-only arrays (issue #13)
- `compute_geometry` accepts read-only arrays
- `misori_cubic(u, u)` allows aliasing (const params)
- `score(u, u)` allows aliasing
- All 61 tests pass

## Functions NOT changed (verified writable params)
- `frelon_lines` — img is modified in-place
- `uint16_to_float_darksub` — img is modified
- `uint16_to_float_darkflm` — img is modified
- `clean_mask` — msk is modified
- `bloboverlaps` — b1, res1, b2, res2 are modified (detected by compiler!)
- `array_mean_var_msk` — msk is modified (`msk[i] = 0`)
- `score_and_refine` — ubi is modified (refined)
- `refine_assigned` — ubi is modified
- `cimaged11_omp_set_num_threads`, `cimaged11_omp_get_max_threads` — no buffers

## Changes made
- 6 C source files + 1 header file
- 35 functions, 66 parameters
- All edits verified by compiler (-Wall -Werror) and 61 tests
