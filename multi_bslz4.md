# Multi-Chunk BSLZ4 Loop Interchange -- Implementation Guide

## Overview

Interchange the block/chunk loops in the bslz4/bszstd sparse decompressors so that
for each 8KB block position we process all N frames before moving to the next
block.  This keeps the CSC matrix in CPU cache (read once per block, reused
across N frames).

## Design

- **Always-multi-chunk C interface**: Every function gains 4 trailing parameters:
  `chunk_offsets` (int64*), `chunk_lengths` (int32*), `nchunks` (int),
  `npx_per_chunk` (int32* output).
  Single-chunk is `nchunks=1` with `offsets=[0]`, `lengths=[compressed_length]`.
  No conditional compilation, no new function variants.

- **Sparse output always present**: `outpx` = `[nchunks * NIJ]` flat (per-chunk
  contiguous regions). `npx_per_chunk` = `[nchunks]` int32 counts.
  For `nchunks=1` this degenerates to current behaviour.

- **Static-inline block processor** in each template.  Called from a loop
  over blocks x chunks (interchanged) or chunk-only (nchunks==1).

- **malloc per-chunk state**: `int[nchunks]` for read-position, remaining-bytes,
  and sparse counts.  Freed at return.

- **Partial final blocks** processed sequentially per chunk (not interchanged;
  they are small and cache benefit is negligible).

## Files to modify (in order)

1. `src/bs_sparse_tmpl.c`      -- basic decompress template
2. `src/bs_sparse_csc_tmpl.c`  -- CSC decompress template
3. `generate_bslz4.py`         -- code generator (signatures + .c2py)
4. Run generator to produce: `src/bs_functions.h`, `_cImageD11_bslz4.c2py`,
   `src/bs_master.c`
5. `c2ImageD11/bslz4.py`       -- Python wrappers
6. `tests/test_bslz4.py`       -- tests
7. Build and verify

---

## Step 1: `src/bs_sparse_tmpl.c`

Replace the entire file.  The current file is 116 lines (basic decompress).
New version adds an inline block processor and restructures the main function.

```c
/* bs_sparse_tmpl.c - basic sparse decompress template.
 *
 * Included from bs_master.c with DATATYPE, NB, KERNEL_FN, BS_DECOMPRESS
 * already defined. Generates one function: KERNEL_FN().
 */

int KERNEL_FN(const uint8_t *restrict compressed, int compressed_length,
              const uint8_t *restrict mask, int NIJ,
              DATATYPE *restrict output, uint32_t *restrict output_adr,
              int threshold,
              const int64_t *restrict chunk_offsets,
              const int32_t *restrict chunk_lengths,
              int nchunks,
              int32_t *restrict npx_per_chunk);

/* ------------------------------------------------------------------ */
static inline void process_block_sparse(
    const uint8_t *restrict chunk_start,
    int *restrict ppos, int *restrict premaining,
    const uint8_t *restrict mask, int NIJ,
    DATATYPE **restrict pp_output, uint32_t **restrict pp_outadr,
    int *restrict pnpx, int threshold, int i0)
{
    uint32_t nbytes, val, cut;
    DATATYPE tmp1[BLK/NB], tmp2[BLK/NB];
#ifdef USE_KCB
    char scratch[BLK];
#endif
    int j, ret;

    cut = (uint32_t)threshold;
    nbytes = READ32BE(&chunk_start[*ppos]);

    ret = BS_DECOMPRESS(&chunk_start[*ppos + 4], nbytes, (char*)tmp1, BLK);
    *ppos += nbytes + 4;
    *premaining -= BLK;
    if (unlikely(ret != BLK)) {
        printf("ret %d expected %d\n", ret, BLK);
        return;
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
            *(*pp_output)++ = tmp2[j];
            *(*pp_outadr)++ = j + i0;
            (*pnpx)++;
        }
    }
}

/* ------------------------------------------------------------------ */
int KERNEL_FN(const uint8_t *restrict compressed, int compressed_length,
              const uint8_t *restrict mask, int NIJ,
              DATATYPE *restrict output, uint32_t *restrict output_adr,
              int threshold,
              const int64_t *restrict chunk_offsets,
              const int32_t *restrict chunk_lengths,
              int nchunks,
              int32_t *restrict npx_per_chunk)
{
    int blocksize, c, j, ret;
    uint32_t nbytes;
    int *chunk_p, *chunk_rem, *chunk_npx;
    DATATYPE *chunk_wr_outpx;
    uint32_t *chunk_wr_outadr;
    int total_npx, max_rem, i0;
    size_t chunk_total;
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
    if (!chunk_p || !chunk_rem || !chunk_npx) {
        free(chunk_p); free(chunk_rem); free(chunk_npx);
        return -200;
    }

    /* ---------- read headers, initialise per-chunk state ---------- */
    for (c = 0; c < nchunks; c++) {
        chunk_p[c] = 12;
        chunk_total = READ64BE(&compressed[chunk_offsets[c]]);
        chunk_rem[c] = (int)chunk_total;
        if (chunk_total / NB > (uint64_t)NIJ) {
            printf("Not enough output space, %zd %d\n", chunk_total, NIJ);
            free(chunk_p); free(chunk_rem); free(chunk_npx);
            return -99;
        }
        if (chunk_total > (size_t)INT_MAX) {
            printf("Too large, %zd > %d\n", chunk_total, INT_MAX);
            free(chunk_p); free(chunk_rem); free(chunk_npx);
            return -98;
        }
        blocksize = (int)READ32BE(&compressed[chunk_offsets[c] + 8]);
        if (blocksize == 0) blocksize = BLK;
        if (blocksize != BLK) {
            printf("Sorry, only for 8192 internal blocks\n");
            free(chunk_p); free(chunk_rem); free(chunk_npx);
            return -101;
        }
        chunk_npx[c] = 0;
    }

    max_rem  = chunk_rem[0];
    i0 = 0;

    /* ---------- main block loop (interchanged when nchunks>1) ---------- */
    for ( ; max_rem >= BLK; max_rem -= BLK) {
        for (c = 0; c < nchunks; c++) {
            process_block_sparse(
                &compressed[chunk_offsets[c]],
                &chunk_p[c], &chunk_rem[c],
                mask, NIJ,
                (DATATYPE **)&output, (uint32_t **)&output_adr,
                &chunk_npx[c], threshold, i0);
        }
        i0 += BLK / NB;
    }

    /* Reset write pointers to per-chunk bases for partial-block pass */
    chunk_wr_outpx  = output  + 0;
    chunk_wr_outadr = output_adr + 0;

    /* ---------- partial final block per chunk ---------- */
    for (c = 0; c < nchunks; c++) {
        int rem = chunk_rem[c];
        if (rem <= 0) continue;
        blocksize = (8 * NB) * (rem / (8 * NB));
        if (blocksize > 0) {
            nbytes = READ32BE(&compressed[chunk_offsets[c] + chunk_p[c]]);
            ret = BS_DECOMPRESS(&compressed[chunk_offsets[c] + chunk_p[c] + 4],
                                nbytes, (char*)tmp1, blocksize);
            chunk_p[c] += nbytes + 4;
            if (unlikely(ret != blocksize)) {
                printf("ret %d blocksize %d\n", ret, blocksize);
                free(chunk_p); free(chunk_rem); free(chunk_npx);
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
            uint32_t val = mask[j + i0] * tmp2[j];
            if (unlikely(val > (uint32_t)threshold)) {
                *(chunk_wr_outpx++)  = tmp2[j];
                *(chunk_wr_outadr++) = j + i0;
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
    return total_npx;
}
```

