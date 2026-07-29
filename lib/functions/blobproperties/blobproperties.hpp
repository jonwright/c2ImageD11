#ifndef BLOBPROPERTIES_HPP
#define BLOBPROPERTIES_HPP

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

enum {
    s_1_bp = 0, s_I_bp = 1, s_I2_bp = 2, s_fI_bp = 3,
    s_ffI_bp = 4, s_sI_bp = 5, s_ssI_bp = 6, s_sfI_bp = 7,
    s_oI_bp = 8, s_ooI_bp = 9, s_soI_bp = 10, s_foI_bp = 11,
    mx_I_bp = 12, mx_I_f_bp = 13, mx_I_s_bp = 14, mx_I_o_bp = 15,
    bb_mx_f_bp = 16, bb_mx_s_bp = 17, bb_mx_o_bp = 18,
    bb_mn_f_bp = 19, bb_mn_s_bp = 20, bb_mn_o_bp = 21,
    avg_i_bp = 22, f_raw_bp = 23, s_raw_bp = 24, o_raw_bp = 25,
    m_ss_bp = 26, m_ff_bp = 27, m_oo_bp = 28, m_sf_bp = 29,
    m_so_bp = 30, m_fo_bp = 31, f_cen_bp = 32, s_cen_bp = 33,
    dety_bp = 34, detz_bp = 35, NPROPERTY_bp = 36
};

#ifdef __cplusplus
extern "C" {
#endif
void add_pixel(double blob[], int i, int j, double val, double omega);
#ifdef __cplusplus
}
#endif

template<typename TPixel>
static void blobproperties_impl(const TPixel *data, const int32_t *labels,
                                 int32_t npk, float omega, int verbose,
                                 intptr_t ns, intptr_t nf, double *res) {
    intptr_t i, j, ipx; int bad;
    double fval;
    int32_t ipk;
    if (verbose) {
        printf("Computing blob moments, ns %td, nf %td, npk %d\n", ns, nf, npk);
    }
    for (i = 0; i < npk; i++) {
        for (j = 0; j < NPROPERTY_bp; j++) {
            res[i * NPROPERTY_bp + j] = 0.;
        }
        res[i * NPROPERTY_bp + bb_mn_f_bp] = (double)(nf + 1);
        res[i * NPROPERTY_bp + bb_mn_s_bp] = (double)(ns + 1);
        res[i * NPROPERTY_bp + bb_mx_f_bp] = -1;
        res[i * NPROPERTY_bp + bb_mx_s_bp] = -1;
        res[i * NPROPERTY_bp + bb_mx_o_bp] = omega;
        res[i * NPROPERTY_bp + bb_mn_o_bp] = omega;
    }
    if (verbose != 0)
        printf("Scanning image\n");

    bad = 0;
    for (i = 0; i < ns; i++) {
        for (j = 0; j < nf; j++) {
            ipx = i * nf + j;
            ipk = labels[ipx];
            if (ipk > 0 && ipk <= npk) {
                fval = (double)data[ipx];
                add_pixel(&res[NPROPERTY_bp * (ipk - 1)], i, j, fval, omega);
            } else {
                if (ipk != 0) {
                    bad++;
                    if (bad < 10) {
                        printf("Found %d in your blob image at i=%td, j=%td\n",
                               ipk, i, j);
                    }
                }
            }
        }
    }
    if (verbose) {
        printf("\nFound %d bad pixels in the blob image\n", bad);
    }
}

#endif
