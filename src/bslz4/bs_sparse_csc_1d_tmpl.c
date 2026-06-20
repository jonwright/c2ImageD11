/* bs_sparse_csc_1d_tmpl.c - 1D padded CSC sparse decompress template.
 *
 * Included from bs_master.c with DATATYPE, NB, KERNEL_CSC1D_FN,
 * CSC_DATA_T, CSC_SUM_T, bs_decompress already defined.
 * Generates one function: KERNEL_CSC1D_FN().
 *
 * Replaces (data, indices, indptr) with (csc_flat, csc_first_bin,
 * csc_entries_per_pixel).  Uses a switch on csc_entries_per_pixel
 * outside the pixel loop to dispatch to fully-unrolled paths.
 *
 * CSC_DATA_T: type of CSC matrix data (float, uint8_t, uint16_t, uint32_t)
 * CSC_SUM_T:  type of histogram output (double for float data, uint64_t for int)
 */

int KERNEL_CSC1D_FN(const uint8_t *restrict compressed, intptr_t compressed_length,
                    const uint8_t *restrict mask, intptr_t NIJ,
                    DATATYPE *restrict outpx, uint32_t *restrict output_adr,
                    int threshold, int encoding,
                    CSC_SUM_T *restrict output, intptr_t nout_total,
                    const CSC_DATA_T *restrict csc_flat,
                    const uint32_t *restrict csc_first_bin,
                    int csc_entries_per_pixel,
                    const int64_t *restrict chunk_offsets,
                    const int32_t *restrict chunk_lengths,
                    intptr_t nchunks,
                    int32_t *restrict npx_per_chunk);

int KERNEL_CSC1D_FN(const uint8_t *restrict compressed, intptr_t compressed_length,
                    const uint8_t *restrict mask, intptr_t NIJ,
                    DATATYPE *restrict outpx, uint32_t *restrict output_adr,
                    int threshold, int encoding,
                    CSC_SUM_T *restrict output, intptr_t nout_total,
                    const CSC_DATA_T *restrict csc_flat,
                    const uint32_t *restrict csc_first_bin,
                    int csc_entries_per_pixel,
                    const int64_t *restrict chunk_offsets,
                    const int32_t *restrict chunk_lengths,
                    intptr_t nchunks,
                    int32_t *restrict npx_per_chunk)
{
    /* Stride for inner pixel loop, fixed at 64.
     * This spreads consecutive inner-loop pixels across ~64 cache lines
     * of the output histogram, reducing write-after-write serialisation. */
    const int csc1d_stride = 64;
    int blocksize, ret;
    intptr_t c;
    int j;
    uint32_t nbytes;
    unsigned int k;
    int *chunk_p, *chunk_rem, *chunk_npx;
    DATATYPE **chunk_wr_outpx;
    uint32_t **chunk_wr_outadr;
    int total_npx, max_rem, i0;
    size_t chunk_total;
    DATATYPE val, cut, tmp1[BLK/NB], tmp2[BLK/NB];
#ifdef USE_KCB
    char scratch[BLK];
#endif

    if (nchunks <= 0) return -1;
    if (nout_total % nchunks != 0) return -103;
    intptr_t nbins = nout_total / nchunks;

    chunk_p   = (int *)malloc((size_t)nchunks * sizeof(int));
    chunk_rem = (int *)malloc((size_t)nchunks * sizeof(int));
    chunk_npx = (int *)malloc((size_t)nchunks * sizeof(int));
    chunk_wr_outpx  = (DATATYPE **)malloc((size_t)nchunks * sizeof(DATATYPE *));
    chunk_wr_outadr = (uint32_t **)malloc((size_t)nchunks * sizeof(uint32_t *));
    if (!chunk_p || !chunk_rem || !chunk_npx || !chunk_wr_outpx || !chunk_wr_outadr) {
        free(chunk_p); free(chunk_rem); free(chunk_npx);
        free(chunk_wr_outpx); free(chunk_wr_outadr);
        return -200;
    }

    for (c = 0; c < nchunks; c++) {
        chunk_p[c] = 12;
        chunk_total = READ64BE(&compressed[chunk_offsets[c]]);
        chunk_rem[c] = (int)chunk_total;
        if (chunk_total / NB > (uint64_t)NIJ) {
            printf("Not enough output space, %zd %td\n", chunk_total, NIJ);
            free(chunk_p); free(chunk_rem); free(chunk_npx);
            free(chunk_wr_outpx); free(chunk_wr_outadr);
            return -99;
        }
        if (chunk_total > (size_t)INT_MAX) {
            printf("Too large, %zd > %d\n", chunk_total, INT_MAX);
            free(chunk_p); free(chunk_rem); free(chunk_npx);
            free(chunk_wr_outpx); free(chunk_wr_outadr);
            return -98;
        }
        blocksize = (int)READ32BE(&compressed[chunk_offsets[c] + 8]);
        if (blocksize == 0) blocksize = BLK;
        if (blocksize != BLK) {
            printf("Sorry, only for 8192 internal blocks\n");
            free(chunk_p); free(chunk_rem); free(chunk_npx);
            free(chunk_wr_outpx); free(chunk_wr_outadr);
            return -101;
        }
        chunk_npx[c] = 0;
        chunk_wr_outpx[c]  = outpx + c * (size_t)NIJ;
        chunk_wr_outadr[c] = output_adr + c * (size_t)NIJ;
    }

    for (c = 0; c < nchunks; c++)
        for (j = 0; j < nbins; j++)
            output[c * (size_t)nbins + j] = (CSC_SUM_T)0;

    max_rem = chunk_rem[0];
    i0 = 0;
    cut = threshold;

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
                free(chunk_wr_outpx); free(chunk_wr_outadr);
                return -2;
            }

