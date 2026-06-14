/*
 * Thin C wrappers for c2ImageD11.
 *
 * Adapts original ImageD11 C functions to c2py23-compatible signatures
 * using only {int, float, double, char} types.
 *
 * All type-punning casts are valid C (strict aliasing exception for char*).
 * The Python caller ensures the buffer has the correct PEP 3118 format.
 */

#include "src/cImageD11.h"
#include "src/blobs.h"
#include "src/cdiffraction.h"

typedef double vec[3];

/* ================================================================
 * Forward declarations of all original C functions
 * ================================================================ */

/* closest.c */
int verify_rounding(int n);
void closest_vec(double x[], int dim, int nv, int closest[]);
void closest(double x[], double v[], int *ribest, double *rbest, int nx, int nv);
int score(vec ubi[3], vec gv[], double tol, int ng);
void score_and_refine(vec ubi[3], vec gv[], double tol, int *n_arg, double *sumdrlv2_arg, int ng);
int score_and_assign(vec ubi[3], vec gv[], double tol, double drlv2[], int labels[], int label, int ng);
void refine_assigned(vec ubi[3], vec gv[], int labels[], int label, int *npk, double *sumdrlv2, int ng);
void put_incr64(float data[], int64_t ind[], float vals[], int boundscheck, int m, int n);
void put_incr32(float data[], int32_t ind[], float vals[], int boundscheck, int m, int n);
void cluster1d(double ar[], int n, int order[], double tol, int *nclusters, int ids[], double avgs[]);
void score_gvec_z(vec ubi[3], vec ub[3], vec gv[], double g0[], double g1[], double g2[], double e[], int recompute, int n);
double misori_cubic(vec u1[3], vec u2[3]);
double misori_orthorhombic(vec u1[3], vec u2[3]);
double misori_tetragonal(vec u1[3], vec u2[3]);
double misori_monoclinic(vec u1[3], vec u2[3]);
int count_shared(int pi[], int ni, int pj[], int nj);

/* darkflat.c */
void uint16_to_float_darksub(float *img, const float *drk, const uint16_t *data, int npx);
void uint16_to_float_darkflm(float *img, const float *drk, const float *flm, const uint16_t *data, int npx);
void frelon_lines(float *img, int ns, int nf, float cut);
void frelon_lines_sub(float *img, float *drk, int ns, int nf, float cut);
void array_mean_var_cut(float *img, int npx, float *mean, float *std, int n, float cut, int verbose);
void array_mean_var_msk(float *img, uint8_t *msk, int npx, float *mean, float *std, int n, float cut, int verbose);
void array_stats(float img[], int npx, float *minval, float *maxval, float *mean, float *var);
void array_histogram(float img[], int npx, float low, float high, int32_t hist[], int nhist);
void reorder_u16_a32(const uint16_t *data, const uint32_t *adr, uint16_t *out, int N);
void reorder_f32_a32(const float *data, const uint32_t *adr, float *out, int N);
void reorderlut_u16_a32(uint16_t *data, uint32_t *lut, uint16_t *out, int N);
void reorderlut_f32_a32(const float *data, uint32_t *lut, float *out, int N);
void reorder_u16_a32_a16(uint16_t *data, uint32_t *a0, int16_t *a1, uint16_t *out, int ns, int nf);
void bgcalc(const float *img, float *bg, uint8_t *msk, int ns, int nf, float gain, float sigmap, float sigmat);

/* cdiffraction.c */
void compute_geometry(double xlylzl[][3], double omega[], double omegasign, double wvln, double wedge, double chi, double t[3], double out[][6], int n);
void compute_gv(double xlylzl[][3], double omega[], double omegasign, double wvln, double wedge, double chi, double t[3], double gv[][3], int n);
void compute_xlylzl(double s[], double f[], double p[4], double r[9], double dist[3], double xlylzl[][3], int n);
void compute_xlylzl_xpos_variable(double s[], double f[], double p[4], double r[9], double dist[3], double xpos[], double xlylzl[][3], int n);
void quickorient(double UBI[9], double BT[9]);

