#!/usr/bin/env python3
"""Reproducible compiler-flag measurement for score_and_refine template.

Measures independent effects of:
  -D opt_level   : O2 vs O3
  -D fast_math   : no-ffast-math vs -ffast-math
  -D isa_target  : baseline vs sse4.1 vs avx2 vs avx512f

Method: generates a standalone .cpp file that includes score_and_refine.hpp
multiple times with distinct SAR_IMPL_NAME per flag combo, compiles each as a
separate .o with the target flags, links into a temp .so, measures via ctypes.

Usage:
    python measure_flags.py           # full matrix
    python measure_flags.py --quick   # fast subset for rapid testing
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, time, subprocess, tempfile, shutil, ctypes
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..", "..")
FUNCTIONS_DIR = SCRIPT_DIR
COMMON_DIR = os.path.join(SCRIPT_DIR, "..", "common")
BUILD_DIR = os.path.join(tempfile.gettempdir(), "sar_flag_measure")
os.makedirs(BUILD_DIR, exist_ok=True)

CXX = "g++"
NG_LARGE = int(15e6)
NG_SMALL = 200000
SEED = 42

# ── flag matrix ──────────────────────────────────────────────────────
OPT_LEVELS  = ["O2", "O3"]
FAST_MATH   = [False, True]
ISA_TARGETS = ["baseline", "sse41", "avx2", "avx512"]

ISA_FLAGS = {
    "baseline":   [],
    "sse41":      ["-msse4.1"],
    "avx2":       ["-mavx2", "-mfma"],
    "avx512":     ["-mavx512f", "-mavx2", "-mfma"],
}

ISA_DEFINES = {
    "sse41":  "__SSE4_1__",
    "avx2":   "__AVX2__",
    "avx512": "__AVX512F__",
}


def flag_combo_name(opt, fm, isa):
    fm_s = "fm" if fm else "nofm"
    return "sar_{}_{}_{}".format(opt, fm_s, isa)


def build_measurement_so():
    """Generate standalone .cpp with all flag combos, compile, link into .so."""
    sources = {}  # combo_name -> .cpp path

    # Build one .cpp per unique flag combo
    for opt in OPT_LEVELS:
        for isa in ISA_TARGETS:
            for fm in FAST_MATH:
                name = flag_combo_name(opt, fm, isa)
                cpp_path = os.path.join(BUILD_DIR, name + ".cpp")

                # Collect base flags
                cflags = ["-" + opt, "-fPIC", "-fopenmp", "-std=c++11"]
                if fm:
                    cflags.append("-ffast-math")
                cflags.extend(ISA_FLAGS[isa])
                cflags.append("-I" + FUNCTIONS_DIR)
                cflags.append("-I" + COMMON_DIR)

                # Write standalone .cpp
                impl_name = "score_and_refine_" + name
                isa_define = ""
                if isa != "baseline":
                    isa_define = "#define {} 1\n".format(ISA_DEFINES[isa])
                else:
                    isa_define = "/* no ISA */\n"

                code = """/* Auto-generated flag measurement unit: {name} */
/* Flags: {flags} */
{isa_define}
#define SAR_IMPL_NAME {impl_name}
#include "score_and_refine.hpp"

