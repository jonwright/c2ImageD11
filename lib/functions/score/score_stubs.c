/* score_stubs.c -- non-x86_64 fallback symbols.
 * Provides the 8 ISA variant function names via scalar loops.
 * Only compiled on non-x86_64 (see meson.build).
 */

#include <stdint.h>
#include <math.h>

static int score_scalar_f64(const double ubi[9], const double *gv, double tol, intptr_t ng)
{
    double t2 = tol * tol;
    int n = 0; intptr_t k;
    for (k = 0; k < ng; k++) {
        double h0 = ubi[0]*gv[k*3] + ubi[1]*gv[k*3+1] + ubi[2]*gv[k*3+2];
        h0 -= nearbyint(h0);
        double h1 = ubi[3]*gv[k*3] + ubi[4]*gv[k*3+1] + ubi[5]*gv[k*3+2];
        h1 -= nearbyint(h1);
        double h2 = ubi[6]*gv[k*3] + ubi[7]*gv[k*3+1] + ubi[8]*gv[k*3+2];
        h2 -= nearbyint(h2);
        if (h0*h0 + h1*h1 + h2*h2 < t2) n++;
    }
    return n;
}

static int score_scalar_f32(const double ubi[9], const float *gv, double tol, intptr_t ng)
{
    double t2 = tol * tol;
    int n = 0; intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = gv[k*3], gy = gv[k*3+1], gz = gv[k*3+2];
        double h0 = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz;
        h0 -= nearbyint(h0);
        double h1 = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz;
        h1 -= nearbyint(h1);
        double h2 = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz;
        h2 -= nearbyint(h2);
        if (h0*h0 + h1*h1 + h2*h2 < t2) n++;
    }
    return n;
}

static int score_scalar_f64_soa(const double ubi[9],
    const double *gvx, const double *gvy, const double *gvz, double tol, intptr_t ng)
{
    double t2 = tol * tol;
    int n = 0; intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = gvx[k], gy = gvy[k], gz = gvz[k];
        double h0 = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz; h0 -= nearbyint(h0);
        double h1 = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz; h1 -= nearbyint(h1);
        double h2 = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz; h2 -= nearbyint(h2);
        if (h0*h0 + h1*h1 + h2*h2 < t2) n++;
    }
    return n;
}

static int score_scalar_f32_soa(const double ubi[9],
    const float *gvx, const float *gvy, const float *gvz, double tol, intptr_t ng)
{
    double t2 = tol * tol;
    int n = 0; intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = gvx[k], gy = gvy[k], gz = gvz[k];
        double h0 = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz; h0 -= nearbyint(h0);
        double h1 = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz; h1 -= nearbyint(h1);
        double h2 = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz; h2 -= nearbyint(h2);
        if (h0*h0 + h1*h1 + h2*h2 < t2) n++;
    }
    return n;
}

/* ── AoS dispatch stubs ── */
int score_f64_avx2(const double ubi[3][3], const double gv[], double tol, intptr_t ng)
{ return score_scalar_f64((const double*)ubi, gv, tol, ng); }
int score_f32_avx2(const double ubi[3][3], const float gv[], double tol, intptr_t ng)
{ return score_scalar_f32((const double*)ubi, gv, tol, ng); }
int score_f64_avx512(const double ubi[3][3], const double gv[], double tol, intptr_t ng)
{ return score_scalar_f64((const double*)ubi, gv, tol, ng); }
int score_f32_avx512(const double ubi[3][3], const float gv[], double tol, intptr_t ng)
{ return score_scalar_f32((const double*)ubi, gv, tol, ng); }

/* ── SoA dispatch stubs ── */
int score_f64_soa_avx2(const double ubi[3][3], const double gv[], double tol, intptr_t ng)
{ const double *x=gv,*y=gv+ng,*z=gv+2*ng; return score_scalar_f64_soa((const double*)ubi,x,y,z,tol,ng); }
int score_f32_soa_avx2(const double ubi[3][3], const float gv[], double tol, intptr_t ng)
{ const float *x=gv,*y=gv+ng,*z=gv+2*ng; return score_scalar_f32_soa((const double*)ubi,x,y,z,tol,ng); }
int score_f64_soa_avx512(const double ubi[3][3], const double gv[], double tol, intptr_t ng)
{ const double *x=gv,*y=gv+ng,*z=gv+2*ng; return score_scalar_f64_soa((const double*)ubi,x,y,z,tol,ng); }
int score_f32_soa_avx512(const double ubi[3][3], const float gv[], double tol, intptr_t ng)
{ const float *x=gv,*y=gv+ng,*z=gv+2*ng; return score_scalar_f32_soa((const double*)ubi,x,y,z,tol,ng); }
