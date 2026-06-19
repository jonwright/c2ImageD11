"""bslz4_to_sparse: decompress bitshuffle-lz4 data directly to sparse arrays.

Ported from the standalone bslz4_to_sparse package. Functions import from
c2ImageD11._cImageD11 (c2py23) instead of the f2py extension.

Provides:
    chunk2sparse(mask, dtype)   -- callable class for frame-by-frame decoding
    chunk2sparseCSC(mask, csc)  -- same with CSC powder integration
    bslz4_to_sparse(ds, num)    -- convenience for HDF5 datasets

CSC powder integration supports both float and integer CSC matrix data:
    float CSC data  -> f64 histogram (existing behaviour)
    integer CSC data -> u64 histogram (exact arithmetic, no roundoff)
"""

from __future__ import print_function

import os
import sys
import numpy as np

# Basic decompress functions (used by chunk2sparse and bslz4_to_sparse)
from c2ImageD11._cImageD11 import (
    bslz4_u8,
    bslz4_u16,
    bslz4_u32,
    bszstd_u8,
    bszstd_u16,
    bszstd_u32,
)

version = "0.2.0"

# Pixel itemsize -> type suffix lookup
_PIXEL_SUFFIX = {1: "u8", 2: "u16", 4: "u32"}

# Integer CSC itemsize -> type suffix lookup (c prefix = csc data type)
_CSC_INT_SUFFIX = {1: "cu8", 2: "cu16", 4: "cu32"}


def _get_csc_function(pixel_dtype, csc_data_dtype):
    """Return the right bslz4_csc_* function for given pixel and CSC data types.

    For float CSC data: uses legacy naming (bslz4_csc_u16)
    For integer CSC data: uses new naming (bslz4_csc_u16_cu16)

    Returns (function, powder_dtype) tuple.
    """
    import c2ImageD11._cImageD11 as _m

    pixel_dt = np.dtype(pixel_dtype)
    pixel_itemsize = pixel_dt.itemsize
    if pixel_itemsize not in _PIXEL_SUFFIX:
        raise ValueError(
            "Unsupported pixel dtype: %s (need uint8/uint16/uint32)" %
            str(pixel_dt))

    pixel_suffix = _PIXEL_SUFFIX[pixel_itemsize]

    csc_dt = np.dtype(csc_data_dtype)
    if np.issubdtype(csc_dt, np.integer):
        csc_itemsize = csc_dt.itemsize
        if csc_itemsize not in _CSC_INT_SUFFIX:
            raise ValueError(
                "Unsupported integer CSC dtype: %s "
                "(need uint8/uint16/uint32)" % str(csc_dt))
        csc_suffix = _CSC_INT_SUFFIX[csc_itemsize]
        fn_name = "bslz4_csc_%s_%s" % (pixel_suffix, csc_suffix)
        powder_dtype = np.uint64
    else:
        fn_name = "bslz4_csc_%s" % pixel_suffix
        powder_dtype = np.float64

    try:
        fun = getattr(_m, fn_name)
    except AttributeError:
        raise ValueError(
            "CSC function %s not found in _cImageD11. "
            "Supported: u8/u16/u32 pixel types x "
            "f32/u8/u16/u32 CSC data types." % fn_name)

    return fun, powder_dtype


class chunk2sparse:
    """Callable object for decompressing bitshuffle-lz4 chunks to sparse.

    Parameters
    ----------
    mask : 2D numpy array
        Detector mask. Active pixels > 0.
    dtype : numpy dtype, optional
        Pixel data type. Default uint16.

    Methods
    -------
    __call__(buffer, cut)
        Returns (npixels, (values, indices))

    coo(buffer, cut)
        Returns (npixels, row, col, values_copy)
    """

    def __init__(self, mask, dtype=np.uint16):
        self.nfast = mask.shape[1]
        self.mask = mask.ravel()
        self.indices = np.empty(mask.size, np.uint32)
        self.values = np.empty(mask.size, dtype)
        self.dtype = dtype
        itemsize = np.dtype(dtype).itemsize
        self.fun = (
            None,
            bslz4_u8,
            bslz4_u16,
            None,
            bslz4_u32,
        )[itemsize]

    def __call__(self, buffer, cut):
        npixels = self.fun(buffer, self.mask,
                           self.values, self.indices, cut)
        return npixels, (self.values, self.indices)

    def coo(self, buffer, cut):
        """Computes i,j indices and MAKES COPIES"""
        npixels, _ = self.__call__(buffer, cut)
        row = np.empty(npixels, np.uint16)
        col = np.empty(npixels, np.uint16)
        np.divmod(self.indices[:npixels], self.nfast, out=(row, col))
        return npixels, row, col, self.values[:npixels].copy()


