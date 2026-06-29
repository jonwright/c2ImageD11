/* sa_stubs.c -- non-x86_64 fallback symbols for score_and_assign().
 * Provides the 8 ISA variant function names via scalar loops.
 * Uses nearbyint() instead of magic trick since callers may use -ffast-math.
 */

#include <stdint.h>
#include <math.h>
#ifdef _OPENMP
#include <omp.h>
#endif

/* ── Scalar kernels ── */

static int
sa_scalar_f64_aos(const double ubi[9], const double *gv, double tol,
                   double *drlv2, int *labels, int label, intptr_t ng)
{
    double tol2=tol*tol; int n=0; intptr_t k;
    for(k=0;k<ng;k++){
        double gx=gv[k*3],gy=gv[k*3+1],gz=gv[k*3+2];
        double hx=ubi[0]*gx+ubi[1]*gy+ubi[2]*gz; hx-=nearbyint(hx);
        double hy=ubi[3]*gx+ubi[4]*gy+ubi[5]*gz; hy-=nearbyint(hy);
        double hz=ubi[6]*gx+ubi[7]*gy+ubi[8]*gz; hz-=nearbyint(hz);
        double s=hx*hx+hy*hy+hz*hz;
        if(s<tol2&&s<drlv2[k]){labels[k]=label;drlv2[k]=s;n++;}
        else if(labels[k]==label)labels[k]=-1;
    }
    return n;
}

static int
sa_scalar_f32_aos(const double ubi[9], const float *gv, double tol,
                   float *drlv2, int *labels, int label, intptr_t ng)
{
    float fubi[9]; for(int i=0;i<9;i++)fubi[i]=(float)ubi[i];
    float tol2=(float)(tol*tol); int n=0; intptr_t k;
    for(k=0;k<ng;k++){
        float gx=gv[k*3],gy=gv[k*3+1],gz=gv[k*3+2];
        float hx=fubi[0]*gx+fubi[1]*gy+fubi[2]*gz; hx-=nearbyintf(hx);
        float hy=fubi[3]*gx+fubi[4]*gy+fubi[5]*gz; hy-=nearbyintf(hy);
        float hz=fubi[6]*gx+fubi[7]*gy+fubi[8]*gz; hz-=nearbyintf(hz);
        float s=hx*hx+hy*hy+hz*hz;
        if(s<tol2&&s<drlv2[k]){labels[k]=label;drlv2[k]=s;n++;}
        else if(labels[k]==label)labels[k]=-1;
    }
    return n;
}

static int
sa_scalar_f64_soa(const double ubi[9], const double *gvx, const double *gvy,
                   const double *gvz, double tol, double *drlv2, int *labels,
                   int label, intptr_t ng)
{
    double tol2=tol*tol; int n=0; intptr_t k;
    for(k=0;k<ng;k++){
        double hx=ubi[0]*gvx[k]+ubi[1]*gvy[k]+ubi[2]*gvz[k]; hx-=nearbyint(hx);
        double hy=ubi[3]*gvx[k]+ubi[4]*gvy[k]+ubi[5]*gvz[k]; hy-=nearbyint(hy);
        double hz=ubi[6]*gvx[k]+ubi[7]*gvy[k]+ubi[8]*gvz[k]; hz-=nearbyint(hz);
        double s=hx*hx+hy*hy+hz*hz;
        if(s<tol2&&s<drlv2[k]){labels[k]=label;drlv2[k]=s;n++;}
        else if(labels[k]==label)labels[k]=-1;
    }
    return n;
}

static int
sa_scalar_f32_soa(const double ubi[9], const float *gvx, const float *gvy,
                   const float *gvz, double tol, float *drlv2, int *labels,
                   int label, intptr_t ng)
{
    float fubi[9]; for(int i=0;i<9;i++)fubi[i]=(float)ubi[i];
    float tol2=(float)(tol*tol); int n=0; intptr_t k;
    for(k=0;k<ng;k++){
        float hx=fubi[0]*gvx[k]+fubi[1]*gvy[k]+fubi[2]*gvz[k]; hx-=nearbyintf(hx);
        float hy=fubi[3]*gvx[k]+fubi[4]*gvy[k]+fubi[5]*gvz[k]; hy-=nearbyintf(hy);
        float hz=fubi[6]*gvx[k]+fubi[7]*gvy[k]+fubi[8]*gvz[k]; hz-=nearbyintf(hz);
        float s=hx*hx+hy*hy+hz*hz;
        if(s<tol2&&s<drlv2[k]){labels[k]=label;drlv2[k]=s;n++;}
        else if(labels[k]==label)labels[k]=-1;
    }
    return n;
}

/* ── AoS dispatch stubs ── */

int score_and_assign_f64_avx2(double ubi[3][3], const double gv[], double tol,
                               double *drlv2, int *labels, int label, intptr_t ng)
{ return sa_scalar_f64_aos((const double*)ubi,gv,tol,drlv2,labels,label,ng); }

int score_and_assign_f32_avx2(double ubi[3][3], const float gv[], double tol,
                               float *drlv2, int *labels, int label, intptr_t ng)
{ return sa_scalar_f32_aos((const double*)ubi,gv,tol,drlv2,labels,label,ng); }

int score_and_assign_f64_avx512(double ubi[3][3], const double gv[], double tol,
                                 double *drlv2, int *labels, int label, intptr_t ng)
{ return sa_scalar_f64_aos((const double*)ubi,gv,tol,drlv2,labels,label,ng); }

int score_and_assign_f32_avx512(double ubi[3][3], const float gv[], double tol,
                                 float *drlv2, int *labels, int label, intptr_t ng)
{ return sa_scalar_f32_aos((const double*)ubi,gv,tol,drlv2,labels,label,ng); }

/* ── SoA dispatch stubs ── */

int score_and_assign_f64_sov_avx2(double ubi[3][3], const double gv[], double tol,
                                   double *drlv2, int *labels, int label, intptr_t ng)
{ const double *x=gv,*y=gv+ng,*z=gv+2*ng;
  return sa_scalar_f64_soa((const double*)ubi,x,y,z,tol,drlv2,labels,label,ng); }

int score_and_assign_f32_sov_avx2(double ubi[3][3], const float gv[], double tol,
                                   float *drlv2, int *labels, int label, intptr_t ng)
{ const float *x=gv,*y=gv+ng,*z=gv+2*ng;
  return sa_scalar_f32_soa((const double*)ubi,x,y,z,tol,drlv2,labels,label,ng); }

int score_and_assign_f64_sov_avx512(double ubi[3][3], const double gv[], double tol,
                                     double *drlv2, int *labels, int label, intptr_t ng)
{ const double *x=gv,*y=gv+ng,*z=gv+2*ng;
  return sa_scalar_f64_soa((const double*)ubi,x,y,z,tol,drlv2,labels,label,ng); }

int score_and_assign_f32_sov_avx512(double ubi[3][3], const float gv[], double tol,
                                     float *drlv2, int *labels, int label, intptr_t ng)
{ const float *x=gv,*y=gv+ng,*z=gv+2*ng;
  return sa_scalar_f32_soa((const double*)ubi,x,y,z,tol,drlv2,labels,label,ng); }
