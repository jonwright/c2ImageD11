"""
c2ImageD11 - compiled C extensions for ImageD11, built with c2py23.

Import chain:
  c2ImageD11/__init__.py (this file)
    -> c2ImageD11._cImageD11 (compiled .so via c2py23)

Provides:
  - All C functions re-exported from _cImageD11
  - Blob property constants (s_1, s_I, NPROPERTY, etc.)
  - OpenMP / multiprocessing safety
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import warnings

from c2ImageD11._cImageD11 import *


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
# Sanity check
# ---------------------------------------------------------------------------

assert verify_rounding(20) == 0, "Problem with cImageD11 fast rounding code"
