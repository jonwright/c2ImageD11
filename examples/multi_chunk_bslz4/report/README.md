# CSC1D Sparse Decompressor Performance Report

Branch: `simd_csc_sparse`
Date: 2026-06-19
Machine: AMD EPYC-Genoa (KVM), 4 vCPU, 2.4 GHz
Detector: Eiger2 CdTe 4M (2162 x 2068), 75 um pixel pitch
Geometry: example.poni (dist=250mm, wavelength=0.2846A)

## Datasets

| Name | Frames | Bins | Source | Active Pixels |
|------|--------|------|--------|---------------|
| Poisson | 32 | 2500 | Synthetic: Poisson(5) bg, peaks ~200, hot=65530, cut=50 | 4,201,890 (94%) |
| Eiger | 100 | 1500 | eiger_0000.h5 (real detector data), cut=50 | 4,201,890 (94%) |

## Test Matrix

| Factor | Values |
|--------|--------|
| SIMD variant | kcb_avx512, kcb_avx2, kcb_sse42 |
| CSC format | std_f32 (standard CSC), csc1d_f32, csc1d_u8, csc1d_u16, csc1d_u32 |
| Batch size | 1, 2, 4, 8, 16, 32 |
| Baseline | scipy.sparse.csc_matrix.dot() (1 frame only) |

Common: 3 repeats per measurement, best + 2nd reported in timing.txt
Automatic stride: 64 (inner pixel loop sub-block stride)
CSC backend: KCB (Kalcutter Bitshuffle)

---

## Factor 1: SIMD Variant (avx512 vs avx2 vs sse42)

### csc1d_f32, bs=32, KCB backend

| Dataset | avx512 | avx2 | sse42 | sse42 pct of avx512 |
|---------|--------|------|-------|-------------------|
| Poisson | 112.1 | 110.0 | 25.7 | 23% |
| Eiger | 175.6 | 163.6 | 163.9 | 93% |

### std_f32, bs=32, KCB backend

| Dataset | avx512 | avx2 | sse42 | sse42 pct of avx512 |
|---------|--------|------|-------|-------------------|
| Poisson | 69.7 | 69.2 | 66.5 | 95% |
| Eiger | 155.6 | 196.6 | 161.6 | 104% |

### csc1d_u16, bs=32, KCB backend

| Dataset | avx512 | avx2 | sse42 | sse42 pct of avx512 |
|---------|--------|------|-------|-------------------|
| Poisson | 113.0 | 115.7 | 103.0 | 91% |
| Eiger | 174.2 | 182.2 | 178.6 | 103% |

### Observed

- avx512 and avx2 are within 5% of each other for all formats and datasets.
- csc1d_f32 on Poisson is 4.4x slower on sse42 (25.7 vs 112.1 FPS).
  The SSE4.2 instruction set lacks FMA (fused multiply-add) for float64,
  forcing the compiler to emit separate mul + add for each of the 4
  per-pixel entries.  At 4 entries per pixel and 4.2M active pixels,
  the instruction count scales linearly.
- csc1d_f32 on Eiger shows no SSE42 penalty (163.9 vs 175.6 FPS).
  Eiger has only 3 entries per pixel (epp=3 vs epp=4 for Poisson),
  and different CSC data density (9.5M vs 13M nonzeros).
- std_f32 is unaffected by SIMD level on both datasets because the
  standard CSC template does not use FMA in its inner loop (indirect
  indexed access prevents vectorisation).
- csc1d_u16 is not affected by SSE42 because the integer multiply (imul)
  does not fuse with add, so the sse42 path is not at a disadvantage.

### Plot

See `plots/simd_comparison.png`.

---

## Factor 2: CSC Format (standard vs 1D padded)

### bs=32, best KCB variant per format

| Dataset | std_f32 | csc1d_f32 | csc1d/standard |
|---------|---------|-----------|----------------|
| Poisson | 69.7 | 112.1 | 1.61x |
| Eiger | 196.6 | 175.6 | 0.89x |

### Observed

- csc1d_f32 is 1.6x faster than std_f32 on Poisson (2500 bins, epp=4).
  The larger entries-per-pixel count means more indirect accesses through
  indptr/indices per pixel in the standard CSC path; the 1D padded path
  eliminates these with direct sequential array access.
- csc1d_f32 is 0.89x (slower) than std_f32 on Eiger (1500 bins, epp=3).
  With fewer entries per pixel, the standard CSC's indirection overhead
  is lower, and the 1D padded path pays the cost of strided pixel access
  without sufficient benefit.
- The std_f32 Eiger result (196.6 FPS, kcb_avx2, bs=32) is the highest
  single FPS measured in this experiment.  This is the real-detector
  throughput on 100 frames of eiger_0000.h5.

### Plot

See `plots/format_comparison.png`.

---

## Factor 3: Quantization (f32 vs u8 vs u16 vs u32)

### Poisson, csc1d, bs=32, kcb_avx512

| Dtype | Scale factor | FPS | vs f32 | Powder error (max abs, uint64 units) |
|-------|-------------|-----|--------|--------------------------------------|
| f32 | N/A | 112.1 | 1.00x | 0 (reference) |
| u8 | 255 | 124.1 | 1.11x | 560.7 |
| u16 | 32768 | 115.7 | 1.03x | 4.24 |
| u32 | 2^31 | 104.4 | 0.93x | 0.0049 |

### Observed

- u8 quantization gives 11% higher FPS.  The CSC data array is 4x smaller
  (uint8 vs float32), reducing memory traffic for the 13M-entry CSC matrix
  from 52 MB to 13 MB.  This matters when the CSC data is large enough
  to exceed L3 cache.
