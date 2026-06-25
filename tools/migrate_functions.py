#!/usr/bin/env python3
"""Split monolithic C files into per-function directories."""

import os, re

SRC_DIR = "lib/src"
FUNCTIONS_DIR = "lib/functions"

# Functions needing ImageD11_cmath.h (vec3sub, matvec, matmat, RAD, DEG, vec)
_NEEDS_CMATH = {
    "compute_geometry", "compute_gv", "compute_xlylzl",
    "compute_xlylzl_xpos_variable", "quickorient",
    "closest_vec", "closest", "score", "score_and_refine",
    "score_and_assign", "refine_assigned", "put_incr64", "put_incr32",
    "cluster1d", "score_gvec_z", "misori_cubic", "misori_orthorhombic",
    "misori_tetragonal", "misori_monoclinic", "count_shared",
}

# Functions needing blobs.h
_NEEDS_BLOBS = {
    "connectedpixels", "blobproperties", "bloboverlaps", "blob_moments",
    "clean_mask", "make_clean_mask", "localmaxlabel",
    "mask_to_coo", "sparse_is_sorted", "sparse_connectedpixels",
    "sparse_connectedpixels_splat", "sparse_blob2Dproperties",
    "sparse_smooth", "sparse_localmaxlabel", "sparse_overlaps",
    "compress_duplicates", "coverlaps",
    "tosparse_u16", "tosparse_u32", "tosparse_f32",
    "array_mean_var_cut", "array_mean_var_msk", "array_stats",
    "array_histogram", "bgcalc", "frelon_lines", "frelon_lines_sub",
    "uint16_to_float_darksub", "uint16_to_float_darkflm",
    "reorder_u16_a32", "reorder_f32_a32", "reorderlut_u16_a32",
    "reorderlut_f32_a32", "reorder_u16_a32_a16", "splat",
}

_SKIP = {"cimaged11_omp_set_num_threads", "cimaged11_omp_get_max_threads",
         "verify_rounding"}


def scan_blocks(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    blocks = []
    in_block = False
    start = -1
    for i, line in enumerate(lines):
        if "C2PY_BEGIN" in line:
            in_block = True
            start = i
        elif "C2PY_END" in line and in_block:
            blocks.append((start, i))
            in_block = False
    return blocks, lines


def get_func_name(lines, block_start, block_end):
    for i in range(block_start, block_end + 1):
        m = re.search(r'"py_sig":\s*"(\w+)', lines[i])
        if m:
            return m.group(1)
    return None


def get_includes(name):
    parts = ['#include "cImageD11.h"']
    if name in _NEEDS_CMATH:
        parts.append('#include "ImageD11_cmath.h"')
    if name in _NEEDS_BLOBS:
        parts.append('#include "blobs.h"')
    return "\n".join(parts) + "\n\n"


def find_func_def(lines, block_end):
    i = block_end + 1
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("!") and \
           "F2PY" not in stripped and not stripped.startswith("/*") and \
           "C2PY_END" not in stripped:
            break
        i += 1
    if i >= len(lines):
        return None, None
    sig_start = i
    while sig_start > block_end:
        sig_start -= 1
        line = lines[sig_start].strip()
        if not line or line.startswith("!") or "F2PY" in line or \
           line.startswith("/*") or line.startswith("*") or "C2PY_END" in line:
            sig_start += 1
            break
    j = sig_start
    while j < len(lines) and "{" not in lines[j]:
        j += 1
    if j >= len(lines):
        return None, None
    depth = 0
    while j < len(lines):
        for ch in lines[j]:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return (sig_start, j)
        j += 1
    return None, None


def write_func(name, block_lines, func_lines):
    outdir = os.path.join(FUNCTIONS_DIR, name)
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, name + ".c")
    with open(outpath, "w") as f:
        f.write(get_includes(name))
        for line in block_lines:
            f.write(line)
        f.write("\n")
        for line in func_lines:
            f.write(line)
    print("  {}.c".format(name))


def process_file(filepath):
    blocks, lines = scan_blocks(filepath)
    for (bs, be) in blocks:
        name = get_func_name(lines, bs, be)
        if not name:
            print("  WARNING: no py_sig at {}:{}".format(filepath, bs))
            continue
        if name in _SKIP:
            print("  SKIP: {}".format(name))
            continue
        start, end = find_func_def(lines, be)
        if start is None:
            print("  WARNING: no func def after {}".format(name))
            continue
        write_func(name, lines[bs:be+1], lines[start:end+1])


def main():
    sources = [
        "lib/src/geometry/cdiffraction.c",
        "lib/src/geometry/closest.c",
        "lib/src/imageproc/connectedpixels.c",
        "lib/src/imageproc/darkflat.c",
        "lib/src/imageproc/localmaxlabel.c",
        "lib/src/imageproc/sparse_image.c",
        "lib/src/imageproc/splat.c",
    ]
    for f in sources:
        print("Processing", f, "...")
        process_file(f)

    # cimaged11utils.c already handled in Step 1
    print("\nDone.")


if __name__ == "__main__":
    main()
