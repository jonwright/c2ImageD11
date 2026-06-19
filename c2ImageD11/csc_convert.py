"""Convert pyFAI CSC matrices to c2ImageD11 1D padded format.

Generates a CSC matrix from a pyFAI PONI geometry file, converts to
the 1D padded format (flat array + first_bin per pixel), quantizes
weights to integer types with a scale factor, and saves/loads via HDF5.

Usage:
    from c2ImageD11.csc_convert import generate_csc, to_1d_padded

    # From PONI
    csc_data, csc_indices, csc_indptr, mask, nbins = generate_csc("example.poni")

    # Convert to 1D padded
    flat, first_bin, epp = to_1d_padded(csc_data, csc_indices, csc_indptr, mask)

    # Quantize
    flat_u16 = quantize_weights(flat, scale_factor=32768, dtype=np.uint16)

    # Save
    save_csc_1d("my_csc.h5", flat_u16, first_bin, nout=nbins,
                 scale_factor=32768, quantized_dtype="uint16")
"""

from __future__ import print_function

import json
import os
import numpy as np

_HAS_PYFAI = False
try:
    import pyFAI
    from pyFAI.integrator.azimuthal import AzimuthalIntegrator
    _HAS_PYFAI = True
except ImportError:
    pass

_HAS_H5PY = False
try:
    import h5py
    _HAS_H5PY = True
except ImportError:
    pass


def generate_csc(poni_path, nout=2500):
    """Generate pyFAI CSC matrix from a PONI file.

    Parameters
    ----------
    poni_path : str
        Path to pyFAI .poni geometry file.
    nout : int
        Number of output bins.

    Returns
    -------
    data : ndarray (nnz,) float32
        CSC data (weights).
    indices : ndarray (nnz,) uint32
        CSC bin indices.
    indptr : ndarray (NIJ+1,) uint32
        CSC column pointers.
    mask : ndarray (ROWS, COLS) uint8
        Detector mask (1=active, 0=masked) normalized to C convention.
    nbins : int
        Number of output bins.
    """
    if not _HAS_PYFAI:
        raise ImportError("pyFAI is required to generate CSC matrices. "
                          "Install with: pip install pyFAI")

    with open(poni_path) as f:
        poni = json.load(f)

    det = pyFAI.detector_factory(poni["detector"])
    ai = AzimuthalIntegrator()
    ai.set_config(poni)
    if hasattr(ai, "wavelength") and "wavelength" in poni:
        ai.wavelength = poni["wavelength"]

    dummy = np.zeros((det.shape[0], det.shape[1]), dtype=np.float64)
    ai.integrate1d(dummy, nout, method=("bbox", "CSC", "python"))

    csc_engine = None
    for k, v in ai.engines.items():
        if hasattr(k, "algo") and k.algo == "CSC":
            csc_engine = v.engine
            break
    if csc_engine is None:
        raise RuntimeError("CSC engine not found in pyFAI")

    data = np.ascontiguousarray(csc_engine.data.astype(np.float32))
    indices = np.ascontiguousarray(csc_engine.indices.astype(np.uint32))
    indptr = np.ascontiguousarray(csc_engine.indptr.astype(np.uint32))
    nbins = csc_engine.bins
    NIJ = len(indptr) - 1

    # Build mask (all 1=active — pyFAI mask is 1=masked)
    if hasattr(ai, "mask") and ai.mask is not None:
        raw_mask = ai.mask.ravel()
    else:
        raw_mask = np.zeros(NIJ, dtype=np.uint8)
    mask = (1 - raw_mask).astype(np.uint8).reshape(det.shape)

    print("CSC: NIJ=%d nnz=%d bins=%d" % (NIJ, len(data), nbins))
    return data, indices, indptr, mask, nbins


