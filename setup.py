"""Setup script for c2ImageD11 - builds C extensions via c2py23.

The build process:
1. Compiles src_simd/*.c kernels 3x with -msse4.2/-mavx2/-mavx512f (amd64)
2. Uses c2py23 parser+generator to produce _cImageD11_wrapper.c
3. Compiles all C sources with setuptools + gcc -fopenmp
4. Links ISA-specific .o files for variant dispatch

Requirements:
  - gcc with -fopenmp
  - c2py23 installed
  - dlfcn.h (POSIX; Linux, macOS)
"""

from __future__ import print_function

import os
import sys
import subprocess

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO_ROOT, "src")
WRAPPER_DIR = os.path.join(REPO_ROOT, "src_wrapper")
SIMD_DIR = os.path.join(REPO_ROOT, "src_simd")
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
# SIMD multi-flag compilation
# ---------------------------------------------------------------------------

# Kernel names -> source file mapping
_SIMD_KERNELS = [
    ("score", "score_kernel.c"),
    ("score_and_refine", "score_and_refine_kernel.c"),
    ("score_and_assign", "score_and_assign_kernel.c"),
    ("compute_gv", "compute_gv_kernel.c"),
    ("compute_geometry", "compute_geometry_kernel.c"),
    ("compute_xlylzl", "compute_xlylzl_kernel.c"),
    ("compute_xlylzl_xpos", "compute_xlylzl_xpos_kernel.c"),
    ("put_incr32", "put_incr32_kernel.c"),
    ("put_incr64", "put_incr64_kernel.c"),
    ("blobproperties", "blobproperties_kernel.c"),
    ("uint16_to_float_darksub", "darksub_kernel.c"),
    ("uint16_to_float_darkflm", "darkflm_kernel.c"),
    ("reorder_f32_a32", "reorder_f32_a32_kernel.c"),
    ("reorderlut_f32_a32", "reorderlut_f32_a32_kernel.c"),
    ("reorder_u16_a32", "reorder_u16_a32_kernel.c"),
    ("reorderlut_u16_a32", "reorderlut_u16_a32_kernel.c"),
]

# ISA variants: (variant_suffix, compiler_flag)
_IS_AMD64 = sys.maxsize > 2**32 and hasattr(os, 'uname') and os.uname()[4] == 'x86_64'

if _IS_AMD64:
    _SIMD_VARIANTS = [
        ("avx512", "-mavx512f"),
        ("avx2", "-mavx2"),
        ("sse42", "-msse4.2"),
    ]
else:
    _SIMD_VARIANTS = [
        ("sse42", None),  # generic -O3, no x86 flag
    ]

_CFLAGS_BASE = ["-O3", "-fPIC", "-fopenmp", "-Wall"]


def _compile_simd_variants(build_dir):
    """Compile each kernel with multiple ISA flags, return list of .o paths."""
    cc = os.environ.get("CC", "gcc")
    objects = []

    include_dirs = ["-I" + SRC_DIR, "-I" + REPO_ROOT]

    for kernel_name, src_file in _SIMD_KERNELS:
        src_path = os.path.join(SIMD_DIR, src_file)
        if not os.path.isfile(src_path):
            print("c2ImageD11: WARNING - SIMD kernel not found: {}".format(src_path))
            continue

        for variant_name, simd_flag in _SIMD_VARIANTS:
            obj_name = "{}_{}.o".format(kernel_name, variant_name)
            obj_path = os.path.join(build_dir, obj_name)

            fn_name = "{}_{}".format(kernel_name, variant_name)
            cflags = _CFLAGS_BASE[:]
            if simd_flag:
                cflags.append(simd_flag)

            cmd = [cc, "-c"] + include_dirs + cflags + [
                "-DKERNEL_FN=" + fn_name,
                src_path, "-o", obj_path,
            ]
            print("c2ImageD11: SIMD compile {}".format(obj_name))
            rc = subprocess.call(cmd)
            if rc != 0:
                sys.exit(rc)
            objects.append(obj_path)

    return objects


# ---------------------------------------------------------------------------
# Build command
# ---------------------------------------------------------------------------

class c2py23_build_ext(build_ext):
    """Generate c2py23 wrapper C code, then compile with setuptools."""

    def build_extensions(self):
        # Step 0: Compile SIMD kernel variants
        print("c2ImageD11: compiling SIMD kernel variants " +
              "({} ISAs on {})...".format(
                  len(_SIMD_VARIANTS),
                  "amd64" if _IS_AMD64 else "non-x86"))
        build_dir = os.path.join(REPO_ROOT, "build")
        if not os.path.isdir(build_dir):
            os.makedirs(build_dir)
        simd_objects = _compile_simd_variants(build_dir)

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
            ext.include_dirs.append(SIMD_DIR)
            for flag in _EXTRA_COMPILE_ARGS:
                if flag not in ext.extra_compile_args:
                    ext.extra_compile_args.append(flag)
            for flag in _EXTRA_LINK_ARGS:
                if flag not in ext.extra_link_args:
                    ext.extra_link_args.append(flag)
            ext.libraries.extend(['dl', 'm'])

            # Link SIMD kernel objects
            if simd_objects:
                for obj in simd_objects:
                    ext.extra_objects.append(os.path.relpath(obj, REPO_ROOT))

        print("c2ImageD11: linked {} SIMD kernel objects".format(
            len(simd_objects)))

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
    version="0.2.0",
    description="C extensions for ImageD11, built with c2py23 (SIMD dispatch)",
    author="Jon Wright",
    author_email="wright@esrf.fr",
    packages=[PACKAGE_NAME],
    ext_modules=[ext],
    cmdclass={"build_ext": c2py23_build_ext},
    python_requires=">=2.7",
    install_requires=["c2py23"],
    zip_safe=False,
)
