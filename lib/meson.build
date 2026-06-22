# lib/meson.build -- _cImageD11 shared module
#
# Regenerate interface files (needs c2py23):
#   python3 tools/harvester.py --output-dir lib/interface
#
# Build:
#   mkdir -p build/libc2ImageD11
#   cd build/libc2ImageD11 && meson setup ../../lib && ninja
#
# Output: build/libc2ImageD11/_cImageD11.so

project('c2ImageD11', 'c',
  default_options: ['c_std=c99', 'warning_level=1'],
  version: '0.1.0')

cc = meson.get_compiler('c')

# ------------------------------------------------------------------
# Compilation
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

c2_c_args = cc.get_supported_arguments(
  '-fPIC', '-O2', '-fopenmp', '-D_DEFAULT_SOURCE',
  '-Wno-format', '-Wno-incompatible-pointer-types')

m_dep = cc.find_library('m', required: false)

c2_inc = include_directories(
  'src', 'src/core', 'src/geometry', 'src/imageproc', 'interface')

shared_module('_cImageD11',
  c2_sources,
  files('interface/c2py_runtime.c', 'interface/_cImageD11_wrapper.c'),
  c_args: c2_c_args,
  include_directories: [c2_inc],
  dependencies: [m_dep],
  link_args: ['-lgomp'],
  name_prefix: '',
  install: false,
)
