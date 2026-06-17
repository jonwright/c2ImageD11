/* bs_master.c - bitshuffle sparse decompression master compilation unit.
 *
 * Compiled multiple times with different -D flags:
 *   -DKERNEL_SUFFIX=_kcb_avx512  (or _bs_sse42, etc.)
 *   -DUSE_KCB  (or leave undefined for bitshuffle-core)
 *   -DUSE_ZSTD (or leave undefined for LZ4)
 *
 * Each compilation includes bs_sparse_tmpl.c and bs_sparse_csc_tmpl.c
 * 3 times (for uint16_t, uint32_t, uint8_t), generating 6 functions.
 */

#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <limits.h>
#include <stdio.h>

/* --------------------------------------------------------------------------
 * Engine selection
 * -------------------------------------------------------------------------- */

#ifdef USE_ZSTD
#define FN_PREFIX bszstd
#include "zstd/lib/zstd.h"
#define BS_DECOMPRESS(src, srcSize, dst, dstSize) \
    ((int)ZSTD_decompress((dst), (size_t)(dstSize), (src), (size_t)(srcSize)))
#else
#define FN_PREFIX bslz4
#include "lz4/lib/lz4.h"
#define BS_DECOMPRESS(src, srcSize, dst, dstSize) \
    LZ4_decompress_safe((const char*)(src), (char*)(dst), (srcSize), (dstSize))
#endif

/* --------------------------------------------------------------------------
 * Bitshuffle backend selection
 * -------------------------------------------------------------------------- */

#ifdef USE_KCB
#include "kcb/src/bitshuffle.h"
#else
int64_t bshuf_untrans_bit_elem(const void* in, void* out, const size_t size,
        const size_t elem_size);
#endif

/* --------------------------------------------------------------------------
 * Utility macros
 * -------------------------------------------------------------------------- */

#define READ32BE(p) \
  ((uint32_t)(255 & (p)[0]) << 24 |\
   (uint32_t)(255 & (p)[1]) << 16 |\
   (uint32_t)(255 & (p)[2]) <<  8 |\
   (uint32_t)(255 & (p)[3]))

#define READ64BE(p) \
  ((uint64_t)(255 & (p)[0]) << 56 |\
   (uint64_t)(255 & (p)[1]) << 48 |\
   (uint64_t)(255 & (p)[2]) << 40 |\
   (uint64_t)(255 & (p)[3]) << 32 |\
   (uint64_t)(255 & (p)[4]) << 24 |\
   (uint64_t)(255 & (p)[5]) << 16 |\
   (uint64_t)(255 & (p)[6]) <<  8 |\
   (uint64_t)(255 & (p)[7]))

#ifndef unlikely
#ifdef _MSC_VER
#define unlikely
#else
#define unlikely(expr) (__builtin_expect(!!(expr), 0))
#endif
#endif

#define BLK 8192

#define CAT_I(a,b) a##b
#define CAT(a,b) CAT_I(a,b)
#define CAT3(a,b,c) CAT(CAT(a,b),c)
#define CAT4(a,b,c,d) CAT(CAT3(a,b,c),d)

#ifndef KERNEL_SUFFIX
#define KERNEL_SUFFIX _sse42
#endif

#define FULL_SUFFIX KERNEL_SUFFIX

/* --------------------------------------------------------------------------
 * Type batch: uint16_t
 * -------------------------------------------------------------------------- */

#define DATATYPE uint16_t
#define DT_SHORT u16
#define NB 2

#define KERNEL_FN  CAT3(FN_PREFIX, _, CAT(DT_SHORT, FULL_SUFFIX))
#define KERNEL_CSC_FN CAT3(FN_PREFIX, _csc_, CAT(DT_SHORT, FULL_SUFFIX))

#include "bs_sparse_tmpl.c"
#include "bs_sparse_csc_tmpl.c"

#undef DATATYPE
#undef DT_SHORT
#undef NB
#undef KERNEL_FN
#undef KERNEL_CSC_FN

/* --------------------------------------------------------------------------
 * Type batch: uint32_t
 * -------------------------------------------------------------------------- */

#define DATATYPE uint32_t
#define DT_SHORT u32
#define NB 4

#define KERNEL_FN  CAT3(FN_PREFIX, _, CAT(DT_SHORT, FULL_SUFFIX))
#define KERNEL_CSC_FN CAT3(FN_PREFIX, _csc_, CAT(DT_SHORT, FULL_SUFFIX))

#include "bs_sparse_tmpl.c"
#include "bs_sparse_csc_tmpl.c"

#undef DATATYPE
#undef DT_SHORT
#undef NB
#undef KERNEL_FN
#undef KERNEL_CSC_FN

/* --------------------------------------------------------------------------
 * Type batch: uint8_t
 * -------------------------------------------------------------------------- */

#define DATATYPE uint8_t
#define DT_SHORT u8
#define NB 1

#define KERNEL_FN  CAT3(FN_PREFIX, _, CAT(DT_SHORT, FULL_SUFFIX))
#define KERNEL_CSC_FN CAT3(FN_PREFIX, _csc_, CAT(DT_SHORT, FULL_SUFFIX))

#include "bs_sparse_tmpl.c"
#include "bs_sparse_csc_tmpl.c"
