/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx512f",
 *         "sig": "int score_and_assign_f32_sov_avx512_asm(double ubi[3][3], const float gv[], double tol, float *drlv2, int *labels, int label, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "drlv2": "drlv2.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[1]"},
 *     }],
 * }
 * C2PY_END */

#include <stdint.h>
#if defined C2_ASM_AVAILABLE
#ifdef _OPENMP
#include <omp.h>
#endif

extern int sa_inner_f32_sov_avx512(const double ubi[9], const float *gvx, const float *gvy,
                         const float *gvz, double tol, float *drlv2, int *labels,
                         int label, intptr_t ng);

int score_and_assign_f32_sov_avx512_asm(double ubi[3][3], const float gv[], double tol,
                  float *drlv2, int *labels, int label, intptr_t ng)
{
    const float *gvx = gv;
    const float *gvy = gv + ng;
    const float *gvz = gv + ng * 2;
    int n = 0;
#ifdef _OPENMP
    int nthr = omp_get_max_threads();
    if (ng > 10000 && nthr > 1) {
        #pragma omp parallel reduction(+:n)
        {
            int tid = omp_get_thread_num();
            intptr_t chunk = (ng + nthr - 1) / nthr;
            intptr_t start = tid * chunk;
            intptr_t end = (start + chunk < ng) ? start + chunk : ng;
            if (start < ng)
                n = sa_inner_f32_sov_avx512((const double*)ubi, gvx + start, gvy + start, gvz + start,
                                  tol, drlv2 + start, labels + start, label, end - start);
        }
        return n;
    }
#endif
    return sa_inner_f32_sov_avx512((const double*)ubi, gvx, gvy, gvz, tol, drlv2, labels, label, ng);
}
#else
extern int score_and_assign_f32_sov_avx512(double ubi[3][3], const float gv[],
    double tol, float *drlv2, int *labels, int label, intptr_t ng);

int score_and_assign_f32_sov_avx512_asm(double ubi[3][3], const float gv[],
    double tol, float *drlv2, int *labels, int label, intptr_t ng)
{
    return score_and_assign_f32_sov_avx512(ubi, gv, tol, drlv2, labels, label, ng);
}
#endif
