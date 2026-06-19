# %% [markdown]
# # Multi-Chunk BSLZ4 CSC Powder Integration Benchmark
# #
# # Processes frames from a bitshuffle-lz4 HDF5 file using pyFAI CSC matrix.
# # Compares batch sizes [1, 2, 4, 8, 16, 32] with loop-interchanged C code.
# # Single core, no parallelism.  Timed via c2py23 + Python time.perf_counter.
# #

# %%
import os, sys, time, json
import numpy as np
import c2ImageD11._cImageD11 as _m
from c2py23.perf import read_perf, set_enabled
from c2ImageD11.bslz4 import chunk2sparseCSC
import h5py
import matplotlib
matplotlib.use("Agg")    # non-interactive for batch runs; comment out in notebook
import matplotlib.pyplot as plt

# ======== USER INPUTS ========
_HOME = os.environ.get("HOME", os.path.expanduser("~"))
HDF5FILE  = os.path.join(_HOME, "test_data", "eiger_0000.h5")
DATASET   = "entry_0000/ESRF-ID11/eiger/data"
MASKFILE  = os.path.join(_HOME, "test_data", "eiger_mask.npy")
PONIFILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example.poni")
NFRAMES   = 100
NOUT      = 1500           # powder histogram bins
BATCH_SIZES = [1, 2, 4, 8, 16, 32]
# ==============================


# %% [markdown]
# ## 1. Create PONI geometry file (if missing)

# %%
PONI_DICT = {
    "poni_version": 2.1,
    "detector": "Eiger2CdTe_4M",
    "detector_config": {"pixel1": 7.5e-05, "pixel2": 7.5e-05, "orientation": 3},
    "dist": 0.25,
    "poni1": 0.07,
    "poni2": 0.08,
    "rot1": 0.01,
    "rot2": 0.02,
    "rot3": 0.03,
    "wavelength": 2.846e-11,
}

if not os.path.exists(PONIFILE):
    with open(PONIFILE, "w") as f:
        json.dump(PONI_DICT, f, indent=2)
    print("Created", PONIFILE)
else:
    print("Using existing", PONIFILE)


# %% [markdown]
# ## 2. Set up pyFAI integrator, extract CSC engine

# %%
import pyFAI
from pyFAI.integrator.azimuthal import AzimuthalIntegrator

with open(PONIFILE) as f:
    poni = json.load(f)

det = pyFAI.detector_factory(poni["detector"])
ai = AzimuthalIntegrator()
ai.set_config(poni)
ai.wavelength = poni.get("wavelength", ai.wavelength)
print("Integrator: dist=%.3f m, detector=%s  shape=%dx%d" % (
    poni["dist"], poni["detector"], det.shape[0], det.shape[1]))

t_build0 = time.perf_counter()
dummy = np.zeros((det.shape[0], det.shape[1]), dtype=np.float64)
res = ai.integrate1d(dummy, NOUT, method=("bbox", "CSC", "python"))
t_build = time.perf_counter() - t_build0
print("CSC engine built in %.1f ms" % (t_build * 1000))

method_key = None
csc_engine = None
for k, v in ai.engines.items():
    if hasattr(k, "algo") and k.algo == "CSC":
        method_key = k
        csc_engine = v.engine
        break
if csc_engine is None:
    raise RuntimeError("CSC engine not found in pyFAI")

csc_data    = np.ascontiguousarray(csc_engine.data.astype(np.float32))
csc_indices = np.ascontiguousarray(csc_engine.indices.astype(np.uint32))
csc_indptr  = np.ascontiguousarray(csc_engine.indptr.astype(np.uint32))
csc_bins    = csc_engine.bins

print("CSC: %d nnz, %d bins, %.1f MB" % (
    len(csc_data), csc_bins,
    (csc_data.nbytes + csc_indices.nbytes + csc_indptr.nbytes) / 1e6))


# %% [markdown]
# ## 3. Load detector mask

