# Multi-Chunk BSLZ4 CSC Benchmark

Processes bitshuffle-lz4 HDF5 frames with pyFAI CSC powder integration,
comparing batch sizes 1-32 frames per C call using the loop-interchanged
multi-chunk CSC decoder.

## Requirements

| Package | Purpose |
|---------|---------|
| python3, numpy | Runtime |
| matplotlib | Plotting |
| h5py, hdf5plugin | HDF5 read + bitshuffle-lz4 filter |
| pyFAI (>=2024) | CSC engine generation from PONI geometry |
| c2ImageD11 (build) | Multi-chunk bslz4_csc_u16 C extension |
| py-spy (optional) | Sampling profiling |

## Usage

```bash
cd examples/multi_chunk_bslz4

# Normal benchmark (single core, pinned)
bash runner.sh

# No core pinning
bash runner.sh --no-pin

# Profile with py-spy
bash runner.sh --profile
```

## Configuration

Edit the first code cell in `bench_csc.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `HDF5FILE` | `$HOME/test_data/eiger_0000.h5` | Input HDF5 file |
| `DATASET` | `entry_0000/ESRF-ID11/eiger/data` | Dataset path inside HDF5 |
| `MASKFILE` | `$HOME/test_data/eiger_mask.npy` | Detector mask |
| `PONIFILE` | `example.poni` (auto-created) | pyFAI geometry file |
| `NFRAMES` | 100 | Number of frames to process |
| `NOUT` | 1500 | Number of powder bins |
| `BATCH_SIZES` | [1,2,4,8,16,32] | Batch sizes to benchmark |

## Output

- `benchmark.png` — three-panel timing plot
- `profile_flame.svg` — py-spy flamegraph (with `--profile`)
- `profile_speedscope.json` — py-spy speedscope trace (with `--profile`)

## Notebook usage

The script uses `# %%` cell markers.  Open in VS Code with the Python
extension, Spyder, or convert to .ipynb:

```bash
pip install jupytext
jupytext --to notebook bench_csc.py -o bench_csc.ipynb
```

Then open `bench_csc.ipynb` in Jupyter.  Comment out the Agg backend line
(`matplotlib.use("Agg")`) and `plt.show()` will render inline.
