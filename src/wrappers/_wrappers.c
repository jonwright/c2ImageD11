/*
 * C wrappers for c2ImageD11 - 2D array to flat pointer adaptation.
 *
 * c2py23 now natively supports all fixed-width integer types
 * (int8_t, uint8_t, int16_t, uint16_t, int32_t, uint32_t,
 *  int64_t, uint64_t), so thin type-adapting wrappers are no longer needed.
 *
 * These wrappers remain for functions with multi-dimensional array
 * parameters (vec[3], double[][3], double[][6]) that the .c2py
 * grammar cannot express directly.
 */

#include "core/cImageD11.h"
#include "imageproc/blobs.h"
#include "geometry/cdiffraction.h"

typedef double vec[3];

/* ================================================================
 * Forward declarations of all original C functions
 * ================================================================ */

/* closest.c */
int verify_rounding(int n);
void closest_vec(double x[], intptr_t dim, intptr_t nv, int closest[]);
void closest(double x[], double v[], int *ribest, double *rbest, intptr_t nx, intptr_t nv);
void refine_assigned(vec ubi[3], vec gv[], int labels[], int label, int *npk, double *sumdrlv2, intptr_t ng);
void put_incr64(float data[], int64_t ind[], float vals[], int boundscheck, intptr_t m, intptr_t n);
void put_incr32(float data[], int32_t ind[], float vals[], int boundscheck, intptr_t m, intptr_t n);
void cluster1d(double ar[], intptr_t n, int order[], double tol, int *nclusters, int ids[], double avgs[]);
void score_gvec_z(vec ubi[3], vec ub[3], vec gv[], double g0[], double g1[], double g2[], double e[], int recompute, intptr_t n);
double misori_cubic(vec u1[3], vec u2[3]);
double misori_orthorhombic(vec u1[3], vec u2[3]);
double misori_tetragonal(vec u1[3], vec u2[3]);
double misori_monoclinic(vec u1[3], vec u2[3]);
int count_shared(int pi[], intptr_t ni, int pj[], intptr_t nj);

/* darkflat.c */
void uint16_to_float_darksub(float *img, const float *drk, const uint16_t *data, intptr_t npx);
void uint16_to_float_darkflm(float *img, const float *drk, const float *flm, const uint16_t *data, intptr_t npx);
void frelon_lines(float *img, intptr_t ns, intptr_t nf, float cut);
void frelon_lines_sub(float *img, float *drk, intptr_t ns, intptr_t nf, float cut);
void array_mean_var_cut(float *img, intptr_t npx, float *mean, float *std, int n, float cut, int verbose);
void array_mean_var_msk(float *img, uint8_t *msk, intptr_t npx, float *mean, float *std, int n, float cut, int verbose);
void array_stats(float img[], intptr_t npx, float *minval, float *maxval, float *mean, float *var);
void array_histogram(float img[], intptr_t npx, float low, float high, int32_t hist[], intptr_t nhist);
void reorder_u16_a32(const uint16_t *data, const uint32_t *adr, uint16_t *out, intptr_t N);
void reorder_f32_a32(const float *data, const uint32_t *adr, float *out, intptr_t N);
void reorderlut_u16_a32(uint16_t *data, uint32_t *lut, uint16_t *out, intptr_t N);
void reorderlut_f32_a32(const float *data, uint32_t *lut, float *out, intptr_t N);
void reorder_u16_a32_a16(uint16_t *data, uint32_t *a0, int16_t *a1, uint16_t *out, intptr_t ns, intptr_t nf);
void bgcalc(const float *img, float *bg, uint8_t *msk, intptr_t ns, intptr_t nf, float gain, float sigmap, float sigmat);

/* cdiffraction.c */
void quickorient(double UBI[9], double BT[9]);

/* connectedpixels.c */
int connectedpixels(float *data, int32_t *labels, float threshold, int verbose, int eightconnected, intptr_t ns, intptr_t nf);
void blobproperties(float *data, int32_t *labels, int32_t npk, float omega, int verbose, intptr_t ns, intptr_t nf, double *res);
int bloboverlaps(int32_t *b1, int32_t n1, double *res1, int32_t *b2, int32_t n2, double *res2, int verbose, intptr_t ns, intptr_t nf);
void blob_moments(double results[], intptr_t np);
int clean_mask(const int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf);
int make_clean_mask(float *img, float cut, int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf);

/* localmaxlabel.c */
int localmaxlabel(const float *im, int32_t *lout, uint8_t *l, intptr_t dim0, intptr_t dim1);

