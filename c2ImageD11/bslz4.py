"""bslz4_to_sparse: decompress bitshuffle-lz4 data directly to sparse arrays.

Ported from the standalone bslz4_to_sparse package. Functions import from
c2ImageD11._cImageD11 (c2py23) instead of the f2py extension.

Provides:
    chunk2sparse(mask, dtype)   -- callable class for frame-by-frame decoding
    chunk2sparseCSC(mask, csc)  -- same with CSC powder integration
    bslz4_to_sparse(ds, num)    -- convenience for HDF5 datasets
"""

import numpy as np

from c2ImageD11._cImageD11 import (
    bslz4_u8,
    bslz4_u16,
    bslz4_u32,
    bslz4_csc_u8,
    bslz4_csc_u16,
    bslz4_csc_u32,
    bszstd_u8,
    bszstd_u16,
    bszstd_u32,
    bszstd_csc_u8,
    bszstd_csc_u16,
    bszstd_csc_u32,
)

version = "0.2.0"


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
    dtype : numpy dtype, optional
        Pixel data type. Default uint16.
    """

    def __init__(self, mask, csc, dtype=np.uint16):
        self.nfast = mask.shape[1]
        self.mask = mask.ravel()
        self.cscdata = csc.data
        self.cscindices = csc.indices
        self.cscindptr = csc.indptr
        assert len(csc.indptr) == len(self.mask) + 1, "csc shape must match mask"
        if hasattr(csc, "shape"):
            self.powder = np.empty(csc.shape[0], dtype=float)
        elif hasattr(csc, "bins"):
            self.powder = np.empty(csc.bins, dtype=float)
        else:
            raise Exception("csc argument has no shape or bins attribute")

        self.indices = np.empty(mask.size, np.uint32)
        self.values = np.empty(mask.size, dtype)

        itemsize = np.dtype(dtype).itemsize
        self.fun = (
            None,
            bslz4_csc_u8,
            bslz4_csc_u16,
            None,
            bslz4_csc_u32,
        )[itemsize]

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