def bslz4_to_sparse(ds, num, cut, mask=None, pixelbuffer=None):
    """Read a bitshuffle-lz4 compressed HDF5 dataset and convert to sparse.

    Parameters
    ----------
    ds : h5py.Dataset
        HDF5 dataset containing [nframes, ni, nj] pixels.
    num : int
        Frame number to read.
    cut : int
        Threshold. Pixels below this value are ignored.
    mask : ndarray, optional
        Detector mask. Active pixels > 0. Default: all ones.
    pixelbuffer : tuple, optional
        (values, indices) storage space.

    Returns
    -------
    npixels : int
        Number of pixels found.
    (values, indices) : tuple of ndarrays
        Pixel values and flat indices.
    """
    if sys.version_info[0] < 3:
        raise RuntimeError(
            "bslz4_to_sparse is not supported on Python 2.7. "
            "TODO: debug and fix"
        )
    if mask is None:
        mask = np.ones((ds.shape[1], ds.shape[2]), np.uint8).ravel()
    if pixelbuffer is None:
        indices = np.empty((ds.shape[1], ds.shape[2]), np.uint32).ravel()
        values = np.empty((ds.shape[1], ds.shape[2]), ds.dtype).ravel()
    else:
        values, indices = pixelbuffer
    filtinfo, buffer = ds.id.read_direct_chunk((num, 0, 0))
    if ds.dtype == np.uint16:
        npixels = bslz4_u16(buffer, mask, values, indices, cut)
    elif ds.dtype == np.uint32:
        npixels = bslz4_u32(buffer, mask, values, indices, cut)
    elif ds.dtype == np.uint8:
        npixels = bslz4_u8(buffer, mask, values, indices, cut)
    else:
        raise Exception("no decoder for your type")
    if npixels < 0:
        raise Exception("Error decoding: %d" % (npixels))
    return npixels, (values, indices)


class chunk2sparseCSC:
    """Callable for decompressing bitshuffle-lz4 chunks with powder integration.

    Parameters
    ----------
    mask : 2D ndarray
        Detector mask.
    csc : scipy.sparse.csc_matrix or pyFAI CSCIntegrator
        Sparse matrix in CSC format (data, indices, indptr, shape/bins).
        CSC data dtype may be float32 (legacy, f64 output) or
        uint8/uint16/uint32 (integer, u64 exact output).
    dtype : numpy dtype, optional
        Pixel data type. Default uint16.

    Float CSC data yields float64 powder (existing behaviour).
    Integer CSC data yields uint64 powder (exact arithmetic, no roundoff).
    """

    def __init__(self, mask, csc, dtype=np.uint16):
        self.nfast = mask.shape[1]
        self.mask = mask.ravel()
        self.cscdata = csc.data
        self.cscindices = csc.indices
        self.cscindptr = csc.indptr
        assert len(csc.indptr) == len(self.mask) + 1, \
            "csc shape must match mask"

        # Determine number of output bins
        if hasattr(csc, "shape"):
            nbins = csc.shape[0]
        elif hasattr(csc, "bins"):
            nbins = csc.bins
        else:
            raise Exception("csc argument has no shape or bins attribute")

        # Look up CSC function and allocate powder with correct dtype
        self.fun, powder_dtype = _get_csc_function(dtype, csc.data.dtype)
        self.powder = np.empty(nbins, dtype=powder_dtype)

        self.indices = np.empty(mask.size, np.uint32)
        self.values = np.empty(mask.size, dtype)

    def __call__(self, buffer, cut):
        """Decompress buffer. All pixels go into powder integration,
        pixels above cut go into (values, indices).

        Returns npixels, (values, indices), powder_sum
        """
        npixels = self.fun(
            buffer,
            self.mask,
            self.values,
            self.indices,
            cut,
            self.powder,
            self.cscdata,
            self.cscindices,
            self.cscindptr,
        )
        return npixels, (self.values, self.indices), self.powder

    def coo(self, buffer, cut):
        """Computes i,j indices and MAKES COPIES"""
        npixels, _, powder = self.__call__(buffer, cut)
        row = np.empty(npixels, np.uint16)
        col = np.empty(npixels, np.uint16)
        np.divmod(self.indices[:npixels], self.nfast, out=(row, col))
        return (npixels, row, col,
                self.values[:npixels].copy(), powder.copy())