/* connectedpixels.c */
int connectedpixels(float *data, int32_t *labels, float threshold, int verbose, int eightconnected, int ns, int nf);
void blobproperties(float *data, int32_t *labels, int32_t npk, float omega, int verbose, int ns, int nf, double *res);
int bloboverlaps(int32_t *b1, int32_t n1, double *res1, int32_t *b2, int32_t n2, double *res2, int verbose, int ns, int nf);
void blob_moments(double results[], int np);
int clean_mask(const int8_t *msk, int8_t *ret, int ns, int nf);
int make_clean_mask(float *img, float cut, int8_t *msk, int8_t *ret, int ns, int nf);

/* localmaxlabel.c */
int localmaxlabel(const float *im, int32_t *lout, uint8_t *l, int dim0, int dim1);

/* sparse_image.c */
int mask_to_coo(int8_t msk[], int ns, int nf, uint16_t i[], uint16_t j[], int nnz, int nrow[]);
int sparse_is_sorted(uint16_t i[], uint16_t j[], int nnz);
int sparse_connectedpixels(float *v, uint16_t *i, uint16_t *j, int nnz, float threshold, int32_t *labels);
int sparse_connectedpixels_splat(float *v, uint16_t *i, uint16_t *j, int nnz, float threshold, int32_t *labels, int32_t *Z, int imax, int jmax);
void sparse_blob2Dproperties(float *data, uint16_t *i, uint16_t *j, int nnz, int32_t *labels, double *res, int32_t npk);
void sparse_smooth(float *v, uint16_t *i, uint16_t *j, int nnz, float *s);
int sparse_localmaxlabel(float *v, uint16_t *i, uint16_t *j, int nnz, float *MV, int32_t *iMV, int32_t *labels);
int sparse_overlaps(uint16_t *i1, uint16_t *j1, int *k1, int nnz1, uint16_t *i2, uint16_t *j2, int *k2, int nnz2);
int compress_duplicates(int *i, int *j, int *oi, int *oj, int *tmp, int n, int nt);
int coverlaps(uint16_t *row1, uint16_t *col1, int *labels1, int nnz1, uint16_t *row2, uint16_t *col2, int *labels2, int nnz2, int *mat, int npk1, int npk2, int *results);
int tosparse_u16(uint16_t *img, uint8_t *msk, uint16_t *row, uint16_t *col, uint16_t *val, int cut, int ns, int nf);
int tosparse_u32(uint32_t *img, uint8_t *msk, uint16_t *row, uint16_t *col, uint32_t *val, float cut, int ns, int nf);
int tosparse_f32(float *img, uint8_t *msk, uint16_t *row, uint16_t *col, float *val, float cut, int ns, int nf);

/* splat.c */
void splat(uint8_t rgba[], int w, int h, double gve[][3], int ng, double u[9], int npx);

/* cimaged11utils.c */
void cimaged11_omp_set_num_threads(int n);
int cimaged11_omp_get_max_threads(void);
double my_get_time(void);


/* ================================================================
 * Thick wrapper functions (2D array -> flat pointer adaptation)
 * ================================================================ */

int
score_wrapper(double *ubi_ptr, const double *gv_ptr, double tol, int ng)
{
    return score((vec *)ubi_ptr, (vec *)gv_ptr, tol, ng);
}

int
score_and_refine_wrapper(double *ubi_ptr, const double *gv_ptr,
                          double tol, double *sumdrlv2_buf, int ng)
{
    int n;
    score_and_refine((vec *)ubi_ptr, (vec *)gv_ptr, tol, &n,
                     sumdrlv2_buf, ng);
    return n;
}

