# Refactoring Plan: One Function Per Directory

## Goal

Move from monolithic `.c` files (`lib/src/`) to per-function directories
(`lib/functions/<name>/`). Each function lives in its own directory with its
own `.c` file containing the `C2PY_BEGIN` block and C implementation.

Shared infrastructure goes in `lib/functions/common/`.

## Current state

```
lib/src/
  core/
    cImageD11.h            # shared: DLL_LOCAL, includes
    ImageD11_cmath.h       # shared: RAD, DEG, vec3sub, matvec, matmat
    cimaged11utils.c       # 2 utility functions
  geometry/
    cdiffraction.c         # 5 functions
    cdiffraction.h         # forward declarations (delete)
    closest.c              # 16 functions
  imageproc/
    blobs.c                # shared: dset_* helpers (no C2PY_BEGIN)
    blobs.h                # shared: dset_* docs + C2PY_BEGIN constants
    connectedpixels.c      # 6 functions
    darkflat.c             # 14 functions
    localmaxlabel.c        # 1 function
    sparse_image.c         # 13 functions
    splat.c                # 1 function
```

## Target state

```
lib/
  functions/
    common/
      cImageD11.h          # DLL_LOCAL, includes stdint/stdio/math/omp
      ImageD11_cmath.h     # RAD, DEG, vec3sub, matvec, matmat
                           # + typedef double vec[3] (ADD THIS)
      blobs.h              # dset_* docs + C2PY_BEGIN constants
      blobs.c              # dset_* implementations
      cimaged11utils.h     # forward declarations (CREATE)
      cimaged11utils.c     # omp_set/omp_get/verify_rounding
    array_histogram/
      array_histogram.c
    ... (58 function directories total)
  meson.build              # updated source list + include dirs
  interface/               # unchanged
```

## Step 1: Create directory tree + move shared files

```bash
cd lib
mkdir -p functions/common
cp src/core/cImageD11.h         functions/common/
cp src/core/ImageD11_cmath.h    functions/common/
cp src/imageproc/blobs.h        functions/common/
cp src/imageproc/blobs.c        functions/common/
```

### CREATE `functions/common/cimaged11utils.h`

```c
#ifndef CIMAGED11UTILS_H
#define CIMAGED11UTILS_H
#include <stdint.h>

void cimaged11_omp_set_num_threads(int n);
int  cimaged11_omp_get_max_threads(void);
int  verify_rounding(int n);

#endif
```

### CREATE `functions/common/cimaged11utils.c`

Copy `lib/src/core/cimaged11utils.c` and edit to:
```c
#include "cImageD11.h"
#include "cimaged11utils.h"
```

### EDIT `functions/common/ImageD11_cmath.h`

Add before `#endif`:
```c
typedef double vec[3];
```

## Step 2: Create migration script

Save as `tools/migrate_functions.py`:

```python
#!/usr/bin/env python3
"""Split monolithic C files into per-function directories.

Usage:
    cd /path/to/c2ImageD11
    python3 tools/migrate_functions.py
"""

import os, re, shutil

SRC_DIR = "lib/src"
FUNCTIONS_DIR = "lib/functions"

_NEEDS_CMATH = {
    "compute_geometry", "compute_gv", "compute_xlylzl",
    "compute_xlylzl_xpos_variable", "quickorient",
    "closest_vec", "closest", "score", "score_and_refine",
    "score_and_assign", "refine_assigned", "put_incr64", "put_incr32",
    "cluster1d", "score_gvec_z", "misori_cubic", "misori_orthorhombic",
    "misori_tetragonal", "misori_monoclinic", "count_shared",
}

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
           "F2PY" not in stripped and not stripped.startswith("/*"):
            break
        i += 1
    if i >= len(lines):
        return None, None
    sig_start = i
    while sig_start > block_end:
        sig_start -= 1
        line = lines[sig_start].strip()
        if not line or line.startswith("!") or "F2PY" in line or \
           line.startswith("/*") or line.startswith("*"):
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
    print(f"  {name}.c")


def process_file(filepath):
    blocks, lines = scan_blocks(filepath)
    for (bs, be) in blocks:
        name = get_func_name(lines, bs, be)
        if not name:
            print(f"  WARNING: no py_sig at {filepath}:{bs}")
            continue
        if name in _SKIP:
            print(f"  SKIP: {name}")
            continue
        start, end = find_func_def(lines, be)
        if start is None:
            print(f"  WARNING: no func def after {name}")
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
        print(f"Processing {f} ...")
        process_file(f)

    src = os.path.join(SRC_DIR, "core", "cimaged11utils.c")
    dst = os.path.join(FUNCTIONS_DIR, "common", "cimaged11utils.c")
    if os.path.exists(src):
        content = open(src).read()
        content = content.replace(
            '#include "cImageD11.h"',
            '#include "cImageD11.h"\n#include "cimaged11utils.h"')
        open(dst, "w").write(content)
        print(f"  -> common/cimaged11utils.c")

    print("\nDone.")


if __name__ == "__main__":
    main()
```

Run:
```bash
python3 tools/migrate_functions.py
```

## Step 3: Update `lib/meson.build`

### Replace source list and include dirs:

```meson
c2_sources = files(
  # Common utilities
  'functions/common/blobs.c',
  'functions/common/cimaged11utils.c',

  # Per-function files (alphabetical)
  'functions/array_histogram/array_histogram.c',
  'functions/array_mean_var_cut/array_mean_var_cut.c',
  'functions/array_mean_var_msk/array_mean_var_msk.c',
  'functions/array_stats/array_stats.c',
  'functions/bgcalc/bgcalc.c',
  'functions/blob_moments/blob_moments.c',
  'functions/bloboverlaps/bloboverlaps.c',
  'functions/blobproperties/blobproperties.c',
  'functions/clean_mask/clean_mask.c',
  'functions/closest/closest.c',
  'functions/closest_vec/closest_vec.c',
  'functions/cluster1d/cluster1d.c',
  'functions/compress_duplicates/compress_duplicates.c',
  'functions/compute_geometry/compute_geometry.c',
  'functions/compute_gv/compute_gv.c',
  'functions/compute_xlylzl/compute_xlylzl.c',
  'functions/compute_xlylzl_xpos_variable/compute_xlylzl_xpos_variable.c',
  'functions/connectedpixels/connectedpixels.c',
  'functions/count_shared/count_shared.c',
  'functions/coverlaps/coverlaps.c',
  'functions/frelon_lines/frelon_lines.c',
  'functions/frelon_lines_sub/frelon_lines_sub.c',
  'functions/localmaxlabel/localmaxlabel.c',
  'functions/make_clean_mask/make_clean_mask.c',
  'functions/mask_to_coo/mask_to_coo.c',
  'functions/misori_cubic/misori_cubic.c',
  'functions/misori_monoclinic/misori_monoclinic.c',
  'functions/misori_orthorhombic/misori_orthorhombic.c',
  'functions/misori_tetragonal/misori_tetragonal.c',
  'functions/put_incr32/put_incr32.c',
  'functions/put_incr64/put_incr64.c',
  'functions/quickorient/quickorient.c',
  'functions/refine_assigned/refine_assigned.c',
  'functions/reorder_f32_a32/reorder_f32_a32.c',
  'functions/reorder_u16_a32/reorder_u16_a32.c',
  'functions/reorder_u16_a32_a16/reorder_u16_a32_a16.c',
  'functions/reorderlut_f32_a32/reorderlut_f32_a32.c',
  'functions/reorderlut_u16_a32/reorderlut_u16_a32.c',
  'functions/score/score.c',
  'functions/score_and_assign/score_and_assign.c',
  'functions/score_and_refine/score_and_refine.c',
  'functions/score_gvec_z/score_gvec_z.c',
  'functions/sparse_blob2Dproperties/sparse_blob2Dproperties.c',
  'functions/sparse_connectedpixels/sparse_connectedpixels.c',
  'functions/sparse_connectedpixels_splat/sparse_connectedpixels_splat.c',
  'functions/sparse_is_sorted/sparse_is_sorted.c',
  'functions/sparse_localmaxlabel/sparse_localmaxlabel.c',
  'functions/sparse_overlaps/sparse_overlaps.c',
  'functions/sparse_smooth/sparse_smooth.c',
  'functions/splat/splat.c',
  'functions/tosparse_f32/tosparse_f32.c',
  'functions/tosparse_u16/tosparse_u16.c',
  'functions/tosparse_u32/tosparse_u32.c',
  'functions/uint16_to_float_darkflm/uint16_to_float_darkflm.c',
  'functions/uint16_to_float_darksub/uint16_to_float_darksub.c',
)
```

Change include dirs from:
```meson
c2_inc = include_directories(
  'src', 'src/core', 'src/geometry', 'src/imageproc', 'interface')
```
to:
```meson
c2_inc = include_directories(
  'functions', 'functions/common', 'interface')
```

## Step 4: Update `tools/harvester.py`

Find the call to `assemble_c2py()` at the bottom of the file.
Change the source directory argument from `"src"` to `"functions"`.

Likely looks like:
```python
assemble_c2py(os.path.join(root, "src"), output_dir)
```
Change to:
```python
assemble_c2py(os.path.join(root, "functions"), output_dir)
```

## Step 5: Delete old source tree

```bash
rm -rf lib/src
```

## Step 6: Rebuild and test

```bash
cd build/libc2ImageD11
meson setup --wipe ../../lib
ninja
cd ../..
cp build/libc2ImageD11/_cImageD11.so c2ImageD11/_cImageD11_x86_64.so
python3 -m pytest tests/ -v
```

## Step 7: Regenerate wrapper (sanity check)

```bash
python3 tools/harvester.py --output-dir lib/interface
cd build/libc2ImageD11 && ninja
cd ../..
python3 -m pytest tests/ -v
```

## Verification checklist

- [ ] `lib/functions/common/` has all 6 files
- [ ] `typedef double vec[3]` in ImageD11_cmath.h
- [ ] 58 function directories under `lib/functions/`
- [ ] Each has one `.c` file with C2PY_BEGIN block + C function
- [ ] `lib/meson.build` lists all files + correct include dirs
- [ ] `tools/harvester.py` scans `lib/functions/`
- [ ] `lib/src/` deleted
- [ ] Clean `ninja` build, 61 tests pass

## Post-merge

The per-function layout enables:
- **f32/f64 variants** — add `array_stats_f32.c` alongside `array_stats.c`
- **SIMD variants** — add `score_and_refine_avx2.c` or `.S`
- **Per-function tests** — `functions/score_and_refine/test_score_and_refine.py`
- **Per-function benchmarks** — `functions/score_and_refine/bench.py`
- **LLM sessions** — point at one directory, see only local context
