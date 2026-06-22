"""
c2ImageD11 - compiled C extensions for ImageD11, built with c2py23.

Import chain:
  c2ImageD11/__init__.py (this file)
    -> c2ImageD11._cImageD11 (compiled .so via c2py23)
    -> c2ImageD11._constants (blob property enum values)
    -> c2ImageD11.bslz4 (bitshuffle-lz4 sparse decoding)

Provides:
  - All C functions re-exported from _cImageD11
  - Module-level blob property constants (s_1, s_I, NPROPERTY, etc.)
  - put_incr dispatch (32 vs 64 bit addressing)
  - OpenMP / multiprocessing safety
  - bslz4 submodule: chunk2sparse, chunk2sparseCSC, bslz4_to_sparse

c2py23 now handles optional parameter defaults and fixed-width
integer types directly, so Python-level wrapper functions are no
longer needed.
"""

from __future__ import print_function

import os
import struct
import warnings

from c2ImageD11._cImageD11 import *
from c2ImageD11._constants import *

# Save C function references before Python wrappers override them
_blobproperties_c = blobproperties
_splat_c = splat
_array_stats_c = array_stats
_array_mean_var_cut_c = array_mean_var_cut
_array_mean_var_msk_c = array_mean_var_msk
_localmaxlabel_c = localmaxlabel
_compute_geometry_c = compute_geometry
_compute_xlylzl_c = compute_xlylzl


def _compat_deprecated(name):
    """Issue DeprecationWarning for f2py-compatibility wrappers."""
    warnings.warn(
        "%s() is an f2py-compatibility wrapper and will be removed "
        "in a future release." % name,
        DeprecationWarning, stacklevel=3)


# ---------------------------------------------------------------------------
# f2py-compatibility wrappers (with DeprecationWarning)
#
# Functions that now use c2py23 `outputs:` return tuples natively
# matching the f2py convention, so they need no wrapper:
#   closest(x, v)        -> (ibest, best)
#   score_and_refine(u,gv,tol) -> (npk, drlv2)
#   array_stats(img)     -> (min, max, mean, var)
#   array_mean_var_cut(img) -> (mean, var)
#   array_mean_var_msk(img, msk) -> (mean, var)
#   refine_assigned(ubi,gv,labels,label) -> (npk, drlv2)
# ---------------------------------------------------------------------------

def blobproperties(data, labels, npk, omega=0.0, verbose=0):
    """Blob properties: allocates and returns results array (f2py-compatible)."""
    _compat_deprecated('blobproperties')
    import numpy as np
    results = np.zeros((npk, 36), dtype=np.float64)
    _blobproperties_c(data, labels, npk, results, omega, verbose)
    return results


def splat(*args):
    """Splat g-vectors into RGBA image. Accepts both f2py and c2py23 calling conventions."""
    import numpy as np
    if len(args) == 4:
        _compat_deprecated('splat')
        rgba, gv, u, npx = args
        if rgba.ndim == 3:
            h, w = rgba.shape[:2]
        else:
            h, w = rgba.shape[0], rgba.shape[1]
        ng = gv.shape[0]
        return _splat_c(rgba, w, h, gv, ng, u, npx)
    return _splat_c(*args)


def array_stats(img, minval=None, maxval=None, mean=None, var=None):
    """Compute min/max/mean/var.
    f2py: array_stats(img) -> (min, max, mean, var) tuple
    c2py23: array_stats(img, minval, maxval, mean, var) -> void"""
    if minval is None:
        import numpy as np
        minval = np.zeros(1, dtype=np.float32)
        maxval = np.zeros(1, dtype=np.float32)
        mean = np.zeros(1, dtype=np.float32)
        var = np.zeros(1, dtype=np.float32)
        _array_stats_c(img, minval, maxval, mean, var)
        return float(minval[0]), float(maxval[0]), float(mean[0]), float(var[0])
    return _array_stats_c(img, minval, maxval, mean, var)


def array_mean_var_cut(img, mean=None, var=None, n=3, cut=3.0, verbose=0):
    """Sigma-clipped mean/var.
    f2py: array_mean_var_cut(img, n=3, cut=3.0, verbose=0) -> (mean, var)
    c2py23: array_mean_var_cut(img, mean, var, n, cut, verbose) -> void"""
    import numpy as np
    if mean is None:
        mean = np.zeros(1, dtype=np.float32)
        var_alloc = np.zeros(1, dtype=np.float32)
        _array_mean_var_cut_c(img, mean, var_alloc, n, cut, verbose)
        return float(mean[0]), float(var_alloc[0])
    return _array_mean_var_cut_c(img, mean, var, n, cut, verbose)


