# bszstd import + bslz4 refactoring - Recovery Plan
# Delete this file when Phase X is complete and committed.
#
# Phase 0: Fix -fopenmp (trivial)
# Phase 1: Add zstd submodule + AGENTS.md submodule notes
# Phase 2: Refactor C code (rename fns, extract pipeline template, split steps)
# Phase 3: Update bs_functions.h with 72 forward declarations
# Phase 4: Update _cImageD11.c2py (12 py_sig × 6 variants)
# Phase 5: Update setup.py (renamed kernels, zstd sources, include dirs)
# Phase 6: Update c2ImageD11/bslz4.py
# Phase 7: Update tests + benchmark for all 72 variants
# Phase 8: Build, test, verify

# Naming: drop _t suffix, shorten type names
#   bslz4_u16_kcb_avx512  (was bslz4_uint16_t_kcb_avx512)
#   bszstd_u16_kcb_avx512 (new)
#   bslz4_csc_u16_kcb_avx512 (was bslz4_csc_uint16_t_kcb_avx512)
#
# 72 C functions = 3 types × 2 (basic+csc) × 2 engines × 2 backends × 3 ISAs
# 12 .o compilations = 2 engines × 2 backends × 3 ISAs
# 12 Python-facing functions (6 lz4 + 6 zstd), each with 6 variants