def to_1d_padded(data, indices, indptr, mask, verify=True, entries_per_pixel=None):
    """Convert standard CSC (data/indices/indptr) to 1D padded format.

    The 1D padded format stores exactly E entries per pixel (zero-padded),
    where E = max entries across all pixels (capped at 12).  The arrays are
    dense (NIJ * E elements for csc_flat, NIJ elements for first_bin).

    Parameters
    ----------
    data : ndarray (nnz,) float32
        Weights.
    indices : ndarray (nnz,) uint32
        Bin indices.
    indptr : ndarray (NIJ+1,) uint32
        Column pointers.
    mask : ndarray (ROWS, COLS) uint8
        Detector mask 1=active.
    verify : bool
        Verify indices are sequential and weights sum to 1.0 (sample).
    entries_per_pixel : int, optional
        Pad width.  If None, computed from data (max entries across all pixels).

    Returns
    -------
    csc_flat : ndarray (NIJ * entries_per_pixel,) float32
        Padded weights, zero-filled.
    first_bin : ndarray (NIJ,) uint32
        First bin index for each pixel.
    entries_per_pixel : int
        Max entries across all pixels (also the pad width).
    """
    if mask.ndim == 2:
        mask = mask.ravel()
    NIJ = len(indptr) - 1

    counts = np.diff(indptr)
    if entries_per_pixel is None:
        entries_per_pixel = int(counts.max())

    if verify and NIJ <= 50000:
        # Verify sequential indices (first 50000 pixels)
        non_seq = 0
        for j in range(min(NIJ, 50000)):
            s = int(indptr[j]); e = int(indptr[j+1])
            if e - s >= 2 and not np.all(np.diff(indices[s:e]) == 1):
                non_seq += 1
        if non_seq:
            print("WARNING: %d/%d pixels have non-sequential indices. "
                  "Use standard CSC (not 1D) for 2D integration." % (non_seq, min(NIJ, 50000)))

        # Verify weight sum = 1 (sample, first 50000 non-zero)
        sums = np.zeros(min(NIJ, 50000), dtype=np.float64)
        for j in range(min(NIJ, 50000)):
            s = int(indptr[j]); e = int(indptr[j+1])
            if e > s:
                sums[j] = data[s:e].sum()
        active = sums > 0
        if active.any():
            print("  Weight sum per pixel: min=%.6f max=%.6f" % (
                sums[active].min(), sums[active].max()))

    # Build padded arrays using vectorized scatter
    csc_flat = np.zeros(NIJ * entries_per_pixel, dtype=np.float32)
    first_bin = np.zeros(NIJ, dtype=np.uint32)

    # first_bin: gather first bin index per pixel (where cnt > 0)
    has_data = counts > 0
    first_bin[has_data] = indices[indptr[:-1][has_data]]

    # csc_flat: scatter data into padded positions
    cnts = counts.astype(np.intp)
    nnz = len(data)
    pixel_idx = np.repeat(np.arange(NIJ, dtype=np.intp), cnts)  # which pixel
    local_idx = np.empty(nnz, dtype=np.intp)
    pos = 0
    for j in range(NIJ):
        if cnts[j]:
            local_idx[pos:pos + cnts[j]] = np.arange(cnts[j], dtype=np.intp)
            pos += cnts[j]
    pad_pos = pixel_idx * entries_per_pixel + local_idx
    csc_flat[pad_pos] = data

    print("1D padded: entries_per_pixel=%d, flat size=%.1f MB" % (
        entries_per_pixel, csc_flat.nbytes / 1e6))
    return csc_flat, first_bin, entries_per_pixel


def quantize_weights(csc_flat, scale_factor, dtype=np.uint16, mask=None,
                     entries_per_pixel=None):
    """Quantize float32 CSC weights to integer type.

    Each pixel's weights are quantized as:
        w_int = nearest_int(w_float * scale_factor)

    The sum of quantized weights per pixel is adjusted to exactly
    equal scale_factor by incrementing the largest entry (handles
    rounding errors).  Masked pixels (all weights zero) are skipped.

    Parameters
    ----------
    csc_flat : ndarray (NIJ * entries_per_pixel,) float32
        Padded 1D CSC weights.
    scale_factor : int
        Scale factor for quantization.
    dtype : numpy dtype
        Target type (np.uint8, np.uint16, np.uint32).
    mask : ndarray (NIJ,), optional
        Active pixel mask (1=active).
    entries_per_pixel : int, optional
        Pad width.  If None, computed from flat array size and mask.

    Returns
    -------
    csc_quant : ndarray (NIJ * entries_per_pixel,) dtype
        Quantized weights.
    """
    NIJ_E = len(csc_flat)
    if entries_per_pixel is not None:
        epp = entries_per_pixel
    elif mask is not None:
        NIJ = len(mask.ravel())
        epp = NIJ_E // NIJ
    else:
        raise ValueError("entries_per_pixel or mask required")
    NIJ = NIJ_E // epp

    csc_quant = np.round(csc_flat * scale_factor).astype(dtype)

    if mask is None:
        mask = np.ones(NIJ, dtype=np.uint8)
    else:
        mask = mask.ravel()

    # Fix per-pixel rounding sum to exactly scale_factor
    active = np.where(mask > 0)[0]
    for j in active:
        base = j * epp
        row = csc_quant[base:base + epp]
        s = int(row.sum(dtype=np.int64))
        if s > 0 and s != scale_factor:
            idx = int(np.argmax(row))
            diff = scale_factor - s
            new_val = int(row[idx]) + diff
            if 0 <= new_val <= np.iinfo(dtype).max:
                row[idx] = dtype(new_val)

    return csc_quant


