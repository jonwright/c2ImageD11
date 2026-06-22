# lib/meson.build -- Tier 1: libc2ImageD11.a static library
#
# Baseline build (no SIMD ISA variants -- deferred to P7).
# Vendor libraries (lz4, zstd, kcb, bitshuffle) compiled with -O2
# as their maintainers intend.  C2ImageD11 sources compiled with -O3.
#
# Build from scratch:
#   rm -rf build/libc2ImageD11
#   mkdir -p build/libc2ImageD11
#   cd build/libc2ImageD11 && meson setup ../../lib && ninja && ninja fat-archive
#
# Incremental rebuild (clean reconfigure):
#   cd build/libc2ImageD11 && meson setup ../../lib --wipe && ninja && ninja fat-archive
#
# Output: build/libc2ImageD11/libc2ImageD11.a (fat archive)

project('c2ImageD11', 'c',
  default_options: ['c_std=c99', 'warning_level=3'],
  version: '0.1.0')

cc = meson.get_compiler('c')

# ------------------------------------------------------------------
# Compiler flags
# ------------------------------------------------------------------
# Vendor libraries: lz4, zstd, kcb, bitshuffle use -O2 (maintainer preference)
vendor_c_args = cc.get_supported_arguments(
  '-fPIC', '-O2', '-D_DEFAULT_SOURCE')

# C2ImageD11 sources: -O3 with fast-math and SSE4.2 baseline
c2_c_args = cc.get_supported_arguments(
  '-fPIC', '-O3', '-ffast-math', '-msse4.2', '-D_DEFAULT_SOURCE')

# OpenMP (only C2ImageD11 uses it)
omp_c_args = cc.get_supported_arguments('-fopenmp')

m_dep = cc.find_library('m', required: false)

# ------------------------------------------------------------------
# Include directories
# ------------------------------------------------------------------
c2_inc = include_directories(
  'src/core', 'src/geometry', 'src/imageproc', 'src/bslz4')

lz4_inc = include_directories('src/bslz4/vendor/lz4/lib')
kcb_inc = include_directories('src/bslz4/vendor/kcb/src')
bshuf_inc = include_directories('src/bslz4/vendor/bitshuffle/src')
zstd_inc = include_directories(
  'src/bslz4/vendor/zstd/lib',
  'src/bslz4/vendor/zstd/lib/common',
  'src/bslz4/vendor/zstd/lib/decompress')

# ------------------------------------------------------------------
# Vendor: lz4 (decompress only, -O2)
# ------------------------------------------------------------------
liblz4 = static_library('lz4',
  files('src/bslz4/vendor/lz4/lib/lz4.c'),
  c_args: vendor_c_args + ['-DXXH_NAMESPACE=LZ4_'],
  include_directories: lz4_inc,
  pic: true)

# ------------------------------------------------------------------
# Vendor: zstd (decompress + common only, -O2)
# ------------------------------------------------------------------
libzstd = static_library('zstd',
  files(
    'src/bslz4/vendor/zstd/lib/common/entropy_common.c',
    'src/bslz4/vendor/zstd/lib/common/error_private.c',
    'src/bslz4/vendor/zstd/lib/common/fse_decompress.c',
    'src/bslz4/vendor/zstd/lib/common/pool.c',
    'src/bslz4/vendor/zstd/lib/common/threading.c',
    'src/bslz4/vendor/zstd/lib/common/xxhash.c',
    'src/bslz4/vendor/zstd/lib/common/zstd_common.c',
    'src/bslz4/vendor/zstd/lib/decompress/huf_decompress.c',
    'src/bslz4/vendor/zstd/lib/decompress/zstd_ddict.c',
    'src/bslz4/vendor/zstd/lib/decompress/zstd_decompress.c',
    'src/bslz4/vendor/zstd/lib/decompress/zstd_decompress_block.c',
    'src/bslz4/vendor/zstd/lib/decompress/huf_decompress_amd64.S',
  ),
  c_args: vendor_c_args + ['-DZSTD_LEGACY_SUPPORT=0'],
  include_directories: zstd_inc,
  pic: true)

# ------------------------------------------------------------------
# Vendor: kcb bitshuffle (-O2)
# ------------------------------------------------------------------
libkcb = static_library('kcb',
  files('src/bslz4/vendor/kcb/src/bitshuffle.c'),
  c_args: vendor_c_args,
  include_directories: kcb_inc,
  pic: true)

# ------------------------------------------------------------------
# Vendor: bitshuffle-core (-O2)
# ------------------------------------------------------------------
libbshuf = static_library('bitshuffle',
  files(
    'src/bslz4/vendor/bitshuffle/src/bitshuffle_core.c',
    'src/bslz4/vendor/bitshuffle/src/iochain.c',
  ),
  c_args: vendor_c_args,
  include_directories: bshuf_inc,
  pic: true)

# ------------------------------------------------------------------
# bslz4 (our generated code, C2 flags)
# ------------------------------------------------------------------
libbslz4 = static_library('bslz4',
  files('src/bslz4/bs_master.c'),
  c_args: c2_c_args,
  include_directories: [c2_inc, lz4_inc, kcb_inc, bshuf_inc, zstd_inc],
  pic: true)

# ------------------------------------------------------------------
# C2ImageD11 core (C2 flags)
# ------------------------------------------------------------------
c2_sources = files(
  'src/core/cimaged11utils.c',
  'src/geometry/cdiffraction.c',
  'src/geometry/closest.c',
  'src/imageproc/blobs.c',
  'src/imageproc/connectedpixels.c',
  'src/imageproc/darkflat.c',
  'src/imageproc/localmaxlabel.c',
  'src/imageproc/sparse_image.c',
  'src/imageproc/splat.c',
)

# ------------------------------------------------------------------
# Main static library: bundle all objects
# ------------------------------------------------------------------
libc2ImageD11 = static_library('c2ImageD11',
  c2_sources,
  c_args: c2_c_args + omp_c_args,
  include_directories: c2_inc,
  objects: [
    liblz4.extract_all_objects(recursive: true),
    libzstd.extract_all_objects(recursive: true),
    libkcb.extract_all_objects(recursive: true),
    libbshuf.extract_all_objects(recursive: true),
    libbslz4.extract_all_objects(recursive: true),
  ],
  dependencies: [m_dep],
  install: false,
  pic: true,
)

# Post-build: convert thin archive to fat.
# meson produces thin archives for static_library() with extract_all_objects().
# setup.py needs a self-contained fat .a file.
run_target('fat-archive',
  command: [
    'sh', '-c',
    'cd ${MESON_BUILD_ROOT} && ' +
    'rm -f libc2ImageD11.a && ' +
    'ar rcs libc2ImageD11.a ' +
    '  libc2ImageD11.a.p/*.o ' +
    '  liblz4.a.p/*.o ' +
    '  libzstd.a.p/*.o ' +
    '  libkcb.a.p/*.o ' +
    '  libbitshuffle.a.p/*.o ' +
    '  libbslz4.a.p/*.o'
  ],
  depends: [libc2ImageD11])
