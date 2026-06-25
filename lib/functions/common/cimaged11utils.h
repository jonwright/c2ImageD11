#ifndef CIMAGED11UTILS_H
#define CIMAGED11UTILS_H
#include <stdint.h>
void cimaged11_omp_set_num_threads(int n);
int  cimaged11_omp_get_max_threads(void);
int  verify_rounding(int n);
int  inverse3x3(double A[3][3]);
void boundscheck(int jpk, int n2, int ipk, int n1);
int  neighbormax(const float *restrict im, int32_t *restrict lout,
                  uint8_t *restrict l, intptr_t dim0, intptr_t dim1);
#endif
