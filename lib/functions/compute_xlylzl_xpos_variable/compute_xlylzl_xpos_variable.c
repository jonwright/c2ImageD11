#include "cImageD11.h"
#include "ImageD11_cmath.h"
static int NOISY = 0;

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_xlylzl_xpos_variable(s: buffer, f: buffer, p: buffer, r: buffer, dist: buffer, xpos: buffer, xlylzl: buffer) -> void",
 *     "doc": "compute_xlylzl_xpos_variable like compute_xlylzl but with extra per-spot x-offset.",
 *     "params": {
 *         "s": "Slow-scan pixel positions (double).",
 *         "f": "Fast-scan pixel positions (double).",
 *         "p": "Detector params (4).",
 *         "r": "Rotation matrix (9).",
 *         "dist": "Detector distance (3).",
 *         "xpos": "Per-spot x-axis offset (double, same size as s).",
 *         "xlylzl": "Output spot positions.",
 *     },
 *     "checks": ["s.format == 'd'", "f.format == 'd'", "f.n == s.n",
 *         "p.format == 'd'", "p.n == 4",
 *         "r.format == 'd'", "r.n == 9",
 *         "dist.format == 'd'", "dist.n == 3",
 *         "xpos.format == 'd'", "xpos.n == s.n",
 *         "xlylzl.format == 'd'", "xlylzl.ndim >= 1"],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "s.format == 'd' and f.format == 'd' and xlylzl.format == 'd'",
 *         "sig": "void compute_xlylzl_xpos_variable(const double s[], const double f[], const double p[4], const double r[9], const double dist[3], const double xpos[], double xlylzl[][3], intptr_t n)",
 *         "map": {"s": "s.ptr", "f": "f.ptr", "p": "p.ptr", "r": "r.ptr", "dist": "dist.ptr", "xpos": "xpos.ptr", "xlylzl": "xlylzl.ptr", "n": "s.n"},
 *     }],
 * }
C2PY_END */

void compute_xlylzl_xpos_variable(const double s[], const double f[], const double p[4], const double r[9],
    const double dist[3], const double xpos[],
    double xlylzl[][3], intptr_t n)
{
double s_cen, f_cen, s_size, f_size, v[3];
intptr_t i; int j;

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