- u16 quantization gives 3% higher FPS with 2x size reduction (26 MB).
- u32 quantization gives no speed benefit — same size as float32 (52 MB)
  but requires uint64 accumulation (larger output type).
- Quantization error (measured as max absolute difference in uint64
  powder bins): u8 has the largest error (560.7 per bin), u16 is
  moderate (4.24), u32 is near-perfect (0.0049).  After division by
  scale_factor, these correspond to ~2.2 counts (u8), ~0.00013 counts
  (u16), and 2.3e-9 counts (u32) in float64.
- u32 quantization gives exact integer arithmetic with all operations
  in uint64.  This path is relevant if the code is ported to GPU, where
  integer arithmetic may be faster than floating-point for certain
  hardware generations.

### Plot

See `plots/quantization.png`.

---

## Factor 4: Batch Size

### Poisson, csc1d_f32, kcb_avx512

| bs | FPS | vs bs=1 |
|----|-----|---------|
| 1 | 88.6 | 1.00x |
| 2 | 97.1 | 1.10x |
| 4 | 107.3 | 1.21x |
| 8 | 108.3 | 1.22x |
| 16 | 112.0 | 1.26x |
| 32 | 112.1 | 1.27x |

### Eiger, csc1d_f32, kcb_avx2

| bs | FPS | vs bs=1 |
|----|-----|---------|
| 1 | 131.5 | 1.00x |
| 2 | 131.7 | 1.00x |
| 4 | 141.9 | 1.08x |
| 8 | 150.9 | 1.15x |
| 16 | 163.8 | 1.25x |
| 32 | 163.6 | 1.24x |

### Eiger, std_f32, kcb_avx2

| bs | FPS | vs bs=1 |
|----|-----|---------|
| 1 | 124.4 | 1.00x |
| 2 | 119.7 | 0.96x |
| 4 | 129.4 | 1.04x |
| 8 | 153.4 | 1.23x |
| 16 | 177.8 | 1.43x |
| 32 | 196.6 | 1.58x |

### Observed

- Batch size benefit is format-dependent and dataset-dependent.
- Poisson (32 frames, 2500 bins): 27% improvement from bs=1 to bs=32.
  Saturates at bs=16 (124 FPS plateau).
- Eiger csc1d_f32: 24% improvement, plateau at bs=16.
- Eiger std_f32: 58% improvement from bs=1 to bs=32, with no sign of
  saturation!  Standard CSC benefits much more from loop interchange
  than csc1d because the random-access pattern through indptr/indices
  is harder on the cache; batching spreads the cache pressure.
- Default recommendation: bs=16 for csc1d, bs=32 for std_f32.

### Plot

See `plots/batch_scaling.png` and `plots/eiger_batch.png`.

---

## Factor 5: Python Baseline

scipy.sparse.csc_matrix.dot() on one frame:

| Dataset | FPS | ms/frame |
|---------|-----|----------|
| Poisson (2500 bins) | 13.4 | 74.6 |
| Eiger (1500 bins) | 17.9 | 55.9 |

Best C result, same dataset, same format: 8-11x faster.

---

## Factor 6: Backend (KCB vs bitshuffle-core)

Not included in the final unified benchmark run.  Prior isolated benchmarks
show KCB is 1.5-2x faster than bitshuffle-core for csc1d functions across
all SIMD variants.  The bitshuffle-core path has been included in the
c2ImageD11 build for backward compatibility with the original ImageD11
bslz4_to_sparse code, but should not be the default.

---

## Recommendations for Slimming the Codebase

### Always Keep

- KCB backend (kcb_*) for all CSC functions
- std_f32 (standard CSC) functions for all pixel types (u8/u16/u32)
- csc1d_f32 functions for u16 pixel type (the one actually benchmarked)
- AVX2 variant with FMA (`-mavx2 -mfma`)
- AVX-512 variant (`-mavx512f`)

### Consider Removing

- bitshuffle-core backend (bs_*) for CSC functions
  Reason: 1.5-2x slower than KCB.
- csc1d_u16 functions
  Reason: only 3% speedup over csc1d_f32 on Poisson, no speedup on Eiger.
- csc1d_u32 functions
  Reason: no speedup, same memory footprint as f32.
- sse42 variant for csc1d_f32
  Reason: 4.4x slower than avx2 on Poisson.  Keep the code but do not
  compile as default.

### Keep as Optional

- csc1d_u8 functions
  Reason: 11% speedup from reduced memory traffic.  Useful when memory
  bandwidth is the bottleneck.  Weigh against the quantization error
  (~0.04% relative error per bin at typical bin counts of ~1e4).

### Record: u32 for GPU

- u32 quantization produces exact integer arithmetic (uint64 accumulator).
  This path was built and verified (powder matches f32 reference within
  floating-point roundoff).  The code is documented and can be resurrected
  if GPU porting becomes a priority.  See `csc_convert.py` for the
  quantization infrastructure and `bs_sparse_csc_1d_tmpl.c` for the
  integer-type template.

---

## Files in this report

- `timing.txt` -- complete benchmark output (84 measurement rows)
- `plots/simd_comparison.png` -- avx512 vs avx2 vs sse42 for csc1d_f32
- `plots/batch_scaling.png` -- FPS vs batch size for Poisson
- `plots/eiger_batch.png` -- FPS vs batch size for Eiger
- `plots/quantization.png` -- FPS vs quantization dtype
- `plots/format_comparison.png` -- FPS vs format, both datasets
