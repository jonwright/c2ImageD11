#!/usr/bin/env python
"""extract_kernels.py - Mechanically extract SIMD kernels from ImageD11.

Reads original C function bodies from ImageD11/src/*.c and outputs KERNEL_FN
macro-wrapped kernel files into src/geometry/simd/ and src/imageproc/simd/.

The function body is copied VERBATIM.  Only the function name is replaced
with the KERNEL_FN macro.  OpenMP pragmas, branches, debug blocks, etc. are
preserved exactly.

The original 2D-array signatures (vec[3], double[][3]) are kept -- these are
ABI-compatible with the flat double* pointers passed by c2py23.
"""

from __future__ import print_function
import os
import re
import subprocess

IMAGED11_SRC = os.path.abspath(os.path.join(
    __file__, "..", "..", "..", "ImageD11", "src"))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_commit():
    try:
        d = os.path.join(IMAGED11_SRC, "..")
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=d, stderr=subprocess.STDOUT).decode().strip()
    except Exception:
        return "unknown"


def read_source(source):
    with open(os.path.join(IMAGED11_SRC, source), "r") as f:
        return f.read()


def extract_lines(text, func_name, start_line):
    """Extract signature + body of a C function from source text.

    Returns (sig_text, body_text).
    """
    lines = text.split("\n")
    idx = start_line - 1
    # Find opening brace
    sig_end = None
    for i in range(idx, len(lines)):
        if '{' in lines[i]:
            sig_end = i
            break
    if sig_end is None:
        raise ValueError("No opening brace for %s" % func_name)
    # Walk from sig_end to find matching close brace
    depth = 0
    brace_open = None
    close_idx = None
    for i in range(sig_end, len(lines)):
        for ch in lines[i]:
            if ch == '{':
                if depth == 0:
                    brace_open = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and brace_open is not None:
                    close_idx = i
                    break
        if close_idx is not None:
            break
    if close_idx is None:
        raise ValueError("Unmatched braces for %s" % func_name)
    sig = "\n".join(lines[idx:brace_open + 1])
    body = "\n".join(lines[brace_open + 1:close_idx + 1])
    return sig, body


def make_kernel(source, func_name, start_line, out_name, subdir,
                extra_includes=None, extra_code=None):
    commit = get_commit()
    text = read_source(source)
    sig, body = extract_lines(text, func_name, start_line)
    # Replace function name with KERNEL_FN
    sig = re.sub(r'\b' + re.escape(func_name) + r'\b', 'KERNEL_FN', sig, count=1)
    incs = "\n".join(extra_includes) if extra_includes else ""
    extra = ("\n" + "\n".join(extra_code)) if extra_code else ""
    header = ("/* Auto-extracted from ImageD11/src/%s, function %s, commit %s\n"
              " *\n"
              " * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py\n"
              " */\n"
              "#ifndef KERNEL_FN\n"
              '#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"\n'
              "#endif\n"
              "\n") % (source, func_name, commit)
    content = header + incs + extra + "\n\n" + sig + "\n" + body + "\n"
    outpath = os.path.join(REPO, "src", subdir, out_name)
    return outpath, content


KERNELS = [
    # (source, func, line, out_name, subdir, includes, extra_code)
    ("closest.c", "score", 227, "score_kernel.c", "geometry/simd",
     ['#include "cImageD11.h"', '#include <math.h>'],
     ['static inline double conv_double_to_int_fast(double x) {',
      '    return (x + 6755399441055744.0) - 6755399441055744.0;',
      '}']),
    ("closest.c", "score_and_refine", 267, "score_and_refine_kernel.c", "geometry/simd",
     ['#include "cImageD11.h"', '#include <math.h>', '#include <string.h>',
      'int inverse3x3(double A[3][3]);  /* defined in closest.c */'],
     ['static inline double conv_double_to_int_fast(double x) {',
      '    return (x + 6755399441055744.0) - 6755399441055744.0;',
      '}']),
    ("closest.c", "score_and_assign", 366, "score_and_assign_kernel.c", "geometry/simd",
     ['#include "cImageD11.h"', '#include <math.h>'],
     ['static inline double conv_double_to_int_fast(double x) {',
      '    return (x + 6755399441055744.0) - 6755399441055744.0;',
      '}']),
    ("cdiffraction.c", "compute_gv", 112, "compute_gv_kernel.c", "geometry/simd",
     ['#include "cImageD11.h"', '#include <math.h>', '#include "cdiffraction.h"'],
     None),
    ("cdiffraction.c", "compute_geometry", 31, "compute_geometry_kernel.c", "geometry/simd",
     ['#include "cImageD11.h"', '#include <math.h>', '#include "cdiffraction.h"'],
     None),
    ("cdiffraction.c", "compute_xlylzl", 190, "compute_xlylzl_kernel.c", "geometry/simd",
     ['#include "cImageD11.h"', '#include <math.h>', '#include "cdiffraction.h"',
      '#define NOISY 0'],
     None),
    ("cdiffraction.c", "compute_xlylzl_xpos_variable", 245,
     "compute_xlylzl_xpos_kernel.c", "geometry/simd",
     ['#include "cImageD11.h"', '#include <math.h>', '#include "cdiffraction.h"',
      '#define NOISY 0'],
     None),
    ("connectedpixels.c", "blobproperties", 213, "blobproperties_kernel.c", "imageproc/simd",
     ['#include "cImageD11.h"', '#include <math.h>', '#include "blobs.h"'],
     None),
    ("darkflat.c", "uint16_to_float_darksub", 49, "darksub_kernel.c", "imageproc/simd",
     ['#include "cImageD11.h"'],
     None),
    ("darkflat.c", "uint16_to_float_darkflm", 74, "darkflm_kernel.c", "imageproc/simd",
     ['#include "cImageD11.h"'],
     None),
    ("darkflat.c", "reorder_f32_a32", 467, "reorder_f32_a32_kernel.c", "imageproc/simd",
     ['#include "cImageD11.h"'],
     None),
    ("darkflat.c", "reorderlut_f32_a32", 513, "reorderlut_f32_a32_kernel.c", "imageproc/simd",
     ['#include "cImageD11.h"'],
     None),
    ("darkflat.c", "reorder_u16_a32", 443, "reorder_u16_a32_kernel.c", "imageproc/simd",
     ['#include "cImageD11.h"'],
     None),
    ("darkflat.c", "reorderlut_u16_a32", 490, "reorderlut_u16_a32_kernel.c", "imageproc/simd",
     ['#include "cImageD11.h"'],
     None),
    ("closest.c", "put_incr64", 492, "put_incr64_kernel.c", "imageproc/simd",
     ['#include "cImageD11.h"'],
     None),
    ("closest.c", "put_incr32", 529, "put_incr32_kernel.c", "imageproc/simd",
     ['#include "cImageD11.h"'],
     None),
]


def main():
    for src, fn, line, out, subdir, incs, extra in KERNELS:
        path, content = make_kernel(src, fn, line, out, subdir, incs, extra)
        with open(path, "w") as f:
            f.write(content)
        print("WROTE: %s (%d bytes)" % (os.path.relpath(path, REPO), len(content)))


if __name__ == "__main__":
    main()