---

## Step 2: `src/bs_sparse_csc_tmpl.c`

Replace the entire file.  The current file is 137 lines.  New version (~230 lines).

```c
/* bs_sparse_csc_tmpl.c - CSC sparse decompress template.
 *
 * Included from bs_master.c with DATATYPE, NB, KERNEL_CSC_FN,
 * CSC_DATA_T, CSC_SUM_T, BS_DECOMPRESS already defined.
 * Generates one function: KERNEL_CSC_FN().
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
                  uint32_t *restrict indptr,
                  const int64_t *restrict chunk_offsets,
                  const int32_t *restrict chunk_lengths,
                  int nchunks,
                  int32_t *restrict npx_per_chunk);

/* ------------------------------------------------------------------ */
static inline void process_block_csc(
    const uint8_t *restrict chunk_start,
    int *restrict ppos, int *restrict premaining,
    const uint8_t *restrict mask, int NIJ,
    DATATYPE **restrict pp_outpx, uint32_t **restrict pp_outadr,
    int *restrict pnpx, int threshold, int i0,
    CSC_SUM_T *restrict output, int NOUT,
    CSC_DATA_T *restrict data, uint32_t *restrict indices,
    uint32_t *restrict indptr)
{
    uint32_t nbytes;
    int j, ret;
    unsigned int k;
    DATATYPE val, cut, tmp1[BLK/NB], tmp2[BLK/NB];
#ifdef USE_KCB
    char scratch[BLK];
#endif

    cut = threshold;
    nbytes = READ32BE(&chunk_start[*ppos]);

    ret = BS_DECOMPRESS(&chunk_start[*ppos + 4], nbytes, (char*)tmp1, BLK);
    *ppos += nbytes + 4;
    *premaining -= BLK;
    if (unlikely(ret != BLK)) {
        printf("ret %d expected %d\n", ret, BLK);
        return;
    }

#ifdef USE_KCB
    bitshuf_decode_block((char*)tmp2, (char*)tmp1, scratch,
                         (size_t)(BLK/NB), (size_t)NB);
#else
    bshuf_untrans_bit_elem((void*)tmp1, (void*)tmp2,
                           (size_t)(BLK/NB), (size_t)NB);
#endif

    for (j = 0; j < BLK/NB; j++) {
        val = tmp2[j] * mask[j + i0];
        if (unlikely(val > 0)) {
            for (k = indptr[j + i0]; k < indptr[j + i0 + 1]; k++) {
                output[indices[k]] += ((CSC_SUM_T)data[k]) * (CSC_SUM_T)tmp2[j];
            }
            if (unlikely(tmp2[j] > cut)) {
                *(*pp_outpx)++  = tmp2[j];
                *(*pp_outadr)++ = j + i0;
                (*pnpx)++;
            }
        }
    }
}

/* ------------------------------------------------------------------ */
int KERNEL_CSC_FN(const uint8_t *restrict compressed, int compressed_length,
                  const uint8_t *restrict mask, int NIJ,
                  DATATYPE *restrict outpx, uint32_t *restrict output_adr,
                  int threshold,
                  CSC_SUM_T *restrict output, int NOUT,
                  CSC_DATA_T *restrict data, uint32_t *restrict indices,
                  uint32_t *restrict indptr,
                  const int64_t *restrict chunk_offsets,
                  const int32_t *restrict chunk_lengths,
                  int nchunks,
                  int32_t *restrict npx_per_chunk)
{
    int blocksize, c, j, ret;
    uint32_t nbytes;
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

    /* ---------- read headers, initialise per-chunk state ---------- */
    for (c = 0; c < nchunks; c++) {
        chunk_p[c] = 12;
        chunk_total = READ64BE(&compressed[chunk_offsets[c]]);
        chunk_rem[c] = (int)chunk_total;
        if (chunk_total / NB > (uint64_t)NIJ) {
            printf("Not enough output space, %zd %d\n", chunk_total, NIJ);
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

    /* ---------- zero histograms ---------- */
    for (c = 0; c < nchunks; c++)
        for (j = 0; j < NOUT; j++)
            output[c * (size_t)NOUT + j] = (CSC_SUM_T)0;

    max_rem = chunk_rem[0];
    i0 = 0;
    cut = threshold;

    /* ---------- main block loop (interchanged) ---------- */
    for ( ; max_rem >= BLK; max_rem -= BLK) {
        for (c = 0; c < nchunks; c++) {
            process_block_csc(
                &compressed[chunk_offsets[c]],
                &chunk_p[c], &chunk_rem[c],
                mask, NIJ,
                &chunk_wr_outpx[c], &chunk_wr_outadr[c],
                &chunk_npx[c], threshold, i0,
                output + c * (size_t)NOUT, NOUT,
                data, indices, indptr);
        }
        i0 += BLK / NB;
    }

    /* ---------- partial final block per chunk ---------- */
    for (c = 0; c < nchunks; c++) {
        int rem = chunk_rem[c];
        if (rem <= 0) continue;
        blocksize = (8 * NB) * (rem / (8 * NB));
        if (blocksize > 0) {
            nbytes = READ32BE(&compressed[chunk_offsets[c] + chunk_p[c]]);
            ret = BS_DECOMPRESS(&compressed[chunk_offsets[c] + chunk_p[c] + 4],
                                nbytes, (char*)tmp1, blocksize);
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
        for (j = 0; j < (rem + blocksize) / NB; j++) {
            val = tmp2[j] * mask[j + i0];
            if (unlikely(val > 0)) {
                for (k = indptr[j + i0]; k < indptr[j + i0 + 1]; k++) {
                    output[c * (size_t)NOUT + indices[k]] +=
                        ((CSC_SUM_T)data[k]) * (CSC_SUM_T)tmp2[j];
                }
                if (unlikely(tmp2[j] > cut)) {
                    *(chunk_wr_outpx[c]++)  = tmp2[j];
                    *(chunk_wr_outadr[c]++) = j + i0;
                    chunk_npx[c]++;
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
```

