#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_gvec_z(ubi: buffer, ub: buffer, gv: buffer, g0: buffer, g1: buffer, g2: buffer, e: buffer, recompute: int) -> void",
 *     "doc": "reads ubi, ub, gv and recompute\nif (recompute) it fills directions to project errors per peak:\n     g0 = gv / |gv|   = unit vector along g\n     g1 = gxy / |gxy| = unit vector perpendicular to z and g (omega)\n     g2 ... ought to be cross( g0, g1 ) ? (eta)\nFor all peaks it computes h = ubi.g, rounds to nearest ih = int(h)\nand then computes gcalc = ub.ih = dot( ub, ( round( dot( ubi, g) ) ) )\nThe error gv - gcalc is then projected into the co-ordinate system\ng0,g1,g2 for errors along g, z and the rhs\nBeware : work in progress. Is z always the right axis?",
 *     "params": {
 *         "ubi": "UBI matrix (9-element flattened double).",
 *         "ub": "UB matrix (9-element flattened double).",
 *         "gv": "Experimental g-vectors, shape (ng, 3) flattened.",
 *         "g0": "Error along g component.",
 *         "g1": "Error along z component.",
 *         "g2": "Error along rhs component.",
 *         "e": "Output error array.",
 *         "recompute": "If non-zero, recompute gcalc from ub.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "ub.format == 'd'",
 *         "ub.n == 9",
 *         "gv.format == 'd'",
 *         "gv.ndim >= 1",
 *         "g0.format == 'd'",
 *         "g1.format == 'd'",
 *         "g2.format == 'd'",
 *         "e.format == 'd'",
 *     ],
 *     "c_overloads": [{
 *         "sig": "void score_gvec_z(const double ubi[3][3], const double ub[3][3], const double gv[][3], double g0[], double g1[], double g2[], double e[], int recompute, intptr_t n)",
 *         "map": {"ubi": "ubi.ptr", "ub": "ub.ptr", "gv": "gv.ptr", "g0": "g0.ptr", "g1": "g1.ptr", "g2": "g2.ptr", "e": "e.ptr", "recompute": "recompute", "n": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */

void score_gvec_z(const vec ubi[3],    // in
                  const vec ub[3],     // in
                  const vec gv[],      // in
                  vec g0[],      // inout  normed(g)
                  vec g1[],      // inout  normed(axis x g)
                  vec g2[],      // inout  normed(axis x (axis x g))
                  vec e[],       // inout
                  int recompute, // in
                   intptr_t n) {
    /*  Axis is z and we hard wire it here
     *     Compute errors in a co-ordinate system given by:
     *         parallel to gv  (gv*imodg)
     *         parallel to cross( axis, gv )
     *         parallel to cross( axis, cross( axis, gv ) )
     */
    intptr_t i;
    double t, txy;
    vec g, h, d;
#pragma omp parallel for private(i, t, txy, g, h, d)
    for (i = 0; i < n; i++) {
        g[0] = gv[i][0];
        g[1] = gv[i][1];
        g[2] = gv[i][2];
        // Test - is it faster to recompute or cache ?
        //        for many ubi ? Loop over peaks or ubis or ?
        if (recompute) { // Fill in ub, modg, ax_x_gv, ax_ax_x_gv
            t = g[0] * g[0] + g[1] * g[1] + g[2] * g[2];
            if (t == 0.0) {
                e[i][0] = e[i][1] = e[i][2] = 0.0;
                continue;
            }
            t = 1. / sqrt(t);
            g0[i][0] = g[0] * t;
            g0[i][1] = g[1] * t;
            g0[i][2] = g[2] * t;
            txy = g[0] * g[0] + g[1] * g[1];
            t = 1. / sqrt(txy);
            g1[i][0] = -g[1] * t; // [-y,x,0]
            g1[i][1] = g[0] * t;
            g1[i][2] = 0.;
            t = 1. / sqrt(g[0] * g[0] * g[2] * g[2] +
                          g[1] * g[1] * g[2] * g[2] + txy * txy);
            g2[i][0] = g[0] * g[2] * t;
            g2[i][1] = g[1] * g[2] * t;
            g2[i][2] = -(g[0] * g[0] + g[1] * g[1]) * t;
        } // end recompute

        // Find integer h,k,l
        h[0] = (double)conv_double_to_int_fast(
            ubi[0][0] * g[0] + ubi[0][1] * g[1] + ubi[0][2] * g[2]);
        h[1] = (double)conv_double_to_int_fast(
            ubi[1][0] * g[0] + ubi[1][1] * g[1] + ubi[1][2] * g[2]);
        h[2] = (double)conv_double_to_int_fast(
            ubi[2][0] * g[0] + ubi[2][1] * g[1] + ubi[2][2] * g[2]);

        // Compute diff, the computed g-vector  - original
        d[0] = ub[0][0] * h[0] + ub[0][1] * h[1] + ub[0][2] * h[2] - g[0];
        d[1] = ub[1][0] * h[0] + ub[1][1] * h[1] + ub[1][2] * h[2] - g[1];
        d[2] = ub[2][0] * h[0] + ub[2][1] * h[1] + ub[2][2] * h[2] - g[2];

        // Now dot this into the local co-ordinate system
        e[i][0] = g0[i][0] * d[0] + g0[i][1] * d[1] + g0[i][2] * d[2];
        e[i][1] = g1[i][0] * d[0] + g1[i][1] * d[1] + g1[i][2] * d[2];
        e[i][2] = g2[i][0] * d[0] + g2[i][1] * d[1] + g2[i][2] * d[2];
    }
}
