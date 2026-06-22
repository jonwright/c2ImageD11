/* Auto-extracted from ImageD11/src/cdiffraction.c, function compute_xlylzl, commit 8f7d29e
 *
 * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py
 */
#ifndef KERNEL_FN
#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"
#endif

#include "cImageD11.h"
#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include "cdiffraction.h"
#define NOISY 0

void KERNEL_FN(double s[], double f[], double p[4], double r[9],
                    double dist[3], double xlylzl[][3], intptr_t n) {
    double s_cen, f_cen, s_size, f_size, v[3];
    intptr_t i;
    int j;
    s_cen = p[0];
    f_cen = p[1];
    s_size = p[2];
    f_size = p[3];
    v[0] = 0.0;
    if (NOISY) {
        printf("s_cen %f f_cen %f s_size %f f_size %f\n", s_cen, f_cen, s_size,
               f_size);
        for (j = 0; j < 3; j++)
            printf("dist[%d]=%f ", j, dist[j]);
        for (j = 0; j < 9; j++)
            printf("r[%d]=%f ", j, r[j]);
        printf("\n");
    }
    for (i = 0; i < n; i++) {
        //     ! Place on the detector plane accounting for centre and size
        //     ! subtraction of centre is done here and not later for fear of
        //     ! rounding errors

        v[1] = (f[i] - f_cen) * f_size;
        v[2] = (s[i] - s_cen) * s_size;
        // ! Apply the flip and rotation, python was :
        // ! fl = dot( [[o11, o12], [o21, o22]], peaks=[[z],[y]] )
        // ! vec = [0,fl[1],fl[0]]
        // ! return dist + dot(rotmat, vec)
        for (j = 0; j < 3; j++) {
            //  ! Skip as v[0] is zero : r(1,j)*v(1)
            xlylzl[i][j] = r[3 * j + 1] * v[1] + r[3 * j + 2] * v[2] + dist[j];
        } // enddo
    } // enddo
} // end subroutine compute_xlylz