int
score_and_assign_wrapper(double *ubi_ptr, const double *gv_ptr,
                          double tol, double *drlv2, int *labels,
                          int label_id, int ng)
{
    return score_and_assign((vec *)ubi_ptr, (vec *)gv_ptr, tol,
                            drlv2, labels, label_id, ng);
}

void
refine_assigned_wrapper(double *ubi_ptr, const double *gv_ptr,
                         int *labels, int label_id,
                         int *npk, double *drlv2, int ng)
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

int
count_shared_wrapper(const int *pi, int ni, const int *pj, int nj)
{
    return count_shared((int *)pi, ni, (int *)pj, nj);
}

void
compute_geometry_wrapper(const double *xlylzl_ptr, const double *omega,
                          double omegasign, double wvln, double wedge,
                          double chi, const double *t_ptr, double *out_ptr, int n)
{
    compute_geometry((double(*)[3])xlylzl_ptr, (double*)omega,
                     omegasign, wvln, wedge, chi, (double*)t_ptr,
                     (double(*)[6])out_ptr, n);
}

void
compute_gv_wrapper(const double *xlylzl_ptr, const double *omega,
                    double omegasign, double wvln, double wedge,
                    double chi, const double *t_ptr, double *gv_ptr, int n)
{
    compute_gv((double(*)[3])xlylzl_ptr, (double*)omega,
               omegasign, wvln, wedge, chi, (double*)t_ptr,
               (double(*)[3])gv_ptr, n);
}

void
compute_xlylzl_wrapper(const double *s, const double *f,
                        const double *p, const double *r,
                        const double *dist, double *xlylzl_ptr, int n)
{
    compute_xlylzl((double*)s, (double*)f, (double*)p, (double*)r,
                   (double*)dist, (double(*)[3])xlylzl_ptr, n);
}

void
compute_xlylzl_xpos_variable_wrapper(const double *s, const double *f,
                                      const double *p, const double *r,
                                      const double *dist, const double *xpos,
                                      double *xlylzl_ptr, int n)
{
    compute_xlylzl_xpos_variable((double*)s, (double*)f, (double*)p, (double*)r,
                                  (double*)dist, (double*)xpos,
                                  (double(*)[3])xlylzl_ptr, n);
}

void
quickorient_wrapper(double *ubi_ptr, const double *bt_ptr)
{
    quickorient(ubi_ptr, (double*)bt_ptr);
}

void
blobproperties_wrapper(float *data, int *labels, int np,
                        double *results, float omega,
                        int verbose, int ns, int nf)
{
    blobproperties(data, (int32_t *)labels, np, omega,
                   verbose, ns, nf, results);
}

void
splat_wrapper(char *rgba_buf, int w, int h, const double *gve_ptr,
               int ng, const double *u_ptr, int npx)
{
    splat((uint8_t *)rgba_buf, w, h, (double(*)[3])gve_ptr, ng,
          (double*)u_ptr, npx);
}


/* ================================================================
 * Thin type-adapting wrappers (fixed-size int types -> char/int)
 * ================================================================ */

/* ---------- uint16_t -> char pointer ---------- */

void
uint16_to_float_darksub_wrapper(float *img, const float *drk,
                                 const char *data_buf, int npx)
{
    uint16_to_float_darksub(img, drk, (const uint16_t *)data_buf, npx);
}

void
uint16_to_float_darkflm_wrapper(float *img, const float *drk,
                                 const float *flm, const char *data_buf, int npx)
{
    uint16_to_float_darkflm(img, drk, flm, (const uint16_t *)data_buf, npx);
}

/* ---------- uint8_t -> char pointer ---------- */

void
array_mean_var_msk_wrapper(float *img, char *msk_buf, int npx,
                            float *mean, float *std, int n, float cut, int verbose)
{
    array_mean_var_msk(img, (uint8_t *)msk_buf, npx, mean, std, n, cut, verbose);
}

