

#include "cImageD11.h"
#include <stdint.h>
#include <float.h>
#include <math.h>
#include <stdio.h>

typedef double vec[3];

#define DEG(x) ((x) * 180. / 3.14159265358979323846264338327950288)

/*
# ImageD11_v1.x Software for beamline ID11
# Copyright (C) 2005-2017  Jon Wright
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

/* inline double conv_double_to_int_fast(double); */

double conv_double_to_int_safe(double x);

double conv_double_to_int_safe(double);

int inverse3x3(double A[3][3]);

/* Utils */
DLL_LOCAL
int inverse3x3(double H[3][3]) {
    double det, inverse[3][3];
    int i, j;
    /*
       # | a11 a12 a13 |-1             |   a33a22-a32a23  -(a33a12-a32a13)
       a23a12-a22a13  | # | a21 a22 a23 |    =  1/DET * | -(a33a21-a31a23)
       a33a11-a31a13  -(a23a11-a21a13) | # | a31 a32 a33 |               |
       a32a21-a31a22  -(a32a11-a31a12)   a22a11-a21a12  |

       # DET=a11   (a33     a22    -a32     a23)-
       a21   (a33      a12   -a32     a13)+
       a31   (a23     a12    -a22     a13)
     */

    det = H[0][0] * (H[2][2] * H[1][1] - H[2][1] * H[1][2]) -
          H[1][0] * (H[2][2] * H[0][1] - H[2][1] * H[0][2]) +
          H[2][0] * (H[1][2] * H[0][1] - H[1][1] * H[0][2]);

    if (det != 0.) {
        inverse[0][0] = (H[2][2] * H[1][1] - H[2][1] * H[1][2]) / det;
        inverse[0][1] = -(H[2][2] * H[0][1] - H[2][1] * H[0][2]) / det;
        inverse[0][2] = (H[1][2] * H[0][1] - H[1][1] * H[0][2]) / det;
        inverse[1][0] = -(H[2][2] * H[1][0] - H[2][0] * H[1][2]) / det;
        inverse[1][1] = (H[2][2] * H[0][0] - H[2][0] * H[0][2]) / det;
        inverse[1][2] = -(H[1][2] * H[0][0] - H[1][0] * H[0][2]) / det;
        inverse[2][0] = (H[2][1] * H[1][0] - H[2][0] * H[1][1]) / det;
        inverse[2][1] = -(H[2][1] * H[0][0] - H[2][0] * H[0][1]) / det;
        inverse[2][2] = (H[1][1] * H[0][0] - H[1][0] * H[0][1]) / det;

        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                H[i][j] = inverse[i][j];

        return 0;

    } else {
        return -1;
    }
}

DLL_LOCAL
double conv_double_to_int_safe(double x) { return floor(x + 0.5); }

/* See
 * https://stackoverflow.com/questions/59632005/why-does-this-code-beat-rint-and-how-to-i-protect-it-from-ffast-math-and-frie
 *
 * Replaced magic-constant trick with C99 nearbyint() because
 * -ffast-math optimizes the (x + MAGIC) - MAGIC expression to x,
 * making all peaks count as indexed regardless of tolerance.
 * nearbyint() maps to ROUNDPD/VRNDSCALEPD hardware on SSE4.1/AVX-512.
 */
#define conv_double_to_int_fast(x) nearbyint(x)

/* DLL_LOCAL
inline double conv_double_to_int_fast(double x) {
    return ((x + MAGIC) - MAGIC);
} */

/* F2PY_WRAPPER_START
    function verify_rounding( n )
!DOC checks the round to nearest int code is correct
        intent(c) verify_rounding
        intent(c)
        integer :: verify_rounding, n
    end function verify_rounding
F2PY_WRAPPER_END */
/* C2PY_BEGIN
 * {
 *     "py_sig": "verify_rounding(n: int) -> int",
 *     "doc": "checks the round to nearest int code is correct",
 *     "params": {
 *         "n": "ask jon about this parameter",
 *     },
 *     "c_overloads": [{
 *         "sig": "int verify_rounding(int n)",
 *         "map": {"n": "n"},
 *     }],
 * }
C2PY_END */
int verify_rounding(int n) {
    int i, hfast, hslow, bad = 0;
    double v;

    for (i = -100; i < 200; i++) {
        v = n + i * 50.0;
        hfast = conv_double_to_int_fast(v);
        hslow = conv_double_to_int_safe(v);
        if (hfast != hslow)
            bad++;
    }
    for (i = -100; i < 200; i++) {
        v = -n + i * 50.0;
        hfast = conv_double_to_int_fast(v);
        hslow = conv_double_to_int_safe(v);
        if (hfast != hslow)
            bad++;
    }
    return bad;
}