---

## Step 3: `generate_bslz4.py`

### 3a. Add `int32_t` format helper to the PIXEL_TYPES / imports

No changes needed in PIXEL_TYPES or imports.  The `npx_per_chunk` format `'i'`
is already understood by c2py23.

### 3b. Update `make_basic_fn_name` and `make_csc_fn_name` -- NO CHANGE

The function names on the C side don't change.  Only the parameter list changes.

### 3c. Update `generate_bs_functions_h()`

In the for-loops at lines ~319-353, change the C forward declaration strings.

**Basic decompress** (line ~325):
```python
lines.append(
    "int {fn}(const uint8_t *restrict compressed, "
    "int compressed_length, "
    "const uint8_t *restrict mask, int NIJ, "
    "{dt} *restrict output, uint32_t *restrict output_adr, "
    "int threshold, "
    "const int64_t *restrict chunk_offsets, "
    "const int32_t *restrict chunk_lengths, "
    "int nchunks, "
    "int32_t *restrict npx_per_chunk);".format(fn=fn_basic, dt=datatype)
)
```

**CSC** (line ~342):
```python
lines.append(
    "int {fn}(const uint8_t *restrict compressed, "
    "int compressed_length, "
    "const uint8_t *restrict mask, int NIJ, "
    "{dt} *restrict outpx, uint32_t *restrict output_adr, "
    "int threshold, "
    "{sum} *restrict output, int NOUT, "
    "{cscdt} *restrict data, uint32_t *restrict indices, "
    "uint32_t *restrict indptr, "
    "const int64_t *restrict chunk_offsets, "
    "const int32_t *restrict chunk_lengths, "
    "int nchunks, "
    "int32_t *restrict npx_per_chunk);".format(
        fn=fn_csc, dt=datatype, sum=sumtype,
        cscdt=cscdatatype)
)
```

