#!/usr/bin/env python3
"""Benchmark score_and_assign -- all ISA tiers via runtime flag toggling.

One .so, one build.  Toggles c2py_amd64_avx512f / c2py_amd64_avx2
to measure avx512, avx2, and baseline tiers without rebuilding.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, time, argparse, struct, numpy as np

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_SIZES = [50000, 200000, 1000000]
N_UBIS  = 1000


def gen_data(ng, seed=42, tol=0.05):
    sys.path.insert(0, os.path.join(PROJECT, "lib", "functions", "score_and_refine"))
    from test_data import generate_random_rotations
    rng = np.random.RandomState(seed)
    B = np.eye(3) / 4.06
    Us = generate_random_rotations(N_UBIS, seed + 77)
    ubis = np.zeros((N_UBIS, 3, 3))
    for i in range(N_UBIS):
        ubis[i] = np.linalg.inv(np.dot(Us[i], B))
    hkls = rng.randint(-8, 9, size=(ng, 3)).astype(np.float64)
    grain_ids = rng.randint(0, N_UBIS, size=ng)
    gv = np.empty((ng, 3))
    for i in range(ng):
        gv[i] = np.dot(hkls[i], np.dot(Us[grain_ids[i]], B).T)
    return ubis, gv, tol, np.full(ng, 999.0), np.full(ng, -1, dtype=np.int32)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    args = p.parse_args()

    n_cores = 2

    # --- f2py ---
    print("=== f2py (f64 AoS, 1T) ===")
    f2py = {}
    for ng in args.sizes:
        ubis, gv, tol, dv, lb = gen_data(ng)
        nc = max(5, int(2e8 / ng))
        try:
            import ImageD11._cImageD11 as old
            old.cimaged11_omp_set_num_threads(1)
            dv2 = dv.copy(); lb2 = lb.copy()
            for _ in range(5): old.score_and_assign(ubis[0].copy(), gv, tol, dv2, lb2, 1)
            dv2 = dv.copy(); lb2 = lb.copy()
            t0 = time.perf_counter()
            for i in range(nc):
                old.score_and_assign(ubis[i % N_UBIS].copy(), gv, tol, dv2, lb2, 1)
            t1 = time.perf_counter()
            f2py[ng] = ng * nc / (t1 - t0) / 1e6
            print("  ng={:>8d}  {:>7.0f}M gv/s".format(ng, f2py[ng]))
        except ImportError:
            f2py[ng] = 0
            print("  ng={:>8d}  (not found)".format(ng))

    # --- measurements ---
    import c2ImageD11
    fn = c2ImageD11.score_and_assign
    mod = c2ImageD11._cImageD11

    header = "{:>8s}  {:>8s}  {:>8s}  {:>9s}  {:>9s}  {:>6s}  {:>6s}  {:>4s}  {:>8s}  {:s}".format(
        "ng", "tier", "layout", "1T_Mgv/s", "nT_Mgv/s", "xf2py1T", "xf2pynT", "nthr", "gve", "variant")
    print()
    print(header)
    print("-" * 140)

    for tier, avx512_val, avx2_val in [("avx512", 1, 1), ("avx2", 0, 1), ("baseline", 0, 0)]:
        mod._c2py_set_avx512f(avx512_val)
        mod._c2py_set_avx2(avx2_val)

        for ng in args.sizes:
            ubis, gv_f64, tol, dv_f64, lb = gen_data(ng)
            nc = max(5, int(2e8 / ng))
            gv_f32 = gv_f64.astype(np.float32)
            dv_f32 = np.full(ng, 999.0, dtype=np.float32)
            gv_s64 = gv_f64.T.copy()
            gv_s32 = gv_f64.T.copy().astype(np.float32)
            for label, gv, dv in [
                    ("AoS_f64", gv_f64, dv_f64),
                    ("SoA_f64", gv_s64, dv_f64),
                    ("AoS_f32", gv_f32, dv_f32),
                    ("SoA_f32", gv_s32, dv_f32)]:
                for a in sorted(dir(mod)):
                    if "_c2py_ol_ptr_score_and_assign__" in a:
                        mod._c2py_perf_reset(int(getattr(mod, a)))
                mod._c2py_perf_set_enabled(1)
                try:
                    fn(ubis[0].copy(), gv, tol, dv.copy(), lb.copy(), 1)
                except (ValueError, SystemError):
                    print("{:>8d}  {:>8s}  {:>8s}  {:>9s}  {:>9s}  {:>6s}  {:>6s}  {:>4d}  {:>8s}  {:s}".format(
                        ng, tier, label, "-", "-", "-", "-", n_cores, "-", "no_match"), flush=True)
                    mod._c2py_perf_set_enabled(0)
                    continue
                mod._c2py_perf_set_enabled(0)
                variant = "none"
                for a in sorted(dir(mod)):
                    if "_c2py_ol_ptr_score_and_assign__" in a:
                        ptr = int(getattr(mod, a))
                        buf = bytearray(128)
                        mod._c2py_perf_read(ptr, buf)
                        if struct.unpack_from("Q", buf)[0] > 0:
                            v = a.replace("_c2py_ol_ptr_score_and_assign__", "")
                            variant = v
                            break
                c2ImageD11.cimaged11_omp_set_num_threads(1)
                dv2 = dv.copy(); lb2 = lb.copy()
                for _ in range(5): fn(ubis[0].copy(), gv, tol, dv2, lb2, 1)
                dv2 = dv.copy(); lb2 = lb.copy()
                t0 = time.perf_counter()
                for i in range(nc):
                    fn(ubis[i % N_UBIS].copy(), gv, tol, dv2, lb2, 1)
                t1 = time.perf_counter()
                thr_1t = ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0
                c2ImageD11.cimaged11_omp_set_num_threads(n_cores)
                dv3 = dv.copy(); lb3 = lb.copy()
                for _ in range(5): fn(ubis[0].copy(), gv, tol, dv3, lb3, 1)
                dv3 = dv.copy(); lb3 = lb.copy()
                t0 = time.perf_counter()
                for i in range(nc):
                    fn(ubis[i % N_UBIS].copy(), gv, tol, dv3, lb3, 1)
                t1 = time.perf_counter()
                thr_nt = ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0
                fp = f2py.get(ng, 0)
                v1 = thr_1t / fp if fp > 0 else 0
                vn = thr_nt / fp if fp > 0 else 0
                shape = "({},{})".format(ng, 3) if "AoS" in label else "(3,{})".format(ng)
                print("{:>8d}  {:>8s}  {:>8s}  {:>9.0f}  {:>9.0f}  {:>5.1f}x  {:>5.1f}x  {:>4d}  {:>8s}  {:s}".format(
                    ng, tier, label, thr_1t, thr_nt, v1, vn, n_cores, shape, variant), flush=True)

    mod._c2py_set_avx512f(1)
    mod._c2py_set_avx2(1)


if __name__ == "__main__":
    main()
