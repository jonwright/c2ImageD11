
/*
# ImageD11_v1.0 Software for beamline ID11
# Copyright (C) 2005-2007  Jon Wright
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/

#ifndef _blobs_h
#define _blobs_h
#include "cImageD11.h"

/* DLL_LOCAL
void match(int32_t * new, int32_t * old, int32_t * S);
*/
#define match(X, Y, Z)                                                         \
    do {                                                                       \
        if ((X) == 0) {                                                        \
            (X) = (Y);                                                         \
        } else {                                                               \
            if ((X) != (Y)) {                                                  \
                dset_makeunion((Z), (X), (Y));                                 \
            }                                                                  \
        }                                                                      \
    } while (0)

DLL_LOCAL
int32_t *dset_initialise(int32_t size); /* array to hold real values of each */

DLL_LOCAL
int32_t *dset_new(int32_t **S, int32_t *v);

DLL_LOCAL
void dset_makeunion(int32_t *S, int32_t r1, int32_t r2);

DLL_LOCAL
void dset_link(int32_t *S, int32_t r1, int32_t r2);

DLL_LOCAL
int32_t dset_find(int32_t x, int32_t *S);

DLL_LOCAL
int32_t *dset_compress(int32_t **pS, int32_t *np);

DLL_PUBLIC
/* Spot_ID - to be generated when writing out */
enum {
    s_1 = 0, /* 1 Npix */
    s_I,     /* 2 Sum intensity */
    s_I2,    /* 3 Sum intensity^2 */
    s_fI,    /* 4 Sum f * intensity */
    s_ffI,   /* 5 Sum f * f* intensity */
    s_sI,    /* 6 Sum s * intensity */
    s_ssI,   /* 7 Sum s * s * intensity */
    s_sfI,   /* 8 Sum f * s * intensity */
    s_oI,    /* 9 sum omega * intensity */
    s_ooI,   /* 10 sum omega2 * intensity */
    s_soI,   /* 11 sum omega * s * intensity */
    s_foI,   /* 12 sum omega * f * intensity */

    mx_I,   /* 13 Max intensity */
    mx_I_f, /* 14 fast at Max intensity */
    mx_I_s, /* 15 slow at Max intensity */
    mx_I_o, /* 16 omega at max I */

    bb_mx_f, /* 17 max of f */
    bb_mx_s, /* 18 max of s */
    bb_mx_o, /* 19 max of omega */
    bb_mn_f, /* 20 min of f */
    bb_mn_s, /* 21 min of s */
    bb_mn_o, /* 22 min of o */

    avg_i, /* Average intensity */
    f_raw, /* fast centre of mass */
    s_raw, /* slow centre of mass */
    o_raw, /* omega centre of mass */
    m_ss,  /* moments */
    m_ff,
    m_oo,
    m_sf,
    m_so,
    m_fo,

    f_cen, /* Filled in elsewhere  - spatial correction */
    s_cen, /* ditto */

    dety, /*Filled in elsewhere  - flip to HFPO book */
    detz, /*Filled in elsewhere  - flip to HFPO book */

    NPROPERTY /* Number of properties if starting at 0 */
};

DLL_PUBLIC
enum {
    s2D_1 = 0,
    s2D_I = 1,
    s2D_fI = 2,
    s2D_sI = 3,
    s2D_ffI = 4,
    s2D_sfI = 5,
    s2D_ssI = 6,
    s2D_bb_mx_f = 7,
    s2D_bb_mx_s = 8,
    s2D_bb_mn_f = 9,
    s2D_bb_mn_s = 10,
    NPROPERTY2D
};

/*void new_blob(double blob[], int i, int j, double val);*/

DLL_LOCAL
void add_pixel(double blob[], int i, int j, double val, double omega);

DLL_LOCAL
void merge(double blob1[], double blob2[]);

DLL_LOCAL
void compute_moments(double blobs[], intptr_t nblobs);

/* C2PY_BEGIN
 * {
 *     "s_1": 0, "s_I": 1, "s_I2": 2, "s_fI": 3,
 *     "s_ffI": 4, "s_sI": 5, "s_ssI": 6, "s_sfI": 7,
 *     "s_oI": 8, "s_ooI": 9, "s_soI": 10, "s_foI": 11,
 *     "mx_I": 12, "mx_I_f": 13, "mx_I_s": 14, "mx_I_o": 15,
 *     "bb_mx_f": 16, "bb_mx_s": 17, "bb_mx_o": 18,
 *     "bb_mn_f": 19, "bb_mn_s": 20, "bb_mn_o": 21,
 *     "avg_i": 22, "f_raw": 23, "s_raw": 24, "o_raw": 25,
 *     "m_ss": 26, "m_ff": 27, "m_oo": 28, "m_sf": 29,
 *     "m_so": 30, "m_fo": 31,
 *     "f_cen": 32, "s_cen": 33, "dety": 34, "detz": 35,
 *     "NPROPERTY": 36,
 *     "s2D_1": 0, "s2D_I": 1, "s2D_fI": 2, "s2D_sI": 3,
 *     "s2D_ffI": 4, "s2D_sfI": 5, "s2D_ssI": 6,
 *     "s2D_bb_mx_f": 7, "s2D_bb_mx_s": 8,
 *     "s2D_bb_mn_f": 9, "s2D_bb_mn_s": 10,
 *     "NPROPERTY2D": 11,
 * }
C2PY_END */
#endif /* _blobs_h */