### 3d. Update `_py_sig_entry_basic()` (lines ~375-409)

Change the py_sig and checks.  Here is the exact replacement for the
`_py_sig_entry_basic` function:

```python
def _py_sig_entry_basic(prefix, dtshort, py_format):
    """Generate a c2py23 basic decompress function entry."""
    fn_name = "{}_{}".format(prefix, dtshort)
    lines = []
    lines.append("")
    lines.append('  - py_sig: "{}'.format(fn_name) +
                 '(compressed: buffer, mask: buffer, '
                 'out: buffer, outP: buffer, thresh: int, '
                 'chunk_offsets: buffer, chunk_lengths: buffer, '
                 'npx_per_chunk: buffer) -> int"')
    if prefix == "bslz4":
        eng_label = "LZ4"
    else:
        eng_label = "ZSTD"
    lines.append('    doc: "{} decompress + unshuffle to sparse '
                 '({} pixels). Returns total npx."'.format(eng_label, dtshort))
    lines.append('    checks:')
    lines.append('      - "compressed.format == \'B\'"')
    lines.append('      - "mask.format == \'B\'"')
    lines.append('      - "out.format == \'{}\'"'.format(py_format))
    lines.append('      - "outP.format == \'I\'"')
    lines.append('      - "chunk_offsets.format == \'q\'"')
    lines.append('      - "chunk_lengths.format == \'i\'"')
    lines.append('      - "npx_per_chunk.format == \'i\'"')
    lines.append('      - "chunk_offsets.n == chunk_lengths.n"')
    lines.append('      - "chunk_offsets.n == npx_per_chunk.n"')
    lines.append('    gil_release: true')
    lines.append('    c_overloads:')
    when = ('      - when: "compressed.format == \'B\' and '
            'mask.format == \'B\' and out.format == \'{pf}\' '
            'and outP.format == \'I\' '
            'and chunk_offsets.format == \'q\' '
            'and chunk_lengths.format == \'i\' '
            'and npx_per_chunk.format == \'i\'"'.format(pf=py_format))
    lines.append(when)
    lines.append('        map: {compressed: "compressed.ptr", '
                 'compressed_length: "compressed.shape[0]", '
                 'mask: "mask.ptr", NIJ: "mask.shape[0]", '
                 'output: "out.ptr", output_adr: "outP.ptr", '
                 'threshold: thresh, '
                 'chunk_offsets: "chunk_offsets.ptr", '
                 'chunk_lengths: "chunk_lengths.ptr", '
                 'nchunks: "chunk_offsets.shape[0]", '
                 'npx_per_chunk: "npx_per_chunk.ptr"}')
    lines.append('        group: {}'.format(fn_name))

    return lines
```

### 3e. Update `_py_sig_variants_basic()` (lines ~412-433)

Append the 4 new params to the C signature string.  Replace the sig line:

```python
def _py_sig_variants_basic(prefix, dtshort):
    """Generate the variants block for a basic decompress function."""
    px = [p for p in PIXEL_TYPES if p["dtshort"] == dtshort][0]
    datatype = px["datatype"]

    lines = []
    lines.append('        variants:')
    for bk in BACKENDS:
        bkd = bk["suffix"]
        for isa in ISAS:
            isa_s = isa["suffix"]
            fn_name = make_basic_fn_name(prefix, dtshort, bkd, isa_s)
            name = "{}_{}".format(bkd, isa_s)
            sig = ("int {fn}(const uint8_t *compressed, int compressed_length, "
                   "const uint8_t *mask, int NIJ, "
                   "{dt} *output, uint32_t *output_adr, "
                   "int threshold, "
                   "const int64_t *chunk_offsets, "
                   "const int32_t *chunk_lengths, "
                   "int nchunks, "
                   "int32_t *npx_per_chunk) -> int".format(fn=fn_name, dt=datatype))
            lines.append('          - name: "{}"'.format(name))
            lines.append('            sig: "{}"'.format(sig))
            if isa["when_cond"]:
                lines.append('            when: "{}"'.format(isa["when_cond"]))
    return lines
```

### 3f. Update `_py_sig_entry_csc()` (lines ~436-507)

