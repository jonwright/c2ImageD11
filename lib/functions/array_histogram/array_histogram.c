#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "array_histogram(img: buffer, low: float, high: float, hist: buffer) -> void",
 *  "doc": "computes the histogram for an image\nGo through the data to compute a histogram of the values\n Previous call of array_stats would help to set up this call\n  compare to np.bincount - this does not gain much\n  better implementations can be done\nimg[]  Input data array  (1D or 2D.ravel(), so sparse or dense)\nnpx    length of data array (contiguous)\nlow    Lower edge of first bin\nhigh   Upper edge of last bin\nhist[] Histogram to be output\nnhist  Number of bins in the histogram",
 *  "checks": ["img.format == 'f'", "( hist.format == 'i' or hist.format == 'l' )"],
 *  "c_overloads": [{"sig": "void array_histogram(const float *img, intptr_t npx, float low, float high, int32_t *hist, intptr_t nhist)",
 *      "map": {"img": "img.ptr", "npx": "img.n", "low": "low", "high": "high", "hist": "hist.ptr", "nhist": "hist.n"}}]}
C2PY_END */

void array_histogram(const float img[], intptr_t npx, float low, float high,
                     int32_t hist[], intptr_t nhist) {
    intptr_t i; int ibin;
    float ostep;
    memset(hist, 0, nhist * sizeof(int32_t));
    /* Compute the multiplier to get the bin numbers */
    if (high <= low) {
        return;
    }
    ostep = nhist / (high - low);
    for (i = 0; i < npx; i++) {
        ibin = (int)floorf((img[i] - low) * ostep);
        /* clip into range at ends */
        if (ibin < 0) {
            ibin = 0;
        }
        if (ibin >= nhist) {
            ibin = nhist - 1;
        }
        hist[ibin] = hist[ibin] + 1;
    }
}
