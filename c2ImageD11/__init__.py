"""
c2ImageD11 - compiled C extensions for ImageD11, built with c2py23.

Import chain:
  c2ImageD11/__init__.py (this file)
    -> c2ImageD11._cImageD11 (compiled .so via c2py23)
    -> c2ImageD11._constants (blob property enum values)

Provides:
  - All C functions re-exported from _cImageD11
  - Module-level blob property constants (s_1, s_I, NPROPERTY, etc.)
  - put_incr dispatch (32 vs 64 bit addressing)
  - Optional parameter defaults for functions needing them
  - OpenMP / multiprocessing safety
"""

from __future__ import print_function

import os
import struct
import warnings

# Import compiled C module
from c2ImageD11._cImageD11 import *

# Re-export constants
from c2ImageD11._constants import *


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
# Optional parameter defaults
# ---------------------------------------------------------------------------
# c2py23 does not yet support |O$ optional args, so we wrap here.
# Each wrapper shadows the C-function name imported via *, providing defaults.
# The imported function is saved under a _raw_* alias before redefinition.

# -- array_mean_var_cut --
if 'array_mean_var_cut' in dir():
    _raw_array_mean_var_cut = array_mean_var_cut

    def array_mean_var_cut(img, mean, var, n=3, cut=3.0, verbose=0):
        return _raw_array_mean_var_cut(img, mean, var,
                                        int(n), float(cut), int(verbose))

# -- array_mean_var_msk --
if 'array_mean_var_msk_wrapper' in dir():
    _raw_array_mean_var_msk = array_mean_var_msk_wrapper

    def array_mean_var_msk(img, msk, mean, var, n=3, cut=3.0, verbose=0):
        return _raw_array_mean_var_msk(img, msk, mean, var,
                                        int(n), float(cut), int(verbose))

# -- put_incr64 --
if 'put_incr64' in dir():
    _raw_put_incr64 = put_incr64

    def put_incr64(data, ind, vals, boundscheck=0):
        return _raw_put_incr64(data, ind, vals, int(boundscheck))

# -- put_incr32 --
if 'put_incr32' in dir():
    _raw_put_incr32 = put_incr32

    def put_incr32(data, ind, vals, boundscheck=0):
        return _raw_put_incr32(data, ind, vals, int(boundscheck))


# ---------------------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------------------

assert verify_rounding(20) == 0, "Problem with cImageD11 fast rounding code"