Replace the function:

```python
def _py_sig_entry_csc(prefix, dtshort, csc, py_format):
    """Generate a c2py23 CSC function entry."""
    cscshort = csc["cscshort"]
    cformat = csc["cformat"]
    sformat = csc["sformat"]
    fn_name = make_py_fn_name(prefix, dtshort, cscshort)

    if csc["is_float"]:
        type_desc = "float"
    elif cformat == "B":
        type_desc = "uint8"
    elif cformat == "H":
        type_desc = "uint16"
    else:
        type_desc = "uint32"

    if prefix == "bslz4":
        eng_label = "LZ4"
    else:
        eng_label = "ZSTD"

    lines = []
    lines.append("")
    lines.append('  - py_sig: "{}'.format(fn_name) +
                 '(compressed: buffer, mask: buffer, '
                 'outpx: buffer, outP: buffer, thresh: int, '
                 'out: buffer, data: buffer, '
                 'indices: buffer, indptr: buffer, '
                 'chunk_offsets: buffer, chunk_lengths: buffer, '
                 'npx_per_chunk: buffer) -> int"')
    lines.append('    doc: "{} decompress + unshuffle + CSC accumulate '
                 '({} CSC data, {} pixels). Returns total npx."'.format(
                     eng_label, type_desc, dtshort))
    lines.append('    checks:')
    lines.append('      - "compressed.format == \'B\'"')
    lines.append('      - "mask.format == \'B\'"')
    lines.append('      - "outpx.format == \'{}\'"'.format(py_format))
    lines.append('      - "outP.format == \'I\'"')
    if csc["is_float"]:
        lines.append('      - "out.format == \'d\'"')
        lines.append('      - "data.format == \'f\'"')
        out_check = 'out.format == \'d\''
        data_check = 'data.format == \'f\''
    else:
        lines.append('      - "out.format == \'Q\' or out.format == \'L\'"')
        lines.append('      - "data.format == \'{}\'"'.format(cformat))
        out_check = "out.format == 'Q' or out.format == 'L'"
        data_check = "data.format == '{}'".format(cformat)
    lines.append('      - "indices.format == \'I\'"')
    lines.append('      - "indptr.format == \'I\'"')
    lines.append('      - "chunk_offsets.format == \'q\'"')
    lines.append('      - "chunk_lengths.format == \'i\'"')
    lines.append('      - "npx_per_chunk.format == \'i\'"')
    lines.append('      - "chunk_offsets.n == chunk_lengths.n"')
    lines.append('      - "chunk_offsets.n == npx_per_chunk.n"')
    lines.append('    gil_release: true')
    lines.append('    c_overloads:')

    when = ('      - when: "compressed.format == \'B\' and '
            'mask.format == \'B\' and outpx.format == \'{pf}\' '
            'and outP.format == \'I\' '
            'and {oc} and {dc} '
            'and indices.format == \'I\' and indptr.format == \'I\' '
            'and chunk_offsets.format == \'q\' '
            'and chunk_lengths.format == \'i\' '
            'and npx_per_chunk.format == \'i\'"'.format(
                pf=py_format, oc=out_check, dc=data_check))
    lines.append(when)
    lines.append('        map: {compressed: "compressed.ptr", '
                 'compressed_length: "compressed.shape[0]", '
                 'mask: "mask.ptr", NIJ: "mask.shape[0]", '
                 'outpx: "outpx.ptr", output_adr: "outP.ptr", '
                 'threshold: thresh, '
                 'output: "out.ptr", NOUT: "out.shape[0]", '
                 'data: "data.ptr", indices: "indices.ptr", '
                 'indptr: "indptr.ptr", '
                 'chunk_offsets: "chunk_offsets.ptr", '
                 'chunk_lengths: "chunk_lengths.ptr", '
                 'nchunks: "chunk_offsets.shape[0]", '
                 'npx_per_chunk: "npx_per_chunk.ptr"}')
    lines.append('        group: {}'.format(fn_name))

    return lines
```

Note: for CSC functions with multi-chunk, the caller passes `out` as a 1D buffer
with shape `(nchunks * NOUT,)`, so `NOUT = out.shape[0] / nchunks`.  The c2py23
check for `out` cannot enforce this division at check time (nchunks is computed
from chunk_offsets.shape[0] inside the map), so the shape check is left to the
caller.  The C code uses `output + c * NOUT` to index.

### 3g. Update `_py_sig_variants_csc()` (lines ~510-538)

Append the 4 new params to the C signature string:

```python
def _py_sig_variants_csc(prefix, dtshort, csc):
    """Generate the variants block for a CSC function."""
    cscshort = csc["cscshort"]
    cscdatatype = csc["cscdatatype"]
    sumtype = csc["sumtype"]

    px = [p for p in PIXEL_TYPES if p["dtshort"] == dtshort][0]
    datatype = px["datatype"]

    lines = []
    lines.append('        variants:')
    for bk in BACKENDS:
        bkd = bk["suffix"]
        for isa in ISAS:
            isa_s = isa["suffix"]
            fn_name = make_csc_fn_name(prefix, dtshort, cscshort, bkd, isa_s)
            name = "{}_{}".format(bkd, isa_s)
            sig = ("int {fn}(const uint8_t *compressed, int compressed_length, "
                   "const uint8_t *mask, int NIJ, "
                   "{dt} *outpx, uint32_t *output_adr, int threshold, "
                   "{sum} *output, int NOUT, "
                   "{cscdt} *data, uint32_t *indices, "
                   "uint32_t *indptr, "
                   "const int64_t *chunk_offsets, "
                   "const int32_t *chunk_lengths, "
                   "int nchunks, "
                   "int32_t *npx_per_chunk) -> int".format(
                       fn=fn_name, dt=datatype, sum=sumtype, cscdt=cscdatatype))
            lines.append('          - name: "{}"'.format(name))
            lines.append('            sig: "{}"'.format(sig))
            if isa["when_cond"]:
                lines.append('            when: "{}"'.format(isa["when_cond"]))
    return lines
```

---

## Step 4: Run the generator

```bash
cd /home/worker/c2ImageD11
python3 generate_bslz4.py            # regenerates the 3 output files
python3 generate_bslz4.py --check    # verify all 3 pass
```

This writes:
- `src/bs_functions.h`  (180 forward declarations, updated)
- `src/bs_master.c`     (unchanged; includes the templates)
- `_cImageD11_bslz4.c2py` (30 Python function defs, updated)

---

## Step 5: `c2ImageD11/bslz4.py` -- Python wrapper

### 5a. `chunk2sparse.__init__` and `__call__`

Update `__init__` (around line 104) to create single-element default arrays:

```python
def __init__(self, mask, dtype=np.uint16):
    self.nfast = mask.shape[1]
    self.mask = mask.ravel()
    self.indices = np.empty(mask.size, np.uint32)
    self.values = np.empty(mask.size, dtype)
    self.dtype = dtype
    itemsize = np.dtype(dtype).itemsize
    self.fun = (
        None,
        bslz4_u8,
        bslz4_u16,
        None,
        bslz4_u32,
    )[itemsize]
    self._offsets  = np.array([0], dtype=np.int64)
    self._lengths  = np.zeros(1, dtype=np.int32)
    self._npx_pc   = np.zeros(1, dtype=np.int32)
```

Update `__call__` (around line 119):

```python
def __call__(self, buffer, cut):
    self._lengths[0] = len(buffer)
    npixels = self.fun(buffer, self.mask,
                       self.values, self.indices, cut,
                       self._offsets, self._lengths, self._npx_pc)
    return npixels, (self.values, self.indices)
```

### 5b. `chunk2sparseCSC.__init__` and `__call__`

Update `__init__` (around line 200) -- add the 3 single-element arrays at the end:

```python
def __init__(self, mask, csc, dtype=np.uint16):
    # ... existing setup (lines 200-222, unchanged) ...
    self._offsets  = np.array([0], dtype=np.int64)
    self._lengths  = np.zeros(1, dtype=np.int32)
    self._npx_pc   = np.zeros(1, dtype=np.int32)
```

Update `__call__` (lines 224-241):

```python
def __call__(self, buffer, cut):
    self._lengths[0] = len(buffer)
    npixels = self.fun(
        buffer,
        self.mask,
        self.values,
        self.indices,
        cut,
        self.powder,
        self.cscdata,
        self.cscindices,
        self.cscindptr,
        self._offsets,
        self._lengths,
        self._npx_pc,
    )
    return npixels, (self.values, self.indices), self.powder
```

### 5c. New `chunk2sparseCSC.multi` method

Add after the `coo` method (before `bslz4_to_sparse`, around line 250):

```python
def multi(self, file_buffer, offsets, lengths, cut=0, nframes=None):
    """Process N frames with loop interchange.

    Parameters
    ----------
    file_buffer : ndarray
        Memory-mapped HDF5 file as uint8 flat buffer (from numpy.memmap).
    offsets : ndarray
        Byte offsets of each chunk (int64, shape [N]).
    lengths : ndarray
        Compressed lengths of each chunk (int32, shape [N]).
    cut : int
        Threshold.  Default 0.
    nframes : int, optional
        Number of frames to process.  Default: len(offsets).

    Returns
    -------
    powder : ndarray (nframes, nbins)
        Per-frame powder histograms.  Dtype matches self.powder.
    """
    if nframes is None:
        nframes = len(offsets)
    if nframes > len(offsets):
        raise ValueError(
            "nframes=%d > len(offsets)=%d" % (nframes, len(offsets)))
    nout = len(self.powder)
    nij  = len(self.mask)
    powder = np.zeros(nframes * nout, dtype=self.powder.dtype)

    outpx   = np.zeros(nframes * nij, dtype=self.values.dtype)
    outadr  = np.zeros(nframes * nij, dtype=np.uint32)
    npx_pc  = np.zeros(nframes, dtype=np.int32)

    off = offsets[:nframes]
    le  = lengths[:nframes]

    total_npx = self.fun(
        file_buffer,
        self.mask,
        outpx, outadr, cut,
        powder, self.cscdata, self.cscindices, self.cscindptr,
        off, le, npx_pc,
    )

    powder_2d = powder.reshape((nframes, nout))
    return powder_2d
```