# %%
mask_2d = np.load(MASKFILE).astype(np.uint8)
flat_mask = mask_2d.ravel()
NIJ = len(flat_mask)
nactive = flat_mask.sum()
print("Mask: %d / %d active pixels (%.1f%%)" % (
    nactive, NIJ, 100.0 * nactive / NIJ))

# NSCA CSC wrapper for chunk2sparseCSC
class CSCObj:
    pass
csc_obj = CSCObj()
csc_obj.data    = csc_data
csc_obj.indices = csc_indices
csc_obj.indptr  = csc_indptr
csc_obj.shape   = (csc_bins,)
csc_obj.bins    = csc_bins


# %% [markdown]
# ## 4. Read chunk offsets from HDF5 (h5py low-level API)

# %%
def get_chunk_offsets(filepath, ds_path, nframes):
    t0 = time.perf_counter()
    offsets = np.full(nframes, -1, dtype=np.int64)
    lengths = np.full(nframes, -1, dtype=np.int32)

    with h5py.File(filepath, "r") as hf:
        ds = hf[ds_path]
        print("Dataset: %s -> shape=%s dtype=%s chunks=%s" % (
            ds_path, ds.shape, ds.dtype, ds.chunks))
        if ds.shape[0] < nframes:
            raise ValueError("File has %d frames, need %d" % (ds.shape[0], nframes))

        def callback(storeinfo):
            logical_offset, filter_mask, file_location, size = storeinfo
            frame = logical_offset[0]
            if frame < nframes:
                offsets[frame] = file_location
                lengths[frame] = size

        ds.id.chunk_iter(callback)

    if (offsets < 0).any() or (lengths < 0).any():
        missing = np.where(offsets < 0)[0]
        raise RuntimeError("Missing chunk offsets for frames: %s" % str(missing[:5]))

    t1 = time.perf_counter()
    print("Chunk offet read: %.1f ms for %d frames" % ((t1 - t0) * 1000, nframes))
    return offsets, lengths

t_hdf5 = time.perf_counter()
chunk_offsets, chunk_lengths = get_chunk_offsets(HDF5FILE, DATASET, NFRAMES)
t_hdf5 = time.perf_counter() - t_hdf5


# %% [markdown]
# ## 5. Memory-map file

# %%
t_mmap0 = time.perf_counter()
mmap = np.memmap(HDF5FILE, dtype="B", mode="r")
t_mmap = time.perf_counter() - t_mmap0
fsize_mb = len(mmap) / 1e6
print("mmap: %.3f ms (file size: %.1f MB)" % (t_mmap * 1000, fsize_mb))


# %% [markdown]
# ## 6. Allocate reusable buffers (sized for the largest batch)

# %%
max_bs = max(BATCH_SIZES)
nout = csc_obj.bins

powder_buf = np.zeros(max_bs * nout, dtype=np.float64)
outpx_buf   = np.zeros(max_bs * NIJ, dtype=np.uint16)
outadr_buf  = np.zeros(max_bs * NIJ, dtype=np.uint32)
# npx_pc_buf allocated per batch call (size = batch_n)

all_sparse_vals = [None] * NFRAMES
all_sparse_inds = [None] * NFRAMES
all_powder      = [None] * NFRAMES

total_mb = (outpx_buf.nbytes + outadr_buf.nbytes
            + powder_buf.nbytes) / 1e6
print("Reusable buffer total: %.0f MB" % total_mb)
print("  outpx  : %.0f MB  (uint16, %d x %d)" % (
    outpx_buf.nbytes / 1e6, max_bs, NIJ))
print("  outadr : %.0f MB  (uint32, %d x %d)" % (
    outadr_buf.nbytes / 1e6, max_bs, NIJ))
print("  powder : %.1f KB  (f64, %d x %d)" % (
    powder_buf.nbytes / 1e3, max_bs, nout))
assert total_mb < 1024, "Buffer exceeds 1 GB limit (%.0f MB)" % total_mb


