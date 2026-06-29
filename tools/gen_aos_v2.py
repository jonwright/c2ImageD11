#!/usr/bin/env python3
"""gen_aos_v2.py — generate AoS v2 kernels with wide-load+permute deinterleave."""

import os

SADIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "lib", "functions", "score_and_assign")

def compute_indices(N, SIMD, comp):
    """Return (r1_indices, r2_indices) for component comp of N AoS triples."""
    comp_idxs = [i * 3 + comp for i in range(N)]
    
    mapped = [(i // SIMD, i % SIMD) for i in comp_idxs]
    
    r1 = []
    for ln, el in mapped:
        if ln == 0:
            r1.append(el)
        elif ln == 1:
            r1.append(el + SIMD)
        else:
            r1.append(0)
    while len(r1) < SIMD:
        r1.append(0)
    r1 = r1[:SIMD]
    
    r2 = []
    for ln, el in mapped:
        if ln <= 1:
            r2.append(r2.count  if False else 0)  # placeholder
    
    r2 = []
    for idx, (ln, el) in enumerate(mapped):
        if ln <= 1:
            # Count how many came before from loads 0-1
            before = sum(1 for j in range(idx) if mapped[j][0] <= 1)
            r2.append(before)
        else:
            r2.append(el + SIMD)
    while len(r2) < SIMD:
        r2.append(0)
    r2 = r2[:SIMD]
    
    return r1, r2


kernel_template = r"""/* {basename}.c -- Wide-load + permute deinterleave AoS {type} {isa}
 *
 * Replaces {scalar_loads} scalar-gather loads per iteration with
 * {num_loads} wide loads + {num_permutes} {permute_intrinsic} permutes.
 *
 * C2PY_BEGIN
 * {{
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "c_overloads": [{{
 *         "when": "ubi.format == 'd' and gv.format == '{fmt}' and gv.shape[1] == 3 and gv.slow_axis == 0 and c2py_amd64_{isa}",
 *         "sig": "int {func_name}(double ubi[3][3], const {ctype} gv[], double tol, {dtype} *drlv2, int *labels, int label, intptr_t ng) -> int",
 *         "map": {{"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "drlv2": "drlv2.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[0]"}},
 *     }}],
 * }}
 * C2PY_END */

#include <immintrin.h>
#include "../score_and_refine/sar_popcnt.h"
#include <stdint.h>
#include <math.h>
#ifdef _OPENMP
#include <omp.h>
#endif

{permute_indices}

static int
{static_func}(const double ubi[9], const {ctype} *gv, double tol,
             {dtype} *drlv2, int *labels, int label, intptr_t ng)
{{
    {u_broadcasts}
    {tvec}
    {lbl_vec}
    {load_indices}
    int n=0; intptr_t k;

    for(k=0;k+{N}<=ng;k+={N}){{
        {load_code}
        {permute_code}
        {fma_code}
        {round_code}
        {sumsq_code}

        {cur_load}
        {mask_code}

        {label_simd}

        if(mask){{
            n+=popcnt32((unsigned)mask);
            {drlv2_store}
        }}
    }}

    double tol2=tol*tol;
    for(;k<ng;k++){{
        {ctype_val} gx=gv[k*3],gy=gv[k*3+1],gz=gv[k*3+2];
        {ctype_val} hx_=ubi[0]*gx+ubi[1]*gy+ubi[2]*gz; {ctype_val} ix={nearbyint}(hx_);
        {ctype_val} hy_=ubi[3]*gx+ubi[4]*gy+ubi[5]*gz; {ctype_val} iy={nearbyint}(hy_);
        {ctype_val} hz_=ubi[6]*gx+ubi[7]*gy+ubi[8]*gz; {ctype_val} iz={nearbyint}(hz_);
        {ctype_val} s=(hx_-ix)*(hx_-ix)+(hy_-iy)*(hy_-iy)+(hz_-iz)*(hz_-iz);
        if(s<tol2&&s<drlv2[k]){{labels[k]=label;drlv2[k]=s;n++;}}
        else if(labels[k]==label)labels[k]=-1;
    }}
    return n;
}}

int {func_name}(double ubi[3][3], const {ctype} gv[], double tol,
                {dtype} *drlv2, int *labels, int label, intptr_t ng)
{{
    int n=0;
#ifdef _OPENMP
    int nthr=omp_get_max_threads();
    if(ng>10000&&nthr>1){{
        #pragma omp parallel reduction(+:n)
        {{ int tid=omp_get_thread_num(); intptr_t chunk=(ng+nthr-1)/nthr,start=tid*chunk;
          intptr_t end=(start+chunk<ng)?start+chunk:ng;
          if(start<ng)n={static_func}((const double*)ubi,gv+start*3,tol,drlv2+start,labels+start,label,end-start);}}
        return n;}}
#endif
    return {static_func}((const double*)ubi,gv,tol,drlv2,labels,label,ng);
}}
"""


def gen_one(basename, N, SIMD, isa, ctype, dtype, set1_suffix, ctype_val, nearbyint,
            permute_intrinsic, scalar_loads, num_loads):
    """Generate one AoS v2 kernel."""
    type_label = "f64" if ctype == "double" else "f32"
    fmt = "d" if ctype == "double" else "f"
    func_name = "score_and_assign_{}_aos_{}_v2".format(type_label, isa.replace("f", ""))
    static_func = "sa_{}_aos_{}_v2_kernel".format(type_label, isa.replace("f", ""))
    
    # Generate permute index arrays
    idx_code = ""
    for comp in range(3):
        r1, r2 = compute_indices(N, SIMD, comp)
        comp_name = ['X', 'Y', 'Z'][comp]
        idx_list1 = ", ".join(str(v) for v in r1)
        idx_list2 = ", ".join(str(v) for v in r2)
        idx_code += "static const int{idx_bits}_t I1{comp}[{SIMD}] __attribute__((aligned(64))) = {{{idx1}}};\n".format(
            idx_bits=32 if dtype == "float" else 64, comp=comp_name, SIMD=SIMD, idx1=idx_list1)
        idx_code += "static const int{idx_bits}_t I2{comp}[{SIMD}] __attribute__((aligned(64))) = {{{idx2}}};\n".format(
            idx_bits=32 if dtype == "float" else 64, comp=comp_name, SIMD=SIMD, idx2=idx_list2)
    
    # Load indices
    load_indices = ""
    for comp in range(3):
        comp_name = ['X', 'Y', 'Z'][comp]
        load_indices += "{loadi} idx1{comp}=_{load}(I1{comp}), idx2{comp}=_{load}(I2{comp});\n".format(
            loadi="__m512i" if SIMD >= 16 else "__m256i",
            comp=comp_name,
            load="mm512_load_si512" if SIMD >= 16 else "mm256_load_si256")
    
    # Load code
    load_code = ""
    for i in range(num_loads):
        load_code += "        {vec} d{i}=_{loadu}(&gv[k*3+{off}]);\n".format(
            vec="__m512d" if ctype == "double" and SIMD >= 8 else 
                "__m512" if ctype == "float" and SIMD >= 16 else
                "__m256d" if ctype == "double" else "__m256",
            i=i,
            loadu="mm512_loadu_pd" if ctype == "double" and SIMD >= 8 else
                  "mm512_loadu_ps" if ctype == "float" and SIMD >= 16 else
                  "mm256_loadu_pd" if ctype == "double" else "mm256_loadu_ps",
            off=i * SIMD)
    
    # Permute code
    permute_code = ""
    for comp in range(3):
        comp_name = ['X', 'Y', 'Z'][comp]
        permute_code += "        {vec} tmp_{c}=_{perm}(d0, idx1{c}, d1);\n".format(
            vec="__m512d" if ctype == "double" and SIMD >= 8 else
                "__m512" if ctype == "float" and SIMD >= 16 else
                "__m256d" if ctype == "double" else "__m256",
            c=comp_name.lower(),
            perm=permute_intrinsic)
        permute_code += "        {vec} gv{c}=_{perm}(tmp_{c}, idx2{c}, d2);\n".format(
            vec="__m512d" if ctype == "double" and SIMD >= 8 else
                "__m512" if ctype == "float" and SIMD >= 16 else
                "__m256d" if ctype == "double" else "__m256",
            c=comp_name.lower(),
            perm=permute_intrinsic)
    
    # Rest of the template
    u_broadcasts = ""
    for i in range(3):
        for j in range(3):
            u_broadcasts += "{vec} u{i}{j}=_{set1}(ubi[{off}]);".format(
                vec="__m512d" if ctype == "double" and SIMD >= 8 else
                    "__m512" if ctype == "float" and SIMD >= 16 else
                    "__m256d" if ctype == "double" else "__m256",
                i=i, j=j,
                set1="mm512_set1_pd" if ctype == "double" and SIMD >= 8 else
                     "mm512_set1_ps" if ctype == "float" and SIMD >= 16 else
                     "mm256_set1_pd" if ctype == "double" else "mm256_set1_ps",
                off=i*3+j)
        u_broadcasts = u_broadcasts.rstrip() + "\n    "
    
    tvec = "{vec} tvec=_{set1}(tol*tol);".format(
        vec="__m512d" if ctype == "double" and SIMD >= 8 else
            "__m512" if ctype == "float" and SIMD >= 16 else
            "__m256d" if ctype == "double" else "__m256",
        set1="mm512_set1_pd" if ctype == "double" and SIMD >= 8 else
             "mm512_set1_ps" if ctype == "float" and SIMD >= 16 else
             "mm256_set1_pd" if ctype == "double" else "mm256_set1_ps")
    
    # Label vec: f64 uses __m256i (4 int32) for AVX2, __m256i (8 int32) for AVX-512
    # f32 uses __m128i (4 int32) for AVX2... wait, no. For f64 with 8 lanes (AVX-512): 8 int32 labels → __m256i
    # For f64 with 4 lanes (AVX2): 4 int32 labels → __m128i
    # For f32 with 16 lanes (AVX-512): 16 int32 labels → __m512i (use AVX-512 mask ops)
    # For f32 with 8 lanes (AVX2): 8 int32 labels → __m256i
    is_avx512 = "512" in isa
    
    if is_avx512:
        lbl_vec_width = 256 if ctype == "double" else 512
        lbl_vec = "__m{0}i lbl_vec=_{0}_set1_epi32(label), neg=_{0}_set1_epi32(-1);".format(
            lbl_vec_width,
            lbl_vec_width)
    else:
        lbl_vec_width = 128 if ctype == "double" else 256
        lbl_vec = "__m{0}i lbl_vec=_{0}_set1_epi32(label), neg=_{0}_set1_epi32(-1);".format(
            lbl_vec_width,
            lbl_vec_width)
    
    fma_code = """        {vec} hx=_{fmadd}(u00,gvx,_{fmadd}(u01,gvy,_{mul}(u02,gvz)));
        {vec} hy=_{fmadd}(u10,gvx,_{fmadd}(u11,gvy,_{mul}(u12,gvz)));
        {vec} hz=_{fmadd}(u20,gvx,_{fmadd}(u21,gvy,_{mul}(u22,gvz)));""".format(
        vec="__m512d" if ctype == "double" and SIMD >= 8 else
            "__m512" if ctype == "float" and SIMD >= 16 else
            "__m256d" if ctype == "double" else "__m256",
        fmadd="mm512_fmadd_pd" if ctype == "double" and SIMD >= 8 else
              "mm512_fmadd_ps" if ctype == "float" and SIMD >= 16 else
              "mm256_fmadd_pd" if ctype == "double" else "mm256_fmadd_ps",
        mul="mm512_mul_pd" if ctype == "double" and SIMD >= 8 else
            "mm512_mul_ps" if ctype == "float" and SIMD >= 16 else
            "mm256_mul_pd" if ctype == "double" else "mm256_mul_ps")
    
    if is_avx512 and ctype == "double":
        round_code = """        {vec} ihx=_{round}(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hx=_{sub}(hx,ihx);
        {vec} ihy=_{round}(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hy=_{sub}(hy,ihy);
        {vec} ihz=_{round}(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hz=_{sub}(hz,ihz);""".format(
            vec="__m512d",
            round="mm512_roundscale_pd",
            sub="mm512_sub_pd")
    elif is_avx512:
        round_code = """        {vec} ihx=_{round}(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hx=_{sub}(hx,ihx);
        {vec} ihy=_{round}(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hy=_{sub}(hy,ihy);
        {vec} ihz=_{round}(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hz=_{sub}(hz,ihz);""".format(
            vec="__m512",
            round="mm512_roundscale_ps",
            sub="mm512_sub_ps")
    elif ctype == "double":
        round_code = """        {vec} ihx=_{round}(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC), ihy=_{round}(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC), ihz=_{round}(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        {vec} tx=_{sub}(hx,ihx),ty=_{sub}(hy,ihy),tz=_{sub}(hz,ihz);""".format(
            vec="__m256d",
            round="mm256_round_pd",
            sub="mm256_sub_pd")
    else:
        round_code = """        {vec} ihx=_{round}(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC), ihy=_{round}(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC), ihz=_{round}(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        {vec} tx=_{sub}(hx,ihx),ty=_{sub}(hy,ihy),tz=_{sub}(hz,ihz);""".format(
            vec="__m256",
            round="mm256_round_ps",
            sub="mm256_sub_ps")
    
    sumsq_var = "tx" if not is_avx512 else "hx"
    # For AVX2, we stored residuals in tx/ty/tz. For AVX-512, we overwrote hx/hy/hz.
    sumsq_code = "        " + "{vec} sumsq=_{fmadd}({v0},{v0},_{fmadd}({v1},{v1},_{mul}({v2},{v2})));".format(
        vec="__m512d" if ctype == "double" and SIMD >= 8 else
            "__m512" if ctype == "float" and SIMD >= 16 else
            "__m256d" if ctype == "double" else "__m256",
        fmadd="mm512_fmadd_pd" if ctype == "double" and SIMD >= 8 else
              "mm512_fmadd_ps" if ctype == "float" and SIMD >= 16 else
              "mm256_fmadd_pd" if ctype == "double" else "mm256_fmadd_ps",
        mul="mm512_mul_pd" if ctype == "double" and SIMD >= 8 else
            "mm512_mul_ps" if ctype == "float" and SIMD >= 16 else
            "mm256_mul_pd" if ctype == "double" else "mm256_mul_ps",
        v0=sumsq_var, v1=sumsq_var, v2=sumsq_var)
    
    cur_load = "        {vec} cur=_{loadu}(&drlv2[k]);".format(
        vec="__m512d" if ctype == "double" and SIMD >= 8 else
            "__m512" if ctype == "float" and SIMD >= 16 else
            "__m256d" if ctype == "double" else "__m256",
        loadu="mm512_loadu_pd" if ctype == "double" and SIMD >= 8 else
              "mm512_loadu_ps" if ctype == "float" and SIMD >= 16 else
              "mm256_loadu_pd" if ctype == "double" else "mm256_loadu_ps")
    
    mask_code = ""
    if is_avx512:
        mask_code = "        __mmask{bits} mask=_{cmp}(sumsq,tvec,_CMP_LT_OS);\n        mask&=_{cmp}(sumsq,cur,_CMP_LT_OS);".format(
            bits=8 if ctype == "double" else 16,
            cmp="mm512_cmp_pd_mask" if ctype == "double" else "mm512_cmp_ps_mask")
    else:
        mask_code = "        {vec} mask1=_{cmp}(sumsq,tvec,_CMP_LT_OS);\n        mask1=_{and}(mask1,_{cmp}(sumsq,cur,_CMP_LT_OS));\n        int mm=_{movemask}(mask1);".format(
            vec="__m256d" if ctype == "double" else "__m256",
            cmp="mm256_cmp_pd" if ctype == "double" else "mm256_cmp_ps",
            and_="mm256_and_pd" if ctype == "double" else "mm256_and_ps",
            movemask="mm256_movemask_pd" if ctype == "double" else "mm256_movemask_ps")
    
    # Label SIMD block
    if is_avx512:
        label_simd = """        /* SIMD label update */
        {lvl} lbl=_{lv}_loadu_si{bits}(({lvl}*)&labels[k]);
        __mmask{mbits} eq=_{lv}_cmpeq_epi32_mask(lbl,lbl_vec);
        __mmask{mbits} clr=_kandn_mask{mbits}(mask,eq);
        lbl=_{lv}_mask_mov_epi32(lbl,mask,lbl_vec);
        lbl=_{lv}_mask_mov_epi32(lbl,clr,neg);
        _{lv}_storeu_si{bits}(({lvl}*)&labels[k],lbl);""".format(
            lv=lbl_vec_width, bits="" if lbl_vec_width <= 128 else str(lbl_vec_width),
            mbits=8 if ctype == "double" else 16)
    else:
        label_simd = """        if(mm){{
            n+=popcnt32(mm);
            {drlv2_store_avx2}
            /* SIMD label update */
            {lvl} lbl=_{lv}_loadu_si{bits}(({lvl}*)&labels[k]);
            {lvl} lbl_vec2=_{lv}_set1_epi32(label), neg2=_{lv}_set1_epi32(-1);
            {lvl} eq2=_{lv}_cmpeq_epi32(lbl,lbl_vec2);
            {lvl} mw=_{lv}_set_epi32({mw_args});
            {lvl} clr2=_{lv}_andnot_si{bits2}(mw,eq2);
            lbl=_{lv}_blendv_epi8(lbl,lbl_vec2,mw);
            lbl=_{lv}_blendv_epi8(lbl,neg2,clr2);
            _{lv}_storeu_si{bits}(({lvl}*)&labels[k],lbl);
        }}""".format(
            lv=lbl_vec_width, bits="" if lbl_vec_width <= 128 else str(lbl_vec_width),
            bits2="" if lbl_vec_width <= 128 else str(lbl_vec_width),
            mw_args=("(mm&8)?-1:0,(mm&4)?-1:0,(mm&2)?-1:0,(mm&1)?-1:0" if ctype == "double" else
                     "(mm&128)?-1:0,(mm&64)?-1:0,(mm&32)?-1:0,(mm&16)?-1:0,(mm&8)?-1:0,(mm&4)?-1:0,(mm&2)?-1:0,(mm&1)?-1:0"),
            drlv2_store_avx2="{vec} _mm{lv}_storeu_{suf}(&drlv2[k],_{lv}_blendv_{suf}(cur,sumsq,mask1));".format(
                vec="__m256d" if ctype == "double" else "__m256",
                lv="256", suf="pd" if ctype == "double" else "ps",
                suf2="pd" if ctype == "double" else "ps"))
    
    drlv2_store = ""
    if is_avx512:
        drlv2_store = "{vec} _mm512_storeu_{suf}(&drlv2[k],_{lv}_mask_blend_{suf}(mask,cur,sumsq));".format(
            vec="__m512d" if ctype == "double" else "__m512",
            lv="mm512", su="pd" if ctype == "double" else "ps")
    
    num_permutes = 6
    
    content = kernel_template.format(
        basename=basename, type=type_label, isa=isa,
        scalar_loads=scalar_loads, num_loads=num_loads, num_permutes=num_permutes,
        permute_intrinsic=permute_intrinsic,
        fmt=fmt, func_name=func_name, ctype=ctype, dtype=dtype,
        static_func=static_func, N=N,
        u_broadcasts=u_broadcasts, tvec=tvec, lbl_vec=lbl_vec,
        load_indices=load_indices, load_code=load_code, permute_code=permute_code,
        fma_code=fma_code, round_code=round_code, sumsq_code=sumsq_code,
        cur_load=cur_load, mask_code=mask_code, label_simd=label_simd,
        drlv2_store=drlv2_store,
        ctype_val="" if ctype == "double" else "float ",  # for scalar tail
        nearbyint=nearbyint,
        permute_indices=idx_code,
    )
    
    path = os.path.join(SADIR, basename + ".c")
    with open(path, 'w') as f:
        f.write(content)
    print("Wrote", path)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # f32 AoS AVX-512 v2
    gen_one("sa_f32_aos_avx512_v2", N=16, SIMD=16, isa="avx512f",
            ctype="float", dtype="float", set1_suffix="ps",
            ctype_val="float", nearbyint="nearbyintf",
            permute_intrinsic="_mm512_permutex2var_ps",
            scalar_loads=48, num_loads=3)
    
    print("Done")