### 5d. Import list

In the import block at the top of `bslz4.py` (lines 23-30), the existing imports
are fine.  The function signatures are the same names; c2py23 wraps them
transparently with the new parameters.

---

## Step 6: Tests

### 6a. Update existing tests

The existing tests in `tests/test_bslz4.py` call bslz4 functions directly.
Each call must now pass 3 extra arrays.  Find every call site like:

```python
bslz4_u16(compressed, mask, out, outP, thresh)
```

and change to:

```python
offs = np.array([0], dtype=np.int64)
lens = np.array([len(compressed)], dtype=np.int32)
npc  = np.zeros(1, dtype=np.int32)
npx = bslz4_u16(compressed, mask, out, outP, thresh, offs, lens, npc)
```

Similarly for bszstd and CSC variants:

```python
offs = np.array([0], dtype=np.int64)
lens = np.array([len(compressed)], dtype=np.int32)
npc  = np.zeros(1, dtype=np.int32)
npx = bslz4_csc_u16(compressed, mask, outpx, outP, thresh,
                     out, data, indices, indptr, offs, lens, npc)
npx = bslz4_csc_u16_cu8(compressed, mask, outpx, outP, thresh,
                          out, data, indices, indptr, offs, lens, npc)
npx = bszstd_csc_u16(compressed, mask, outpx, outP, thresh,
                       out, data, indices, indptr, offs, lens, npc)
npx = bszstd_csc_u16_cu8(compressed, mask, outpx, outP, thresh,
                           out, data, indices, indptr, offs, lens, npc)
```

### 6b. Add multi-chunk smoke test

Add at the end of `tests/test_bslz4.py`:

```python
def test_csc_multi_chunk_u16():
    """Multi-chunk CSC with 3 frames: each frame gives same powder."""
    import c2ImageD11._cImageD11 as _m

    nframes = 3
    nij = 256*4
    nout = 16

    # Build toy CSC matrix (one entry per pixel, sequential assignment)
    data = np.ones(nij, dtype=np.float32)
    indices = np.arange(nij, dtype=np.uint32) % nout
    indptr = np.arange(nij + 1, dtype=np.uint32)

    mask = np.ones(nij, dtype=np.uint8)
    mask[:100] = 0
    mask[-100:] = 0

    # Build one compressed chunk
    from c2ImageD11._cImageD11 import bslz4_csc_u16
    import lz4.block
    import bitshuffle

    # Create raw uint16 data: 3 different frames
    rng = np.random.RandomState(42)
    pix = rng.randint(0, 33, size=(nframes, nij), dtype=np.uint16)

    chunks = []
    for f in range(nframes):
        raw = pix[f].copy()
        raw[:100] = 0
        raw[-100:] = 0
        bshuf = bitshuffle.compress_lz4(raw).tobytes()
        chunks.append(np.frombuffer(bshuf, dtype=np.uint8))

    clen = len(chunks[0])
    for c in chunks:
        assert len(c) == clen, "all chunks must have same compressed length"

    # Concatenate into a single buffer
    bigbuf = np.concatenate(chunks)
    offsets = np.array([0, clen, 2*clen], dtype=np.int64)
    lengths = np.array([clen, clen, clen], dtype=np.int32)
    npx_pc  = np.zeros(nframes, dtype=np.int32)

    powder = np.zeros(nframes * nout, dtype=np.float64)
    outpx  = np.zeros(nframes * nij, dtype=np.uint16)
    outP   = np.zeros(nframes * nij, dtype=np.uint32)

    total_npx = bslz4_csc_u16(bigbuf, mask, outpx, outP, 0,
                               powder, data, indices, indptr,
                               offsets, lengths, npx_pc)

    assert total_npx > 0
    for f in range(nframes):
        assert npx_pc[f] > 0

    # Verify per-frame powder matches single-chunk call
    powder_2d = powder.reshape((nframes, nout))
    for f in range(nframes):
        single_pow = np.zeros(nout, dtype=np.float64)
        single_outpx = np.zeros(nij, dtype=np.uint16)
        single_outP  = np.zeros(nij, dtype=np.uint32)
        single_npx_pc = np.zeros(1, dtype=np.int32)
        s_offs = np.array([0], dtype=np.int64)
        s_lens = np.array([clen], dtype=np.int32)

        bslz4_csc_u16(chunks[f], mask, single_outpx, single_outP, 0,
                       single_pow, data, indices, indptr,
                       s_offs, s_lens, single_npx_pc)

        np.testing.assert_allclose(powder_2d[f], single_pow,
                                   err_msg="powder mismatch frame %d" % f)


def test_sparse_multi_chunk_u16():
    """Multi-chunk basic sparse decompress with 3 frames."""
    import c2ImageD11._cImageD11 as _m

    nframes = 3
    nij = 256
    mask = np.ones(nij, dtype=np.uint8)
    mask[:10] = 0

    from c2ImageD11._cImageD11 import bslz4_u16
    import bitshuffle

    rng = np.random.RandomState(123)
    pix = rng.randint(0, 65535, size=(nframes, nij), dtype=np.uint16)
    pix[:, :10] = 0

    chunks = []
    for f in range(nframes):
        raw = pix[f].copy()
        bshuf = bitshuffle.compress_lz4(raw).tobytes()
        chunks.append(np.frombuffer(bshuf, dtype=np.uint8))

    clen = len(chunks[0])
    bigbuf = np.concatenate(chunks)
    offsets = np.array([0, clen, 2*clen], dtype=np.int64)
    lengths = np.array([clen, clen, clen], dtype=np.int32)
    npx_pc  = np.zeros(nframes, dtype=np.int32)

    out   = np.zeros(nframes * nij, dtype=np.uint16)
    outP  = np.zeros(nframes * nij, dtype=np.uint32)

    total_npx = bslz4_u16(bigbuf, mask, out, outP, 0,
                           offsets, lengths, npx_pc)

    assert total_npx > 0
    for f in range(nframes):
        assert npx_pc[f] > 0
        # Verify values are in expected range
        vals_f = out[f * nij : f * nij + npx_pc[f]]
        assert np.all(vals_f > 0)
        assert np.all(vals_f <= 65535)
```

