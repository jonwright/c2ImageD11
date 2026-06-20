/* Auto-extracted from ImageD11/src/cdiffraction.c, function compute_xlylzl_xpos_variable, commit 8f7d29e
 *
 * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py
 */
#ifndef KERNEL_FN
#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"
#endif

#include "cImageD11.h"
#include <stdio.h>
#include <math.h>
#include "cdiffraction.h"
#define NOISY 0

void KERNEL_FN(double s[], double f[], double p[4], double r[9],
    double dist[3], double xpos[],
    double xlylzl[][3], int n)
{
double s_cen, f_cen, s_size, f_size, v[3];
int i, j;

s_cen  = p[0];
f_cen  = p[1];
s_size = p[2];
f_size = p[3];
v[0]   = 0.0;

if (NOISY) {
printf("s_cen %f f_cen %f s_size %f f_size %f\n", s_cen, f_cen, s_size, f_size);
for (j = 0; j < 3; j++)
printf("dist[%d]=%f ", j, dist[j]);
for (j = 0; j < 9; j++)
printf("r[%d]=%f ", j, r[j]);
printf("\n");
}

for (i = 0; i < n; i++) {
/* Place on the detector plane accounting for centre and size */
v[1] = (f[i] - f_cen) * f_size;
v[2] = (s[i] - s_cen) * s_size;

/* Apply flip and rotation, then add per-spot x-offset */
xlylzl[i][0] = r[3 * 0 + 1] * v[1] + r[3 * 0 + 2] * v[2] + dist[0] - xpos[i];
xlylzl[i][1] = r[3 * 1 + 1] * v[1] + r[3 * 1 + 2] * v[2] + dist[1];
xlylzl[i][2] = r[3 * 2 + 1] * v[1] + r[3 * 2 + 2] * v[2] + dist[2];
}
} /* end subroutine compute_xlylzl_xpos_variable */
