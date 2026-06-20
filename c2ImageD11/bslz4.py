"""bitshuffle decompress to sparse arrays.

Ported from the standalone bslz4_to_sparse package. Functions import from
c2ImageD11._cImageD11 (c2py23) instead of the f2py extension.

Provides:
    chunk2sparse(mask, ...)       -- frame-by-frame decoding
    chunk2sparseCSC(mask, csc, ..) -- CSC powder integration
    chunk2sparseCSC_1d(...)       -- 1D-padded CSC integration

Usage:
    mask = np.load("mask.npy")
    dc = chunk2sparse(mask, dtype=np.uint16, encoding=LZ4)
    npx, (vals, inds) = dc(chunk_bytes, cut=50)

    # Or from an h5py Dataset (auto-detects dtype and encoding):
    with h5py.File("data.h5") as f:
        dc = chunk2sparse(mask, dataset=f["entry/data"])
    npx, (vals, inds) = dc(chunk_bytes, cut=50)
"""

from __future__ import print_function

import os
import sys
import numpy as np

from c2ImageD11._cImageD11 import (
    bs_u8, bs_u16, bs_u32,
    bs_csc_u8, bs_csc_u16, bs_csc_u32,
    bs_csc1d_u8, bs_csc1d_u16, bs_csc1d_u32,
)

version = "0.3.0"

# encoding values matching bshuf_h5filter.h
LZ4  = 2
ZSTD = 3

# Pixel itemsize -> (basic_func, csc_func, csc1d_func)
_FUN_MAP = {
    1: (bs_u8,      bs_csc_u8,      bs_csc1d_u8),
    2: (bs_u16,     bs_csc_u16,     bs_csc1d_u16),
    4: (bs_u32,     bs_csc_u32,     bs_csc1d_u32),
}


def _get_fun_tuple(pixel_dtype):
    """Return (basic, csc, csc1d) functions for given pixel dtype."""
    pixel_dt = np.dtype(pixel_dtype)
    if pixel_dt.itemsize not in _FUN_MAP:
        raise ValueError(
            "Unsupported pixel dtype: %s (need uint8/uint16/uint32)" %
            str(pixel_dt))
    return _FUN_MAP[pixel_dt.itemsize]


def _detect_encoding(ds):
    """Read encoding (2=LZ4, 3=ZSTD) from h5py Dataset filter 32008.

    Filter 32008 params: (block_size, compressor, ...)
    compressor=2 for LZ4, 3 for ZSTD (bshuf_h5filter.h).
    """
    try:
        plist = ds.id.get_create_plist()
        nf = plist.get_nfilters()
        for i in range(nf):
            _, fid, _, parms, _ = plist.get_filter(i)
            if fid == 32008 and len(parms) >= 2:
                return parms[1]
    except Exception:
        pass
    return LZ4  # default


def _resolve_dtype_encoding(dtype, encoding, dataset):
    """Resolve dtype/encoding from args or dataset.

    Returns (dtype, encoding).
    Raises ValueError if dataset and explicit args conflict.
    """
    if dataset is not None:
        if dtype is not None or encoding is not None:
            raise ValueError(
                "cannot specify dtype or encoding when dataset is given")
        dtype = dataset.dtype
        encoding = _detect_encoding(dataset)
    else:
        if dtype is None or encoding is None:
            raise ValueError(
                "must specify either dataset, or both dtype and encoding")
    return np.dtype(dtype), encoding


class chunk2sparse:
    """Callable object for decompressing bitshuffle chunks to sparse.

    Parameters
    ----------
    mask : 2D numpy array
        Detector mask. Active pixels > 0.
    dtype : numpy dtype, optional
        Pixel data type. Required if dataset is not given.
    encoding : int, optional
        Compression format: LZ4=2, ZSTD=3. Required if dataset not given.
    dataset : h5py.Dataset, optional
        HDF5 dataset. If given, dtype and encoding are auto-detected.
        No reference to the dataset is stored.
    """

    def __init__(self, mask, dtype=None, encoding=None, dataset=None):
        dtype, encoding = _resolve_dtype_encoding(dtype, encoding, dataset)
        if dataset is not None:
            if mask.shape != dataset.shape[1:]:
                raise ValueError(
                    "mask shape %s does not match dataset frame shape %s" %
                    (mask.shape, dataset.shape[1:]))

        self.nfast = mask.shape[1]
        self.mask = mask.ravel()
        self.indices = np.empty(mask.size, np.uint32)
        self.values = np.empty(mask.size, dtype)
        self.encoding = encoding
        self.fun = _get_fun_tuple(dtype)[0]
        self._offsets  = np.array([0], dtype=np.int64)
        self._lengths  = np.zeros(1, dtype=np.int32)
        self._npx_pc   = np.zeros(1, dtype=np.int32)

    def __call__(self, buffer, cut):
        self._lengths[0] = len(buffer)
        npixels = self.fun(buffer, self.mask,
                           self.values, self.indices, cut, self.encoding,
                           self._offsets, self._lengths, self._npx_pc)
        return npixels, (self.values, self.indices)

    def coo(self, buffer, cut):
        """Computes i,j indices and MAKES COPIES"""
        npixels, _ = self.__call__(buffer, cut)
        row = np.empty(npixels, np.uint16)
        col = np.empty(npixels, np.uint16)
        np.divmod(self.indices[:npixels], self.nfast, out=(row, col))
        return npixels, row, col, self.values[:npixels].copy()