/* sparse_image.c */
int mask_to_coo(int8_t msk[], intptr_t ns, intptr_t nf, uint16_t i[], uint16_t j[], intptr_t nnz, int nrow[]);
int sparse_is_sorted(uint16_t i[], uint16_t j[], intptr_t nnz);
int sparse_connectedpixels(float *v, uint16_t *i, uint16_t *j, intptr_t nnz, float threshold, int32_t *labels);
int sparse_connectedpixels_splat(float *v, uint16_t *i, uint16_t *j, intptr_t nnz, float threshold, int32_t *labels, int32_t *Z, intptr_t imax, intptr_t jmax);
void sparse_blob2Dproperties(float *data, uint16_t *i, uint16_t *j, intptr_t nnz, int32_t *labels, double *res, int32_t npk);
void sparse_smooth(float *v, uint16_t *i, uint16_t *j, intptr_t nnz, float *s);
int sparse_localmaxlabel(float *v, uint16_t *i, uint16_t *j, intptr_t nnz, float *MV, int32_t *iMV, int32_t *labels);
int sparse_overlaps(uint16_t *i1, uint16_t *j1, int *k1, intptr_t nnz1, uint16_t *i2, uint16_t *j2, int *k2, intptr_t nnz2);
int compress_duplicates(int *i, int *j, int *oi, int *oj, int *tmp, intptr_t n, intptr_t nt);
int coverlaps(uint16_t *row1, uint16_t *col1, int *labels1, intptr_t nnz1, uint16_t *row2, uint16_t *col2, int *labels2, intptr_t nnz2, int *mat, int npk1, int npk2, int *results);
int tosparse_u16(uint16_t *img, uint8_t *msk, uint16_t *row, uint16_t *col, uint16_t *val, int cut, intptr_t ns, intptr_t nf);
int tosparse_u32(uint32_t *img, uint8_t *msk, uint16_t *row, uint16_t *col, uint32_t *val, float cut, intptr_t ns, intptr_t nf);
int tosparse_f32(float *img, uint8_t *msk, uint16_t *row, uint16_t *col, float *val, float cut, intptr_t ns, intptr_t nf);

/* splat.c */
void splat(uint8_t rgba[], intptr_t w, intptr_t h, double gve[][3], intptr_t ng, double u[9], intptr_t npx);

/* cimaged11utils.c */
void cimaged11_omp_set_num_threads(int n);
int cimaged11_omp_get_max_threads(void);
double my_get_time(void);


/* ================================================================
 * 2D-array-to-flat-pointer wrappers
 *
 * These adapt the vec[3] / double[][N] multi-dimensional array
 * parameters used by ImageD11 functions.  c2py23 handles flat
 * buffers via .ptr, so we cast flat double* back to vec* or
 * double(*)[N] here to match the original function signatures.
 * ================================================================ */

void
refine_assigned_wrapper(double *ubi_ptr, const double *gv_ptr,
                         int *labels, int label_id,
                         int *npk, double *drlv2, intptr_t ng)
{
    refine_assigned((vec *)ubi_ptr, (vec *)gv_ptr, labels,
                    label_id, npk, drlv2, ng);
}

double
misori_cubic_wrapper(const double *u1_ptr, const double *u2_ptr)
{
    return misori_cubic((vec *)u1_ptr, (vec *)u2_ptr);
}

double
misori_orthorhombic_wrapper(const double *u1_ptr, const double *u2_ptr)
{
    return misori_orthorhombic((vec *)u1_ptr, (vec *)u2_ptr);
}

double
misori_tetragonal_wrapper(const double *u1_ptr, const double *u2_ptr)
{
    return misori_tetragonal((vec *)u1_ptr, (vec *)u2_ptr);
}

double
misori_monoclinic_wrapper(const double *u1_ptr, const double *u2_ptr)
{
    return misori_monoclinic((vec *)u1_ptr, (vec *)u2_ptr);
}

void
splat_wrapper(uint8_t *rgba_buf, intptr_t w, intptr_t h, const double *gve_ptr,
              intptr_t ng, const double *u_ptr, intptr_t npx)
{
    splat(rgba_buf, w, h, (double(*)[3])gve_ptr, ng, (double*)u_ptr, npx);
}

/* ================================================================
 * SIMD kernel bridge wrappers
 *
 * The score_and_refine kernels were mechanically extracted from
 * ImageD11 source, changing their signature from int fn(..., int ng)
 * to void fn(..., int *n_arg, double *sumdrlv2_arg, int ng).
 * These wrappers bridge the .c2py variant sig (int return, flat ptrs)
 * to the new kernel signatures (void return, vec types, extra n_arg).
 * ================================================================ */

extern void score_and_refine_avx512_impl(vec ubi[3], vec gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng);
extern void score_and_refine_avx2_impl(vec ubi[3], vec gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng);
extern void score_and_refine_sse42_impl(vec ubi[3], vec gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng);

int score_and_refine_avx512(const double *ubi, const double *gv, double tol,
    double *sumdrlv2_arg, intptr_t ng)
{
    int n;
    score_and_refine_avx512_impl((vec*)ubi, (vec*)gv, tol, &n, sumdrlv2_arg, ng);
    return n;
}

int score_and_refine_avx2(const double *ubi, const double *gv, double tol,
    double *sumdrlv2_arg, intptr_t ng)
{
    int n;
    score_and_refine_avx2_impl((vec*)ubi, (vec*)gv, tol, &n, sumdrlv2_arg, ng);
    return n;
}

int score_and_refine_sse42(const double *ubi, const double *gv, double tol,
    double *sumdrlv2_arg, intptr_t ng)
{
    int n;
    score_and_refine_sse42_impl((vec*)ubi, (vec*)gv, tol, &n, sumdrlv2_arg, ng);
    return n;
}
