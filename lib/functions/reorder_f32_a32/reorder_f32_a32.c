#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "reorder_f32_a32(data: buffer, adr: buffer, out: buffer) -> void",
 *  "doc": "called in sandbox/fazit.py simple\nloop with openmp saying out[adr[i]] in data[i]\ne.g. semi-random writing",
 *  "checks": ["data.format == 'f'", "adr.format == 'I' or adr.itemsize == 4",
 *      "adr.n == data.n", "out.format == 'f'", "out.n >= data.n"],
 *  "gil_release": true,
 *  "c_overloads": [{"when": "data.format == 'f' and out.format == 'f'",
 *      "sig": "void reorder_f32_a32(const float *data, const uint32_t *adr, float *out, intptr_t N)",
 *      "map": {"data": "data.ptr", "adr": "adr.ptr", "out": "out.ptr", "N": "data.n"}}]}
C2PY_END */

void reorder_f32_a32(const float *restrict data, const uint32_t *restrict adr,
                     float *restrict out, intptr_t N) {
    intptr_t i;
    /*  printf("Hello, got N=%d\n",N);*/
#pragma omp parallel for
    for (i = 0; i < N; i++) {
        out[adr[i]] = data[i];
    }
}