extern "C" void {impl_name}_f64(
    double ubi[3][3], const double gv[][3], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{{
    SAR_IMPL_NAME<double, double>(ubi, (const double *)gv, tol,
                                  n_arg, sumdrlv2_arg, ng);
}}

extern "C" void {impl_name}_f32(
    double ubi[3][3], const float gv[][3], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{{
    SAR_IMPL_NAME<float, float>(ubi, (const float *)gv, tol,
                                n_arg, sumdrlv2_arg, ng);
}}
""".format(name=name, flags=" ".join(cflags),
           isa_define=isa_define, impl_name=impl_name)

                with open(cpp_path, "w") as f:
                    f.write(code)
                sources[name] = (cpp_path, cflags)

    # Compile each .cpp -> .o
    obj_files = []
    for name, (cpp_path, cflags) in sorted(sources.items()):
        obj_path = cpp_path.replace(".cpp", ".o")
        cmd = [CXX, "-c", cpp_path, "-o", obj_path] + cflags
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("COMPILE ERROR {}:".format(name))
            print(r.stderr)
            sys.exit(1)
        obj_files.append(obj_path)

    # Link into .so
    so_path = os.path.join(BUILD_DIR, "sar_flag_measure.so")
    link_cmd = [CXX, "-shared", "-o", so_path] + obj_files + [
        "-lgomp", "-lm"
    ]
    # Need inverse3x3 from the main .so
    main_so = os.path.join(PROJECT_ROOT, "c2ImageD11", "_cImageD11_x86_64.so")
    if os.path.exists(main_so):
        link_cmd.append(main_so)
    else:
        # Fallback: compile inverse3x3 from utilities
        util_o = os.path.join(BUILD_DIR, "inverse3x3.o")
        subprocess.run([CXX, "-c",
            os.path.join(COMMON_DIR, "cimaged11utils.c"),
            "-o", util_o, "-O2", "-fPIC", "-I" + COMMON_DIR],
            capture_output=True)
        if os.path.exists(util_o):
            link_cmd.insert(-2, util_o)

    r = subprocess.run(link_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("LINK ERROR:")
        print(r.stderr)
        sys.exit(1)

    return so_path


def measure_one(lib, sym_name, is_f32, ng, ubi, gv_f64, gv_f32):
    """Measure throughput of one variant at given ng size. Returns M gv/s."""
    fn = getattr(lib, sym_name)
    fn.restype = None
    fn.argtypes = [ctypes.c_void_p] * 2 + [ctypes.c_double,
                  ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double),
                  ctypes.c_int64]

    gv = gv_f32 if is_f32 else gv_f64
    n = ctypes.c_int(); s = ctypes.c_double()

    lib.omp_set_num_threads(1)
    for _ in range(2):
        fn(ubi.ctypes.data, gv.ctypes.data, 0.05, ctypes.byref(n), ctypes.byref(s), ng)

    n_iter = max(5, int(0.5 / max(ng / 3e8, 1e-15))) if ng < 1e6 else max(3, int(0.2 / (ng / 3e8)))
    n_iter = min(n_iter, 2000)

    t0 = time.perf_counter()
    for _ in range(n_iter):
        fn(ubi.ctypes.data, gv.ctypes.data, 0.05, ctypes.byref(n), ctypes.byref(s), ng)
    t1 = time.perf_counter()
    return ng * n_iter / (t1 - t0) / 1e6


def run_measurements(quick=False):
    """Build and measure all flag combos."""
    print("=" * 85)
    print("Scientific compiler-flag measurement for score_and_refine template")
    print("=" * 85)
    print()
    print("Factors:  opt_level  x  fast_math  x  isa_target")
    print("  opt_level : O2, O3")
    print("  fast_math : no-ffast-math, -ffast-math")
    print("  isa_target: baseline, sse4.1, avx2, avx512")
    if quick:
        print("  [quick mode: f64 only, ng=%dM only]" % (NG_SMALL // 1e6))
    print()

    print("[1/3] Generating standalone .cpp files...")
    so_path = build_measurement_so()
    print("      %d compilation units generated" %
          (len(OPT_LEVELS) * len(FAST_MATH) * len(ISA_TARGETS)))

    print("[2/3] Generating test data...")
    rng = np.random.RandomState(SEED)
    ubi = rng.randn(3, 3).astype(np.float64)
    gv_f64_l = rng.randn(NG_LARGE, 3).astype(np.float64)
    gv_f64_s = rng.randn(NG_SMALL, 3).astype(np.float64)
    gv_f32_l = rng.randn(NG_LARGE, 3).astype(np.float32)
    gv_f32_s = rng.randn(NG_SMALL, 3).astype(np.float32)

    print("[3/3] Measuring (via ctypes, 1T)...")
    print()

    lib = ctypes.CDLL(so_path)
    lib.omp_set_num_threads.argtypes = [ctypes.c_int]
    lib.omp_set_num_threads.restype = None

    isa_order = ["baseline", "sse41", "avx2", "avx512"]
    opt_order  = ["O2", "O3"]

    for dtype, gv_l, gv_s in [("f64", gv_f64_l, gv_f64_s),
                               ("f32", gv_f32_l, gv_f32_s)]:
        if quick and dtype == "f32":
            continue
        is_f32 = (dtype == "f32")
        gv_l_n = NG_LARGE
        gv_s_n = NG_SMALL

        print("  {:-^78}".format("  " + dtype + "  "))
        print("  {:>20s}  {:>12s}  {:>12s}  {:>12s}  {:>12s}".format(
            "variant", "ng=%dM" % (gv_s_n // 1e6), "ng=%dM" % (gv_l_n // 1e6),
            "S/L ratio", "notes"))
        print("  " + "-" * 76)

        results = {}
        for isa in isa_order:
            for opt in opt_order:
                for fm in [False, True]:
                    name = flag_combo_name(opt, fm, isa)
                    sym = "score_and_refine_" + name + ("_f32" if is_f32 else "_f64")
                    fm_s = "+fm" if fm else "-fm"
                    label = "{:>20s}".format("{}_{} {}".format(opt, fm_s, isa))

                    try:
                        thr_s = measure_one(lib, sym, is_f32, gv_s_n, ubi, gv_f64_s, gv_f32_s)
                    except Exception as e:
                        print("  {}  {:>12s}  {:>12s}  {:>12s}  skipped ({})".format(
                            label, "-", "-", "-", str(e)[:30]))
                        continue

                    if quick:
                        print("  {}  {:>10.0f}M  {:>12s}  {:>12s}  {:>12s}".format(
                            label, thr_s, "-", "-", ""))
                        results[label.strip()] = thr_s
                        continue

                    try:
                        thr_l = measure_one(lib, sym, is_f32, gv_l_n, ubi, gv_f64_l, gv_f32_l)
                    except Exception:
                        thr_l = 0

                    ratio = thr_s / thr_l if thr_l else 0
                    notes = ""
                    if thr_l > 0:
                        notes = "%.2f us" % (gv_s_n / thr_s / 1e6 * 1e6)
                    print("  {}  {:>10.0f}M  {:>10.0f}M  {:>10.3f}  {:>12s}".format(
                        label, thr_s, thr_l, ratio, notes))
                    results[label.strip()] = thr_s

        # Best per ISA for each opt level
        if not quick:
            print()
            print("  --- best per ISA within each opt level (small ng) ---")
            for isa in isa_order:
                best_o2 = max([results.get("{}_{} {}".format("O2", "+fm" if f else "-fm", isa), 0)
                              for f in [False, True]])
                best_o3 = max([results.get("{}_{} {}".format("O3", "+fm" if f else "-fm", isa), 0)
                              for f in [False, True]])
                if best_o2 or best_o3:
                    print("  {:>7s}: O2_best={:>7.0f}M  O3_best={:>7.0f}M  delta={:+d}M".format(
                        isa, best_o2, best_o3, int(best_o3 - best_o2)))

    print()
    print("=" * 85)
    print("Done. Build artifacts in: {}".format(BUILD_DIR))
    print("Reproduce with: python {}".format(os.path.abspath(__file__)))


def main():
    import argparse
    p = argparse.ArgumentParser(description="Measure compiler flag effects")
    p.add_argument("--quick", action="store_true", help="f64 only, one size")
    args = p.parse_args()
    run_measurements(quick=args.quick)


if __name__ == "__main__":
    main()
