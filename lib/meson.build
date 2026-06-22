# lib/meson.build -- Tier 1: libc2ImageD11.a static library
#
# Baseline build (no SIMD ISA variants -- deferred to P7).
#
# Build:
#   cd lib && meson setup ../../build/libc2ImageD11
#   cd ../../build/libc2ImageD11 && ninja
#
# Output: build/libc2ImageD11/libc2ImageD11.a

project('c2ImageD11', 'c',
  default_options: ['c_std=c99', 'warning_level=3'],
  version: '0.1.0')

cc = meson.get_compiler('c')

# ------------------------------------------------------------------
# Base compiler flags
# ------------------------------------------------------------------
add_project_arguments(
  '-fPIC',
  '-O3',
  '-ffast-math',
  '-msse4.2',
  '-D_DEFAULT_SOURCE',
  language: 'c')

# OpenMP
if cc.has_argument('-fopenmp')
  add_project_arguments('-fopenmp', language: 'c')
  add_project_link_arguments('-fopenmp', language: 'c')
endif

# Math library
m_dep = cc.find_library('m', required: false)

# ------------------------------------------------------------------
# Include directories (C2ImageD11 sources + vendored headers)
# ------------------------------------------------------------------
inc_dirs = include_directories(
  'src/core',
  'src/geometry',
  'src/imageproc',
  'src/bslz4',
  # lz4
  'src/bslz4/vendor/lz4/lib',
  # kcb
  'src/bslz4/vendor/kcb/src',
  # bitshuffle
  'src/bslz4/vendor/bitshuffle/src',
  # zstd (relative includes like "../common/foo.h" need both dirs)
  'src/bslz4/vendor/zstd/lib',
  'src/bslz4/vendor/zstd/lib/common',
  'src/bslz4/vendor/zstd/lib/compress',
  'src/bslz4/vendor/zstd/lib/decompress',
)

# ------------------------------------------------------------------
# Sources
# ------------------------------------------------------------------

# C2ImageD11 core sources (no SIMD kernels yet)
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

# bslz4 (generated master file, includes templates)
bslz4_sources = files('src/bslz4/bs_master.c')

# zstd (decompress only)
zstd_sources = files(
  'src/bslz4/vendor/zstd/lib/common/debug.c',
  'src/bslz4/vendor/zstd/lib/common/entropy_common.c',
  'src/bslz4/vendor/zstd/lib/common/error_private.c',
  'src/bslz4/vendor/zstd/lib/common/fse_decompress.c',
  'src/bslz4/vendor/zstd/lib/common/pool.c',
  'src/bslz4/vendor/zstd/lib/common/threading.c',
  'src/bslz4/vendor/zstd/lib/common/xxhash.c',
  'src/bslz4/vendor/zstd/lib/common/zstd_common.c',
  'src/bslz4/vendor/zstd/lib/compress/fse_compress.c',
  'src/bslz4/vendor/zstd/lib/compress/hist.c',
  'src/bslz4/vendor/zstd/lib/compress/huf_compress.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_compress.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_compress_literals.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_compress_sequences.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_compress_superblock.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_double_fast.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_fast.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_lazy.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_ldm.c',
  'src/bslz4/vendor/zstd/lib/compress/zstdmt_compress.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_opt.c',
  'src/bslz4/vendor/zstd/lib/compress/zstd_preSplit.c',
  'src/bslz4/vendor/zstd/lib/decompress/huf_decompress.c',
  'src/bslz4/vendor/zstd/lib/decompress/zstd_ddict.c',
  'src/bslz4/vendor/zstd/lib/decompress/zstd_decompress_block.c',
  'src/bslz4/vendor/zstd/lib/decompress/zstd_decompress.c',
)
# zstd assembly (amd64 only)
zstd_asm = files('src/bslz4/vendor/zstd/lib/decompress/huf_decompress_amd64.S')

# Vendor C sources
lz4_sources = files('src/bslz4/vendor/lz4/lib/lz4.c')
kcb_sources = files('src/bslz4/vendor/kcb/src/bitshuffle.c')
bshuf_sources = files(
  'src/bslz4/vendor/bitshuffle/src/bitshuffle_core.c',
  'src/bslz4/vendor/bitshuffle/src/iochain.c',
)

# ------------------------------------------------------------------
# Static library
# ------------------------------------------------------------------
libc2ImageD11 = static_library('c2ImageD11',
  c2_sources,
  bslz4_sources,
  zstd_sources,
  zstd_asm,
  lz4_sources,
  kcb_sources,
  bshuf_sources,
  include_directories: inc_dirs,
  dependencies: [m_dep],
  install: false,
)