def array_mean_var_msk(img, msk, mean=None, var=None, n=3, cut=3.0, verbose=0):
    """Sigma-clipped mean/var with mask.
    f2py: array_mean_var_msk(img, msk, n=3, cut=3.0, verbose=0) -> (mean, var)
    c2py23: array_mean_var_msk(img, msk, mean, var, n, cut, verbose) -> void"""
    import numpy as np
    if mean is None:
        mean = np.zeros(1, dtype=np.float32)
        var_alloc = np.zeros(1, dtype=np.float32)
        _array_mean_var_msk_c(img, msk, mean, var_alloc, n, cut, verbose)
        return float(mean[0]), float(var_alloc[0])
    return _array_mean_var_msk_c(img, msk, mean, var, n, cut, verbose)


def localmaxlabel(data, labels, wrk):
    """Local maximum label assignment. Casts integer data to float32."""
    _compat_deprecated('localmaxlabel')
    import numpy as np
    if hasattr(data, 'dtype') and data.dtype not in (np.float32,):
        data = np.asarray(data, dtype=np.float32)
    return _localmaxlabel_c(data, labels, wrk)


def compute_geometry(xlylzl, omega, omegasign, wvln, wedge, chi, t, out):
    """Update geometry: computes tth, eta, ds, gve from xlylzl. Casts integer arrays to float64."""
    _compat_deprecated('compute_geometry')
    import numpy as np
    def _f64(a):
        if hasattr(a, 'dtype') and a.dtype not in (np.float64, np.float32):
            return np.asarray(a, dtype=np.float64)
        return a
    return _compute_geometry_c(
        _f64(xlylzl), _f64(omega), omegasign, wvln, wedge, chi, _f64(t), out)


def compute_xlylzl(s, f, p, r, dist, xlylzl):
    """Spot positions in lab frame. Casts integer arrays to float64."""
    _compat_deprecated('compute_xlylzl')
    import numpy as np
    def _f64(a):
        if hasattr(a, 'dtype') and a.dtype not in (np.float64, np.float32):
            return np.asarray(a, dtype=np.float64)
        return a
    return _compute_xlylzl_c(_f64(s), _f64(f), _f64(p), _f64(r), _f64(dist), xlylzl)


# ---------------------------------------------------------------------------
# OpenMP safety
# ---------------------------------------------------------------------------

def _check_multiprocessing(patch=False):
    """Warn about fork+threads interaction with OpenMP.

    You cannot safely use os.fork together with threads.
    But the cImageD11 codes uses threads via openmp, and you are importing them.
    So please use forkserver or spawn for multiprocessing.
    """
    if not hasattr(os, "fork"):
        return
    import multiprocessing
    if not hasattr(multiprocessing, "get_start_method"):
        warnings.warn(
            "python2.7 with c2ImageD11: for multiprocessing use spawn\n"
        )
        return
    method = multiprocessing.get_start_method(allow_none=True)
    if method == "fork":
        warnings.warn(_check_multiprocessing.__doc__)
    parent = None
    if hasattr(multiprocessing, "parent_process"):
        parent = multiprocessing.parent_process()
        if parent is not None:
            if "OMP_NUM_THREADS" not in os.environ:
                cimaged11_omp_set_num_threads(1)


check_multiprocessing = _check_multiprocessing  # public alias (f2py compat)

if cimaged11_omp_get_max_threads() == 0:
    OPENMP = False
else:
    OPENMP = True
    _check_multiprocessing()


# ---------------------------------------------------------------------------
# 32/64-bit put_incr dispatch
# ---------------------------------------------------------------------------

_nbyte = struct.calcsize("P")

if _nbyte == 8:
    def put_incr(*a, **k):
        """Redirects to put_incr64 (64-bit addressing)."""
        return put_incr64(*a, **k)
elif _nbyte == 4:
    def put_incr(*a, **k):
        """Redirects to put_incr32 (32-bit addressing)."""
        return put_incr32(*a, **k)


# ---------------------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------------------

assert verify_rounding(20) == 0, "Problem with cImageD11 fast rounding code"
