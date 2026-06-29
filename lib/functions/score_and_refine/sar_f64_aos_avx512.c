/* sar_f64_aos_avx512.c -- f64 AoS AVX-512 intrinsics variant
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[1] == 3 and gv.slow_axis == 0 and c2py_amd64_avx512f",
 *         "sig": "void score_and_refine_f64_avx512(double ubi[3][3], const double gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
 * C2PY_END
 */

#include <immintrin.h>
#include "sar_popcnt.h"
#include <stdint.h>
#include "sar_omp.h"
#include <math.h>

extern int inverse3x3(double A[3][3]);

static void
sar_f64_aos_avx512_kernel(const double ubi[9], const double *__restrict gv,
    double tol, intptr_t ng, double *__restrict H, double *__restrict R,
    int *__restrict n_out, double *__restrict sumdrlv2_out)
{
    __m512d u00 = _mm512_set1_pd(ubi[0]), u01 = _mm512_set1_pd(ubi[1]), u02 = _mm512_set1_pd(ubi[2]);
    __m512d u10 = _mm512_set1_pd(ubi[3]), u11 = _mm512_set1_pd(ubi[4]), u12 = _mm512_set1_pd(ubi[5]);
    __m512d u20 = _mm512_set1_pd(ubi[6]), u21 = _mm512_set1_pd(ubi[7]), u22 = _mm512_set1_pd(ubi[8]);
    __m512d tvec = _mm512_set1_pd(tol * tol);
    __m512d H00=_mm512_setzero_pd(),H01=_mm512_setzero_pd(),H02=_mm512_setzero_pd(),
            H10=_mm512_setzero_pd(),H11=_mm512_setzero_pd(),H12=_mm512_setzero_pd(),
            H20=_mm512_setzero_pd(),H21=_mm512_setzero_pd(),H22=_mm512_setzero_pd();
    __m512d R00=_mm512_setzero_pd(),R01=_mm512_setzero_pd(),R02=_mm512_setzero_pd(),
            R10=_mm512_setzero_pd(),R11=_mm512_setzero_pd(),R12=_mm512_setzero_pd(),
            R20=_mm512_setzero_pd(),R21=_mm512_setzero_pd(),R22=_mm512_setzero_pd();
    __m512d s_vec = _mm512_setzero_pd(); int n_scalar = 0; intptr_t k;
    for (k = 0; k + 8 <= ng; k += 8) {
        __m512d gvx = _mm512_set_pd(gv[k*3+21],gv[k*3+18],gv[k*3+15],gv[k*3+12],
                                     gv[k*3+9],gv[k*3+6],gv[k*3+3],gv[k*3+0]);
        __m512d gvy = _mm512_set_pd(gv[k*3+22],gv[k*3+19],gv[k*3+16],gv[k*3+13],
                                     gv[k*3+10],gv[k*3+7],gv[k*3+4],gv[k*3+1]);
        __m512d gvz = _mm512_set_pd(gv[k*3+23],gv[k*3+20],gv[k*3+17],gv[k*3+14],
                                     gv[k*3+11],gv[k*3+8],gv[k*3+5],gv[k*3+2]);

        __m512d hx = _mm512_fmadd_pd(u00, gvx, _mm512_fmadd_pd(u01, gvy, _mm512_mul_pd(u02, gvz)));
        __m512d hy = _mm512_fmadd_pd(u10, gvx, _mm512_fmadd_pd(u11, gvy, _mm512_mul_pd(u12, gvz)));
        __m512d hz = _mm512_fmadd_pd(u20, gvx, _mm512_fmadd_pd(u21, gvy, _mm512_mul_pd(u22, gvz)));

        __m512d ihx = _mm512_roundscale_pd(hx, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m512d ihy = _mm512_roundscale_pd(hy, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m512d ihz = _mm512_roundscale_pd(hz, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);

        __m512d tx = _mm512_sub_pd(hx, ihx), ty = _mm512_sub_pd(hy, ihy), tz = _mm512_sub_pd(hz, ihz);
        __m512d sumsq = _mm512_fmadd_pd(tx, tx, _mm512_fmadd_pd(ty, ty, _mm512_mul_pd(tz, tz)));
        __mmask8 mask = _mm512_cmp_pd_mask(sumsq, tvec, _CMP_LT_OS);
        if (mask == 0) continue;

        n_scalar += popcnt32((unsigned int)mask);
        s_vec = _mm512_mask_add_pd(s_vec, mask, s_vec, sumsq);
#define MA(a, v) a = _mm512_mask_add_pd(a, mask, a, v)
        MA(H00,_mm512_mul_pd(ihx,ihx));MA(H01,_mm512_mul_pd(ihx,ihy));MA(H02,_mm512_mul_pd(ihx,ihz));
        MA(H10,_mm512_mul_pd(ihy,ihx));MA(H11,_mm512_mul_pd(ihy,ihy));MA(H12,_mm512_mul_pd(ihy,ihz));
        MA(H20,_mm512_mul_pd(ihz,ihx));MA(H21,_mm512_mul_pd(ihz,ihy));MA(H22,_mm512_mul_pd(ihz,ihz));
        MA(R00,_mm512_mul_pd(ihx,gvx));MA(R01,_mm512_mul_pd(ihy,gvx));MA(R02,_mm512_mul_pd(ihz,gvx));
        MA(R10,_mm512_mul_pd(ihx,gvy));MA(R11,_mm512_mul_pd(ihy,gvy));MA(R12,_mm512_mul_pd(ihz,gvy));
        MA(R20,_mm512_mul_pd(ihx,gvz));MA(R21,_mm512_mul_pd(ihy,gvz));MA(R22,_mm512_mul_pd(ihz,gvz));
#undef MA
    }
    H[0]=_mm512_reduce_add_pd(H00);H[1]=_mm512_reduce_add_pd(H01);H[2]=_mm512_reduce_add_pd(H02);
    H[3]=_mm512_reduce_add_pd(H10);H[4]=_mm512_reduce_add_pd(H11);H[5]=_mm512_reduce_add_pd(H12);
    H[6]=_mm512_reduce_add_pd(H20);H[7]=_mm512_reduce_add_pd(H21);H[8]=_mm512_reduce_add_pd(H22);
    R[0]=_mm512_reduce_add_pd(R00);R[1]=_mm512_reduce_add_pd(R01);R[2]=_mm512_reduce_add_pd(R02);
    R[3]=_mm512_reduce_add_pd(R10);R[4]=_mm512_reduce_add_pd(R11);R[5]=_mm512_reduce_add_pd(R12);
    R[6]=_mm512_reduce_add_pd(R20);R[7]=_mm512_reduce_add_pd(R21);R[8]=_mm512_reduce_add_pd(R22);
    *n_out = n_scalar; *sumdrlv2_out = _mm512_reduce_add_pd(s_vec);
    double tol2=tol*tol;
    for(;k<ng;k++){double gx=gv[k*3],gy=gv[k*3+1],gz=gv[k*3+2];
        double hx_=ubi[0]*gx+ubi[1]*gy+ubi[2]*gz,hy_=ubi[3]*gx+ubi[4]*gy+ubi[5]*gz,hz_=ubi[6]*gx+ubi[7]*gy+ubi[8]*gz;
        double ix=nearbyint(hx_),iy=nearbyint(hy_),iz=nearbyint(hz_);
        double tx_=hx_-ix,ty_=hy_-iy,tz_=hz_-iz,s=tx_*tx_+ty_*ty_+tz_*tz_;
        if(s<tol2){(*n_out)++;*sumdrlv2_out+=s;
            H[0]+=ix*ix;H[1]+=ix*iy;H[2]+=ix*iz;H[3]+=iy*ix;H[4]+=iy*iy;H[5]+=iy*iz;H[6]+=iz*ix;H[7]+=iz*iy;H[8]+=iz*iz;
            R[0]+=ix*gx;R[1]+=iy*gx;R[2]+=iz*gx;R[3]+=ix*gy;R[4]+=iy*gy;R[5]+=iz*gy;R[6]+=ix*gz;R[7]+=iy*gz;R[8]+=iz*gz;}}
}

void score_and_refine_f64_avx512(double ubi[3][3], const double gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    double H[3][3]={{0}},R[3][3]={{0}},UB[3][3]={{0}}; int n; double sd;
        SAR_OMP_DISPATCH_AOS(sar_f64_aos_avx512_kernel, (const double *)ubi, gv, sizeof(double), ng, tol, H, R, &n, &sd);
    if(n>0)sd/=n;
    if(inverse3x3(H)==0){int i,j,l;for(i=0;i<3;i++)for(j=0;j<3;j++)for(l=0;l<3;l++)UB[i][j]+=R[i][l]*H[l][j];}
    if(inverse3x3(UB)==0){int i,j;for(i=0;i<3;i++)for(j=0;j<3;j++)ubi[i][j]=UB[i][j];}
    *n_arg=n;*sumdrlv2_arg=sd;
}