#ifdef USE_KCB
            bitshuf_decode_block((char*)tmp2, (char*)tmp1, scratch,
                                 (size_t)(BLK/NB), (size_t)NB);
#else
            bshuf_untrans_bit_elem((void*)tmp1, (void*)tmp2,
                                   (size_t)(BLK/NB), (size_t)NB);
#endif

            /* ---- pixel loop with switch on csc_entries_per_pixel ---- */
            int npix = BLK / NB;
            switch (csc_entries_per_pixel) {
            case 4: {
                int ii;
                for (ii = 0; ii < csc1d_stride; ii++) {
                    for (j = ii; j < npix; j += csc1d_stride) {
                        int jj = j + i0;
                        val = tmp2[j] * mask[jj];
                        if (unlikely(val > 0)) {
                            int bin = (int)csc_first_bin[jj];
                            if (unlikely(bin + 4 > nbins)) return -102;
                            int off = jj * 4;
                            CSC_SUM_T v = (CSC_SUM_T)tmp2[j];
                            size_t base = c * (size_t)nbins;
                            output[base + bin]     += (CSC_SUM_T)csc_flat[off]   * v;
                            output[base + bin + 1] += (CSC_SUM_T)csc_flat[off+1] * v;
                            output[base + bin + 2] += (CSC_SUM_T)csc_flat[off+2] * v;
                            output[base + bin + 3] += (CSC_SUM_T)csc_flat[off+3] * v;
                            if (unlikely(tmp2[j] > cut)) {
                                *(chunk_wr_outpx[c]++)  = tmp2[j];
                                *(chunk_wr_outadr[c]++) = jj;
                                chunk_npx[c]++;
                            }
                        }
                    }
                }
                } break;
            case 6: {
                int ii;
                for (ii = 0; ii < csc1d_stride; ii++) {
                    for (j = ii; j < npix; j += csc1d_stride) {
                        int jj = j + i0;
                        val = tmp2[j] * mask[jj];
                        if (unlikely(val > 0)) {
                            int bin = (int)csc_first_bin[jj];
                            if (unlikely(bin + 6 > nbins)) return -102;
                            int off = jj * 6;
                            CSC_SUM_T v = (CSC_SUM_T)tmp2[j];
                            size_t base = c * (size_t)nbins;
                            output[base + bin]     += (CSC_SUM_T)csc_flat[off]   * v;
                            output[base + bin + 1] += (CSC_SUM_T)csc_flat[off+1] * v;
                            output[base + bin + 2] += (CSC_SUM_T)csc_flat[off+2] * v;
                            output[base + bin + 3] += (CSC_SUM_T)csc_flat[off+3] * v;
                            output[base + bin + 4] += (CSC_SUM_T)csc_flat[off+4] * v;
                            output[base + bin + 5] += (CSC_SUM_T)csc_flat[off+5] * v;
                            if (unlikely(tmp2[j] > cut)) {
                                *(chunk_wr_outpx[c]++)  = tmp2[j];
                                *(chunk_wr_outadr[c]++) = jj;
                                chunk_npx[c]++;
                            }
                        }
                    }
                }
                } break;
            case 8: {
                int ii;
                for (ii = 0; ii < csc1d_stride; ii++) {
                    for (j = ii; j < npix; j += csc1d_stride) {
                        int jj = j + i0;
                        val = tmp2[j] * mask[jj];
                        if (unlikely(val > 0)) {
                            int bin = (int)csc_first_bin[jj];
                            if (unlikely(bin + 8 > nbins)) return -102;
                            int off = jj * 8;
                            CSC_SUM_T v = (CSC_SUM_T)tmp2[j];
                            size_t base = c * (size_t)nbins;
                            output[base + bin]     += (CSC_SUM_T)csc_flat[off]   * v;
                            output[base + bin + 1] += (CSC_SUM_T)csc_flat[off+1] * v;
                            output[base + bin + 2] += (CSC_SUM_T)csc_flat[off+2] * v;
                            output[base + bin + 3] += (CSC_SUM_T)csc_flat[off+3] * v;
                            output[base + bin + 4] += (CSC_SUM_T)csc_flat[off+4] * v;
                            output[base + bin + 5] += (CSC_SUM_T)csc_flat[off+5] * v;
                            output[base + bin + 6] += (CSC_SUM_T)csc_flat[off+6] * v;
                            output[base + bin + 7] += (CSC_SUM_T)csc_flat[off+7] * v;
                            if (unlikely(tmp2[j] > cut)) {
                                *(chunk_wr_outpx[c]++)  = tmp2[j];
                                *(chunk_wr_outadr[c]++) = jj;
                                chunk_npx[c]++;
                            }
                        }
                    }
                }
                } break;
            default: {
                int ii;
                for (ii = 0; ii < csc1d_stride; ii++) {
                    for (j = ii; j < npix; j += csc1d_stride) {
                        int jj = j + i0;
                        val = tmp2[j] * mask[jj];
                        if (unlikely(val > 0)) {
                            int bin = (int)csc_first_bin[jj];
                            int off = jj * csc_entries_per_pixel;
                            size_t base = c * (size_t)nbins;
                            CSC_SUM_T v = (CSC_SUM_T)tmp2[j];
                            int remain = nbins - bin;
                            for (k = 0; k < (unsigned int)csc_entries_per_pixel && (int)k < remain; k++)
                                output[base + bin + k] += (CSC_SUM_T)csc_flat[off + k] * v;
                            if (unlikely(tmp2[j] > cut)) {
                                *(chunk_wr_outpx[c]++)  = tmp2[j];
                                *(chunk_wr_outadr[c]++) = jj;
                                chunk_npx[c]++;
                            }
                        }
                    }
                }
                } break;
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
                free(chunk_wr_outpx); free(chunk_wr_outadr);
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
        {
            int ii, npix2 = (rem + blocksize) / NB;
            for (ii = 0; ii < csc1d_stride; ii++) {
                for (j = ii; j < npix2; j += csc1d_stride) {
                    int jj = j + i0;
                    val = tmp2[j] * mask[jj];
                    if (unlikely(val > 0)) {
                        int bin = (int)csc_first_bin[jj];
                        int off = jj * csc_entries_per_pixel;
                        size_t base = c * (size_t)nbins;
                        CSC_SUM_T v = (CSC_SUM_T)tmp2[j];
                        int remain = nbins - bin;
                        for (k = 0; k < (unsigned int)csc_entries_per_pixel && (int)k < remain; k++)
                            output[base + bin + k] += (CSC_SUM_T)csc_flat[off + k] * v;
                        if (unlikely(tmp2[j] > cut)) {
                            *(chunk_wr_outpx[c]++)  = tmp2[j];
                            *(chunk_wr_outadr[c]++) = jj;
                            chunk_npx[c]++;
                        }
                    }
                }
            }
        }
    }

    total_npx = 0;
    for (c = 0; c < nchunks; c++)
        total_npx += chunk_npx[c];

    if (npx_per_chunk)
        memcpy(npx_per_chunk, chunk_npx, (size_t)nchunks * sizeof(int32_t));

    free(chunk_p); free(chunk_rem); free(chunk_npx);
    free(chunk_wr_outpx); free(chunk_wr_outadr);
    return total_npx;
}
