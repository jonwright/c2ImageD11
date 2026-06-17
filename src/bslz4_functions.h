/* Forward declarations for bslz4_to_sparse template-generated functions.
 * c2py23 uses these to generate wrapper code. The actual implementations
 * come from bslz4_to_sparse.c compiled with -DKERNEL_SUFFIX= variants.
 */

#ifndef BSLZ4_FUNCTIONS_H
#define BSLZ4_FUNCTIONS_H

#include <stdint.h>

/* --------------------------------------------------------------------------
 * KCB backend functions (compiled with -DUSE_KCB)
 * -------------------------------------------------------------------------- */

/* uint8_t — basic sparse */
int bslz4_uint8_t_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint8_t_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint8_t_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);

/* uint8_t — CSC sparse */
int bslz4_csc_uint8_t_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint8_t_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint8_t_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* uint16_t — basic sparse */
int bslz4_uint16_t_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint16_t_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint16_t_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);

/* uint16_t — CSC sparse */
int bslz4_csc_uint16_t_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint16_t_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint16_t_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* uint32_t — basic sparse */
int bslz4_uint32_t_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint32_t_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint32_t_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);

/* uint32_t — CSC sparse */
int bslz4_csc_uint32_t_kcb_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint32_t_kcb_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint32_t_kcb_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* --------------------------------------------------------------------------
 * Bitshuffle (original) backend functions (compiled without -DUSE_KCB)
 * -------------------------------------------------------------------------- */

/* uint8_t — basic sparse */
int bslz4_uint8_t_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint8_t_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint8_t_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict output, uint32_t *restrict output_adr, int threshold);

/* uint8_t — CSC sparse */
int bslz4_csc_uint8_t_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint8_t_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint8_t_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint8_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* uint16_t — basic sparse */
int bslz4_uint16_t_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint16_t_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint16_t_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict output, uint32_t *restrict output_adr, int threshold);

/* uint16_t — CSC sparse */
int bslz4_csc_uint16_t_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint16_t_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint16_t_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint16_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

/* uint32_t — basic sparse */
int bslz4_uint32_t_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint32_t_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);
int bslz4_uint32_t_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict output, uint32_t *restrict output_adr, int threshold);

/* uint32_t — CSC sparse */
int bslz4_csc_uint32_t_bs_sse42(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint32_t_bs_avx2(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);
int bslz4_csc_uint32_t_bs_avx512(const uint8_t *restrict compressed, int compressed_length,
    const uint8_t *restrict mask, int NIJ,
    uint32_t *restrict outpx, uint32_t *restrict output_adr, int threshold,
    double *restrict output, int NOUT,
    float *restrict data, uint32_t *restrict indices, uint32_t *restrict indptr);

#endif /* BSLZ4_FUNCTIONS_H */
