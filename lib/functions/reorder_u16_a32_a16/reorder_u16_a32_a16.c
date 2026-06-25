#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "reorder_u16_a32_a16(data: buffer, adr0: buffer, adr1: buffer, out: buffer) -> void",
 *  "doc": "2D reorder with per-row base + per-pixel offsets.",
 *  "checks": ["data.format == 'H' or data.itemsize == 2", "data.ndim == 2",
 *      "adr0.format == 'I' or adr0.itemsize == 4", "adr0.n == data.shape[0]",
 *      "adr1.format == 'h' or adr1.itemsize == 2", "adr1.n == data.n",
 *      "out.format == 'H' or out.itemsize == 2", "out.n >= data.n"],
 *  "c_overloads": [{"sig": "void reorder_u16_a32_a16(const uint16_t *data, const uint32_t *a0, const int16_t *a1, uint16_t *out, intptr_t ns, intptr_t nf)",
 *      "map": {"data": "data.ptr", "a0": "adr0.ptr", "a1": "adr1.ptr", "out": "out.ptr", "ns": "data.shape[0]", "nf": "data.shape[1]"}}]}
C2PY_END */

void reorder_u16_a32_a16(const uint16_t *restrict data, const uint32_t *restrict a0,
                         const int16_t *restrict a1, uint16_t *restrict out, intptr_t ns,
                         intptr_t nf) {
    intptr_t i, j; int p;
    /*  printf("Hello, got ns=%d nf=%d\n",ns, nf);*/
#pragma omp parallel for private(p, j)
    for (i = 0; i < ns; i++) {
        p = a0[i];
        for (j = 0; j < nf; j++) {
            p += a1[i * nf + j];
            out[p] = data[i * nf + j];
        }
    }
}
