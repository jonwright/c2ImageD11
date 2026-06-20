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


# ---------------------------------------------------------------------------
# API compatibility wrappers (f2py calling conventions)
# ---------------------------------------------------------------------------

def closest(x, v):
    """Closest match: returns (index, value) tuple (f2py-compatible)."""
    import numpy as np
    ibest = np.zeros(1, dtype=np.int32)
    best = np.zeros(1, dtype=np.float64)
    _closest_c(x, v, ibest, best)
    return ibest[0], best[0]


def score_and_refine(ubi, gv, tol):
    """Score and refine: returns (npk, drlv2) tuple (f2py-compatible)."""
    import numpy as np
    sumdrlv2 = np.zeros(1, dtype=np.float64)
    npk = _score_and_refine_c(ubi, gv, tol, sumdrlv2)
    return npk, sumdrlv2[0]


def blobproperties(data, labels, npk, omega=0.0, verbose=0):
    """Blob properties: allocates and returns results array (f2py-compatible)."""
    import numpy as np
    results = np.zeros((npk, 36), dtype=np.float64)
    _blobproperties_c(data, labels, npk, results, omega, verbose)
    return results


def splat(*args):
    """Splat g-vectors into RGBA image. Accepts both f2py and c2py23 calling conventions."""
    import numpy as np
    if len(args) == 4:
        rgba, gv, u, npx = args
        if rgba.ndim == 3:
            h, w = rgba.shape[:2]
        else:
            h, w = rgba.shape[0], rgba.shape[1]
        ng = gv.shape[0]
        return _splat_c(rgba, w, h, gv, ng, u, npx)
    return _splat_c(*args)


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
