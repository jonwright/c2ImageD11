# %% [markdown]
# # Multi-Chunk BSLZ4 CSC Powder Integration Benchmark
# #
# # Processes frames from a bitshuffle-lz4 HDF5 file using pyFAI CSC matrix.
# # Compares batch sizes 1-16 with loop-interchanged C code.
# # Single core, no parallelism.  C time measured via time.perf_counter.
# #
# # NOTE: c2py23's built-in timer uses rdtsc on x86_64, which measures CPU
# # cycles, not wall-clock nanoseconds.  There is no option to switch to
# # clock_gettime.  We advise adding "c2py_ticks_use_clock_gettime" as a
# # compile-time flag.  Until then, C call time is measured from Python
# # with time.perf_counter() (which includes the ~2 us wrapper overhead).

# %%
import os, sys, time, json
import numpy as np
import c2ImageD11._cImageD11 as _m
from c2ImageD11.bslz4 import chunk2sparseCSC
import h5py
import matplotlib
matplotlib.use("Agg")    # comment out for notebook
import matplotlib.pyplot as plt

# ======== USER INPUTS ========
_HOME = os.environ.get("HOME", os.path.expanduser("~"))
HDF5FILE  = os.path.join(_HOME, "test_data", "eiger_0000.h5")
DATASET   = "entry_0000/ESRF-ID11/eiger/data"
MASKFILE  = os.path.join(_HOME, "test_data", "eiger_mask.npy")
PONIFILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example.poni")
NFRAMES   = 1000
NOUT      = 1500           # powder histogram bins
BATCH_SIZES = list(range(1, 17))
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

outpx_buf   = np.zeros(max_bs * NIJ, dtype=np.uint16)
outadr_buf  = np.zeros(max_bs * NIJ, dtype=np.uint32)

# Pre-allocated per-frame powder storage (C function writes directly in-place)
all_powder = np.zeros((NFRAMES, nout), dtype=np.float64)

# Per-frame sparse output (variable length per frame)
all_sparse_vals = np.empty(NFRAMES, dtype=object)
all_sparse_inds = np.empty(NFRAMES, dtype=object)

total_mb = (outpx_buf.nbytes + outadr_buf.nbytes) / 1e6
print("Reusable buffer total: %.0f MB" % total_mb)
print("  outpx  : %.0f MB  (uint16, %d x %d)" % (
    outpx_buf.nbytes / 1e6, max_bs, NIJ))
print("  outadr : %.0f MB  (uint32, %d x %d)" % (
    outadr_buf.nbytes / 1e6, max_bs, NIJ))
print("  powder : %.1f KB  (f64, %d x %d) -- in all_powder, written in-place" % (
    all_powder.nbytes / 1e3, NFRAMES, nout))
print("  (max batch %d: %.0f MB, 1 GB limit for all reused buffers)" % (max_bs, total_mb))
assert total_mb < 1024, "Buffer exceeds 1 GB limit (%.0f MB)" % total_mb


# %% [markdown]
# ## 7. Create CSC function handle

# %%
dc = chunk2sparseCSC(mask_2d, csc_obj, dtype=np.uint16)


# %% [markdown]
# ## 8. Warmup (fault in mmap pages, fill caches)

# %%
print("\nWarming up...")
sys.stdout.flush()
# Process one batch (bs=4, 4 frames) to bring pages into RAM
warm_offs = chunk_offsets[:4]
warm_lens = chunk_lengths[:4]
warm_npc  = np.zeros(4, dtype=np.int32)
warm_pow  = all_powder[:4].ravel()
dc.fun(mmap, flat_mask, outpx_buf, outadr_buf, 0,
       warm_pow, csc_data, csc_indices, csc_indptr,
       warm_offs, warm_lens, warm_npc)
print("Warmup done.\n")
sys.stdout.flush()


# %% [markdown]
# ## 9. Benchmark: process N frames with different batch sizes

# %%
# c2py23's built-in timer uses rdtsc on x86_64, which returns CPU cycles
# rather than wall-clock nanoseconds.  No compile-time option exists to
# switch to clock_gettime (we recommend adding C2PY_USE_CLOCK_GETTIME).
# We measure C time from Python with time.perf_counter() as a workaround.

results = {}