/* F2PY_WRAPPER_START
    subroutine closest_vec( x, dim, nv, ic )
!DOC closest_vec finds the closest neighbors for each row of X
!DOC ignoring the self. Treated as a X=[v1,v2,v3,...], computes
!DOC sum{(vi-vj)**2} for all i!=j and places minimum in ic.
        intent(c) closest_vec
        intent(c)
        double precision, intent(in) :: x(nv, dim)
        integer, intent(hide), depend(x) :: dim=shape(x,1)
        integer, intent(hide), depend(x) :: nv=shape(x,0)
        integer, intent(inout) :: ic( nv )
    end subroutine closest_vec
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "closest_vec(x: buffer, ic: buffer) -> void",
 *     "doc": "closest_vec finds the closest neighbors for each row of X ignoring the self.",
 *     "params": {
 *         "x": "2D array of feature vectors, shape (nv, dim). Each row is a vector.",
 *         "ic": "Output array of shape (nv,). For each row i, ic[i] = index j of the nearest neighbor (j != i).",
 *     },
 *     "checks": [
 *         "x.format == 'd'",
 *         "x.ndim == 2",
 *         "x.shape[1] >= 1",
 *         "( ic.format == 'i' or ic.format == 'l' )",
 *         "ic.n == x.shape[0]",
 *     ],
 *     "c_overloads": [{
 *         "sig": "void closest_vec(double *x, intptr_t dim, intptr_t nv, int *ic)",
 *         "map": {"x": "x.ptr", "dim": "x.shape[1]", "nv": "x.shape[0]", "ic": "ic.ptr"},
 *     }],
 * }
C2PY_END */
void closest_vec(double x[], intptr_t dim, intptr_t nv, int closest[]) {
    /*
     * For each x it finds the closest neighbor
     *   this will grow as n^2, which means it rapidly becomes slow
     */
    intptr_t i, j, k; int ib;
    double scor, best, t;

#pragma omp parallel for private(i, j, k, ib, scor, best, t)
    for (i = 0; i < nv; i++) { /* source vector */
        /* init with something */
        j = (i + 1) % nv;
        best = 0.;
        for (k = 0; k < dim; k++) {
            t = x[i * dim + k] - x[j * dim + k];
            best += t * t;
        }
        ib = j;
        /* now check all the others */
        for (j = 0; j < nv; j++) {
            if (i == j)
                continue;
            scor = 0.;
            for (k = 0; k < dim; k++) {
                t = x[i * dim + k] - x[j * dim + k];
                scor += t * t;
            }
            if (scor < best) {
                ib = j;
                best = scor;
            }
        }
        closest[i] = ib;
    }
}

/* F2PY_WRAPPER_START
    subroutine closest( x, v, ibest, best, nx, nv  )
!DOC closest finds the value and index in x closest to a value in v.
!DOC e.g. x = cosine of angles between pairs of peaks
!DOC      v = idealised values based on hkl geometry
!DOC   ibest set to the x[i] matching to a v[j] with diff "best"
        intent(c) closest
        double precision, intent(in) :: x(nx)
        double precision, intent(in) :: v(nv)
        ! Note : these are intent(fortran) to pass as pointers
        integer, intent( out ) :: ibest
        double precision, intent( out ) :: best
        ! Note : these are intent(c) to pass by reference
        integer, intent(c, hide), depend(x) :: nx=shape(x,0)
        integer, intent(c, hide), depend(v) :: nv=shape(v,0)
        threadsafe
    end subroutine closest
F2PY_WRAPPER_END */
/* C2PY_BEGIN
 * {
 *     "py_sig": "closest(x: buffer, v: buffer) -> void",
 *     "doc": "closest finds the value and index in x closest to a value in v.",
 *     "params": {
 *         "x": "Array of candidate values to search (e.g. ideal cosines from hkl geometry).",
 *         "v": "Array of values to search for (e.g. experimental cosines).",
 *     },
 *     "checks": [
 *         "x.format == 'd'",
 *         "v.format == 'd'",
 *     ],
 *     "c_overloads": [{
 *         "sig": "void closest(double *x, double *v, int *ribest, double *rbest, intptr_t nx, intptr_t nv)",
 *         "outputs": {"ribest": "int", "rbest": "double"},
 *         "doc": "Standard O(nx*nv) scan-find-closest.",
 *         "map": {"x": "x.ptr", "v": "v.ptr", "nx": "x.n", "nv": "v.n"},
 *     }],
 * }
C2PY_END */
void closest(double x[], double v[], int *ribest, double *rbest, intptr_t nx,
             intptr_t nv) {
    /*
     * Finds value and index in x closest to a value in v
     */
    intptr_t i, j; int ibest;
    double best;
    best = DBL_MAX;
    ibest = 0;
    for (i = 0; i < nx; i++) {
        for (j = 0; j < nv; j++) {
            if (fabs(x[i] - v[j]) < best) {
                best = fabs(x[i] - v[j]);
                ibest = i;
            }
        }
    }
    *ribest = ibest;
    *rbest = best;
}

/* F2PY_WRAPPER_START

    function score( ubi, gv, tol, ng )
!DOC score takes a ubi matrix and list of g-vectors and computes
!DOC hkl = dot(ubi, gv), then rounds these g-vectors to integer
!DOC and computes drlv2 = (h-int(h))**2 + (k-int(k))**2 + (l-int(l))**2
!DOC If drlv2 is less than tol*tol then the peak is considered to
!DOC be indexed. Returns the number of peaks found.
        intent(c) score
        intent(c)
        integer :: score
        integer, intent(hide), depend(gv) :: ng
        double precision, intent(in) :: ubi(3,3)
        double precision, intent(in) :: gv(ng, 3)
        double precision, intent(in) :: tol
        ! only reads gvectors
    end function score
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "score(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "doc": "Count g-vectors indexed by ubi matrix within tol.",
 *     "params": {
 *         "ubi": "Orientation matrix UBI (UB inverse), shape (9,) flattened double.",
 *         "gv": "G-vectors array, shape (ng, 3) flattened.",
 *         "tol": "Tolerance on |h - round(h)|.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "gv.format == 'd'",
 *         "gv.ndim >= 1",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd'",
 *         "sig": "int score(double ubi[3][3], double gv[][3], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */
int score(vec ubi[3], vec gv[], double tol, intptr_t ng) {
    /*
     * Counts g-vectors indexed by ubi within tol
     */
    double sumsq, h0, h1, h2, atol;
    int n; intptr_t k;
    n = 0;
    atol = tol * tol;
    for (k = 0; k < ng; k++) {
        h0 = ubi[0][0] * gv[k][0] + ubi[0][1] * gv[k][1] + ubi[0][2] * gv[k][2];
        h0 -= conv_double_to_int_fast(h0);
        h1 = ubi[1][0] * gv[k][0] + ubi[1][1] * gv[k][1] + ubi[1][2] * gv[k][2];
        h1 -= conv_double_to_int_fast(h1);
        h2 = ubi[2][0] * gv[k][0] + ubi[2][1] * gv[k][1] + ubi[2][2] * gv[k][2];
        h2 -= conv_double_to_int_fast(h2);
        sumsq = h0 * h0 + h1 * h1 + h2 * h2;
        if (sumsq < atol) {
            n = n + 1;
        }
    }
    return n;
}

