"""bslz4_to_sparse: decompress bitshuffle-lz4 data directly to sparse arrays.

Ported from the standalone bslz4_to_sparse package. Functions import from
c2ImageD11._cImageD11 (c2py23) instead of the f2py extension.

Provides:
    chunk2sparse(mask, dtype)   -- callable class for frame-by-frame decoding
    chunk2sparseCSC(mask, csc)  -- same with CSC powder integration
    bslz4_to_sparse(ds, num)    -- convenience for HDF5 datasets
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


def _get_csc_function(pixel_dtype):
    """Return the right bslz4_csc_* function for given pixel type.

    Returns function object (powder is always float64).
    """
    import c2ImageD11._cImageD11 as _m

    pixel_dt = np.dtype(pixel_dtype)
    pixel_itemsize = pixel_dt.itemsize
    if pixel_itemsize not in _PIXEL_SUFFIX:
        raise ValueError(
            "Unsupported pixel dtype: %s (need uint8/uint16/uint32)" %
            str(pixel_dt))

    fn_name = "bslz4_csc_%s" % _PIXEL_SUFFIX[pixel_itemsize]

    try:
        return getattr(_m, fn_name)
    except AttributeError:
        raise ValueError(
            "CSC function %s not found in _cImageD11." % fn_name)


def _get_csc_1d_function(pixel_dtype):
    """Return the right bslz4_csc1d_* function for given pixel type.

    Returns function object (powder is always float64).
    """
    import c2ImageD11._cImageD11 as _m

    pixel_dt = np.dtype(pixel_dtype)
    pixel_itemsize = pixel_dt.itemsize
    if pixel_itemsize not in _PIXEL_SUFFIX:
        raise ValueError(
            "Unsupported pixel dtype: %s (need uint8/uint16/uint32)" %
            str(pixel_dt))

    fn_name = "bslz4_csc1d_%s" % _PIXEL_SUFFIX[pixel_itemsize]

    try:
        return getattr(_m, fn_name)
    except AttributeError:
        raise ValueError(
            "CSC1D function %s not found in _cImageD11." % fn_name)


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
        self._offsets  = np.array([0], dtype=np.int64)
        self._lengths  = np.zeros(1, dtype=np.int32)
        self._npx_pc   = np.zeros(1, dtype=np.int32)

    def __call__(self, buffer, cut):
        self._lengths[0] = len(buffer)
        npixels = self.fun(buffer, self.mask,
                           self.values, self.indices, cut,
                           self._offsets, self._lengths, self._npx_pc)
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
    offs  = np.array([0], dtype=np.int64)
    lens  = np.array([len(buffer)], dtype=np.int32)
    npc   = np.zeros(1, dtype=np.int32)
    if ds.dtype == np.uint16:
        npixels = bslz4_u16(buffer, mask, values, indices, cut,
                            offs, lens, npc)
    elif ds.dtype == np.uint32:
        npixels = bslz4_u32(buffer, mask, values, indices, cut,
                            offs, lens, npc)
    elif ds.dtype == np.uint8:
        npixels = bslz4_u8(buffer, mask, values, indices, cut,
                           offs, lens, npc)
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
    dtype : numpy dtype, optional
        Pixel data type. Default uint16.
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

        # Look up CSC function. Powder is always float64.
        self.fun = _get_csc_function(dtype)
        self.powder = np.empty(nbins, dtype=np.float64)

        self.indices = np.empty(mask.size, np.uint32)
        self.values = np.empty(mask.size, dtype)
        self._offsets  = np.array([0], dtype=np.int64)
        self._lengths  = np.zeros(1, dtype=np.int32)
        self._npx_pc   = np.zeros(1, dtype=np.int32)

    def __call__(self, buffer, cut):
        """Decompress buffer. All pixels go into powder integration,
        pixels above cut go into (values, indices).

        Returns npixels, (values, indices), powder_sum
        """
        self._lengths[0] = len(buffer)
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
            self._offsets,
            self._lengths,
            self._npx_pc,
        )
        return npixels, (self.values, self.indices), self.powder

    def multi(self, file_buffer, offsets, lengths, cut=0, nframes=None):
        """Process N frames with loop interchange.

        Parameters
        ----------
        file_buffer : ndarray
            Memory-mapped HDF5 file as uint8 flat buffer (from numpy.memmap).
        offsets : ndarray
            Byte offsets of each chunk (int64, shape [N]).
        lengths : ndarray
            Compressed lengths of each chunk (int32, shape [N]).
        cut : int
            Threshold. Default 0.
        nframes : int, optional
            Number of frames to process. Default: len(offsets).

        Returns
        -------
        powder : ndarray (nframes, nbins)
            Per-frame powder histograms.
        """
        if nframes is None:
            nframes = len(offsets)
        if nframes > len(offsets):
            raise ValueError(
                "nframes=%d > len(offsets)=%d" % (nframes, len(offsets)))
        nout = len(self.powder)
        nij  = len(self.mask)
        powder = np.zeros(nframes * nout, dtype=self.powder.dtype)

        outpx   = np.zeros(nframes * nij, dtype=self.values.dtype)
        outadr  = np.zeros(nframes * nij, dtype=np.uint32)
        npx_pc  = np.zeros(nframes, dtype=np.int32)

        off = offsets[:nframes]
        le  = lengths[:nframes]

        self.fun(
            file_buffer, self.mask,
            outpx, outadr, cut,
            powder, self.cscdata, self.cscindices, self.cscindptr,
            off, le, npx_pc,
        )

        return powder.reshape((nframes, nout))

    def coo(self, buffer, cut):
        """Computes i,j indices and MAKES COPIES"""
        npixels, _, powder = self.__call__(buffer, cut)
        row = np.empty(npixels, np.uint16)
        col = np.empty(npixels, np.uint16)
        np.divmod(self.indices[:npixels], self.nfast, out=(row, col))
        return (npixels, row, col,
                self.values[:npixels].copy(), powder.copy())


class chunk2sparseCSC_1d(object):
    """1D padded CSC integration with uniform padded entries.

    Uses bslz4_csc1d_* functions where each pixel has exactly
    entries_per_pixel entries (zero-padded if fewer in pyFAI matrix).

    Parameters
    ----------
    mask : 2D ndarray
        Detector mask (1=active).
    csc_flat : ndarray (NIJ * entries_per_pixel)
        Padded weights (float32).
    csc_first_bin : ndarray (NIJ,)
        First bin index per pixel.
    entries_per_pixel : int
        Pad width (max entries per pixel).
    dtype : numpy dtype, optional
        Pixel data type. Default uint16.
    """

    def __init__(self, mask, csc_flat, csc_first_bin,
                 entries_per_pixel,
                 dtype=np.uint16):
        self.nfast = mask.shape[1]
        self.mask = mask.ravel()
        self.csc_flat = csc_flat
        self.csc_first_bin = csc_first_bin
        self.entries_per_pixel = entries_per_pixel

        self.indices = np.empty(self.mask.size, np.uint32)
        self.values = np.empty(self.mask.size, dtype)

        # Look up CSC1D function. Powder is always float64.
        self.fun = _get_csc_1d_function(dtype)

        self.powder = np.empty(0, dtype=np.float64)
        self._offsets  = np.array([0], dtype=np.int64)
        self._lengths  = np.zeros(1, dtype=np.int32)
        self._npx_pc   = np.zeros(1, dtype=np.int32)

    def __call__(self, buffer, cut):
        """Decompress one chunk.

        Returns npixels, (values, indices), powder
        """
        if len(self.powder) == 0:
            raise RuntimeError("powder not initialized; call set_nout(nbins)")
        self._lengths[0] = len(buffer)
        npixels = self.fun(
            buffer,
            self.mask,
            self.values,
            self.indices,
            cut,
            self.powder,
            self.csc_flat,
            self.csc_first_bin,
            self.entries_per_pixel,
            self._offsets,
            self._lengths,
            self._npx_pc,
        )
        return npixels, (self.values, self.indices), self.powder

    def set_nout(self, nout):
        """Allocate powder buffer.  Must be called before processing."""
        self.powder = np.zeros(nout, dtype=self.powder.dtype)

    def multi(self, file_buffer, offsets, lengths, cut=0, nframes=None):
        """Process N frames with loop interchange.

        Returns powder array (nframes, nbins), float64.
        """
        if nframes is None:
            nframes = len(offsets)
        if nframes > len(offsets):
            raise ValueError(
                "nframes=%d > len(offsets)=%d" % (nframes, len(offsets)))
        if len(self.powder) == 0:
            raise RuntimeError("powder not initialized; call set_nout(nbins)")
        nout = len(self.powder)
        nij  = len(self.mask)
        powder = np.zeros(nframes * nout, dtype=self.powder.dtype)

        outpx  = np.zeros(nframes * nij, dtype=self.values.dtype)
        outadr = np.zeros(nframes * nij, dtype=np.uint32)
        npx_pc = np.zeros(nframes, dtype=np.int32)

        off = offsets[:nframes]
        le  = lengths[:nframes]

        self.fun(
            file_buffer, self.mask,
            outpx, outadr, cut,
            powder, self.csc_flat, self.csc_first_bin,
            self.entries_per_pixel,
            off, le, npx_pc,
        )

        return powder.reshape((nframes, nout))
