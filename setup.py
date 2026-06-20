"""Setup script for c2ImageD11 - builds C extensions.

Build process:
1. Compiles SIMD kernels 3x with -msse4.2/-mavx2/-mavx512f (amd64)
2. Uses pre-generated c2py23 wrapper by default; regenerates if c2py23 is
   available and C2PY23_REBUILD env var is set
3. Compiles all C sources with setuptools + gcc -fopenmp
4. Links ISA-specific .o files for variant dispatch

Requirements:
  - gcc with -fopenmp
  - dlfcn.h (POSIX; Linux, macOS)
  - For rebuild: c2py23 installed
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
WRAPPER_DIR = os.path.join(SRC_DIR, "wrappers")
LZ4_DIR = os.path.join(SRC_DIR, "bslz4", "vendor", "lz4")
KCB_DIR = os.path.join(SRC_DIR, "bslz4", "vendor", "kcb")
BITSHUFFLE_DIR = os.path.join(SRC_DIR, "bslz4", "vendor", "bitshuffle")
ZSTD_DIR = os.path.join(SRC_DIR, "bslz4", "vendor", "zstd")
INTERFACE_DIR = os.path.join(REPO_ROOT, "interface")
C2PY_BASE_FILE = os.path.join(INTERFACE_DIR, "_cImageD11_base.c2py")
C2PY_BSLZ4_FILE = os.path.join(INTERFACE_DIR, "_cImageD11_bslz4.c2py")
C2PY_FILE = os.path.join(INTERFACE_DIR, "_cImageD11.c2py")
MODULE_NAME = "_cImageD11"
PACKAGE_NAME = "c2ImageD11"

# Pre-generated wrapper (shipped in sdist, no c2py23 needed)
WRAPPER_GENERATED = os.path.join(WRAPPER_DIR, "__cImageD11_wrapper.c")
RUNTIME_C = os.path.join(WRAPPER_DIR, "c2py_runtime.c")


# ---------------------------------------------------------------------------
# c2py23 - for wrapper regeneration and runtime files
# ---------------------------------------------------------------------------

_C2PY23_AVAILABLE = False
_C2PY23_RUNTIME_DIR = None

try:
    import c2py23
    _C2PY23_AVAILABLE = True
    _C2PY23_DIR = os.path.dirname(os.path.abspath(c2py23.__file__))
    _C2PY23_RUNTIME_DIR = os.path.join(_C2PY23_DIR, "runtime")
except ImportError:
    pass


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

if os.environ.get("ASAN"):
    _EXTRA_COMPILE_ARGS = _EXTRA_COMPILE_ARGS + ["-fsanitize=address", "-fno-omit-frame-pointer"]
    _EXTRA_LINK_ARGS = _EXTRA_LINK_ARGS + ["-fsanitize=address"]


# ---------------------------------------------------------------------------
# SIMD multi-flag compilation
# ---------------------------------------------------------------------------

# (kernel_name, subdir_path)
_SIMD_KERNELS = [
    ("score", "geometry/simd/score_kernel.c"),
    ("score_and_refine", "geometry/simd/score_and_refine_kernel.c"),
    ("score_and_assign", "geometry/simd/score_and_assign_kernel.c"),
    ("compute_gv", "geometry/simd/compute_gv_kernel.c"),
    ("compute_geometry", "geometry/simd/compute_geometry_kernel.c"),
    ("compute_xlylzl", "geometry/simd/compute_xlylzl_kernel.c"),
    ("compute_xlylzl_xpos", "geometry/simd/compute_xlylzl_xpos_kernel.c"),
    ("put_incr32", "imageproc/simd/put_incr32_kernel.c"),
    ("put_incr64", "imageproc/simd/put_incr64_kernel.c"),
    ("blobproperties", "imageproc/simd/blobproperties_kernel.c"),
    ("uint16_to_float_darksub", "imageproc/simd/darksub_kernel.c"),
    ("uint16_to_float_darkflm", "imageproc/simd/darkflm_kernel.c"),
    ("reorder_f32_a32", "imageproc/simd/reorder_f32_a32_kernel.c"),
    ("reorderlut_f32_a32", "imageproc/simd/reorderlut_f32_a32_kernel.c"),
    ("reorder_u16_a32", "imageproc/simd/reorder_u16_a32_kernel.c"),
    ("reorderlut_u16_a32", "imageproc/simd/reorderlut_u16_a32_kernel.c"),
]

_BSLZ4_KERNELS = [
    ("bs_master", "bslz4/bs_master.c"),
]

# ISA variants: (variant_suffix, compiler_flag)
_IS_AMD64 = sys.maxsize > 2**32 and hasattr(os, 'uname') and os.uname()[4] == 'x86_64'

if _IS_AMD64:
    _SIMD_VARIANTS = [
        ("avx512", ["-mavx512f"]),
        ("avx2",   ["-mavx2", "-mfma"]),
        ("sse42",  ["-msse4.2"]),
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

    include_dirs = [
        "-I" + SRC_DIR,
        "-I" + os.path.join(SRC_DIR, "core"),
        "-I" + os.path.join(SRC_DIR, "geometry"),
        "-I" + os.path.join(SRC_DIR, "geometry", "simd"),
        "-I" + os.path.join(SRC_DIR, "imageproc"),
        "-I" + os.path.join(SRC_DIR, "imageproc", "simd"),
        "-I" + os.path.join(SRC_DIR, "bslz4"),
        "-I" + os.path.join(SRC_DIR, "wrappers"),
        "-I" + REPO_ROOT,
    ]

    for kernel_name, subpath in _SIMD_KERNELS:
        src_path = os.path.join(SRC_DIR, subpath)
        if not os.path.isfile(src_path):
            print("c2ImageD11: WARNING - SIMD kernel not found: {}".format(src_path))
            continue

        for variant_name, simd_flag in _SIMD_VARIANTS:
            obj_name = "{}_{}.o".format(kernel_name, variant_name)
            obj_path = os.path.join(build_dir, obj_name)

            fn_name = "{}_{}".format(kernel_name, variant_name)
            if kernel_name == "score_and_refine":
                fn_name = fn_name + "_impl"
            cflags = _CFLAGS_OMP[:]
            if simd_flag:
                cflags.extend(simd_flag)

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
    """Compile bs_master.c with backendxISA combinations.

    Each compilation produces all 9 type-variant functions
    (u8/u16/u32 x basic/CSC/CSC1D) with names like
    bs_u16_kcb_avx512(), bs_csc_u16_kcb_sse42(), etc.

    Encoding (LZ4=2, ZSTD=3) is dispatched at runtime via parameter.

    Backends:
       - kcb:  uses KCB bitshuffle  (-DUSE_KCB)

    ISA levels: sse42, avx2, avx512 (on x86-64); sse42 only (otherwise)
    """
    cc = os.environ.get("CC", "gcc")
    objects = []

    include_dirs = [
        "-I" + SRC_DIR,
        "-I" + os.path.join(SRC_DIR, "bslz4"),
        "-I" + os.path.join(SRC_DIR, "core"),
        "-I" + REPO_ROOT,
        "-I" + os.path.join(LZ4_DIR, "lib"),
        "-I" + os.path.join(KCB_DIR, "src"),
        "-I" + os.path.join(ZSTD_DIR, "lib"),
        "-I" + os.path.join(ZSTD_DIR, "lib", "common"),
        "-I" + os.path.join(ZSTD_DIR, "lib", "compress"),
        "-I" + os.path.join(ZSTD_DIR, "lib", "decompress"),
    ]

    for kernel_name, subpath in _BSLZ4_KERNELS:
        src_path = os.path.join(SRC_DIR, subpath)
        if not os.path.isfile(src_path):
            print("c2ImageD11: WARNING - bslz4 kernel not found: {}".format(src_path))
            continue

        for backend_suffix, backend_cflags in [
            ("kcb", ["-DUSE_KCB"]),
        ]:
            for variant_name, simd_flag in _SIMD_VARIANTS:
                fn_suffix = "_{}_{}".format(backend_suffix, variant_name)
                obj_name = "{}{}.o".format(kernel_name, fn_suffix)
                obj_path = os.path.join(build_dir, obj_name)

                cflags = _CFLAGS_BASE[:]
                if simd_flag:
                    cflags.extend(simd_flag)
                cflags.extend(backend_cflags)

                cmd = [cc, "-c"] + include_dirs + cflags + [
                    "-DKERNEL_SUFFIX=" + fn_suffix,
                    src_path, "-o", obj_path,
                ]
                print("c2ImageD11: BSLZ4 compile {}".format(obj_name))
                rc = subprocess.call(cmd)
                if rc != 0:
                    sys.exit(rc)
                objects.append(obj_path)

    return objects


def _regenerate_wrapper():
    """Regenerate __cImageD11_wrapper.c using c2py23."""
    if not _C2PY23_AVAILABLE:
        return False

    from c2py23.parser import load_c2py
    from c2py23.generator import generate

    try:
        os.makedirs(os.path.dirname(C2PY_FILE))
    except OSError:
        pass

    print("c2ImageD11: assembling {} from {} + {}".format(
        os.path.basename(C2PY_FILE),
        os.path.basename(C2PY_BASE_FILE),
        os.path.basename(C2PY_BSLZ4_FILE)))
    with open(C2PY_BASE_FILE, "r") as fb:
        base_content = fb.read()
    with open(C2PY_BSLZ4_FILE, "r") as fb:
        bslz4_content = fb.read()
    with open(C2PY_FILE, "w") as fout:
        fout.write(base_content)
        fout.write(bslz4_content)

    print("c2ImageD11: generating c2py23 wrapper...")
    module_def = load_c2py(C2PY_FILE)
    wrapper_c = generate(module_def)

    try:
        os.makedirs(WRAPPER_DIR)
    except OSError:
        pass
    wrapper_path = os.path.join(WRAPPER_DIR, "__cImageD11_wrapper.c")
    with open(wrapper_path, "w") as f:
        f.write(wrapper_c)
    print("c2ImageD11: wrapper written to", wrapper_path)
    return True


def _sync_runtime():
    """Copy runtime files from c2py23 to WRAPPER_DIR for compilation."""
    if not _C2PY23_AVAILABLE or not _C2PY23_RUNTIME_DIR:
        return False
    try:
        os.makedirs(WRAPPER_DIR)
    except OSError:
        pass
    updated = False
    for fname in ("c2py_runtime.h", "c2py_runtime.c", "c2py_amd64.h"):
        src = os.path.join(_C2PY23_RUNTIME_DIR, fname)
        dst = os.path.join(WRAPPER_DIR, fname)
        if not os.path.isfile(src):
            continue
        if (not os.path.isfile(dst) or
                os.path.getmtime(src) > os.path.getmtime(dst)):
            with open(src, "rb") as f:
                content = f.read()
            with open(dst, "wb") as f:
                f.write(content)
            updated = True
    if updated:
        print("c2ImageD11: synced runtime files from c2py23")
    return True


# ---------------------------------------------------------------------------
# Build command
# ---------------------------------------------------------------------------

class c2py23_build_ext(build_ext):
    """Compile C extensions with SIMD and c2py23 wrapper support."""

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

        # Step 0b: Compile bslz4 kernel variants (backend x ISA)
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

        # Step 1: Regenerate wrapper if requested/needed
        wrapper_used = None
        if os.environ.get("C2PY23_REBUILD"):
            if _regenerate_wrapper():
                wrapper_used = os.path.join(WRAPPER_DIR, "__cImageD11_wrapper.c")
            else:
                print("c2ImageD11: C2PY23_REBUILD set but c2py23 not available; "
                      "using pre-generated wrapper")
        elif os.path.isfile(WRAPPER_GENERATED):
            wrapper_used = WRAPPER_GENERATED
            print("c2ImageD11: using pre-generated wrapper: {}".format(WRAPPER_GENERATED))
        else:
            # No pre-generated wrapper; try regenerating
            if _regenerate_wrapper():
                wrapper_used = os.path.join(WRAPPER_DIR, "__cImageD11_wrapper.c")
            else:
                print("c2ImageD11: ERROR - no pre-generated wrapper found and "
                      "c2py23 not available. Generate one with: "
                      "pip install c2py23 && C2PY23_REBUILD=1 pip install -e .")
                sys.exit(1)

        # Step 1.5: Sync runtime files from installed c2py23 (always fresh)
        _sync_runtime()

        # Step 2: Add wrapper + runtime to each extension's sources
        wrapper_rel = os.path.relpath(wrapper_used, REPO_ROOT)
        for ext in self.extensions:
            ext.sources.insert(0, wrapper_rel)
            ext.sources.insert(0, os.path.relpath(RUNTIME_C, REPO_ROOT))
        ext.include_dirs.append(WRAPPER_DIR)
        ext.include_dirs.append(REPO_ROOT)
        ext.include_dirs.append(SRC_DIR)
        ext.include_dirs.append(os.path.join(SRC_DIR, "core"))
        ext.include_dirs.append(os.path.join(SRC_DIR, "geometry"))
        ext.include_dirs.append(os.path.join(SRC_DIR, "imageproc"))
        ext.include_dirs.append(os.path.join(SRC_DIR, "bslz4"))
        ext.include_dirs.append(os.path.join(SRC_DIR, "wrappers"))
        ext.include_dirs.append(os.path.join(LZ4_DIR, "lib"))
        ext.include_dirs.append(os.path.join(KCB_DIR, "src"))
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

        # Step 3: Standard compilation
        build_ext.build_extensions(self)


# ---------------------------------------------------------------------------
# Extension definition
# ---------------------------------------------------------------------------

SOURCES = [
    os.path.join("src", "core", "cimaged11utils.c"),
    os.path.join("src", "geometry", "cdiffraction.c"),
    os.path.join("src", "geometry", "closest.c"),
    os.path.join("src", "imageproc", "blobs.c"),
    os.path.join("src", "imageproc", "connectedpixels.c"),
    os.path.join("src", "imageproc", "darkflat.c"),
    os.path.join("src", "imageproc", "localmaxlabel.c"),
    os.path.join("src", "imageproc", "sparse_image.c"),
    os.path.join("src", "imageproc", "splat.c"),
    os.path.join("src", "wrappers", "_wrappers.c"),
    # bslz4 dependencies (KCB backend only)
    os.path.join("src", "bslz4", "vendor", "lz4", "lib", "lz4.c"),
    os.path.join("src", "bslz4", "vendor", "kcb", "src", "bitshuffle.c"),
    # zstd decompress engine
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "common", "debug.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "common", "entropy_common.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "common", "error_private.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "common", "fse_decompress.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "common", "pool.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "common", "threading.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "common", "xxhash.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "common", "zstd_common.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "decompress", "huf_decompress.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "decompress", "zstd_ddict.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "decompress", "zstd_decompress.c"),
    os.path.join("src", "bslz4", "vendor", "zstd", "lib", "decompress", "zstd_decompress_block.c"),
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
    install_requires=["numpy"],
    zip_safe=False,
)