# %% [markdown]
# ## 7. Create CSC function handle, enable c2py23 timing

# %%
dc = chunk2sparseCSC(mask_2d, csc_obj, dtype=np.uint16)

set_enabled(_m._c2py_timing_enabled, 1)

timer_ptr = _m._perf_bslz4_csc_u16


# %% [markdown]
# ## 8. Benchmark: process N frames with different batch sizes

# %%
results = {}

s_offs = np.array([0], dtype=np.int64)
s_lens = np.zeros(1, dtype=np.int32)
s_npc  = np.zeros(1, dtype=np.int32)

for bs in BATCH_SIZES:
    print("\n--- batch_size = %d ---" % bs)

    # Record baseline C timer
    set_enabled(_m._c2py_timing_enabled, 0)
    set_enabled(_m._c2py_timing_enabled, 1)
    t0_stats = read_perf(timer_ptr)

    t_py0 = time.perf_counter()

    if bs == 1:
        for frame in range(NFRAMES):
            chunk_start = int(chunk_offsets[frame])
            chunk_len   = int(chunk_lengths[frame])
            s_lens[0]   = chunk_len

            chunk_view = mmap[chunk_start:chunk_start + chunk_len]
            # mmap slices are memoryviews; copy to ensure contiguous
            chunk_copy = np.frombuffer(chunk_view, dtype=np.uint8).copy()

            npx = dc.fun(
                chunk_copy,
                flat_mask,
                outpx_buf, outadr_buf, 0,
                powder_buf, csc_data, csc_indices, csc_indptr,
                s_offs, s_lens, s_npc,
            )
            all_sparse_vals[frame] = outpx_buf[:npx].copy()
            all_sparse_inds[frame] = outadr_buf[:npx].copy()
            all_powder[frame]      = powder_buf[:nout].copy()
    else:
        for batch_start in range(0, NFRAMES, bs):
            batch_n = min(bs, NFRAMES - batch_start)
            batch_offs = chunk_offsets[batch_start:batch_start + batch_n]
            batch_lens = chunk_lengths[batch_start:batch_start + batch_n]

            powder_buf[:batch_n * nout] = 0.0
            npx_pc = np.zeros(batch_n, dtype=np.int32)

            dc.fun(
                mmap, flat_mask,
                outpx_buf, outadr_buf, 0,
                powder_buf, csc_data, csc_indices, csc_indptr,
                batch_offs, batch_lens, npx_pc,
            )

            for f in range(batch_n):
                frame = batch_start + f
                npx = npx_pc[f]
                all_sparse_vals[frame] = outpx_buf[f * NIJ : f * NIJ + npx_pc[f]].copy()
                all_sparse_inds[frame] = outadr_buf[f * NIJ : f * NIJ + npx_pc[f]].copy()
                all_powder[frame]      = powder_buf[f * nout : (f + 1) * nout].copy()

    t_py1 = time.perf_counter()
    t1_stats = read_perf(timer_ptr)

    py_total_ms = (t_py1 - t_py0) * 1000
    c_total_ns  = t1_stats["c_dur_ns"]  - t0_stats["c_dur_ns"]
    c_wrap_ns   = t1_stats["wrap_dur_ns"] - t0_stats["wrap_dur_ns"]
    c_prec_ns   = t1_stats["t_enter"]   - t0_stats["t_enter"]
    c_postc_ns  = t1_stats["t_post_c"]  - t0_stats["t_post_c"]
    c_calls     = t1_stats["call_count"] - t0_stats["call_count"]

    c_total_ms = max(0.0, c_total_ns / 1e6)  # clamp negative noise
    print("  Python total: %.0f ms   C total: %.0f ms   C calls: %d" % (
        py_total_ms, c_total_ms, c_calls))
    print("  Per frame: %.2f ms" % (py_total_ms / NFRAMES))

    results[bs] = {
        "py_total_ms": py_total_ms,
        "c_total_ms":  c_total_ns / 1e6,
        "c_calls":     c_calls,
        "c_wrap_ms":   c_wrap_ns / 1e6,
        "per_frame_ms": py_total_ms / NFRAMES,
    }


