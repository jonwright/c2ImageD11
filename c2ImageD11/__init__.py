"""
c2ImageD11 - compiled C extensions for ImageD11, built with c2py23.

Provides:
  - All C functions re-exported from the arch-named .so
  - Blob property constants (s_1, s_I, NPROPERTY, etc.)
  - OpenMP / multiprocessing safety
"""

from __future__ import absolute_import, division, print_function, unicode_literals

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
    raise ImportError("c2ImageD11: no binary at {} or {}".format(
        os.path.join(_here, _lib_name), os.path.join(_here, "_cImageD11" + _ext)))

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

# Make _cImageD11 importable as c2ImageD11._cImageD11
sys.modules[__name__]._cImageD11 = _mod

# Re-export all non-private names from the loaded module
for _k in dir(_mod):
    if not _k.startswith("_"):
        globals()[_k] = getattr(_mod, _k)


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