for bs in BATCH_SIZES:
    print("\n--- batch_size = %d ---" % bs)
    c_total = 0.0
    copy_total = 0.0
    t_py0 = time.perf_counter()

    for batch_start in range(0, NFRAMES, bs):
        batch_n = min(bs, NFRAMES - batch_start)
        batch_offs = chunk_offsets[batch_start:batch_start + batch_n]
        batch_lens = chunk_lengths[batch_start:batch_start + batch_n]
        npx_pc = np.zeros(batch_n, dtype=np.int32)

        # Pass a direct slice of all_powder so the C function writes in-place
        batch_powder_flat = all_powder[batch_start:batch_start + batch_n].ravel()

        t0 = time.perf_counter()
        dc.fun(
            mmap, flat_mask,
            outpx_buf, outadr_buf, 0,
            batch_powder_flat, csc_data, csc_indices, csc_indptr,
            batch_offs, batch_lens, npx_pc,
        )
        t1 = time.perf_counter()
        c_total += t1 - t0

        for f in range(batch_n):
            frame = batch_start + f
            npx = npx_pc[f]
            all_sparse_vals[frame] = outpx_buf[f * NIJ : f * NIJ + npx].copy()
            all_sparse_inds[frame] = outadr_buf[f * NIJ : f * NIJ + npx].copy()
        t2 = time.perf_counter()
        copy_total += t2 - t1

    t_py1 = time.perf_counter()
    total_s = t_py1 - t_py0
    total_ms = total_s * 1000
    c_ms = c_total * 1000
    copy_ms = copy_total * 1000
    overhead_ms = total_ms - c_ms - copy_ms
    fps = NFRAMES / total_s

    print("  C call: %.0f ms   Copy: %.0f ms   Overhead: %.0f ms   FPS: %.1f" % (
        c_ms, copy_ms, overhead_ms, fps))

    results[bs] = {
        "total_ms": total_ms,
        "c_ms": c_ms,
        "copy_ms": copy_ms,
        "overhead_ms": overhead_ms,
        "fps": fps,
    }


# %% [markdown]
# ## 10. Plots

# %%
fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 5))

# Panel 1: FPS vs batch size
x = np.array(BATCH_SIZES, dtype=float)
y = np.array([results[bs]["fps"] for bs in BATCH_SIZES])
ax0.plot(x, y, "o-", color="steelblue", lw=2, ms=8)
ax0.axhline(y=y[0], color="gray", ls="--", alpha=0.5, label="bs=1 baseline (%.0f FPS)" % y[0])
ax0.set_xlabel("Batch size (frames per C call)")
ax0.set_ylabel("Throughput (frames / second)")
ax0.set_title("CSC Powder Integration Throughput")
ax0.set_xticks(BATCH_SIZES)
ax0.grid(True, alpha=0.3)
ax0.legend(fontsize=9)

# Panel 2: Stacked time breakdown
xr = np.arange(len(BATCH_SIZES))
c_vals   = np.array([results[bs]["c_ms"] for bs in BATCH_SIZES])
copy_vals = np.array([results[bs]["copy_ms"] for bs in BATCH_SIZES])
ov_vals  = np.array([results[bs]["overhead_ms"] for bs in BATCH_SIZES])

ax1.bar(xr, c_vals,    label="C function (decompress + CSC)", color="steelblue")
ax1.bar(xr, copy_vals, bottom=c_vals, label="Data copy (sparse + powder)", color="goldenrod")
ax1.bar(xr, ov_vals,   bottom=c_vals+copy_vals, label="Python overhead", color="lightcoral")

# Annotate total at top of each bar
for i in range(len(BATCH_SIZES)):
    tot = c_vals[i] + copy_vals[i] + ov_vals[i]
    ax1.text(i, tot + max(c_vals)*0.02, "%.0f ms" % tot, ha="center", fontsize=8)

ax1.set_xticks(xr)
ax1.set_xticklabels([str(bs) for bs in BATCH_SIZES])
ax1.set_xlabel("Batch size")
ax1.set_ylabel("Time (ms) for %d frames" % NFRAMES)
ax1.set_title("Time Breakdown (C vs Python)")
ax1.legend(fontsize=8)
ax1.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark.png")
plt.savefig(plot_path, dpi=120)
print("\nSaved plot: %s" % plot_path)


# %% [markdown]
# ## 11. Summary

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
print("  %-6s %10s %10s %10s %10s" % (
    "bs", "total_ms", "c_ms", "copy_ms", "FPS"))
print("  " + "-" * 54)
for bs in BATCH_SIZES:
    r = results[bs]
    print("  %-6d %10.0f %10.0f %10.0f %10.1f" % (
        bs, r["total_ms"], r["c_ms"], r["copy_ms"], r["fps"]))
print("=" * 65)

# Check sparse output sanity
npx_total = sum(len(v) for v in all_sparse_vals)
print("\nSparse pixels stored: %d across %d frames" % (npx_total, NFRAMES))
print("Powder shape: %s, dtype: %s" % (all_powder.shape, all_powder.dtype))
