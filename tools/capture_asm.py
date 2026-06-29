#!/usr/bin/env python3
"""capture_asm.py — Clang-captured cross-platform NASM kernels.

For each SoA ISA kernel, extracts the inner SIMD function, compiles it
with clang-18 for both Linux (System V) and Windows (MinGW) ABIs,
converts to NASM via gas_to_nasm.py, and merges into a single .asm file
behind %ifidn __OUTPUT_FORMAT__, win64 / %else / %endif.

Usage:
    python3 tools/capture_asm.py
    python3 tools/capture_asm.py --kernel sa_f64_sov_avx512  # single kernel

Requires: clang-18, gcc-mingw-w64-x86-64 (for Windows cross-compilation)
"""

import subprocess, sys, os, re, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SADIR = os.path.join(ROOT, "lib", "functions", "score_and_assign")
ASMDIR = os.path.join(SADIR, "asm")
G2N    = os.path.join(ROOT, "tools", "gas_to_nasm.py")
CLANG  = "clang-18"

INCLUDES = f"-I {ROOT}/lib/functions -I {ROOT}/lib/functions/common -I {ROOT}/lib/interface"

# All SoA ISA kernel definitions
ALL_KERNELS = [
    ("sa_f64_sov_avx512", "sa_inner_f64_sov_avx512", "double", "double",
     "-mavx512f -mavx512vl -mavx512dq -mavx512bw -mavx2 -mfma"),
    ("sa_f64_sov_avx2",   "sa_inner_f64_sov_avx2",   "double", "double",
     "-mavx2 -mfma"),
    ("sa_f32_sov_avx512", "sa_inner_f32_sov_avx512", "float", "float",
     "-mavx512f -mavx512vl -mavx512dq -mavx512bw -mavx2 -mfma"),
    ("sa_f32_sov_avx2",   "sa_inner_f32_sov_avx2",   "float", "float",
     "-mavx2 -mfma"),
]


def capture_one_abi(src_base, inner_name, ctype, dtype, isa_flags, target, abi_label):
    """Capture the inner kernel for one ABI. Returns NASM text or None."""
    c_path = os.path.join(SADIR, src_base + ".c")
    with open(c_path) as f:
        c_text = f.read()

    # Extract kernel body from the C source
    orig_name = "sa_" + src_base[3:] + "_kernel"
    sig_start = c_text.find(orig_name + "(")
    if sig_start < 0:
        print(f"  {abi_label}: function '{orig_name}' not found in {src_base}.c")
        return None
    brace_pos = c_text.find('{', sig_start)
    depth, end = 0, brace_pos
    for i in range(brace_pos, len(c_text)):
        if c_text[i] == '{': depth += 1
        elif c_text[i] == '}':
            depth -= 1
            if depth == 0: end = i; break
    body = c_text[brace_pos+1:end]

    # Build standalone C file
    standalone = (
        f"#include <immintrin.h>\n"
        f"#include <stdint.h>\n"
        f"#include <math.h>\n"
        f'#include "../score_and_refine/sar_popcnt.h"\n'
        f"\n"
        f"__attribute__((noinline))\n"
        f"static int {inner_name}(const double ubi[9], const {ctype} *gvx,"
        f" const {ctype} *gvy, const {ctype} *gvz, double tol,"
        f" {dtype} *drlv2, int *labels, int label, intptr_t ng)\n"
        f"{{{body}\n"
        f"}}\n"
        f"\n"
        f"int call_{inner_name}(const double ubi[9], const {ctype} *gvx,"
        f" const {ctype} *gvy, const {ctype} *gvz, double tol,"
        f" {dtype} *drlv2, int *labels, int label, intptr_t ng)\n"
        f"{{ return {inner_name}(ubi, gvx, gvy, gvz, tol, drlv2, labels, label, ng); }}\n"
    )

    tmp_c = f"/tmp/{src_base}_{abi_label}.c"
    tmp_s = f"/tmp/{src_base}_{abi_label}.s"
    with open(tmp_c, 'w') as f:
        f.write(standalone)

    # Compile
    target_flag = f"-target {target} " if target else ""
    cmd = f"{CLANG} -O3 -ffast-math {target_flag}{isa_flags} -masm=intel -S -o {tmp_s} {tmp_c} {INCLUDES}"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  {abi_label}: clang-18 failed:\n{r.stderr[:300]}")
        return None

    # Convert to NASM
    with open(tmp_s) as f:
        gas_text = f.read()
    r = subprocess.run([sys.executable, G2N], input=gas_text, capture_output=True, text=True)
    nasm_text = r.stdout

    # Extract inner function
    for pat in [inner_name + ":  ; @", inner_name + ": ; @", inner_name + ":"]:
        pos = nasm_text.find(pat)
        if pos >= 0:
            start = nasm_text.rfind('\n', 0, pos) + 1
            return nasm_text[start:]
    print(f"  {abi_label}: inner function '{inner_name}' not found in NASM output")
    return None


def capture(src_base, inner_name, ctype, dtype, isa_flags):
    """Capture both ABIs and merge into one .asm file."""
    os.makedirs(ASMDIR, exist_ok=True)

    linux_asm = capture_one_abi(src_base, inner_name, ctype, dtype, isa_flags, None, "linux")
    win64_asm = capture_one_abi(src_base, inner_name, ctype, dtype, isa_flags,
                                 "x86_64-pc-windows-gnu", "win64")
    if not linux_asm or not win64_asm:
        return False

    # Merge with %ifidn
    final = (
        f"SECTION .note.GNU-stack noalloc noexec nowrite progbits\n"
        f'%include "c2_abi.asm"\n'
        f"SECTION .text\n"
        f"\n"
        f"%ifidn __OUTPUT_FORMAT__, win64\n"
        f"global {inner_name}\n"
        f"{win64_asm}"
        f"%else\n"
        f"global {inner_name}\n"
        f"{linux_asm}"
        f"%endif\n"
    )

    asm_path = os.path.join(ASMDIR, src_base + ".asm")
    with open(asm_path, 'w') as f:
        f.write(final)

    # Validate both formats
    ok = True
    for fmt, label in [("elf64", "linux"), ("win64", "win64")]:
        r = subprocess.run(
            ["nasm", "-f", fmt, "-I", ASMDIR, "-o", "/dev/null", asm_path],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  {label}: NASM ERROR: {r.stderr[:200]}")
            ok = False
        else:
            print(f"  {label}: NASM OK")
    return ok


def main():
    p = argparse.ArgumentParser(description="Capture Clang-generated NASM kernels")
    p.add_argument("--kernel", help="Single kernel basename (e.g. sa_f64_sov_avx512)")
    args = p.parse_args()

    kernels = ALL_KERNELS
    if args.kernel:
        kernels = [k for k in ALL_KERNELS if k[0] == args.kernel]
        if not kernels:
            print(f"Unknown kernel: {args.kernel}")
            sys.exit(1)

    ok = True
    for src_base, inner_name, ctype, dtype, isa_flags in kernels:
        print(f"\n--- {src_base}.c ---")
        if not capture(src_base, inner_name, ctype, dtype, isa_flags):
            print(f"  FAILED")
            ok = False

    if ok:
        print("\nAll kernels captured successfully.")
        sys.exit(0)
    else:
        print("\nSome kernels failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
