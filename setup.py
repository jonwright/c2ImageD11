"""Setup script for c2ImageD11 - builds C extensions via c2py23.

The build process:
1. Uses c2py23 parser+generator to produce _cImageD11_wrapper.c
2. Compiles all C sources with setuptools + gcc -fopenmp

Requirements:
  - gcc with -fopenmp
  - c2py23 installed
  - dlfcn.h (POSIX; Linux, macOS)
"""

from __future__ import print_function

import os
import sys

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO_ROOT, "src")
WRAPPER_DIR = os.path.join(REPO_ROOT, "src_wrapper")
C2PY_FILE = os.path.join(REPO_ROOT, "_cImageD11.c2py")
MODULE_NAME = "_cImageD11"
PACKAGE_NAME = "c2ImageD11"

# Find c2py23 - try import first, then guess sibling directory
try:
    import c2py23
    C2PY23_DIR = os.path.dirname(os.path.abspath(c2py23.__file__))
except ImportError:
    C2PY23_DIR = os.path.join(os.path.dirname(REPO_ROOT), "c2py23", "c2py23")
    sys.path.insert(0, os.path.dirname(C2PY23_DIR))

C2PY_RUNTIME_DIR = os.path.join(C2PY23_DIR, "runtime")
RUNTIME_C = os.path.join(C2PY_RUNTIME_DIR, "c2py_runtime.c")


# ---------------------------------------------------------------------------
# Compiler options (mirrors ImageD11/setup.py)
# ---------------------------------------------------------------------------

COPT = {
    "linux": ["-fopenmp", "-fPIC"],
    "unix": ["-fopenmp", "-fPIC"],
    "mingw32": ["-fopenmp", "-fPIC"],
    "msvc": ["/openmp"],
}

if sys.platform == "darwin":
    for key in COPT:
        if "-fopenmp" in COPT.get(key, []):
            COPT[key].remove("-fopenmp")

_EXTRA_COMPILE_ARGS = COPT.get(sys.platform, ["-fopenmp", "-fPIC"])
_EXTRA_LINK_ARGS = COPT.get(sys.platform, ["-fopenmp", "-fPIC"])


# ---------------------------------------------------------------------------
# Build command
# ---------------------------------------------------------------------------

class c2py23_build_ext(build_ext):
    """Generate c2py23 wrapper C code, then compile with setuptools."""

    def build_extensions(self):
        # Step 1: Generate wrapper C code
        from c2py23.parser import load_c2py
        from c2py23.generator import generate

        print("c2ImageD11: generating c2py23 wrapper...")
        module_def = load_c2py(C2PY_FILE)
        wrapper_c = generate(module_def)

        wrapper_rel = "_{}_wrapper.c".format(MODULE_NAME)
        wrapper_path = os.path.join(REPO_ROOT, wrapper_rel)
        with open(wrapper_path, "w") as f:
            f.write(wrapper_c)
        print("c2ImageD11: wrapper written to", wrapper_path)

        # Add wrapper + runtime to each extension's sources
        runtime_rel = os.path.relpath(RUNTIME_C, REPO_ROOT)
        for ext in self.extensions:
            ext.sources.insert(0, wrapper_rel)
            ext.sources.insert(0, runtime_rel)
            ext.include_dirs.append(C2PY_RUNTIME_DIR)
            ext.include_dirs.append(REPO_ROOT)
            ext.include_dirs.append(SRC_DIR)
            ext.include_dirs.append(WRAPPER_DIR)
            for flag in _EXTRA_COMPILE_ARGS:
                if flag not in ext.extra_compile_args:
                    ext.extra_compile_args.append(flag)
            for flag in _EXTRA_LINK_ARGS:
                if flag not in ext.extra_link_args:
                    ext.extra_link_args.append(flag)
            ext.libraries.extend(['dl', 'm'])

        # Step 2: Standard compilation
        build_ext.build_extensions(self)


# ---------------------------------------------------------------------------
# Extension definition
# ---------------------------------------------------------------------------

SOURCES = [
    os.path.join("src", "blobs.c"),
    os.path.join("src", "cdiffraction.c"),
    os.path.join("src", "cimaged11utils.c"),
    os.path.join("src", "closest.c"),
    os.path.join("src", "connectedpixels.c"),
    os.path.join("src", "darkflat.c"),
    os.path.join("src", "localmaxlabel.c"),
    os.path.join("src", "sparse_image.c"),
    os.path.join("src", "splat.c"),
    os.path.join("src_wrapper", "_wrappers.c"),
]

ext = Extension(
    PACKAGE_NAME + "." + MODULE_NAME,
    sources=SOURCES,  # runtime.c + wrapper.c added by build command
)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup(
    name=PACKAGE_NAME,
    version="0.1.0",
    description="C extensions for ImageD11, built with c2py23",
    author="Jon Wright",
    author_email="wright@esrf.fr",
    packages=[PACKAGE_NAME],
    ext_modules=[ext],
    cmdclass={"build_ext": c2py23_build_ext},
    python_requires=">=2.7",
    install_requires=["c2py23"],
    zip_safe=False,
)
