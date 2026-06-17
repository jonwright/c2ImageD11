/* Forward declarations for all bitshuffle sparse decompress functions.
 *
 * 72 functions = 3 types (u8/u16/u32) × 2 variants (basic/csc)
 *              × 2 engines (lz4/zstd) × 2 backends (kcb/bs)
 *              × 3 ISAs (sse42/avx2/avx512)
 *
 * Generated from bs_master.c templates. Used by c2py23 for wrapper codegen.
 */

#ifndef BS_FUNCTIONS_H
#define BS_FUNCTIONS_H

#include <stdint.h>

/* =========================================================================
 * LZ4 engine × KCB backend
 * ========================================================================= */

/* u16 basic */
int bslz4_u16_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u16_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u16_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);

/* u16 CSC */
int bslz4_csc_u16_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u16_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u16_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* u32 basic */
int bslz4_u32_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u32_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u32_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);

/* u32 CSC */
int bslz4_csc_u32_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u32_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u32_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* u8 basic */
int bslz4_u8_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u8_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u8_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);

/* u8 CSC */
int bslz4_csc_u8_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u8_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u8_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* =========================================================================
 * LZ4 engine × bitshuffle-core backend
 * ========================================================================= */

/* u16 */
int bslz4_u16_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u16_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u16_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_csc_u16_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u16_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u16_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* u32 */
int bslz4_u32_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u32_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u32_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_csc_u32_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u32_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u32_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* u8 */
int bslz4_u8_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u8_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_u8_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_csc_u8_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u8_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_u8_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* =========================================================================
 * ZSTD engine × KCB backend
 * ========================================================================= */

/* u16 */
int bszstd_u16_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u16_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u16_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_csc_u16_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u16_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u16_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* u32 */
int bszstd_u32_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u32_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u32_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_csc_u32_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u32_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u32_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* u8 */
int bszstd_u8_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u8_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u8_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_csc_u8_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u8_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u8_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* =========================================================================
 * ZSTD engine × bitshuffle-core backend
 * ========================================================================= */

/* u16 */
int bszstd_u16_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u16_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u16_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_csc_u16_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u16_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u16_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* u32 */
int bszstd_u32_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u32_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u32_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_csc_u32_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u32_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u32_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* u8 */
int bszstd_u8_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u8_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_u8_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bszstd_csc_u8_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u8_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bszstd_csc_u8_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

#endif /* BS_FUNCTIONS_H */
