#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "reorder_u16_a32(data: buffer, adr: buffer, out: buffer) -> void",
 *  "doc": "called in sandbox/fazit.py simple\nloop with openmp saying out[adr[i]] in data[i]\ne.g. semi-random writing",
 *  "checks": ["data.format == 'H' or data.itemsize == 2", "adr.format == 'I' or adr.itemsize == 4",
 *      "adr.n == data.n", "out.format == 'H' or out.itemsize == 2", "out.n >= data.n"],
 *  "gil_release": true,
 *  "c_overloads": [{"when": "adr.format == 'I' or adr.itemsize == 4",
 *      "sig": "void reorder_u16_a32(const uint16_t *data, const uint32_t *adr, uint16_t *out, intptr_t N)",
 *      "map": {"data": "data.ptr", "adr": "adr.ptr", "out": "out.ptr", "N": "data.n"}}]}
C2PY_END */

void reorder_u16_a32(const uint16_t *restrict data,
                     const uint32_t *restrict adr, uint16_t *restrict out,
                     intptr_t N) {
    intptr_t i;
    /*  printf("Hello, got N=%d\n",N);*/
#pragma omp parallel for
    for (i = 0; i < N; i++) {
        out[adr[i]] = data[i];
    }
}
