/* bs_sparse_csc_tmpl.c - CSC sparse decompress template.
 *
 * Included from bs_master.c with DATATYPE, NB, KERNEL_CSC_FN,
 * CSC_DATA_T, CSC_SUM_T, BS_DECOMPRESS already defined.
 * Generates one function: KERNEL_CSC_FN().
 *
 * Same pipeline as bs_sparse_tmpl.c but additionally accumulates
 * every non-zero pixel into a CSC sparse matrix (powder integration).
 *
 * CSC_DATA_T: type of CSC matrix data (float, uint8_t, uint16_t, uint32_t)
 * CSC_SUM_T:  type of histogram output (double for float data, uint64_t for int)
 */

int KERNEL_CSC_FN(const uint8_t *restrict compressed, int compressed_length,
                  const uint8_t *restrict mask, int NIJ,
                  DATATYPE *restrict outpx, uint32_t *restrict output_adr,
                  int threshold,
                  CSC_SUM_T *restrict output, int NOUT,
                  CSC_DATA_T *restrict data, uint32_t *restrict indices,
                  uint32_t *restrict indptr);

int KERNEL_CSC_FN(const uint8_t *restrict compressed, int compressed_length,
                  const uint8_t *restrict mask, int NIJ,
                  DATATYPE *restrict outpx, uint32_t *restrict output_adr,
                  int threshold,
                  CSC_SUM_T *restrict output, int NOUT,
                  CSC_DATA_T *restrict data, uint32_t *restrict indices,
                  uint32_t *restrict indptr)
{
    size_t total_output_length;
    int blocksize, remaining, p;
    uint32_t nbytes;
    DATATYPE val, cut, tmp1[BLK/NB], tmp2[BLK/NB];
#ifdef USE_KCB
    char scratch[BLK];
#endif
    int npx, i0, j, ret;
    unsigned int k;

    npx = 0;
    i0 = 0;
    cut = threshold;
    total_output_length = READ64BE(compressed);
    if (total_output_length/NB > (uint64_t)NIJ) {
        printf("Not enough output space, %zd %d\n", total_output_length, NIJ);
        return -99;
    }
    if (total_output_length > (size_t)INT_MAX) {
        printf("Too large, %zd > %d\n", total_output_length, INT_MAX);
        return -98;
    }
    blocksize = (int)READ32BE(compressed + 8);
    if (blocksize == 0) blocksize = BLK;
    if (blocksize != BLK) {
        printf("Sorry, only for 8192 internal blocks\n");
        return -101;
    }

    for (j = 0; j < NOUT; j++) output[j] = (CSC_SUM_T)0;

    p = 12;
    for (remaining = (int)total_output_length; remaining >= BLK;
         remaining -= BLK) {
        nbytes = READ32BE(&compressed[p]);

        /* --- step 1: decompress --- */
        ret = BS_DECOMPRESS(&compressed[p + 4], nbytes, (char*)tmp1, BLK);
        p += nbytes + 4;
        if (unlikely(ret != BLK)) {
            printf("ret %d blocksize %d\n", ret, blocksize);
            return -2;
        }

        /* --- step 2: unshuffle --- */
#ifdef USE_KCB
        bitshuf_decode_block((char*)tmp2, (char*)tmp1, scratch,
                             (size_t)(BLK/NB), (size_t)NB);
#else
        bshuf_untrans_bit_elem((void*)tmp1, (void*)tmp2,
                               (size_t)(BLK/NB), (size_t)NB);
#endif

        /* --- step 3: mask -> sparse + CSC accumulate --- */
        for (j = 0; j < BLK/NB; j++) {
            val = tmp2[j] * mask[j + i0];
            if (unlikely(val > 0)) {
                for (k = indptr[j + i0]; k < indptr[j + i0 + 1]; k++) {
                    output[indices[k]] += ((CSC_SUM_T)data[k]) * (CSC_SUM_T)tmp2[j];
                }
                if (unlikely(tmp2[j] > cut)) {
                    *(outpx++) = tmp2[j];
                    *(output_adr++) = j + i0;
                    npx++;
                }
            }
        }
        i0 += BLK / NB;
    }

    /* partial final block */
    blocksize = (8 * NB) * (remaining / (8 * NB));
    if (blocksize > 0) {
        nbytes = READ32BE(&compressed[p]);
        ret = BS_DECOMPRESS(&compressed[p + 4], nbytes, (char*)tmp1, blocksize);
        p += nbytes + 4;
        if (unlikely(ret != blocksize)) {
            printf("ret %d blocksize %d\n", ret, blocksize);
            return -2;
        }
#ifdef USE_KCB
        bitshuf_decode_block((char*)tmp2, (char*)tmp1, scratch,
                             (size_t)(blocksize/NB), (size_t)NB);
#else
        bshuf_untrans_bit_elem((void*)tmp1, (void*)tmp2,
                               (size_t)(blocksize/NB), (size_t)NB);
#endif
    }
    remaining -= blocksize;
    if (remaining > 0) {
        memcpy(&tmp2[blocksize/NB], &compressed[compressed_length - remaining],
               (size_t)remaining);
    }
    for (j = 0; j < (remaining + blocksize)/NB; j++) {
        val = tmp2[j] * mask[j + i0];
        if (unlikely(val > 0)) {
            for (k = indptr[j + i0]; k < indptr[j + i0 + 1]; k++) {
                output[indices[k]] += ((CSC_SUM_T)data[k]) * (CSC_SUM_T)tmp2[j];
            }
            if (unlikely(tmp2[j] > cut)) {
                *(outpx++) = tmp2[j];
                *(output_adr++) = j + i0;
                npx++;
            }
        }
    }
    return npx;
}
