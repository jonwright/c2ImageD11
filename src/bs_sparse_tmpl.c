/* bs_sparse_tmpl.c - basic sparse decompress template.
 *
 * Included from bs_master.c with DATATYPE, NB, KERNEL_FN, BS_DECOMPRESS
 * already defined. Generates one function: KERNEL_FN().
 */

int KERNEL_FN(const uint8_t *restrict compressed, int compressed_length,
              const uint8_t *restrict mask, int NIJ,
              DATATYPE *restrict output, uint32_t *restrict output_adr,
              int threshold);

int KERNEL_FN(const uint8_t *restrict compressed, int compressed_length,
              const uint8_t *restrict mask, int NIJ,
              DATATYPE *restrict output, uint32_t *restrict output_adr,
              int threshold)
{
    size_t total_output_length;
    int blocksize, remaining, p;
    uint32_t nbytes;
    DATATYPE tmp1[BLK/NB], tmp2[BLK/NB];
#ifdef USE_KCB
    char scratch[BLK];
#endif
    int npx, i0, j, ret;
    uint32_t val, cut;

    npx = 0;
    i0 = 0;
    if (threshold < 0) {
        printf("Threshold must be zero or positive\n");
        return -100;
    }
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

        /* --- step 3: mask → sparse --- */
        for (j = 0; j < BLK/NB; j++) {
            val = mask[j + i0] * tmp2[j];
            if (unlikely(val > cut)) {
                *(output++) = tmp2[j];
                *(output_adr++) = j + i0;
                npx++;
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
        val = mask[j + i0] * tmp2[j];
        if (unlikely(val > cut)) {
            *(output++) = tmp2[j];
            *(output_adr++) = j + i0;
            npx++;
        }
    }
    return npx;
}