void
bgcalc_wrapper(const float *img, float *bg, char *msk_buf,
                int ns, int nf, float gain, float sigmap, float sigmat)
{
    bgcalc(img, bg, (uint8_t *)msk_buf, ns, nf, gain, sigmap, sigmat);
}

/* ---------- int32_t -> int pointer ---------- */

void
array_histogram_wrapper(float img[], int npx, float low, float high,
                         int *hist_buf, int nhist)
{
    array_histogram(img, npx, low, high, (int32_t *)hist_buf, nhist);
}

int
connectedpixels_wrapper(float *data, int *labels_p, float threshold,
                         int verbose, int eightconnected, int ns, int nf)
{
    return connectedpixels(data, (int32_t *)labels_p, threshold, verbose,
                           eightconnected, ns, nf);
}

int
localmaxlabel_wrapper(float *data, int *labels_p, char *wrk_buf,
                       int ns, int nf)
{
    return localmaxlabel(data, (int32_t *)labels_p, (uint8_t *)wrk_buf,
                         ns, nf);
}

/* ---------- int8_t -> char pointer ---------- */

int
clean_mask_wrapper(const char *msk_buf, char *ret_buf, int ns, int nf)
{
    return clean_mask((const int8_t *)msk_buf, (int8_t *)ret_buf, ns, nf);
}

int
make_clean_mask_wrapper(const float *img, float cut,
                         char *msk_buf, char *ret_buf, int ns, int nf)
{
    return make_clean_mask((float*)img, cut, (int8_t *)msk_buf,
                           (int8_t *)ret_buf, ns, nf);
}

/* ---------- uint32_t -> int pointer ---------- */

void
reorder_u16_a32_wrapper(const char *data_buf, const int *adr_buf,
                         char *out_buf, int N)
{
    reorder_u16_a32((const uint16_t *)data_buf, (const uint32_t *)adr_buf,
                    (uint16_t *)out_buf, N);
}

void
reorder_f32_a32_wrapper(const float *data, const int *adr_buf,
                         float *out, int N)
{
    reorder_f32_a32(data, (const uint32_t *)adr_buf, out, N);
}

void
reorderlut_u16_a32_wrapper(char *data_buf, int *lut_buf,
                            char *out_buf, int N)
{
    reorderlut_u16_a32((uint16_t *)data_buf, (uint32_t *)lut_buf,
                       (uint16_t *)out_buf, N);
}

void
reorderlut_f32_a32_wrapper(const float *data, int *lut_buf,
                            float *out, int N)
{
    reorderlut_f32_a32(data, (uint32_t *)lut_buf, out, N);
}

void
reorder_u16_a32_a16_wrapper(const char *data_buf, const int *a0_buf,
                             const char *a1_buf, char *out_buf,
                             int ns, int nf)
{
    reorder_u16_a32_a16((uint16_t *)data_buf, (uint32_t *)a0_buf,
                        (int16_t *)a1_buf, (uint16_t *)out_buf, ns, nf);
}

/* ---------- int64_t -> char pointer ---------- */

void
put_incr64_wrapper(float *data, const char *ind_buf, float *vals,
                    int boundscheck, int m, int n)
{
    put_incr64(data, (int64_t *)ind_buf, vals, boundscheck, m, n);
}

/* ---------- sparse_image uint16_t -> char pointer ---------- */

int
mask_to_coo_wrapper(const char *msk_buf, int ns, int nf,
                     char *i_buf, char *j_buf, int nnz, int *w_buf)
{
    return mask_to_coo((int8_t *)msk_buf, ns, nf,
                       (uint16_t *)i_buf, (uint16_t *)j_buf, nnz, w_buf);
}

int
sparse_is_sorted_wrapper(const char *i_buf, const char *j_buf, int nnz)
{
    return sparse_is_sorted((uint16_t *)i_buf, (uint16_t *)j_buf, nnz);
}

