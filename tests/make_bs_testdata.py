"""Generate bitshuffle-lz4 and bitshuffle-zstd test datasets for regression testing.

Creates small HDF5 files with known content across multiple shapes,
dtypes, and data distributions. Test functions can then compare
c2ImageD11 decompress output against pure-numpy reference.

Usage: python3 tests/make_bs_testdata.py [--all] [--zstd]
"""

import os, sys
import h5py
import hdf5plugin  # noqa: registers filter 32008
import numpy as np

H5NAME_LZ4 = os.path.join(os.path.dirname(__file__), "bslz4_testdata.h5")
H5NAME_ZSTD = os.path.join(os.path.dirname(__file__), "bszstd_testdata.h5")

SHAPES = [
    ("256sq", (4, 256, 256)),
    ("149x211", (4, 149, 211)),
]

DTYPES = [
    (np.uint8, "u8"),
    (np.uint16, "u16"),
    (np.uint32, "u32"),
]

METHODS = {
    "uniform15":  lambda n, dt: np.random.randint(0, 15, size=n, dtype=dt),
    "poisson1":   lambda n, dt: np.random.poisson(lam=1.0, size=n).astype(dt),
    "range_step": lambda n, dt: (np.arange(n, dtype=np.float64) / 31).astype(dt),
    "linear":     lambda n, dt: np.arange(n, dtype=dt),
}


def write_dataset(f, dsname, ary, engine):
    """Write a 3D array as a chunked+compressed dataset."""
    copts = (0, 3, 2, 0, 2) if engine == "zstd" else (0, 2, 0, 0, 2)
    f.create_dataset(dsname, data=ary,
                     chunks=(1, ary.shape[1], ary.shape[2]),
                     compression=32008, compression_opts=copts)


def generate(h5name, engine, shapes, dtypes):
    np.random.seed(10007 * 10009)

    if os.path.exists(h5name):
        os.remove(h5name)

    with h5py.File(h5name, "w") as f:
        for shape_name, shp in shapes:
            for dt, dt_label in dtypes:
                for method_name, method_fn in METHODS.items():
                    ary = method_fn(np.prod(shp), dt).reshape(shp)
                    dsname = f"{shape_name}_{dt_label}_{method_name}"
                    write_dataset(f, dsname, ary, engine)
                    print(f"  {engine} {dsname}: {shp} {dt_label}")


def main():
    args = set(sys.argv[1:])
    do_lz4 = True
    do_zstd = "--zstd" in args

    if do_lz4:
        print("Generating LZ4 test data...")
        generate(H5NAME_LZ4, "lz4", SHAPES, DTYPES)
        print("  ->", H5NAME_LZ4)

    if do_zstd:
        print("Generating ZSTD test data...")
        generate(H5NAME_ZSTD, "zstd", SHAPES, DTYPES)
        print("  ->", H5NAME_ZSTD)


if __name__ == "__main__":
    main()