def save_csc_1d(h5path, csc_flat, csc_first_bin, nout,
                scale_factor=None, quantized_dtype=None,
                entries_per_pixel=None, description=""):
    """Save 1D padded CSC to HDF5.

    Parameters
    ----------
    h5path : str
        Output .h5 path.
    csc_flat : ndarray
        Padded weights (float32 or integer).
    csc_first_bin : ndarray (NIJ,) uint32
        First bin index per pixel.
    nout : int
        Number of output bins.
    scale_factor : int, optional
        Scale factor if quantized.
    quantized_dtype : str, optional
        "uint8", "uint16", "uint32" if quantized.
    entries_per_pixel : int, optional
        Auto-detected if not provided.
    description : str
        Dataset attribute.
    """
    if not _HAS_H5PY:
        raise ImportError("h5py required to save CSC to HDF5")

    NIJ_E = len(csc_flat)
    NIJ = len(csc_first_bin)
    entries_per_pixel = NIJ_E // NIJ
    if entries_per_pixel * NIJ != NIJ_E:
        # Detect differently
        eps_val = NIJ_E // NIJ
        entries_per_pixel = eps_val

    with h5py.File(h5path, "w") as f:
        f.attrs["format"] = "c2ImageD11_csc_1d"
        f.attrs["version"] = 1
        f.attrs["nout"] = nout
        f.attrs["entries_per_pixel"] = entries_per_pixel
        f.attrs["description"] = str(description)
        if scale_factor is not None:
            f.attrs["scale_factor"] = scale_factor
        if quantized_dtype is not None:
            f.attrs["quantized_dtype"] = quantized_dtype

        f.create_dataset("csc_flat", data=csc_flat, compression="gzip",
                         shuffle=True)
        f.create_dataset("csc_first_bin", data=csc_first_bin, compression="gzip",
                         shuffle=True)

    print("Saved: %s (%.1f MB)" % (h5path, os.path.getsize(h5path) / 1e6))


def load_csc_1d(h5path, dataset="csc_flat"):
    """Load 1D padded CSC from HDF5.

    Parameters
    ----------
    h5path : str
        Input .h5 path.
    dataset : str
        Dataset name.

    Returns
    -------
    csc_flat : ndarray or None
        Padded weights.
    csc_first_bin : ndarray or None
        First bin index per pixel.
    nout : int
        Number of output bins.
    entries_per_pixel : int
        Pad width.
    scale_factor : int or None
        Scale factor if quantized.
    quantized_dtype : str or None
        Quantized data type if quantized.
    """
    if not _HAS_H5PY:
        raise ImportError("h5py required to load CSC from HDF5")

    if not os.path.exists(h5path):
        print("File not found: %s" % h5path)
        return None, None, 0, 0, None, None

    with h5py.File(h5path, "r") as f:
        fmt = f.attrs.get("format", "")
        if fmt != "c2ImageD11_csc_1d":
            raise ValueError("Unknown format: %s" % fmt)

        nout = int(f.attrs["nout"])
        entries_per_pixel = int(f.attrs.get("entries_per_pixel", 0))
        scale_factor = int(f.attrs["scale_factor"]) if "scale_factor" in f.attrs else None
        quantized_dtype = str(f.attrs.get("quantized_dtype", "")) or None

        csc_flat = np.ascontiguousarray(f["csc_flat"][:])
        csc_first_bin = np.ascontiguousarray(f["csc_first_bin"][:])

    if entries_per_pixel == 0:
        entries_per_pixel = len(csc_flat) // len(csc_first_bin)

    print("Loaded: %s (%.1f MB, nout=%d, epp=%d)" % (
        h5path, csc_flat.nbytes / 1e6, nout, entries_per_pixel))
    return csc_flat, csc_first_bin, nout, entries_per_pixel, scale_factor, quantized_dtype