/* F2PY_WRAPPER_START

    subroutine score_and_refine( ubi, gv, tol, n, sumdrlv2, ng)
!DOC score_and_refine is very similar to score but it also refines the UB
!DOC matrix using the assigned peaks and overwrite the argument.
!DOC It returns the number of peaks and fit prior to refinement.
        intent(c) score_and_refine
        ! Note: fortran, pass by ref here  = C has double *sumdrlv2 etc.
        integer, intent( out ) :: n
        double precision, intent(out) :: sumdrlv2
        double precision, intent(c, inout) :: ubi(3,3)
        double precision, intent(c, in) :: gv(ng,3)
        integer, intent(c, hide), depend( gv ) :: ng
        double precision, intent(c, in) :: tol
        threadsafe
    end subroutine score_and_refine
F2PY_WRAPPER_END */
/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "doc": "score_and_refine also refines the UB matrix using the assigned peaks.",
 *     "params": {
 *         "ubi": "Orientation matrix UBI (9-element flattened double).",
 *         "gv": "G-vectors array, shape (ng, 3) flattened.",
 *         "tol": "Matching tolerance on |h - round(h)|.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "gv.format == 'd'",
 *         "gv.ndim >= 1",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd'",
 *         "sig": "void score_and_refine(double ubi[3][3], double gv[][3], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */
void score_and_refine(vec ubi[3], vec gv[], double tol, int *n_arg,
                      double *sumdrlv2_arg, intptr_t ng) {
    /* ng = number of g vectors */
    double h0, h1, h2, t0, t1, t2, ih[3];
    double sumsq, tolsq, sumdrlv2;
    double R[3][3], H[3][3], UB[3][3];
    int n; intptr_t k; int i, j, l;
    /* Zero some stuff for refinement */
    for (i = 0; i < 3; i++) {
        ih[i] = 0;
        for (j = 0; j < 3; j++) {
            R[i][j] = 0.;
            H[i][j] = 0.;
            UB[i][j] = 0.;
        }
    }
    tolsq = tol * tol;
    n = 0;
    sumdrlv2 = 0.;
    /* Test peaks */
    for (k = 0; k < ng; k++) {
        h0 = ubi[0][0] * gv[k][0] + ubi[0][1] * gv[k][1] + ubi[0][2] * gv[k][2];
        h1 = ubi[1][0] * gv[k][0] + ubi[1][1] * gv[k][1] + ubi[1][2] * gv[k][2];
        h2 = ubi[2][0] * gv[k][0] + ubi[2][1] * gv[k][1] + ubi[2][2] * gv[k][2];
        t0 = h0 - conv_double_to_int_fast(h0);
        t1 = h1 - conv_double_to_int_fast(h1);
        t2 = h2 - conv_double_to_int_fast(h2);
        sumsq = t0 * t0 + t1 * t1 + t2 * t2;
        if (sumsq < tolsq) { /* Add into lsq problem */
            n = n + 1;
            sumdrlv2 += sumsq;
            /*   From Paciorek et al Acta A55 543 (1999)
             *   UB = R H-1
             *   where:
             *   R = sum_n r_n h_n^t
             *   H = sum_n h_n h_n^t
             *   r = g-vectors
             *   h = hkl indices
             *   The hkl integer indices are: */
            ih[0] = conv_double_to_int_fast(h0);
            ih[1] = conv_double_to_int_fast(h1);
            ih[2] = conv_double_to_int_fast(h2);
            /* The g-vector is: gv[k][012] */
            for (i = 0; i < 3; i++) {
                for (j = 0; j < 3; j++) {
                    /* Robust weight factor, fn(tol), would go here */
                    R[i][j] = R[i][j] + ih[j] * gv[k][i];
                    H[i][j] = H[i][j] + ih[j] * ih[i];
                }
            } /* End lsq addins */
        } /* End selected peaks */
    } /* End first loop over spots */

    /* Now solve the least squares problem */
    /* inverse overwrites H with the inverse */
    k = inverse3x3(H);
    if (k == 0) {
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                for (l = 0; l < 3; l++)
                    UB[i][j] += R[i][l] * H[l][j];
    }
    /* Now form ubi and copy to argument */
    if ((k == 0) && (inverse3x3(UB) == 0)) {
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                ubi[i][j] = UB[i][j];
    } else {
        /* Determinant was zero - leave ubi as it is */
    }

    if (n > 0) {
        sumdrlv2 /= n;
    }

    /* return values */
    *n_arg = n;
    *sumdrlv2_arg = sumdrlv2;
}

/* F2PY_WRAPPER_START
    function score_and_assign( ubi, gv, tol, drlv2, labels,label, ng )
!DOC score_and_assign is similar to score but it assigns peaks to this
!DOC ubi only if they fit the data better than the current UBI.
!DOC It updates drlv2 and labels to use best fitting grain for each peak.
!DOC  ... perhaps this is not what you want for overlapping peaks in twins!
        intent(c) score_and_assign
        intent(c)
        integer score_and_assign
        double precision, intent(in) :: ubi(3,3)
        double precision, intent(in) :: gv(ng,3)
        integer, intent(hide), depend( gv ) :: ng
        double precision, intent(in) :: tol
        double precision, intent(inout) :: drlv2(ng)
        integer*4, intent(inout) :: labels(ng)
        integer, intent(in) :: label
        ! NOT threadsafe - labels will be shared
    end function score_and_assign
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "doc": "score_and_assign assigns peaks to this ubi only if they fit the data better.",
 *     "params": {
 *         "ubi": "Orientation matrix (9-element flattened double).",
 *         "gv": "G-vectors array, shape (ng, 3) flattened.",
 *         "tol": "Matching tolerance.",
 *         "drlv2": "Input/output array (ng). Current best squared residuals per peak.",
 *         "labels": "Input/output array (ng). Current grain labels per peak.",
 *         "label": "Grain label assigned to peaks that match this UBI.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "gv.format == 'd'",
 *         "drlv2.format == 'd'",
 *         "drlv2.n == gv.shape[0]",
 *         "( labels.format == 'i' or labels.format == 'l' )",
 *         "labels.n == gv.shape[0]",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd'",
 *         "sig": "int score_and_assign(double ubi[3][3], double gv[][3], double tol, double *drlv2, int *labels, int label, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "drlv2": "drlv2.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */
int score_and_assign(vec *restrict ubi, vec *restrict gv, double tol,
                     double *restrict drlv2, int *restrict labels, int label,
                     intptr_t ng) {

    double h0, h1, h2, t0, t1, t2, sumsq, tolsq;
    intptr_t k; int n;
    tolsq = tol * tol;
    n = 0;
#pragma omp parallel for private(h0, h1, h2, t0, t1, t2, sumsq)                \
    reduction(+ : n) schedule(static, 4096)
    for (k = 0; k < ng; k++) {
        h0 = ubi[0][0] * gv[k][0] + ubi[0][1] * gv[k][1] + ubi[0][2] * gv[k][2];
        h1 = ubi[1][0] * gv[k][0] + ubi[1][1] * gv[k][1] + ubi[1][2] * gv[k][2];
        h2 = ubi[2][0] * gv[k][0] + ubi[2][1] * gv[k][1] + ubi[2][2] * gv[k][2];
        t0 = h0 - conv_double_to_int_fast(h0);
        t1 = h1 - conv_double_to_int_fast(h1);
        t2 = h2 - conv_double_to_int_fast(h2);
        sumsq = t0 * t0 + t1 * t1 + t2 * t2;
        /* If this peak fits better than the one in drlv2 then we
         * assign it:
         */
        if ((sumsq < tolsq) && (sumsq < drlv2[k])) {
            labels[k] = label;
            drlv2[k] = sumsq;
            n++;
        } else if (labels[k] == label) {
            /* We thought it belonged but it does not */
            labels[k] = -1;
        }
    }
    return n;
}

/* F2PY_WRAPPER_START
    subroutine refine_assigned( ubi, gv, labels, label, npk, drlv2, ng )
!DOC refine_assigned fits a ubi matrix to a set of g-vectors and assignments
!DOC in labels. e.g. where(labels==label) it uses the peaks.
!DOC   ... perhaps this is not what you want for overlapping peaks in twins!
        intent(c) refine_assigned
        double precision, intent(c,in) :: ubi(3,3)
        double precision, intent(c,in) :: gv(ng,3)
        integer, intent(c,in) :: labels(ng)
        integer, intent(c,in) :: label
        ! Note : pass by ref
        integer, intent(out) :: npk
        double precision, intent(out) :: drlv2
        integer, intent(c,hide), depend( gv ) :: ng
        threadsafe
    end subroutine refine_assigned
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "refine_assigned(ubi: buffer, gv: buffer, labels: buffer, label: int) -> void",
 *     "doc": "refine_assigned fits a ubi matrix to a set of g-vectors and assignments in labels.",
 *     "params": {
 *         "ubi": "Orientation matrix (9-element flattened double).",
 *         "gv": "G-vectors array, shape (ng, 3) flattened.",
 *         "labels": "Peak-to-grain assignments (ng ints).",
 *         "label": "Grain label to refine.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "gv.format == 'd'",
 *         "( labels.format == 'i' or labels.format == 'l' )",
 *         "labels.n == gv.shape[0]",
 *     ],
 *     "c_overloads": [{
 *         "sig": "void refine_assigned(double ubi[3][3], double gv[][3], int *labels, int label, int *npk, double *drlv2, intptr_t ng)",
 *         "outputs": {"npk": "int", "drlv2": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */
void refine_assigned(vec ubi[3], vec gv[], int labels[], int label, int *npk,
                     double *sumdrlv2, intptr_t ng) {
    /* Skip the part about weights, not used */
    double sumsqtot, sumsq, h[3], t[3], ih[3];
    double R[3][3], H[3][3], UB[3][3];
    int i, j, n; intptr_t k; int l;
    n = 0;
    sumsqtot = 0;
    for ( i = 0; i < 3; i++ ){
        for ( j = 0; j < 3; j++ ){
            R[i][j] = 0.;
            H[i][j] = 0.;
            UB[i][j] = 0.;
        }
    }
    for (k = 0; k < ng; k++) {
        if (label != labels[k]) {
            continue;
        }
        n++;
        for (j = 0; j < 3; j++) {
            h[j] = ubi[j][0] * gv[k][0] + ubi[j][1] * gv[k][1] +
                   ubi[j][2] * gv[k][2];
            ih[j] = conv_double_to_int_fast(h[j]);
            t[j] = h[j] - ih[j];
        }
        sumsq = t[0] * t[0] + t[1] * t[1] + t[2] * t[2];
        sumsqtot += sumsq;
        for (i = 0; i < 3; i++) {
            for (j = 0; j < 3; j++) {
                R[i][j] = R[i][j] + ih[j] * gv[k][i];
                H[i][j] = H[i][j] + ih[j] * ih[i];
            }
        }
    }
    /* outputs */
    *npk = n;
    if (n > 0) {
        *sumdrlv2 = sumsqtot / n;
    } else {
        *sumdrlv2 = 0.;
    }
    /* And the fitted matrix */
    k = inverse3x3(H);
    if (k == 0) {
        /* Form best fit UB */
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                for (l = 0; l < 3; l++)
                    UB[i][j] = UB[i][j] + R[i][l] * H[l][j];
    }

    if (k == 0 && inverse3x3(UB) == 0) {
        /* Copy to output */
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                ubi[i][j] = UB[i][j];
    }
}

/* F2PY_WRAPPER_START
    subroutine put_incr64( data, ind, vals,  boundscheck, n, m)
!DOC put_incr64 does the simple loop : data[ind] += vals
!DOC not sure why this isn't in numpy
!DOC uses 64 bit addressing
        intent(c) put_incr64
        intent(c)
        real, intent(inout) :: data(m)
        real, intent(in) :: vals(n)
        integer(kind=8), dimension(n), intent(in) :: ind
        integer, intent(hide), depend( data ) :: m
        integer, intent(hide), depend( ind) :: n
        integer, optional :: boundscheck = 0
        ! NOT threadsafe? meant for updating data with increments
    end subroutine put_incr
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "put_incr64(data: buffer, ind: buffer, vals: buffer, boundscheck: int = 0) -> void",
 *     "doc": "put_incr64 does the simple loop: data[ind] += vals, 64 bit addressing",
 *     "params": {
 *         "data": "Destination array (float32). Updated in place with scatter-add.",
 *         "ind": "Indices array (int64).",
 *         "vals": "Values array (float32) to add.",
 *         "boundscheck": "If non-zero, enables bounds checking on ind. Default 0 (no check).",
 *     },
 *     "checks": [
 *         "data.format == 'f'",
 *         "ind.format == 'q' or ind.itemsize == 8",
 *         "ind.n == vals.n",
 *         "vals.format == 'f'",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "data.format == 'f' and vals.format == 'f'",
 *         "sig": "void put_incr64(float *data, const int64_t *ind, const float *vals, int boundscheck, intptr_t n, intptr_t m)",
 *         "map": {"data": "data.ptr", "ind": "ind.ptr", "vals": "vals.ptr", "boundscheck": "boundscheck", "n": "ind.n", "m": "data.n"},
 *     }],
 * }
C2PY_END */
void put_incr64(float data[], int64_t ind[], float vals[], int boundscheck,
                intptr_t n, intptr_t m) {
    int64_t k, ik;
    if (boundscheck == 0) {
        for (k = 0; k < n; k++)
            data[ind[k]] += vals[k];
    } else {
        for (k = 0; k < n; k++) {
            ik = ind[k];
            if (ik < 0 || ik >= m) {
                printf("Array bounds error! k=%d ind[k]=%d\n", (int)k,
                       (int)ind[k]);
            } else {
                data[ind[k]] += vals[k];
            }
        }
    }
}

/* F2PY_WRAPPER_START

    subroutine put_incr32( data, ind, vals,  boundscheck, n, m)
!DOC put_incr32 does the simple loop : data[ind] += vals
!DOC not sure why this isn't in numpy
!DOC uses 32 bit addressing
        intent(c) put_incr32
        intent(c)
        real, intent(inout) :: data(m)
        real, intent(in) :: vals(n)
        integer(kind=4), dimension(n), intent(in) :: ind
        integer, intent(hide), depend( data ) :: m
        integer, intent(hide), depend( ind) :: n
        integer, optional :: boundscheck = 0
        ! NOT threadsafe? meant for updating data with increments
    end subroutine put_incr

F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "put_incr32(data: buffer, ind: buffer, vals: buffer, boundscheck: int = 0) -> void",
 *     "doc": "put_incr32 does the simple loop: data[ind] += vals, 32 bit addressing",
 *     "params": {
 *         "data": "Destination array (float32).",
 *         "ind": "Indices array (int32).",
 *         "vals": "Values array (float32) to add.",
 *         "boundscheck": "If non-zero, enables bounds checking on ind.",
 *     },
 *     "checks": [
 *         "data.format == 'f'",
 *         "( ind.format == 'i' or ind.format == 'l' )",
 *         "ind.n == vals.n",
 *         "vals.format == 'f'",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "data.format == 'f' and vals.format == 'f' and (ind.format == 'i' or ind.format == 'l')",
 *         "sig": "void put_incr32(float *data, const int32_t *ind, const float *vals, int boundscheck, intptr_t n, intptr_t m)",
 *         "map": {"data": "data.ptr", "ind": "ind.ptr", "vals": "vals.ptr", "boundscheck": "boundscheck", "n": "ind.n", "m": "data.n"},
 *     }],
 * }
C2PY_END */
void put_incr32(float data[], int32_t ind[], float vals[], int boundscheck,
                intptr_t n, intptr_t m) {
    int32_t k, ik;
    if (boundscheck == 0) {
        for (k = 0; k < n; k++)
            data[ind[k]] += vals[k];
    } else {
        for (k = 0; k < n; k++) {
            ik = ind[k];
            if (ik < 0 || ik >= m) {
                printf("Array bounds error! k=%d ind[k]=%d\n", (int)k,
                       (int)ind[k]);
            } else {
                data[ind[k]] += vals[k];
            }
        }
    }
}

/* F2PY_WRAPPER_START

    subroutine cluster1d( ar, n, order, tol, nclusters, ids, avgs)
!DOC cluster1d is used in sandbox/friedel.py to find clusters of peaks
!DOC work in progress
        intent(c) cluster1d
        double precision, intent(c, in) :: ar(n)
        integer, intent(c, hide), depend( ar ) :: n
        integer, intent(c, in) :: order(n)
        double precision, intent(c, in) :: tol
        integer, intent(out) :: nclusters
        integer, intent(c,inout) :: ids(n)
        double precision, intent(c, inout) :: avgs(n)
        ! NOT threadsafe since ids may be shared
    end subroutine cluster1d
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "cluster1d(ar: buffer, order: buffer, tol: float, nclusters: buffer, ids: buffer, avgs: buffer) -> void",
 *     "doc": "cluster1d is used to find clusters of peaks.",
 *     "params": {
 *         "ar": "Array of values to cluster.",
 *         "order": "Permutation that sorts ar ascending.",
 *         "tol": "Distance tolerance for cluster membership.",
 *         "nclusters": "Output: number of clusters found.",
 *         "ids": "Output: cluster id for each element.",
 *         "avgs": "Output: average value of each cluster.",
 *     },
 *     "checks": [
 *         "ar.format == 'd'",
 *         "( order.format == 'i' or order.format == 'l' )",
 *         "order.n == ar.n",
 *         "( nclusters.format == 'i' or nclusters.format == 'l' )",
 *         "nclusters.n == 1",
 *         "( ids.format == 'i' or ids.format == 'l' )",
 *         "ids.n == ar.n",
 *         "avgs.format == 'd'",
 *         "avgs.n == ar.n",
 *     ],
 *     "c_overloads": [{
 *         "sig": "void cluster1d(double *ar, intptr_t n, int *order, double tol, int *nclusters, int *ids, double *avgs)",
 *         "map": {"ar": "ar.ptr", "n": "ar.n", "order": "order.ptr", "tol": "tol", "nclusters": "nclusters.ptr", "ids": "ids.ptr", "avgs": "avgs.ptr"},
 *     }],
 * }
C2PY_END */
void cluster1d(double ar[], intptr_t n, int order[], double tol, // IN
               int *nclusters, int ids[], double avgs[]) {  // OUT
    // Used in sandbox/friedel.py
    intptr_t i; int ncl;
    double dv;
    // order is the order of the peaks to get them sorted
    avgs[0] = ar[order[0]];
    ncl = 1;    // number in this cluster
    ids[0] = 0; // cluster assignments ( in order )
    for (i = 1; i < n; i++) {
        dv = ar[order[i]] - ar[order[i - 1]]; // difference in values
        if (dv > tol) {                       // make a new cluster
            if (ncl > 1) {                    // make avg for the last one
                avgs[ids[i - 1]] = avgs[ids[i - 1]] / ncl;
            }
            ids[i] = ids[i - 1] + 1;     // increment id
            ncl = 1;                     // pks in this cluster
            avgs[ids[i]] = ar[order[i]]; // store value for avg
        } else {
            ids[i] = ids[i - 1]; // copy last id
            ncl = ncl + 1;
            avgs[ids[i]] = avgs[ids[i]] + ar[order[i]]; // sum on for avg
        }
    } // end for(i ...
    // make the last average if necessary
    if (ncl > 1) {
        avgs[ids[i - 1]] /= ncl;
    }
    *nclusters = ids[n - 1] + 1;
}

/* F2PY_WRAPPER_START
    subroutine score_gvec_z( ubi, ub, gv, g0, g1, g2, e, recompute, n )
!DOC score_gvec_z reads ubi, ub, gv and recompute
!DOC if (recompute) it fills directions to project errors per peak:
!DOC      g0 = gv / |gv|   = unit vector along g
!DOC      g1 = gxy / |gxy| = unit vector perpendicular to z and g (omega)
!DOC      g2 ... ought to be cross( g0, g1 ) ? (eta)
!DOC For all peaks it computes h = ubi.g, rounds to nearest ih = int(h)
!DOC and then computes gcalc = ub.ih = dot( ub, ( round( dot( ubi, g) ) ) )
!DOC The error gv - gcalc is then projected into the co-ordinate system
!DOC g0,g1,g2 for errors along g, z and the rhs
!DOC Beware : work in progress. Is z always the right axis?
        intent(c) score_gvec_z
        intent(c)
        double precision, intent(in)    :: ubi(3,3)
        double precision, intent(in)    :: ub(3,3)
        integer, intent(c, hide), depend( gv ) :: n
        double precision, intent(in)    :: gv(n,3)
        double precision, intent(inout) :: g0(n,3)
        double precision, intent(inout) :: g1(n,3)
        double precision, intent(inout) :: g2(n,3)
        double precision, intent(inout) ::  e(n,3)
        integer, intent(in) :: recompute
        ! NOT threadsafe since gi may be shared
    end subroutine score_gvec_z
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_gvec_z(ubi: buffer, ub: buffer, gv: buffer, g0: buffer, g1: buffer, g2: buffer, e: buffer, recompute: int) -> void",
 *     "doc": "score_gvec_z computes error projections for g-vectors.",
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
 *         "sig": "void score_gvec_z(double ubi[3][3], double ub[3][3], double gv[][3], double g0[], double g1[], double g2[], double e[], int recompute, intptr_t n)",
 *         "map": {"ubi": "ubi.ptr", "ub": "ub.ptr", "gv": "gv.ptr", "g0": "g0.ptr", "g1": "g1.ptr", "g2": "g2.ptr", "e": "e.ptr", "recompute": "recompute", "n": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */
void score_gvec_z(vec ubi[3],    // in
                  vec ub[3],     // in
                  vec gv[],      // in
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

/* F2PY_WRAPPER_START

    function misori_cubic( u1, u2)
!DOC misori_cubic computes the trace of the smallest misorientation
!DOC  for cubic symmetry
!DOC  u1 and u2 are both orientation matrices "U"
!DOC      compute u1. u2.T  to get the rotation from one to the other
!DOC      find the permutation that will maximise the trace
!DOC        one of six...
!DOC           xyz   yxz   zxy
!DOC           xzy   yzx   zyx
!DOC Beware : work in progress. Which point group is this?
        intent(c) misori_cubic
        intent(c)
        double precision, intent(in) :: u1(3,3), u2(3,3)
        ! Returns
        double precision :: misori_cubic
        threadsafe
    end function misori_cubic
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "misori_cubic(u1: buffer, u2: buffer) -> float",
 *     "doc": "misori_cubic computes the smallest misorientation for cubic symmetry.",
 *     "params": {
 *         "u1": "Orientation matrix U (9-element flattened double).",
 *         "u2": "Orientation matrix U (9-element flattened double).",
 *     },
 *     "checks": [
 *         "u1.format == 'd'",
 *         "u1.n == 9",
 *         "u2.format == 'd'",
 *         "u2.n == 9",
 *     ],
 *     "c_overloads": [{
 *         "sig": "double misori_cubic(double u1[3][3], double u2[3][3]) -> double",
 *         "map": {"u1": "u1.ptr", "u2": "u2.ptr"},
 *     }],
 * }
C2PY_END */
double misori_cubic(vec u1[3], vec u2[3]) {
    /* Compute the trace of the smallest misorientation
     * for cubic symmetry
     *  u1 and u2 are both orientation matrices "U"
     *
     * compute u1. u2.T  to get the rotation from one to the other
     * find the permutation that will maximise the trace
     *   one of six...
     *      xyz   yxz   zxy
     *      xzy   yzx   zyx
     */
    int i, j, k;
    double t[6], m1, m2, m3;
    vec r[3];
    for (i = 0; i < 3; i++) {
        for (j = 0; j < 3; j++) {
            r[i][j] = 0.;
            for (k = 0; k < 3; k++)
                r[i][j] += u1[k][i] * u2[k][j];
        }
    }
    /* 6 possibilities, 18 entries, each appears twice
       [0,0][1,1][2,2]
       [0,0][1,2][2,1]
       [0,1][1,0][2,2]
       [0,1][2,0][1,2]
       [0,2][1,0][2,1]
       [0,2][2,0][1,1]
     */
    t[0] = fabs(r[0][0]) + fabs(r[1][1]) + fabs(r[2][2]);
    t[1] = fabs(r[0][0]) + fabs(r[1][2]) + fabs(r[2][1]);
    t[2] = fabs(r[0][1]) + fabs(r[1][0]) + fabs(r[2][2]);
    t[3] = fabs(r[0][1]) + fabs(r[2][0]) + fabs(r[1][2]);
    t[4] = fabs(r[0][2]) + fabs(r[1][0]) + fabs(r[2][1]);
    t[5] = fabs(r[0][2]) + fabs(r[2][0]) + fabs(r[1][1]);
    /* select the maximum */
    m1 = (t[0] > t[1]) ? t[0] : t[1];
    m2 = (t[2] > t[3]) ? t[2] : t[3];
    m3 = (t[4] > t[5]) ? t[4] : t[5];
    m2 = (m2 > m3) ? m2 : m3;
    m1 = (m1 > m2) ? m1 : m2;
    return m1;
}

/* F2PY_WRAPPER_START

    function misori_orthorhombic( u1, u2)
!DOC misori_orthorhombic computes the trace of the smallest misorientation
!DOC  u1 and u2 are both orientation matrices "U"
!DOC      compute u1. u2.T  to get the rotation from one to the other
!DOC      find the flips that will maximise the trace:
!DOC        abs( trace(dot(u1,u2.T) ))
!DOC  Looks like point group mmm. Not sure why this is in C?
!DOC  Beware: work in progress
        intent(c) misori_orthorhombic
        intent(c)
        double precision, intent(in) :: u1(3,3), u2(3,3)
        ! Returns
        double precision :: misori_orthorhombic
        threadsafe
    end function misori_orthorhombic
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "misori_orthorhombic(u1: buffer, u2: buffer) -> float",
 *     "doc": "misori_orthorhombic computes the smallest misorientation for orthorhombic symmetry.",
 *     "params": {
 *         "u1": "Orientation matrix U (9-element flattened double).",
 *         "u2": "Orientation matrix U (9-element flattened double).",
 *     },
 *     "checks": [
 *         "u1.format == 'd'",
 *         "u1.n == 9",
 *         "u2.format == 'd'",
 *         "u2.n == 9",
 *     ],
 *     "c_overloads": [{
 *         "sig": "double misori_orthorhombic(double u1[3][3], double u2[3][3]) -> double",
 *         "map": {"u1": "u1.ptr", "u2": "u2.ptr"},
 *     }],
 * }
C2PY_END */
double misori_orthorhombic(vec u1[3], vec u2[3]) {
    /* Compute the trace of the smallest misorientation
     * for orthorhombic symmetry
     *  u1 and u2 are both orientation matrices "U"
     *
     * compute u1. u2.T  to get the rotation from one to the other
     * find the flips - just abs(trace)
     */
    int i, k;
    double ti, t;
    t = 0;
    for (i = 0; i < 3; i++) {
        ti = 0.;
        for (k = 0; k < 3; k++) {
            ti += u1[k][i] * u2[k][i];
        }
        t += fabs(ti);
    }
    return t;
}

/* F2PY_WRAPPER_START
    function misori_tetragonal( u1, u2)
!DOC misori_tetragonal computes the trace of the smallest misorientation
!DOC  u1 and u2 are both orientation matrices "U"
!DOC      compute u1. u2.T  to get the rotation from one to the other
!DOC      finds the flips a/b and c->-c that will maximise the trace:
!DOC        abs( trace(dot(u1,u2.T) ))
!DOC  Looks like point group 4/mmm. What about 4/m ?
!DOC  Beware: work in progress
        intent(c) misori_tetragonal
        intent(c)
        double precision, intent(in) :: u1(3,3), u2(3,3)
        ! Returns
        double precision :: misori_tetragonal
        threadsafe
    end function misori_tetragonal
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "misori_tetragonal(u1: buffer, u2: buffer) -> float",
 *     "doc": "misori_tetragonal computes the smallest misorientation for tetragonal symmetry.",
 *     "params": {
 *         "u1": "Orientation matrix U (9-element flattened double).",
 *         "u2": "Orientation matrix U (9-element flattened double).",
 *     },
 *     "checks": [
 *         "u1.format == 'd'",
 *         "u1.n == 9",
 *         "u2.format == 'd'",
 *         "u2.n == 9",
 *     ],
 *     "c_overloads": [{
 *         "sig": "double misori_tetragonal(double u1[3][3], double u2[3][3]) -> double",
 *         "map": {"u1": "u1.ptr", "u2": "u2.ptr"},
 *     }],
 * }
C2PY_END */
double misori_tetragonal(vec u1[3], vec u2[3]) {
    /* Compute the trace of the smallest misorientation
     * for orthorhombic symmetry
     *  u1 and u2 are both orientation matrices "U"
     *
     * compute u1. u2.T  to get the rotation from one to the other
     * find the flips for c and select ab versus ba
     */
    int i, j, k;
    double m1, m2, m3;
    vec r[3];
    /* c-axis */
    m3 = 0.;
    for (k = 0; k < 3; k++) {
        m3 += u1[k][2] * u2[k][2];
    }
    m3 = fabs(m3);
    /* ab */
    for (i = 0; i < 2; i++) {
        for (j = 0; j < 2; j++) {
            r[i][j] = 0.;
            for (k = 0; k < 3; k++) {
                r[i][j] += u1[k][i] * u2[k][j];
            }
        }
    }
    m1 = fabs(r[0][0]) + fabs(r[1][1]);
    m2 = fabs(r[1][0]) + fabs(r[0][1]);
    if (m2 > m3) {
        return m1 + m3;
    } else {
        return m2 + m3;
    }
}

/* F2PY_WRAPPER_START

    function misori_monoclinic( u1, u2)
!DOC misori_monoclinic assumes a unique b axis and only checks
!DOC the flip of b -> -b
!DOC Not sure about the point group here. Is is 2/m  ??
!DOC  Beware: work in progress
        intent(c) misori_monoclinic
        intent(c)
        double precision, intent(in) :: u1(3,3), u2(3,3)
        ! Returns
        double precision :: misori_monoclinic
        threadsafe
    end function misori_monoclinic
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "misori_monoclinic(u1: buffer, u2: buffer) -> float",
 *     "doc": "misori_monoclinic assumes a unique b axis and only checks the flip of b -> -b.",
 *     "params": {
 *         "u1": "Orientation matrix U (9-element flattened double).",
 *         "u2": "Orientation matrix U (9-element flattened double).",
 *     },
 *     "checks": [
 *         "u1.format == 'd'",
 *         "u1.n == 9",
 *         "u2.format == 'd'",
 *         "u2.n == 9",
 *     ],
 *     "c_overloads": [{
 *         "sig": "double misori_monoclinic(double u1[3][3], double u2[3][3]) -> double",
 *         "map": {"u1": "u1.ptr", "u2": "u2.ptr"},
 *     }],
 * }
C2PY_END */
double misori_monoclinic(vec u1[3], vec u2[3]) {
    /* Compute the trace of the smallest misorientation
     * for orthorhombic symmetry
     *  u1 and u2 are both orientation matrices "U"
     *
     * compute u1. u2.T  to get the rotation from one to the other
     * find the flips - can only flip b -> -b
     */
    int i, k;
    double ti, t;
    t = 0;
    for (i = 0; i < 3; i++) {
        ti = 0.;
        for (k = 0; k < 3; k++) {
            ti += u1[k][i] * u2[k][i];
        }
        if (i == 1) { /* can only flip b to -b */
            t += fabs(ti);
        } else {
            t += ti;
        }
    }
    return t;
}

/* F2PY_WRAPPER_START
    function count_shared( pi, ni, pj, nj )
!DOC count_shared takes two sorted arrays in pi and pj and counts
!DOC how many collisions there are. Useful to compare two lists of
!DOC peak to grain assignments, or pixel to peak assignments, etc
        intent(c) count_shared
        intent(c)
        integer, intent(in) :: pi(ni)
        integer, intent( hidden ), depend(pi) :: ni
        integer, intent(in) :: pj(nj)
        integer, intent( hidden ), depend(pj) :: nj
        ! return value is int too
        integer :: count_shared
        threadsafe
    end function count_shared
F2PY_WRAPPER_END */

/* C2PY_BEGIN
 * {
 *     "py_sig": "count_shared(pi: buffer, pj: buffer) -> int",
 *     "doc": "count_shared takes two sorted arrays and counts collisions.",
 *     "params": {
 *         "pi": "First sorted array of integer labels.",
 *         "pj": "Second sorted array of integer labels.",
 *     },
 *     "checks": [
 *         "( pi.format == 'i' or pi.format == 'l' )",
 *         "( pj.format == 'i' or pj.format == 'l' )",
 *     ],
 *     "c_overloads": [{
 *         "sig": "int count_shared(int *pi, intptr_t ni, int *pj, intptr_t nj) -> int",
 *         "map": {"pi": "pi.ptr", "ni": "pi.n", "pj": "pj.ptr", "nj": "pj.n"},
 *     }],
 * }
C2PY_END */
int count_shared(int pi[], intptr_t ni, int pj[], intptr_t nj) {
    /* Given two sorted arrays compute how many collisions
     * For comparing list of grain - peak indices for overlap
     */
    intptr_t i, j; int c;
    i = 0;
    j = 0;
    c = 0;
    while ((i < ni) && (j < nj)) {
        if (pi[i] > pj[j]) {
            j++;
        } else if (pi[i] < pj[j]) {
            i++;
        } else {
            i++;
            j++;
            c++;
        }
    }
    return c;
}
