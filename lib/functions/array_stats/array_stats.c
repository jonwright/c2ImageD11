#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "array_stats(img: buffer) -> void",
 *  "doc": "Compute min, max, mean, variance.",
 *  "checks": ["img.format == 'f'"],
 *  "c_overloads": [{"sig": "void array_stats(const float *img, intptr_t npx, float *minval, float *maxval, float *mean, float *var)",
 *      "map": {"img": "img.ptr", "npx": "img.n"},
 *      "outputs": {"minval": "float", "maxval": "float", "mean": "float", "var": "float"}}]}
C2PY_END */

void array_stats(const float img[], intptr_t npx, float *minval, float *maxval,
                 float *mean, float *var) {
    intptr_t i;
    /* Use double to reduce rounding and subtraction errors */
    double t, s1, s2, y0, ts1, ts2;
    float mini, maxi, tmin, tmax;
    mini = FLT_MAX;
    maxi = FLT_MIN;
    s1 = 0.;
    s2 = 0.;
    y0 = img[0];
    /* Merge results - openmp 2.0 for windows has no min/max     */
#pragma omp parallel private(i, t, ts1, ts2, tmin, tmax)
    {
        tmin = FLT_MAX;
        tmax = FLT_MIN;
        ts1 = 0.;
        ts2 = 0.;
#ifdef GOT_OMP_SIMD
#pragma omp for simd
#else
#pragma omp for
#endif
        for (i = 0; i < npx; i++) {
            t = img[i] - y0;
            ts1 = ts1 + t;
            ts2 = ts2 + t * t;
            if (img[i] < tmin)
                tmin = img[i];
            if (img[i] > tmax)
                tmax = img[i];
        } // for
#pragma omp critical
        {
            s1 += ts1;
            s2 += ts2;
            if (tmin < mini)
                mini = tmin;
            if (tmax > maxi)
                maxi = tmax;
        }
    } // parallel
    /* results */
    *mean = (float)(s1 / npx + y0);
    *var = (float)((s2 - (s1 * s1 / npx)) / npx);
    *minval = mini;
    *maxval = maxi;
}
