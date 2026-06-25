"""
c2ImageD11 - compiled C extensions for ImageD11, built with c2py23.

Provides:
  - All C functions re-exported from the arch-named .so
  - Blob property constants (s_1, s_I, NPROPERTY, etc.)
  - Allocation wrappers for f2py-compatible tuple returns
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import platform
import sys

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


_blobproperties_c = _mod.blobproperties  # save raw C function

def blobproperties(data, labels, npk, omega=0.0, verbose=0):
    """Allocate results and call C blobproperties, matching f2py convention."""
    import numpy as np
    results = np.zeros((npk, 36), dtype=np.float64)
    _blobproperties_c(data, labels, npk, results, omega, verbose)
    return results

_sparse_blob2Dproperties_c = _mod.sparse_blob2Dproperties

def sparse_blob2Dproperties(v, i, j, labels, npk):
    """Allocate results and call C sparse_blob2Dproperties, matching f2py convention."""
    import numpy as np
    results = np.zeros((npk, 11), dtype=np.float64)
    _sparse_blob2Dproperties_c(v, i, j, labels, npk, results)
    return results

# Replace raw C functions on submodule with allocation wrappers
_mod.blobproperties = blobproperties
_mod.sparse_blob2Dproperties = sparse_blob2Dproperties