# %% [markdown]
# ## 9. Plots

# %%
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Plot 1: Per-frame time vs batch size
ax = axes[0]
x = np.array(BATCH_SIZES, dtype=float)
y = np.array([results[bs]["per_frame_ms"] for bs in BATCH_SIZES])
ax.plot(x, y, "o-", color="steelblue", lw=2, ms=8)
ax.set_xlabel("Batch size (frames per C call)")
ax.set_ylabel("Time per frame (ms)")
ax.set_title("Per-Frame Processing Time vs Batch Size")
ax.set_xscale("log", base=2)
ax.grid(True, alpha=0.3)

# Plot 2: Time breakdown
ax = axes[1]
c_times  = np.array([results[bs]["c_total_ms"] for bs in BATCH_SIZES])
w_times  = np.array([results[bs]["c_wrap_ms"] for bs in BATCH_SIZES])
py_times = np.array([results[bs]["py_total_ms"] for bs in BATCH_SIZES])
ov_times = py_times - c_times
xr = np.arange(len(BATCH_SIZES))
ax.bar(xr, c_times, label="C execution", color="steelblue")
ax.bar(xr, (ov_times - w_times), bottom=c_times,
       label="Python overhead", color="lightcoral")
ax.set_xticks(xr)
ax.set_xticklabels([str(bs) for bs in BATCH_SIZES])
ax.set_xlabel("Batch size")
ax.set_ylabel("Total time (ms) for %d frames" % NFRAMES)
ax.set_title("Time Breakdown")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis="y")

# Plot 3: Speedup
ax = axes[2]
speedups = [results[1]["py_total_ms"] / results[bs]["py_total_ms"]
            for bs in BATCH_SIZES]
ax.bar(xr, speedups, color="darkseagreen")
ax.set_xticks(xr)
ax.set_xticklabels([str(bs) for bs in BATCH_SIZES])
ax.set_xlabel("Batch size")
ax.set_ylabel("Speedup vs bs=1")
ax.set_title("Speedup from Multi-Chunk Loop Interchange")
for i, v in enumerate(speedups):
    ax.text(i, v + 0.05, "%.1fx" % v, ha="center", fontsize=9)
ax.grid(True, alpha=0.3, axis="y")
ax.set_ylim(0, max(speedups) * 1.3)

plt.tight_layout()
plot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark.png")
plt.savefig(plot_path, dpi=120)
print("\nSaved plot: %s" % plot_path)


# %% [markdown]
# ## 10. Summary

# %%
print()
print("=" * 65)
print("  File:    %s" % HDF5FILE)
print("  Dataset: %s (%d frames)" % (DATASET, NFRAMES))
print("  Mask:    %d / %d active" % (nactive, NIJ))
print("  CSC:     %d bins, %.1f MB" % (nout, csc_data.nbytes / 1e6))
print()
print("  HDF5 chunk offset read: %.1f ms" % (t_hdf5 * 1000))
print("  File mmap:               %.1f ms" % (t_mmap * 1000))
print("  CSC engine build:        %.1f ms" % (t_build * 1000))
print()
print("  Batch processing (%d frames):" % NFRAMES)
print("  %-6s %10s %12s %12s" % ("bs", "total_ms", "ms/frame", "speedup"))
print("  " + "-" * 44)
for bs in BATCH_SIZES:
    r = results[bs]
    sp = results[1]["py_total_ms"] / r["py_total_ms"]
    print("  %-6d %10.0f %12.2f %11.1fx" % (bs, r["py_total_ms"],
                                                r["per_frame_ms"], sp))
print("=" * 65)

# Check sparse output sanity
npx_total = sum(len(v) for v in all_sparse_vals)
print("\nSparse pixels stored: %d across %d frames" % (npx_total, NFRAMES))
