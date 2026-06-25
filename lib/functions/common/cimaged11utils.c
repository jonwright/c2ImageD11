/* Various utility things that do not belong elsewhere */

#include "cImageD11.h"
#include "cimaged11utils.h"
#include <stdint.h>
#ifdef _MSC_VER
#include <windows.h>
#else
#include <sys/time.h>
#endif

/* C2PY_BEGIN
 * {
 *     "py_sig": "cimaged11_omp_set_num_threads(n: int) -> void",
 *     "doc": "Set the number of OpenMP threads used by all subsequent C calls.",
 *     "params": {
 *         "n": "Number of OpenMP threads. Pass 1 for single-threaded execution.",
 *     },
 *     "c_overloads": [{
 *         "sig": "void cimaged11_omp_set_num_threads(int n)",
 *         "map": {"n": "n"},
 *     }],
 * }
C2PY_END */

#ifdef _OPENMP
#include <omp.h>
void cimaged11_omp_set_num_threads(int n) { omp_set_num_threads(n); }
int cimaged11_omp_get_max_threads(void) { return omp_get_max_threads(); }
#else
void cimaged11_omp_set_num_threads(int n) {}
int cimaged11_omp_get_max_threads(void) { return 0; }
#endif

/* C2PY_BEGIN
 * {
 *     "py_sig": "cimaged11_omp_get_max_threads() -> int",
 *     "doc": "Return the maximum number of OpenMP threads available.",
 *     "c_overloads": [{
 *         "sig": "int cimaged11_omp_get_max_threads()",
 *         "map": {},
 *     }],
 * }
C2PY_END */

double my_get_time(void) {
#if defined(_MSC_VER) || defined(__MINGW32__)
    LARGE_INTEGER t, f;
    QueryPerformanceCounter(&t);
    QueryPerformanceFrequency(&f);
    return (double)t.QuadPart / (double)f.QuadPart;
#else
    struct timeval t;
    gettimeofday(&t, NULL);
    return t.tv_sec + t.tv_usec * 1e-6;
#endif
}

double conv_double_to_int_safe(double x) { return floor(x + 0.5); }

int inverse3x3(double H[3][3]) {
    double det, inverse[3][3];
    int i, j;
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

void boundscheck(int jpk, int n2, int ipk, int n1) {
    if ((jpk < 0) || jpk >= n2) {
        printf("Bounds check error, jpk, n2\n");
        return;
    }
    if ((ipk < 0) || ipk >= n1) {
        printf("Bounds check error, jpk, n1\n");
        return;
    }
}

#define pick(A, B, I, J)                                                       \
    if ((A) > (B)) {                                                           \
        (B) = (A);                                                             \
        (I) = (J);                                                             \
    }

int neighbormax(const float *restrict im, int32_t *restrict lout,
                uint8_t *restrict l, intptr_t dim0, intptr_t dim1) {
    intptr_t i, j; int p, k0, k1, k2, npks;
    float mx0, mx1, mx2;
    npks = 0;

    for (i = 0; i < dim1; i++) {
        lout[i] = 0;
        l[i] = 0;
        lout[dim1 * (dim0 - 1) + i] = 0;
        l[dim1 * (dim0 - 1) + i] = 0;
    }

#pragma omp parallel for private(j, p, k0, k1, k2, mx0, mx1, mx2) reduction(+ : npks)
    for (i = dim1; i < (dim0 - 1) * dim1; i = i + dim1) {
        lout[i] = 0;
        l[i] = 0;
        p = i + 1;
        mx0 = im[p - 1 - dim1];
        k0 = 1;
        pick(im[p - 1], mx0, k0, 2);
        pick(im[p - 1 + dim1], mx0, k0, 3);
        k1 = 4;
        mx1 = im[p - dim1];
        pick(im[p], mx1, k1, 5);
        pick(im[p + dim1], mx1, k1, 6);
        for (j = 1; j < dim1 - 1; j++) {
            p = i + j;
            mx2 = im[p + 1 - dim1];
            k2 = 7;
            pick(im[p + 1], mx2, k2, 8);
            pick(im[p + 1 + dim1], mx2, k2, 9);
            pick(mx1, mx0, k0, k1);
            pick(mx2, mx0, k0, k2);
            l[p] = k0;
            if (k0 == 5) {
                lout[i]++;
            }
            mx0 = mx1;
            k0 = k1 - 3;
            mx1 = mx2;
            k1 = k2 - 3;
        }
        lout[i + dim1 - 1] = 0;
        l[i + dim1 - 1] = 0;
        npks += lout[i];
    }
    return npks;
}

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
        hfast = (int)conv_double_to_int_fast(v);
        hslow = (int)conv_double_to_int_safe(v);
        if (hfast != hslow) { bad++; }
        v = -v;
        hfast = (int)conv_double_to_int_fast(v);
        hslow = (int)conv_double_to_int_safe(v);
        if (hfast != hslow) { bad++; }
    }
    return bad;
}
