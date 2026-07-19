#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "sparse_blob2Dproperties(v: buffer, i: buffer, j: buffer, labels: buffer, npk: int, results: buffer) -> void",
 *  "doc": "fills the array results with properties of\neach labelled object described by v and labels (pixel values and blob)\nand positions i,j in the image.\nresults are:\n  results[ipk,s2D_1]   = sum(1), number of pixels\n  results[ipk,s2D_I]   = sum (I), total intensity\n  results[ipk,s2D_fI]  = sum (f*I), intensity weighted fast index\n  results[ipk,s2D_sI]  = sum (s*I), intensity weighted slow index\n  results[ipk,s2D_ffI] = sum (f*f*I), intensity weighted fast^2 index\n  results[ipk,s2D_sfI] = sum (s*f*I), intensity weighted slow*fast index\n  results[ipk,s2D_ssI] = sum (s*s*I), intensity weighted slow^2 index",
 *  "params": {"v": "Values (float32).", "i": "Rows (uint16).", "j": "Cols (uint16).",
 *      "labels": "Labels (int32).", "npk": "Number of objects.", "results": "Output (npk, 11)."},
 *  "checks": ["v.format == 'f'", "i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2",
 *      "j.n == i.n", "v.n == i.n", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == i.n",
 *      "results.format == 'd'", "results.shape[0] == npk", "results.shape[1] == 11"],
 *  "c_overloads": [{"sig": "void sparse_blob2Dproperties(float *data, uint16_t *i, uint16_t *j, intptr_t nnz, int32_t *labels, double *res, int32_t npk)",
 *      "map": {"data": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "labels": "labels.ptr", "res": "results.ptr", "npk": "npk"}}]}
C2PY_END */

void sparse_blob2Dproperties(float *restrict data, uint16_t *restrict i,
                             uint16_t *restrict j, intptr_t nnz,
                             int32_t *restrict labels, double *restrict res,
                             int32_t npk) {
    int k, kpk, f, s;
    double fval;
    /* init to zero */
    for (k = 0; k < npk * NPROPERTY2D; k++) {
        res[k] = 0.0;
    }
    for (k = 0; k < npk; k++) {
        res[k * NPROPERTY2D + s2D_bb_mn_f] = 65534.;
        res[k * NPROPERTY2D + s2D_bb_mn_s] = 65534.;
    }
    /*  printf("nnz : %d\n",nnz); */
    for (k = 0; k < nnz; k++) {
        if (labels[k] == 0) {
            continue; /* background pixel */
        }
        if (labels[k] > npk) {
            printf("Error,k %td,labels[k] %d, npk %td \n", k, labels[k], npk);
        }
        kpk = (labels[k] - 1) * NPROPERTY2D;
        fval = (double)data[k];
        s = (int)i[k];
        f = (int)j[k];
        res[kpk + s2D_1] += 1.;
        res[kpk + s2D_I] += fval;
        res[kpk + s2D_fI] += (fval * f);
        res[kpk + s2D_sI] += (fval * s);
        res[kpk + s2D_ffI] += (fval * f * f);
        res[kpk + s2D_sfI] += (fval * s * f);
        res[kpk + s2D_ssI] += (fval * s * s);

        if (res[kpk + s2D_bb_mx_s] < s)
            res[kpk + s2D_bb_mx_s] = s;
        if (res[kpk + s2D_bb_mx_f] < f)
            res[kpk + s2D_bb_mx_f] = f;
        if (res[kpk + s2D_bb_mn_s] > s)
            res[kpk + s2D_bb_mn_s] = s;
        if (res[kpk + s2D_bb_mn_f] > f)
            res[kpk + s2D_bb_mn_f] = f;
    }
}