class chunk2sparseCSC:
    """Callable for decompressing bitshuffle chunks with powder integration.

    Parameters
    ----------
    mask : 2D ndarray
        Detector mask.
    csc : scipy.sparse.csc_matrix or pyFAI CSCIntegrator
        Sparse matrix in CSC format (data, indices, indptr, shape/bins).
    dtype : numpy dtype, optional
        Pixel data type. Required if dataset is not given.
    encoding : int, optional
        Compression format: LZ4=2, ZSTD=3. Required if dataset not given.
    dataset : h5py.Dataset, optional
        HDF5 dataset. If given, dtype and encoding are auto-detected.
    """

    def __init__(self, mask, csc, dtype=None, encoding=None, dataset=None):
        dtype, encoding = _resolve_dtype_encoding(dtype, encoding, dataset)
        if dataset is not None:
            if mask.shape != dataset.shape[1:]:
                raise ValueError(
                    "mask shape %s does not match dataset frame shape %s" %
                    (mask.shape, dataset.shape[1:]))

        self.nfast = mask.shape[1]
        self.mask = mask.ravel()
        self.cscdata = csc.data
        self.cscindices = csc.indices
        self.cscindptr = csc.indptr
        self.encoding = encoding
        assert len(csc.indptr) == len(self.mask) + 1, \
            "csc shape must match mask"

        # Determine number of output bins
        if hasattr(csc, "shape"):
            nbins = csc.shape[0]
        elif hasattr(csc, "bins"):
            nbins = csc.bins
        else:
            raise Exception("csc argument has no shape or bins attribute")

        self.fun = _get_fun_tuple(dtype)[1]
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
            buffer, self.mask, self.values, self.indices, cut,
            self.encoding,
            self.powder, self.cscdata, self.cscindices, self.cscindptr,
            self._offsets, self._lengths, self._npx_pc,
        )
        return npixels, (self.values, self.indices), self.powder

    def multi(self, file_buffer, offsets, lengths, cut=0, nframes=None):
        """Process N frames with loop interchange.

        Returns powder array (nframes, nbins).
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

        self.fun(
            file_buffer, self.mask,
            outpx, outadr, cut, self.encoding,
            powder, self.cscdata, self.cscindices, self.cscindptr,
            offsets[:nframes], lengths[:nframes], npx_pc,
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
        Pixel data type. Required if dataset is not given.
    encoding : int, optional
        Compression format: LZ4=2, ZSTD=3. Required if dataset not given.
    dataset : h5py.Dataset, optional
        HDF5 dataset. If given, dtype and encoding are auto-detected.
    """

    def __init__(self, mask, csc_flat, csc_first_bin,
                 entries_per_pixel,
                 dtype=None, encoding=None, dataset=None):
        dtype, encoding = _resolve_dtype_encoding(dtype, encoding, dataset)
        if dataset is not None:
            if mask.shape != dataset.shape[1:]:
                raise ValueError(
                    "mask shape %s does not match dataset frame shape %s" %
                    (mask.shape, dataset.shape[1:]))

        self.nfast = mask.shape[1]
        self.mask = mask.ravel()
        self.csc_flat = csc_flat
        self.csc_first_bin = csc_first_bin
        self.entries_per_pixel = entries_per_pixel
        self.encoding = encoding

        self.indices = np.empty(self.mask.size, np.uint32)
        self.values = np.empty(self.mask.size, dtype)

        self.fun = _get_fun_tuple(dtype)[2]

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
            buffer, self.mask, self.values, self.indices, cut,
            self.encoding,
            self.powder, self.csc_flat, self.csc_first_bin,
            self.entries_per_pixel,
            self._offsets, self._lengths, self._npx_pc,
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

        self.fun(
            file_buffer, self.mask,
            outpx, outadr, cut, self.encoding,
            powder, self.csc_flat, self.csc_first_bin,
            self.entries_per_pixel,
            offsets[:nframes], lengths[:nframes], npx_pc,
        )

        return powder.reshape((nframes, nout))


def index_file_2d(h5file, dataset):
    """Read chunk offsets from an HDF5 dataset (utility for multi-chunk IO).

    Returns (nframes, 3) array of [filter_mask, file_location, size]
    for each chunk/frame in the dataset.
    """
    import h5py
    with h5py.File(h5file, 'r') as hin:
        ds = hin[dataset]
        chunk_infos = np.zeros((3, len(ds)), dtype=np.int64)
        def callback(storeinfo):
            logical_offset, filter_mask, file_location, size = storeinfo
            chunk_infos[:, logical_offset[0]] = filter_mask, file_location, size
        ds.id.chunk_iter(callback)
    return chunk_infos