---

## Step 7: Build and verify

```bash
cd /home/worker/c2ImageD11

# Clean previous build artifacts
rm -rf build/

# Build (setup.py assembles .c2py, compiles templates, links)
python3 setup.py build_ext --inplace

# Run the tests
python3 -m pytest tests/test_bslz4.py -v -x

# Run full test suite
python3 -m pytest tests/ -v -x

# Verify generated files are in sync
python3 generate_bslz4.py --check
```

Expected test results:
- All existing bslz4 smoke tests pass (function signatures updated)
- `test_csc_multi_chunk_u16` passes
- `test_sparse_multi_chunk_u16` passes
- No regressions in `test_buffer.py` or `test_equivalence.py`

---

## Common Pitfalls

1. **Forgetting to pass the 3 new arrays in existing test calls**.  Every call to
   `bslz4_u*`, `bszstd_u*`, `bslz4_csc_*`, `bszstd_csc_*` must include
   `offsets`, `lengths`, `npx_per_chunk`.

2. **Wrong dtypes for the new arrays**: `offsets` must be `int64` (`'q'`/`np.int64`),
   `lengths` must be `int32` (`'i'`/`np.int32`), `npx_per_chunk` must be `int32`.

3. **`compressed_length` is still in the signature** but is unused in multi-chunk
   mode.  The Python side always passes `compressed.shape[0]` (the total buffer
   length).  For single-chunk this is the chunk length; for multi-chunk this is
   the entire file buffer length but the C code ignores it and uses
   `chunk_lengths[c]` instead.

4. **The c2py23 `map:` expression defines `nchunks: "chunk_offsets.shape[0]"`.**
   This means `nchunks` is derived from the buffer dimension at runtime.  The
   generator must use exactly this expression for every function.

5. **`bs_master.c` does not need changes.**  It only `#includes` the templates;
   the templates define their own inline functions.

6. **CSC output `out.shape[0]` must equal `nchunks * NOUT`.**  The c2py23 checks
   cannot verify this at the when-clause level (nchunks is computed inside the
   map expression), so the Python caller is responsible for passing the correct
   shape.  A mismatch will cause out-of-bounds writes in C.

7. **The inline function uses `static inline`** which is supported by GCC, Clang,
   and MSVC (as `static __inline` or just `static` with optimisation).
   The existing codebase already uses `inline` qualifiers.

---

## Verification Checklist After Implementation

- [ ] `python3 generate_bslz4.py --check` passes
- [ ] `python3 setup.py build_ext --inplace` succeeds with no warnings
- [ ] All existing tests in `tests/test_bslz4.py` pass
- [ ] `tests/test_buffer.py` passes
- [ ] `tests/test_equivalence.py` passes
- [ ] `test_csc_multi_chunk_u16` passes (multi-chunk powder matches single-chunk)
- [ ] `test_sparse_multi_chunk_u16` passes (multi-chunk sparse output correct)
- [ ] All generated files committed: `src/bs_functions.h`, `_cImageD11_bslz4.c2py`
- [ ] `src/bs_master.c` is unchanged (verify with `git diff src/bs_master.c`)
