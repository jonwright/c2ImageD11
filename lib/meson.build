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
  default_options: ['c_std=c11', 'warning_level=1', 'buildtype=release', 'strip=true'],
  # Keep in sync with c2ImageD11/__init__.py __version__ (single source of truth)
  version: '0.3.0')

cc = meson.get_compiler('c')

# ------------------------------------------------------------------
# Compilation
# ------------------------------------------------------------------
c2_sources = files(
  'functions/array_histogram/array_histogram.c',
  'functions/array_mean_var_cut/array_mean_var_cut.c',
  'functions/array_mean_var_msk/array_mean_var_msk.c',
  'functions/array_stats/array_stats.c',
  'functions/bgcalc/bgcalc.c',
  'functions/blob_moments/blob_moments.c',
  'functions/bloboverlaps/bloboverlaps.c',
  'functions/blobproperties/blobproperties.c',
  'functions/clean_mask/clean_mask.c',
  'functions/closest/closest.c',
  'functions/closest_vec/closest_vec.c',
  'functions/cluster1d/cluster1d.c',
  'functions/common/blobs.c',
  'functions/common/cimaged11utils.c',
  'functions/compress_duplicates/compress_duplicates.c',
  'functions/compute_geometry/compute_geometry.c',
  'functions/compute_gv/compute_gv.c',
  'functions/compute_xlylzl/compute_xlylzl.c',
  'functions/compute_xlylzl_xpos_variable/compute_xlylzl_xpos_variable.c',
  'functions/connectedpixels/connectedpixels.c',
  'functions/count_shared/count_shared.c',
  'functions/coverlaps/coverlaps.c',
  'functions/frelon_lines/frelon_lines.c',
  'functions/frelon_lines_sub/frelon_lines_sub.c',
  'functions/localmaxlabel/localmaxlabel.c',
  'functions/make_clean_mask/make_clean_mask.c',
  'functions/mask_to_coo/mask_to_coo.c',
  'functions/misori_cubic/misori_cubic.c',
  'functions/misori_monoclinic/misori_monoclinic.c',
  'functions/misori_orthorhombic/misori_orthorhombic.c',
  'functions/misori_tetragonal/misori_tetragonal.c',
  'functions/put_incr32/put_incr32.c',
  'functions/put_incr64/put_incr64.c',
  'functions/quickorient/quickorient.c',
  'functions/refine_assigned/refine_assigned.c',
  'functions/reorder_f32_a32/reorder_f32_a32.c',
  'functions/reorderlut_f32_a32/reorderlut_f32_a32.c',
  'functions/reorderlut_u16_a32/reorderlut_u16_a32.c',
  'functions/reorder_u16_a32_a16/reorder_u16_a32_a16.c',
  'functions/reorder_u16_a32/reorder_u16_a32.c',
  'functions/score_and_assign/score_and_assign.c',
  'functions/score_and_refine/score_and_refine.c',
  'functions/score_gvec_z/score_gvec_z.c',
  'functions/score/score.c',
  'functions/sparse_blob2Dproperties/sparse_blob2Dproperties.c',
  'functions/sparse_connectedpixels/sparse_connectedpixels.c',
  'functions/sparse_connectedpixels_splat/sparse_connectedpixels_splat.c',
  'functions/sparse_is_sorted/sparse_is_sorted.c',
  'functions/sparse_localmaxlabel/sparse_localmaxlabel.c',
  'functions/sparse_overlaps/sparse_overlaps.c',
  'functions/sparse_smooth/sparse_smooth.c',
  'functions/splat/splat.c',
  'functions/tosparse_f32/tosparse_f32.c',
  'functions/tosparse_u16/tosparse_u16.c',
  'functions/tosparse_u32/tosparse_u32.c',
  'functions/uint16_to_float_darkflm/uint16_to_float_darkflm.c',
  'functions/uint16_to_float_darksub/uint16_to_float_darksub.c',
)

# Platform-specific compiler and link flags
is_msvc = cc.get_id() == 'msvc'
if is_msvc
  c2_c_args = ['/openmp', '/O2', '/fp:fast', '/D_DEFAULT_SOURCE']
  c2_link_args = []
else
  c2_c_args = cc.get_supported_arguments(
    '-fPIC', '-O3', '-ffast-math', '-fopenmp', '-D_DEFAULT_SOURCE',
    '-Wno-format', '-Wno-incompatible-pointer-types')
  c2_link_args = ['-lgomp']
endif

m_dep = cc.find_library('m', required: false)

c2_inc = include_directories(
  'functions', 'functions/common', 'interface')

shared_module('_cImageD11',
  c2_sources,
  files('interface/c2py_runtime.c', 'interface/_cImageD11_wrapper.c'),
  c_args: c2_c_args,
  include_directories: [c2_inc],
  dependencies: [m_dep],
  link_args: c2_link_args,
  name_prefix: '',
  install: false,
)

# Regenerate interface from C2PY_BEGIN blocks in C sources (CI only).
# Requires c2py23.  Pre-generated files are checked into git for release builds.
run_target('regenerate-interface',
  command: [
    'python3', '../../tools/harvester.py', '--output-dir',
    '../../lib/interface',
  ],
)
