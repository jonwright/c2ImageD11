#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "splat(rgba: buffer, gve: buffer, u: buffer, npx: int) -> void",
 *  "doc": "draws gvectors into an rgba image. The horror of maintaining plot3d\nover the years motivated this code. See test/demo/tksplat\n* set the color and markersize per peak\n* perhaps also a draw order (back to front, top to bottom) ?",
 *  "params": {"rgba": "Output uint8 RGBA (h, w, 4).",
 *      "gve": "G-vectors (ng, 3).",
 *      "u": "Projection matrix (9).", "npx": "Marker half-size."},
 *  "checks": ["rgba.format == 'B' or rgba.format == 'b'", "rgba.ndim >= 1",
 *      "gve.format == 'd'", "gve.ndim >= 1", "u.format == 'd'", "u.n == 9",
 *      "gve.slow_axis == 0", "gve.ndim == 2", "gve.shape[1] == 3"],
 *  "c_overloads": [{"sig": "void splat(uint8_t *rgba, intptr_t w, intptr_t h, const double gve[][3], intptr_t ng, const double *u, intptr_t npx)",
 *      "map": {"rgba": "rgba.ptr", "w": "rgba.shape[1]", "h": "rgba.shape[0]", "gve": "gve.ptr", "ng": "gve.shape[0]", "u": "u.ptr", "npx": "npx"}}]}
C2PY_END */

void splat(uint8_t rgba[], intptr_t w, intptr_t h, const double gve[][3], intptr_t ng, const double u[9],
           intptr_t npx) {
    intptr_t i, j, k; int32_t imx, imy, imz, w2, h2;
    double s[9];

    /* init */
    h2 = h / 2;
    w2 = w / 2;
    for (i = 0; i < 6; i++) {
        s[i] = u[i] * ((w + h) / 4);
    }
    s[6] = u[6] * 64;
    s[7] = u[7] * 64;
    s[8] = u[8] * 64;
    /* Not parallel - seems to be fast anyway and rgba is shared on write */
    for (i = 0; i < w * h * 4; i = i + 4) {
        rgba[i] = 0;
        rgba[i + 1] = 0;
        rgba[i + 2] = 0;
        rgba[i + 3] = 255;
    }
    for (i = 0; i < ng; i++) {
        imx =
            (int)(s[0] * gve[i][0] + s[1] * gve[i][1] + s[2] * gve[i][2]) + w2;
        imy =
            (int)(s[3] * gve[i][0] + s[4] * gve[i][1] + s[5] * gve[i][2]) + h2;
        imz =
            (int)(s[6] * gve[i][0] + s[7] * gve[i][1] + s[8] * gve[i][2]) + 128;
        if ((imx > npx) && (imx < w - npx) && (imy > npx) && (imy < h - npx) &&
            (imz >= 0) && (imz < 256)) {
            for (j = -npx; j <= npx; j++) {
                for (k = -npx; k <= npx; k++) {
                    rgba[w * (imy + j) * 4 + (imx + k) * 4 + 0] = 255;
                    rgba[w * (imy + j) * 4 + (imx + k) * 4 + 1] = 255;
                    rgba[w * (imy + j) * 4 + (imx + k) * 4 + 2] = 255;
                    rgba[w * (imy + j) * 4 + (imx + k) * 4 + 3] = imz;
                }
            }
        }
    }
}