#!/usr/bin/env python3
"""capture_asm.py -- Clang-captured cross-platform NASM kernels.

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

INCLUDES = "-I {0}/lib/functions -I {0}/lib/functions/common -I {0}/lib/interface".format(ROOT)

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
        print("  {0}: function '{1}' not found in {2}.c".format(abi_label, orig_name, src_base))
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
        "#include <immintrin.h>\n"
        "#include <stdint.h>\n"
        "#include <math.h>\n"
        '#include "../score_and_refine/sar_popcnt.h"\n'
        "\n"
        "__attribute__((noinline))\n"
        "static int {0}(const double ubi[9], const {1} *gvx,"
        " const {1} *gvy, const {1} *gvz, double tol,"
        " {2} *drlv2, int *labels, int label, intptr_t ng)\n"
        "{{{3}\n"
        "}}\n"
        "\n"
        "int call_{0}(const double ubi[9], const {1} *gvx,"
        " const {1} *gvy, const {1} *gvz, double tol,"
        " {2} *drlv2, int *labels, int label, intptr_t ng)\n"
        "{{ return {0}(ubi, gvx, gvy, gvz, tol, drlv2, labels, label, ng); }}\n"
    ).format(inner_name, ctype, dtype, body)

    tmp_c = "/tmp/{0}_{1}.c".format(src_base, abi_label)
    tmp_s = "/tmp/{0}_{1}.s".format(src_base, abi_label)
    with open(tmp_c, 'w') as f:
        f.write(standalone)

    # Compile
    target_flag = "-target {0} ".format(target) if target else ""
    cmd = "{0} -O3 -ffast-math {1}{2} -masm=intel -S -o {3} {4} {5}".format(
        CLANG, target_flag, isa_flags, tmp_s, tmp_c, INCLUDES)
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print("  {0}: clang-18 failed:\n{1}".format(abi_label, r.stderr[:300]))
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
    print("  {0}: inner function '{1}' not found in NASM output".format(abi_label, inner_name))
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
        "SECTION .note.GNU-stack noalloc noexec nowrite progbits\n"
        '%include "c2_abi.asm"\n'
        "SECTION .text\n"
        "\n"
        "%ifidn __OUTPUT_FORMAT__, win64\n"
        "global {0}\n".format(inner_name) +
        win64_asm +
        "%else\n"
        "global {0}\n".format(inner_name) +
        linux_asm +
        "%endif\n"
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
            print("  {0}: NASM ERROR: {1}".format(label, r.stderr[:200]))
            ok = False
        else:
            print("  {0}: NASM OK".format(label))
    return ok


def main():
    p = argparse.ArgumentParser(description="Capture Clang-generated NASM kernels")
    p.add_argument("--kernel", help="Single kernel basename (e.g. sa_f64_sov_avx512)")
    args = p.parse_args()

    kernels = ALL_KERNELS
    if args.kernel:
        kernels = [k for k in ALL_KERNELS if k[0] == args.kernel]
        if not kernels:
            print("Unknown kernel: {0}".format(args.kernel))
            sys.exit(1)

    ok = True
    for src_base, inner_name, ctype, dtype, isa_flags in kernels:
        print("\n--- {0}.c ---".format(src_base))
        if not capture(src_base, inner_name, ctype, dtype, isa_flags):
            print("  FAILED")
            ok = False

    if ok:
        print("\nAll kernels captured successfully.")
        sys.exit(0)
    else:
        print("\nSome kernels failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
