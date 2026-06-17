"""pyFAI CSC integration regression test for bslz4.

Ported from bslz4_to_sparse/test/test_dot.py.
Compares bslz4_csc_u16 powder integration output against
pyFAI's reference AzimuthalIntegrator.integrate1d().

Requires: pyFAI, h5py, hdf5plugin
"""

import os
import numpy as np
import pytest
import c2ImageD11._cImageD11 as _m

pyFAI = pytest.importorskip("pyFAI")
h5py = pytest.importorskip("h5py")
hdf5plugin = pytest.importorskip("hdf5plugin")  # noqa

NFRAMES = 5
SHAPE = (NFRAMES, 2162, 2068)
TESTFILE = os.path.join(os.path.dirname(__file__), "sparsetest_dot.h5")


@pytest.fixture(scope="module")
def sparsetest():
    """Create a small Poisson test file if not present."""
    if not os.path.exists(TESTFILE):
        data = np.random.poisson(0.01, SHAPE).astype(np.uint16)
        with h5py.File(TESTFILE, "w") as f:
            f.create_dataset("data", data=data,
                             chunks=(1, SHAPE[1], SHAPE[2]),
                             compression=32008,
                             compression_opts=(0, 2))
    with h5py.File(TESTFILE, "r") as f:
        ds = f["data"]
        chunks = [(ds.id.read_direct_chunk((i, 0, 0)))
                  for i in range(NFRAMES)]
        ref_data = ds[:]
    return chunks, ref_data


@pytest.fixture(scope="module")
def integrator():
    """Set up a pyFAI AzimuthalIntegrator with CSC engine."""
    import pyFAI
    ai = pyFAI.AzimuthalIntegrator(
        dist=0.25, poni1=0.07, poni2=0.08,
        rot1=0.01, rot2=0.02, rot3=0.03,
        pixel1=75e-6, pixel2=75e-6,
        wavelength=12.3984 / 43.57,
        detector=pyFAI.detector_factory("Eiger2CdTe_4M"),
    )
    return ai


def test_csc_vs_pyfai(sparsetest, integrator):
    """Compare bslz4_csc_u16 powder against pyFAI integrate1d."""
    chunks, ref_data = sparsetest

    # pyFAI reference integration
    method = ("bbox", "CSC", "python")
    npt = 1500
    reference = [integrator.integrate1d(frm, npt, method=method)
                 for frm in ref_data]

    # Get CSC engine data
    method_key = None
    for k, v in integrator.engines.items():
        if hasattr(k, "algo") and k.algo == "CSC":
            method_key = k
            csc_engine = v.engine
            break
    if method_key is None:
        pytest.skip("CSC engine not available in this pyFAI build")

    data = np.ascontiguousarray(csc_engine.data.astype(np.float32))
    indices = np.ascontiguousarray(csc_engine.indices.astype(np.uint32))
    indptr = np.ascontiguousarray(csc_engine.indptr.astype(np.uint32))

    mask = (1 - integrator.mask).astype(np.uint8)
    N = mask.size
    powder_out = np.zeros(csc_engine.bins, dtype=np.float64)
    outpx = np.empty(N, dtype=np.uint16)
    outP = np.empty(N, dtype=np.uint32)

    for i, (filt_info, chunk) in enumerate(chunks):
        chunk_buf = np.frombuffer(chunk, dtype=np.uint8)
        npx = _m.bslz4_csc_u16(chunk_buf, mask.ravel(),
                                outpx, outP, 1,
                                powder_out,
                                data, indices, indptr)

        err_abs = np.abs(powder_out - reference[i].sum_signal)
        max_err = err_abs.max()
        # Relative error only where reference > 0
        nonzero = reference[i].sum_signal > 0
        max_rel = 0.0
        if nonzero.any():
            max_rel = (err_abs[nonzero] / reference[i].sum_signal[nonzero]).max()
        max_idx = err_abs.argmax()

        # Verify powder matches pyFAI reference within numerical tolerance
        assert max_err < 1e-4, (
            f"frame {i}: max abs error={max_err} at bin {max_idx}, "
            f"powder={powder_out[max_idx]:.6g} ref={reference[i].sum_signal[max_idx]:.6g}"
        )
        assert max_rel < 1e-4, (
            f"frame {i}: max rel error={max_rel} at bin {max_idx}"
        )
