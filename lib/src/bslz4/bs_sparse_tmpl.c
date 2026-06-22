/* bs_sparse_tmpl.c - basic sparse decompress template.
 *
 * Included from bs_master.c with DATATYPE, NB, KERNEL_FN, bs_decompress
 * already defined. Generates one function: KERNEL_FN().
 */

int KERNEL_FN(const uint8_t *restrict compressed, intptr_t compressed_length,
              const uint8_t *restrict mask, intptr_t NIJ,
              DATATYPE *restrict output, uint32_t *restrict output_adr,
              int threshold, int encoding,
              const int64_t *restrict chunk_offsets,
              const int32_t *restrict chunk_lengths,
              intptr_t nchunks,
              int32_t *restrict npx_per_chunk);

int KERNEL_FN(const uint8_t *restrict compressed, intptr_t compressed_length,
              const uint8_t *restrict mask, intptr_t NIJ,
              DATATYPE *restrict output, uint32_t *restrict output_adr,
              int threshold, int encoding,
              const int64_t *restrict chunk_offsets,
              const int32_t *restrict chunk_lengths,
              intptr_t nchunks,
              int32_t *restrict npx_per_chunk)
{
    int blocksize, ret;
    intptr_t c;
    int j;
    uint32_t nbytes;
    int *chunk_p, *chunk_rem, *chunk_npx;
    DATATYPE **chunk_wr_out;
    uint32_t **chunk_wr_outadr;
    int total_npx, max_rem, i0;
    size_t chunk_total;
    uint32_t val, cut;
    DATATYPE tmp1[BLK/NB], tmp2[BLK/NB];
#ifdef USE_KCB
    char scratch[BLK];
#endif

    if (nchunks <= 0) return -1;
    if (threshold < 0) {
        printf("Threshold must be zero or positive\n");
        return -100;
    }

    chunk_p   = (int *)malloc((size_t)nchunks * sizeof(int));
    chunk_rem = (int *)malloc((size_t)nchunks * sizeof(int));
    chunk_npx = (int *)malloc((size_t)nchunks * sizeof(int));
    chunk_wr_out   = (DATATYPE **)malloc((size_t)nchunks * sizeof(DATATYPE *));
    chunk_wr_outadr = (uint32_t **)malloc((size_t)nchunks * sizeof(uint32_t *));
    if (!chunk_p || !chunk_rem || !chunk_npx || !chunk_wr_out || !chunk_wr_outadr) {
        free(chunk_p); free(chunk_rem); free(chunk_npx);
        free(chunk_wr_out); free(chunk_wr_outadr);
        return -200;
    }

    for (c = 0; c < nchunks; c++) {
        chunk_p[c] = 12;
        chunk_total = READ64BE(&compressed[chunk_offsets[c]]);
        chunk_rem[c] = (int)chunk_total;
        if (chunk_total / NB > (uint64_t)NIJ) {
            free(chunk_p); free(chunk_rem); free(chunk_npx);
            free(chunk_wr_out); free(chunk_wr_outadr);
            return -99;
        }
        if (chunk_total > (size_t)INT_MAX) {
            printf("Too large, %zd > %d\n", chunk_total, INT_MAX);
            free(chunk_p); free(chunk_rem); free(chunk_npx);
            free(chunk_wr_out); free(chunk_wr_outadr);
            return -98;
        }
        blocksize = (int)READ32BE(&compressed[chunk_offsets[c] + 8]);
        if (blocksize == 0) blocksize = BLK;
        if (blocksize != BLK) {
            printf("Sorry, only for 8192 internal blocks\n");
            free(chunk_p); free(chunk_rem); free(chunk_npx);
            free(chunk_wr_out); free(chunk_wr_outadr);
            return -101;
        }
        chunk_npx[c] = 0;
        chunk_wr_out[c]   = output  + c * (size_t)NIJ;
        chunk_wr_outadr[c] = output_adr + c * (size_t)NIJ;
    }

    max_rem = chunk_rem[0];
    i0 = 0;
    cut = (uint32_t)threshold;

    for ( ; max_rem >= BLK; max_rem -= BLK) {
        for (c = 0; c < nchunks; c++) {
            nbytes = READ32BE(&compressed[chunk_offsets[c] + chunk_p[c]]);

            ret = bs_decompress(&compressed[chunk_offsets[c] + chunk_p[c] + 4],
                                nbytes, (char*)tmp1, BLK, encoding);
            chunk_p[c] += nbytes + 4;
            chunk_rem[c] -= BLK;
            if (unlikely(ret != BLK)) {
                printf("ret %d expected %d\n", ret, BLK);
                free(chunk_p); free(chunk_rem); free(chunk_npx);
                free(chunk_wr_out); free(chunk_wr_outadr);
                return -2;
            }

#ifdef USE_KCB
            bitshuf_decode_block((char*)tmp2, (char*)tmp1, scratch,
                                 (size_t)(BLK/NB), (size_t)NB);
#else
            bshuf_untrans_bit_elem((void*)tmp1, (void*)tmp2,
                                   (size_t)(BLK/NB), (size_t)NB);
#endif

            for (j = 0; j < BLK/NB; j++) {
                val = mask[j + i0] * tmp2[j];
                if (unlikely(val > cut)) {
                    *(chunk_wr_out[c]++)   = tmp2[j];
                    *(chunk_wr_outadr[c]++) = j + i0;
                    chunk_npx[c]++;
                }
            }
        }
        i0 += BLK / NB;
    }

    for (c = 0; c < nchunks; c++) {
        int rem = chunk_rem[c];
        if (rem <= 0) continue;
        blocksize = (8 * NB) * (rem / (8 * NB));
        if (blocksize > 0) {
            nbytes = READ32BE(&compressed[chunk_offsets[c] + chunk_p[c]]);
            ret = bs_decompress(&compressed[chunk_offsets[c] + chunk_p[c] + 4],
                                nbytes, (char*)tmp1, blocksize, encoding);
            chunk_p[c] += nbytes + 4;
            if (unlikely(ret != blocksize)) {
                printf("ret %d blocksize %d\n", ret, blocksize);
                free(chunk_p); free(chunk_rem); free(chunk_npx);
                free(chunk_wr_out); free(chunk_wr_outadr);
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
        rem -= blocksize;
        if (rem > 0) {
            memcpy(&tmp2[blocksize/NB],
                   &compressed[chunk_offsets[c] + chunk_lengths[c] - rem],
                   (size_t)rem);
        }
        for (j = 0; j < (rem + blocksize) / NB; j++) {
            val = mask[j + i0] * tmp2[j];
            if (unlikely(val > cut)) {
                *(chunk_wr_out[c]++)   = tmp2[j];
                *(chunk_wr_outadr[c]++) = j + i0;
                chunk_npx[c]++;
            }
        }
    }

    total_npx = 0;
    for (c = 0; c < nchunks; c++)
        total_npx += chunk_npx[c];

    if (npx_per_chunk)
        memcpy(npx_per_chunk, chunk_npx, (size_t)nchunks * sizeof(int32_t));

    free(chunk_p); free(chunk_rem); free(chunk_npx);
    free(chunk_wr_out); free(chunk_wr_outadr);
    return total_npx;
}
