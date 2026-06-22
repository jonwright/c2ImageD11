"""Setup script for c2ImageD11 -- Python extension (Tier 2).

Tier 1 (libc2ImageD11.a) is built by meson in lib/.
This script compiles only the Python bridge and links the static library.

Build:
  1. cd lib && meson setup ../../build/libc2ImageD11 && cd ../../build/libc2ImageD11
  2. ninja
  3. ninja fat-archive
  4. ninja c2py-wrapper
  5. cd ../.. && python setup.py build_ext --inplace

Requirements: c2py23 installed (for the generated wrapper's runtime).
"""

from __future__ import print_function

import os
import sys

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(REPO_ROOT, "build", "libc2ImageD11")
WRAPPER_SRC = os.path.join(REPO_ROOT, "src", "wrappers")
PACKAGE_DIR = os.path.join(REPO_ROOT, "c2ImageD11")

# Pre-built from meson
STATIC_LIB = os.path.join(BUILD_DIR, "libc2ImageD11.a")
WRAPPER_C  = os.path.join(BUILD_DIR, "_cImageD11_wrapper.c")
RUNTIME_C  = os.path.join(WRAPPER_SRC, "c2py_runtime.c")
WRAPPERS_C = os.path.join(WRAPPER_SRC, "_wrappers.c")

# Include directories for the bridge compilation
INCLUDE_DIRS = [
    BUILD_DIR,
    WRAPPER_SRC,
    os.path.join(REPO_ROOT, "lib", "src"),
    os.path.join(REPO_ROOT, "lib", "src", "core"),
    os.path.join(REPO_ROOT, "lib", "src", "geometry"),
    os.path.join(REPO_ROOT, "lib", "src", "imageproc"),
    os.path.join(REPO_ROOT, "lib", "src", "bslz4"),
    # Vendor headers
    os.path.join(REPO_ROOT, "lib", "src", "bslz4", "vendor", "lz4", "lib"),
    os.path.join(REPO_ROOT, "lib", "src", "bslz4", "vendor", "kcb", "src"),
    os.path.join(REPO_ROOT, "lib", "src", "bslz4", "vendor", "bitshuffle", "src"),
    os.path.join(REPO_ROOT, "lib", "src", "bslz4", "vendor", "zstd", "lib"),
    os.path.join(REPO_ROOT, "lib", "src", "bslz4", "vendor", "zstd", "lib", "common"),
    os.path.join(REPO_ROOT, "lib", "src", "bslz4", "vendor", "zstd", "lib", "decompress"),
]


class c2image_build_ext(build_ext):
    """Build the Python extension, linking the pre-built static library."""

    def build_extensions(self):
        arch = self.build_temp.split('.')[-1]
        lib = os.path.join(BUILD_DIR, "libc2ImageD11.a")

        if not os.path.isfile(lib):
            print("ERROR: Static library not found at:", lib,
                  file=sys.stderr)
            print("Build it first with meson (see lib/meson.build)",
                  file=sys.stderr)
            sys.exit(1)

        wrapper = os.path.join(BUILD_DIR, "_cImageD11_wrapper.c")
        if not os.path.isfile(wrapper):
            print("ERROR: Wrapper not found at:", wrapper, file=sys.stderr)
            print("Run 'ninja c2py-wrapper' in build/libc2ImageD11/",
                  file=sys.stderr)
            sys.exit(1)

        for ext in self.extensions:
            ext.extra_objects = [lib]
            ext.sources = [wrapper, RUNTIME_C, WRAPPERS_C]

        build_ext.build_extensions(self)


def main():
    extension = Extension(
        "_cImageD11",
        sources=[],  # filled in by c2image_build_ext
        include_dirs=INCLUDE_DIRS,
        extra_compile_args=["-O2", "-fPIC"],
        extra_link_args=["-ldl", "-lm", "-lgomp"],
    )

    setup(
        name="c2ImageD11",
        version="0.1.0",
        packages=["c2ImageD11"],
        package_dir={"c2ImageD11": PACKAGE_DIR},
        ext_modules=[extension],
        cmdclass={"build_ext": c2image_build_ext},
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