int
sparse_connectedpixels_wrapper(float *v, const char *i_buf, const char *j_buf,
                                int nnz, float threshold, int *labels_p)
{
    return sparse_connectedpixels(v, (uint16_t *)i_buf, (uint16_t *)j_buf,
                                  nnz, threshold, (int32_t *)labels_p);
}

int
sparse_connectedpixels_splat_wrapper(float *v, const char *i_buf,
                                      const char *j_buf, int nnz,
                                      float threshold, int *labels_p,
                                      int *Z_buf, int imax, int jmax)
{
    return sparse_connectedpixels_splat(v, (uint16_t *)i_buf,
                                        (uint16_t *)j_buf, nnz, threshold,
                                        (int32_t *)labels_p,
                                        (int32_t *)Z_buf, imax, jmax);
}

void
sparse_blob2Dproperties_wrapper(float *v, const char *i_buf, const char *j_buf,
                                 int nnz, int *labels_p, int npk,
                                 double *results)
{
    sparse_blob2Dproperties(v, (uint16_t *)i_buf, (uint16_t *)j_buf,
                            nnz, (int32_t *)labels_p, results, npk);
}

void
sparse_smooth_wrapper(float *v, const char *i_buf, const char *j_buf,
                       int nnz, float *s)
{
    sparse_smooth(v, (uint16_t *)i_buf, (uint16_t *)j_buf, nnz, s);
}

int
sparse_localmaxlabel_wrapper(float *v, const char *i_buf, const char *j_buf,
                              int nnz, float *MV, int *iMV, int *labels_p)
{
    return sparse_localmaxlabel(v, (uint16_t *)i_buf, (uint16_t *)j_buf,
                                nnz, MV, (int32_t *)iMV, (int32_t *)labels_p);
}

int
sparse_overlaps_wrapper(const char *i1_buf, const char *j1_buf,
                         int *k1, int nnz1,
                         const char *i2_buf, const char *j2_buf,
                         int *k2, int nnz2)
{
    return sparse_overlaps((uint16_t *)i1_buf, (uint16_t *)j1_buf,
                           k1, nnz1,
                           (uint16_t *)i2_buf, (uint16_t *)j2_buf,
                           k2, nnz2);
}

int
tosparse_u16_wrapper(const char *img_buf, const char *msk_buf,
                      char *row_buf, char *col_buf, char *val_buf,
                      int cut, int ns, int nf)
{
    return tosparse_u16((uint16_t *)img_buf, (uint8_t *)msk_buf,
                        (uint16_t *)row_buf, (uint16_t *)col_buf,
                        (uint16_t *)val_buf, cut, ns, nf);
}

int
tosparse_u32_wrapper(const int *img_buf, const char *msk_buf,
                      char *row_buf, char *col_buf, int *val_buf,
                      float cut, int ns, int nf)
{
    return tosparse_u32((uint32_t *)img_buf, (uint8_t *)msk_buf,
                        (uint16_t *)row_buf, (uint16_t *)col_buf,
                        (uint32_t *)val_buf, cut, ns, nf);
}

int
tosparse_f32_wrapper(const float *img, const char *msk_buf,
                      char *row_buf, char *col_buf, float *val,
                      float cut, int ns, int nf)
{
    return tosparse_f32((float*)img, (uint8_t *)msk_buf,
                        (uint16_t *)row_buf, (uint16_t *)col_buf,
                        val, cut, ns, nf);
}

int
coverlaps_wrapper(const char *row1_buf, const char *col1_buf,
                   int *labels1, int nnz1,
                   const char *row2_buf, const char *col2_buf,
                   int *labels2, int nnz2,
                   int *mat, int npk1, int npk2, int *results)
{
    return coverlaps((uint16_t *)row1_buf, (uint16_t *)col1_buf,
                     labels1, nnz1,
                     (uint16_t *)row2_buf, (uint16_t *)col2_buf,
                     labels2, nnz2,
                     mat, npk1, npk2, results);
}
