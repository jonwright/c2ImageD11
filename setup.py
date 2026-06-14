"""Setup script for c2ImageD11 - builds C extensions via c2py23.

The build process:
1. Invokes c2py23 CLI to parse _cImageD11.c2py and generate wrapper C code
2. Compiles the generated wrapper + src/ C files + src_wrapper/ into _cImageD11.so

Requirements:
  - gcc with -fopenmp
  - c2py23 installed (for the 'c2py23 build' command and parser/generator modules)
  - dlfcn.h (POSIX; Linux, macOS)
"""

from __future__ import print_function

import os
import sys
import glob
import subprocess
import tempfile
import shutil

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

# C2PY23 paths
# c2py23 is expected to be installed in the same workspace
try:
    import c2py23
    C2PY23_DIR = os.path.dirname(c2py23.__file__)
except ImportError:
    C2PY23_DIR = os.path.join(os.path.dirname(REPO_ROOT), "c2py23", "c2py23")

C2PY_RUNTIME_DIR = os.path.join(C2PY23_DIR, "runtime")


# ---------------------------------------------------------------------------
# Compiler options (mirrors ImageD11/setup.py)
# ---------------------------------------------------------------------------

COPT = {
    "msvc": ["/openmp"],
    "unix": ["-fopenmp", "-fPIC"],
    "mingw32": ["-fopenmp", "-fPIC"],
    "linux": ["-fopenmp", "-fPIC"],
}

if sys.platform == "darwin":
    for key in COPT:
        if "-fopenmp" in COPT[key]:
            COPT[key].remove("-fopenmp")


# ---------------------------------------------------------------------------
# Build command
# ---------------------------------------------------------------------------

class C2Py23BuildExt(build_ext):
    """Build extension by invoking c2py23 to generate wrapper C, then compile."""

    def build_extension(self, ext):
        # Step 1: Generate the wrapper C code via c2py23 CLI
        # c2py23 build writes the .so directly, but we need to hook into
        # setuptools. We generate the wrapper C, then compile ourselves.

        full_so_name = self.get_ext_fullpath(ext.name)
        build_dir = os.path.dirname(full_so_name)
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)

        # Use c2py23 build command to do everything
        # It generates _cImageD11_wrapper.c and compiles
        cmd = [
            sys.executable, "-m", "c2py23.cli", "build", C2PY_FILE,
            "-o", full_so_name,
        ]

        print("c2ImageD11: building with c2py23...")
        print("  Command:", " ".join(cmd))
        print("  Output:", full_so_name)

        result = subprocess.call(cmd)
        if result != 0:
            raise RuntimeError("c2py23 build failed with exit code %d" % result)

        print("c2ImageD11: built successfully:", full_so_name)


# ---------------------------------------------------------------------------
# Extension definition (informational; C2Py23BuildExt handles actual build)
# ---------------------------------------------------------------------------

ext = Extension(
    PACKAGE_NAME + "." + MODULE_NAME,
    sources=[],  # c2py23 handles source collection
)


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

def get_version():
    """Read version from _constants or default."""
    return "0.1.0"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup(
    name=PACKAGE_NAME,
    version=get_version(),
    description="C extension for ImageD11, built with c2py23",
    author="Jon Wright",
    author_email="wright@esrf.fr",
    packages=[PACKAGE_NAME],
    ext_modules=[ext],
    cmdclass={"build_ext": C2Py23BuildExt},
    python_requires=">=3.8",
    install_requires=[
        "c2py23",
    ],
    zip_safe=False,
)
