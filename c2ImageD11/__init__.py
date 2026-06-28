"""
c2ImageD11 - compiled C extensions for ImageD11, built with c2py23.

Provides:
  - All C functions re-exported from the arch-named .so
  - Blob property constants (s_1, s_I, NPROPERTY, etc.)
  - Allocation wrappers for f2py-compatible tuple returns
  - __version__
"""

from __future__ import absolute_import, division, print_function, unicode_literals

__version__ = "0.3.0"

import os
import platform
import sys
import warnings

# ---------------------------------------------------------------------------
# Arch-aware .so loader
#
# The .so files in this directory follow the naming convention:
#   _cImageD11_{arch}.so   (Linux)
#   _cImageD11_{arch}.pyd  (Windows)
#
# Where {arch} matches platform.machine() output:
#   x86_64, aarch64, ppc64le, AMD64 (Windows), arm64 (Windows)
#
# The same binary works across Python 2.7-3.14 because c2py23 emits both
# init_cImageD11 (Py2) and PyInit__cImageD11 (Py3) entry points.
# ---------------------------------------------------------------------------

_here = os.path.dirname(__file__)
_arch = platform.machine()
_ext = ".pyd" if sys.platform == "win32" else ".so"
_lib_name = "_cImageD11_{}{}".format(_arch, _ext)
_lib_path = os.path.join(_here, _lib_name)

# Fallback: plain name _cImageD11.so (no arch suffix)
if not os.path.exists(_lib_path):
    _lib_path = os.path.join(_here, "_cImageD11" + _ext)

if not os.path.exists(_lib_path):
    # .so not built yet (e.g. during setuptools metadata reading).
    # __version__ is still available; C functions will not be.
    _mod = None
else:
    if sys.version_info[0] >= 3:
        import importlib.util
        _spec = importlib.util.spec_from_file_location(
            "c2ImageD11._cImageD11", _lib_path)
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["c2ImageD11._cImageD11"] = _mod
        _spec.loader.exec_module(_mod)
    else:
        import imp
        _mod = imp.load_dynamic("c2ImageD11._cImageD11", _lib_path)

if _mod is not None:
    # Make _cImageD11 importable as c2ImageD11._cImageD11
    sys.modules[__name__]._cImageD11 = _mod

    # Save raw C functions before any overwrites
    _score_and_refine_c = _mod.score_and_refine
    _score_and_refine_soa_c = _mod.score_and_refine_soa
    _blobproperties_c = _mod.blobproperties
    _sparse_blob2Dproperties_c = _mod.sparse_blob2Dproperties

    # Re-export all non-private names from the loaded module
    for _k in dir(_mod):
        if not _k.startswith("_"):
            globals()[_k] = getattr(_mod, _k)

    # -----------------------------------------------------------------------
    # Shape-based dispatch: AoS (N,3) vs SoA (3,N)
    # -----------------------------------------------------------------------
    import numpy as np

    def score_and_refine(ubi, gv, tol, **kw):
        """Score and refine UBI using g-vectors.

        Auto-detects layout from gv shape:
          (N,3) → AoS (interleaved x/y/z, default)
          (3,N) → SoA (rows are gvx,gvy,gvz components)
        Handles float32 and float64.

        To force single-threaded:
          c2ImageD11.cimaged11_omp_set_num_threads(1)

        Returns (n, sumdrlv2) where n is the number of inlier peaks
        and sumdrlv2 is the mean squared deviation.
        """
        if gv.ndim != 2:
            raise ValueError("gv must be 2D, got shape %s" % (gv.shape,))

        nrows, ncols = gv.shape[0], gv.shape[1]

        # Detect layout from shape
        if ncols == 3 and nrows != 3:
            layout = 'AoS'  # (N,3) — interleaved
        elif nrows == 3 and ncols != 3:
            layout = 'SoA'  # (3,N) — component rows
        elif nrows == 3 and ncols == 3:
            # Ambiguous (3,3): use stride to disambiguate
            layout = 'AoS' if gv.strides[0] > gv.strides[1] else 'SoA'
        else:
            raise ValueError(
                "gv must have one axis of size 3, got shape %s" % (gv.shape,))

        if layout == 'AoS':
            return _score_and_refine_c(ubi, gv, tol)
        else:
            # SoA: extract rows as 1D arrays (may need copy for contiguity)
            gvx = np.ascontiguousarray(gv[0])
            gvy = np.ascontiguousarray(gv[1])
            gvz = np.ascontiguousarray(gv[2])
            return _score_and_refine_soa_c(ubi, gvx, gvy, gvz, tol)

    # Overwrite the C function with the Python dispatch
    globals()['score_and_refine'] = score_and_refine

    def blobproperties(data, labels, npk, omega=0.0, verbose=0):
        """Allocate results and call C blobproperties, matching f2py convention."""
        results = np.zeros((npk, 36), dtype=np.float64)
        _blobproperties_c(data, labels, npk, results, omega, verbose)
        return results

    def sparse_blob2Dproperties(v, i, j, labels, npk):
        """Allocate results and call C sparse_blob2Dproperties, matching f2py convention."""
        results = np.zeros((npk, 11), dtype=np.float64)
        _sparse_blob2Dproperties_c(v, i, j, labels, npk, results)
        return results

    # Replace raw C functions on submodule with wrappers
    _mod.blobproperties = blobproperties
    _mod.sparse_blob2Dproperties = sparse_blob2Dproperties

    # -----------------------------------------------------------------------
    # OpenMP minimum ng threshold.  Must match the `ng > 50000` guard in
    # lib/functions/score_and_refine/score_and_refine.hpp.  Measured cutoff:
    # ng <= 50000 → single-thread; ng >= 75000 → ~2x speedup on x86_64.
    # -----------------------------------------------------------------------
    OMP_MIN_NG = 50000


    # -----------------------------------------------------------------------
    # OpenMP safety
    # -----------------------------------------------------------------------

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


    # -----------------------------------------------------------------------
    # Sanity check
    # -----------------------------------------------------------------------

    assert verify_rounding(20) == 0, "Problem with cImageD11 fast rounding code"
