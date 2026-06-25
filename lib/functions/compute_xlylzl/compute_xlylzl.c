#include "cImageD11.h"
#include "ImageD11_cmath.h"
static int NOISY = 0;

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_xlylzl(s: buffer, f: buffer, p: buffer, r: buffer, dist: buffer, xlylzl: buffer) -> void",
 *     "doc": "compute_xlylzl finds spot positions in the laboratory frame using packed parameters.",
 *     "params": {
 *         "s": "Slow-scan pixel positions (double).",
 *         "f": "Fast-scan pixel positions (double, same size as s).",
 *         "p": "Detector params (4): [s_cen, f_cen, s_size, f_size].",
 *         "r": "Rotation matrix (9): det(rotation)*flip.",
 *         "dist": "Detector distance (3): [dx, dy, dz].",
 *         "xlylzl": "Output spot positions (n, 3).",
 *     },
 *     "checks": ["s.format == 'd'", "f.format == 'd'", "f.n == s.n",
 *         "p.format == 'd'", "p.n == 4",
 *         "r.format == 'd'", "r.n == 9",
 *         "dist.format == 'd'", "dist.n == 3",
 *         "xlylzl.format == 'd'", "xlylzl.ndim >= 1"],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "s.format == 'd' and f.format == 'd' and xlylzl.format == 'd'",
 *         "sig": "void compute_xlylzl(const double s[], const double f[], const double p[4], const double r[9], const double dist[3], double xlylzl[][3], intptr_t n)",
 *         "map": {"s": "s.ptr", "f": "f.ptr", "p": "p.ptr", "r": "r.ptr", "dist": "dist.ptr", "xlylzl": "xlylzl.ptr", "n": "s.n"},
 *     }],
 * }
C2PY_END */

void compute_xlylzl(const double s[], const double f[], const double p[4], const double r[9],
                    const double dist[3], double xlylzl[][3], intptr_t n) {
    double s_cen, f_cen, s_size, f_size, v[3];
    intptr_t i; int j;
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
