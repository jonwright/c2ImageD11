/* blobproperties_kernel.c -- SIMD kernel for blobproperties()
 *
 * Computes blob peak properties (moments, bounds) from labeled 2D image.
 * add_pixel() logic is inlined here (original is DLL_LOCAL in blobs.c).
 * The dense 2D scan over 4.2e6 pixels benefits from compiler auto-vectorization.
 */

#include "cImageD11.h"
#include <stdio.h>

#ifndef KERNEL_FN
#define KERNEL_FN blobproperties_sse42
#endif

/* Blob property enum indices (mirrors blobs.h NPROPERTY enum, all 36) */
enum {
    bl_s_1 = 0,
    bl_s_I, bl_s_I2,
    bl_s_fI, bl_s_ffI, bl_s_sI, bl_s_ssI, bl_s_sfI,
    bl_s_oI, bl_s_ooI, bl_s_soI, bl_s_foI,
    bl_mx_I, bl_mx_I_f, bl_mx_I_s, bl_mx_I_o,
    bl_bb_mx_f, bl_bb_mx_s, bl_bb_mx_o,
    bl_bb_mn_f, bl_bb_mn_s, bl_bb_mn_o,
    bl_avg_i, bl_f_raw, bl_s_raw, bl_o_raw,
    bl_m_ss, bl_m_ff, bl_m_oo, bl_m_sf, bl_m_so, bl_m_fo,
    bl_f_cen, bl_s_cen,
    bl_dety, bl_detz,
    bl_NPROPERTY
};

static inline void add_pixel_local(double b[], int s, int f, double I, double o)
{
    b[bl_s_1] += 1;
    b[bl_s_I] += I;
    b[bl_s_I2] += I * I;
    b[bl_s_fI] += f * I;
    b[bl_s_ffI] += f * f * I;
    b[bl_s_sI] += s * I;
    b[bl_s_ssI] += s * s * I;
    b[bl_s_sfI] += s * f * I;
    b[bl_s_oI] += o * I;
    b[bl_s_ooI] += o * o * I;
    b[bl_s_soI] += s * o * I;
    b[bl_s_foI] += f * o * I;

    if (I > b[bl_mx_I]) {
        b[bl_mx_I] = I;
        b[bl_mx_I_f] = f;
        b[bl_mx_I_s] = s;
        b[bl_mx_I_o] = o;
    }
    b[bl_bb_mx_f] = (f > b[bl_bb_mx_f]) ? f : b[bl_bb_mx_f];
    b[bl_bb_mx_s] = (s > b[bl_bb_mx_s]) ? s : b[bl_bb_mx_s];
    b[bl_bb_mx_o] = (o > b[bl_bb_mx_o]) ? o : b[bl_bb_mx_o];
    b[bl_bb_mn_f] = (f < b[bl_bb_mn_f]) ? f : b[bl_bb_mn_f];
    b[bl_bb_mn_s] = (s < b[bl_bb_mn_s]) ? s : b[bl_bb_mn_s];
    b[bl_bb_mn_o] = (o < b[bl_bb_mn_o]) ? o : b[bl_bb_mn_o];
}

void KERNEL_FN(const float *restrict data, const int32_t *restrict labels,
               int32_t npk, float omega, int verbose, int ns, int nf,
               double *restrict res)
{
    int i, j, bad, ipx;
    double fval;
    int32_t ipk;
    int ntot = ns * nf;

    if (verbose)
        printf("Computing blob moments, ns %d, nf %d, npk %d\n", ns, nf, npk);

    for (i = 0; i < npk; i++) {
        for (j = 0; j < bl_NPROPERTY; j++)
            res[i * bl_NPROPERTY + j] = 0.0;
        res[i * bl_NPROPERTY + bl_bb_mn_f] = nf + 1;
        res[i * bl_NPROPERTY + bl_bb_mn_s] = ns + 1;
        res[i * bl_NPROPERTY + bl_bb_mx_f] = -1;
        res[i * bl_NPROPERTY + bl_bb_mx_s] = -1;
        res[i * bl_NPROPERTY + bl_bb_mx_o] = omega;
        res[i * bl_NPROPERTY + bl_bb_mn_o] = omega;
    }

    bad = 0;
    for (ipx = 0; ipx < ntot; ipx++) {
        ipk = labels[ipx];
        if (ipk > 0 && ipk <= npk) {
            i = ipx / nf;
            j = ipx % nf;
            fval = (double)data[ipx];
            add_pixel_local(&res[bl_NPROPERTY * (ipk - 1)], i, j, fval, omega);
        } else {
            if (ipk != 0) {
                bad++;
                if (bad < 10 && verbose)
                    printf("Found %d in blob image at i=%d, j=%d\n",
                           ipk, i, j);
            }
        }
    }
    if (verbose)
        printf("Found %d bad pixels in the blob image\n", bad);
}
