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
LZ4_DIR = os.path.join(REPO_ROOT, "lz4")
KCB_DIR = os.path.join(REPO_ROOT, "kcb")
BITSHUFFLE_DIR = os.path.join(REPO_ROOT, "bitshuffle")
ZSTD_DIR = os.path.join(REPO_ROOT, "zstd")
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

# bslz4/bszstd kernel compilation: one source → 12 ISA×backend×engine variants
_BSLZ4_KERNELS = [
    ("bs_master", "src/bs_master.c"),
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

_CFLAGS_BASE = ["-O3", "-fPIC", "-Wall"]
_CFLAGS_OMP = ["-O3", "-fPIC", "-fopenmp", "-Wall"]


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
            cflags = _CFLAGS_OMP[:]
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


def _compile_bslz4_variants(build_dir):
    """Compile bs_master.c with engine×backend×ISA combinations.

    Each compilation produces all 6 type-variant functions
    (u8/u16/u32 × basic/CSC) with names like
    bslz4_u16_kcb_avx512(), bszstd_u16_bs_sse42(), etc.

    Engines:
       - lz4:  uses LZ4 decompress
       - zstd: uses ZSTD decompress  (-DUSE_ZSTD)

    Backends:
       - kcb:  uses KCB bitshuffle  (-DUSE_KCB)
       - bs:   uses bitshuffle-core  (original kiyo-masui)

    ISA levels: sse42, avx2, avx512 (on x86-64); sse42 only (otherwise)
    """
    cc = os.environ.get("CC", "gcc")
    objects = []

    include_dirs = [
        "-I" + SRC_DIR,
        "-I" + REPO_ROOT,
        "-I" + LZ4_DIR + "/lib",
        "-I" + KCB_DIR + "/src",
        "-I" + BITSHUFFLE_DIR + "/src",
        "-I" + ZSTD_DIR + "/lib",
        "-I" + ZSTD_DIR + "/lib/common",
        "-I" + ZSTD_DIR + "/lib/compress",
        "-I" + ZSTD_DIR + "/lib/decompress",
    ]

    src_path = os.path.join(REPO_ROOT, "src", "bs_master.c")
    if not os.path.isfile(src_path):
        print("c2ImageD11: WARNING - bslz4 kernel not found: {}".format(src_path))
        return objects

    for kernel_name, src_file in _BSLZ4_KERNELS:
        src_path_full = os.path.join(REPO_ROOT, src_file)

        # Engine: lz4 (default) or zstd (-DUSE_ZSTD)
        for engine_suffix, engine_cflags in [
            ("lz4", []),
            ("zstd", ["-DUSE_ZSTD"]),
        ]:
            for backend_suffix, backend_cflags in [
                ("kcb", ["-DUSE_KCB"]),
                ("bs", []),
            ]:
                for variant_name, simd_flag in _SIMD_VARIANTS:
                    full_suffix = "_{}_{}_{}".format(engine_suffix, backend_suffix, variant_name)
                    obj_name = "{}{}.o".format(kernel_name, full_suffix)
                    obj_path = os.path.join(build_dir, obj_name)

                    cflags = _CFLAGS_BASE[:]
                    if simd_flag:
                        cflags.append(simd_flag)
                    cflags.extend(backend_cflags)
                    cflags.extend(engine_cflags)

                    fn_suffix = "_{}_{}".format(backend_suffix, variant_name)
                    cmd = [cc, "-c"] + include_dirs + cflags + [
                        "-DKERNEL_SUFFIX=" + fn_suffix,
                        src_path_full, "-o", obj_path,
                    ]
                    print("c2ImageD11: BSLZ4 compile {}".format(obj_name))
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

        # Step 0b: Compile bslz4 kernel variants (backend × ISA)
        print("c2ImageD11: compiling BSLZ4 kernel variants...")
        bslz4_objects = _compile_bslz4_variants(build_dir)

        # Step 0c: Compile zstd assembly file (setuptools doesn't handle .S)
        zstd_asm = os.path.join(ZSTD_DIR, "lib", "decompress",
                                "huf_decompress_amd64.S")
        zstd_asm_o = os.path.join(build_dir, "huf_decompress_amd64.o")
        if os.path.isfile(zstd_asm):
            cc = os.environ.get("CC", "gcc")
            cmd = [cc, "-c", "-O3", "-fPIC", "-Wall",
                   "-I", os.path.join(ZSTD_DIR, "lib"),
                   "-I", os.path.join(ZSTD_DIR, "lib", "common"),
                   "-I", os.path.join(ZSTD_DIR, "lib", "decompress"),
                   zstd_asm, "-o", zstd_asm_o]
            print("c2ImageD11: compiling zstd asm")
            rc = subprocess.call(cmd)
            if rc != 0:
                sys.exit(rc)
            bslz4_objects.append(zstd_asm_o)

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
            ext.include_dirs.append(os.path.join(LZ4_DIR, "lib"))
            ext.include_dirs.append(os.path.join(KCB_DIR, "src"))
            ext.include_dirs.append(os.path.join(BITSHUFFLE_DIR, "src"))
            ext.include_dirs.append(os.path.join(ZSTD_DIR, "lib"))
            ext.include_dirs.append(os.path.join(ZSTD_DIR, "lib", "common"))
            ext.include_dirs.append(os.path.join(ZSTD_DIR, "lib", "compress"))
            ext.include_dirs.append(os.path.join(ZSTD_DIR, "lib", "decompress"))
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
            if bslz4_objects:
                for obj in bslz4_objects:
                    ext.extra_objects.append(os.path.relpath(obj, REPO_ROOT))

        print("c2ImageD11: linked {} SIMD + {} BSLZ4 kernel objects".format(
            len(simd_objects), len(bslz4_objects)))

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
    # bslz4 dependencies
    os.path.join("lz4", "lib", "lz4.c"),
    os.path.join("kcb", "src", "bitshuffle.c"),
    os.path.join("bitshuffle", "src", "bitshuffle_core.c"),
    os.path.join("bitshuffle", "src", "iochain.c"),
    # zstd decompress engine
    os.path.join("zstd", "lib", "common", "debug.c"),
    os.path.join("zstd", "lib", "common", "entropy_common.c"),
    os.path.join("zstd", "lib", "common", "error_private.c"),
    os.path.join("zstd", "lib", "common", "fse_decompress.c"),
    os.path.join("zstd", "lib", "common", "pool.c"),
    os.path.join("zstd", "lib", "common", "threading.c"),
    os.path.join("zstd", "lib", "common", "xxhash.c"),
    os.path.join("zstd", "lib", "common", "zstd_common.c"),
    os.path.join("zstd", "lib", "decompress", "huf_decompress.c"),
    os.path.join("zstd", "lib", "decompress", "zstd_ddict.c"),
    os.path.join("zstd", "lib", "decompress", "zstd_decompress.c"),
    os.path.join("zstd", "lib", "decompress", "zstd_decompress_block.c"),
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
