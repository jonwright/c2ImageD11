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
_closest_c = closest
_score_and_refine_c = score_and_refine
_blobproperties_c = blobproperties
_splat_c = splat
_array_stats_c = array_stats
_array_mean_var_cut_c = array_mean_var_cut
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
# ---------------------------------------------------------------------------

def closest(x, v):
    """Closest match: returns (index, value) tuple (f2py-compatible)."""
    _compat_deprecated('closest')
    import numpy as np
    ibest = np.zeros(1, dtype=np.int32)
    best = np.zeros(1, dtype=np.float64)
    _closest_c(x, v, ibest, best)
    return int(ibest[0]), best[0]


def score_and_refine(ubi, gv, tol):
    """Score and refine: returns (npk, drlv2) tuple (f2py-compatible)."""
    _compat_deprecated('score_and_refine')
    import numpy as np
    sumdrlv2 = np.zeros(1, dtype=np.float64)
    npk = _score_and_refine_c(ubi, gv, tol, sumdrlv2)
    return int(npk), sumdrlv2[0]


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


def array_stats(*args):
    """Compute min/max/mean/var.
    f2py: array_stats(img) -> (min, max, mean, var) tuple
    c2py23: array_stats(img, minval, maxval, mean, var) -> void"""
    if len(args) != 1:
        return _array_stats_c(*args)
    _compat_deprecated('array_stats')
    import numpy as np
    mn = np.zeros(1, dtype=np.float32)
    mx = np.zeros(1, dtype=np.float32)
    me = np.zeros(1, dtype=np.float32)
    va = np.zeros(1, dtype=np.float32)
    _array_stats_c(args[0], mn, mx, me, va)
    return float(mn[0]), float(mx[0]), float(me[0]), float(va[0])


def array_mean_var_cut(img, n=3, cut=3.0, verbose=0):
    """Sigma-clipped mean/var. Returns (mean, var) tuple (f2py-compatible)."""
    _compat_deprecated('array_mean_var_cut')
    import numpy as np
    me = np.zeros(1, dtype=np.float32)
    va = np.zeros(1, dtype=np.float32)
    _array_mean_var_cut_c(img, me, va, n, cut, verbose)
    return float(me[0]), float(va[0])


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
