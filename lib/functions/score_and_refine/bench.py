#!/usr/bin/env python3
"""Benchmark score_and_refine() -- all ISA tiers via _rebind_ variant switching."""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, time, argparse, struct, numpy as np

# ---- guard: refuse to pipe to head/tail ----
def _check_pipe_truncator():
    if sys.stdout.isatty():
        return
    s = os.fstat(1)
    if not s.st_mode & 0o010000:
        return
    try:
        my_ino = os.stat("/proc/self/fd/1").st_ino
        for pid_dir in os.listdir("/proc"):
            if not pid_dir.isdigit():
                continue
            try:
                fd0_ino = os.stat("/proc/%s/fd/0" % pid_dir).st_ino
            except OSError:
                continue
            if fd0_ino == my_ino:
                with open("/proc/%s/cmdline" % pid_dir, "rb") as f:
                    cmd = f.read().replace(b"\x00", b" ").decode("utf-8", "replace")
                basename = os.path.basename(cmd.split()[0]) if cmd.strip() else ""
                if basename in ("head", "tail"):
                    sys.exit("ERROR: DO NOT pipe bench.py output through head or tail. "
                             "You must see ALL benchmark output.")
                break
    except Exception:
        pass

_check_pipe_truncator()

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
N_UBIS  = 1000
DEFAULT_SIZES = [50000, 200000]

TIER_VARIANTS = {
    "avx512": {
        "AoS_f64": "score_and_refine_f64_avx512",
        "SoA_f64": "score_and_refine_f64_soa_avx512",
        "AoS_f32": "score_and_refine_f32_avx512",
        "SoA_f32": "score_and_refine_f32_soa_avx512",
    },
    "avx2": {
        "AoS_f64": "score_and_refine_f64_avx2",
        "SoA_f64": "score_and_refine_f64_soa_avx2",
        "AoS_f32": "score_and_refine_f32_avx2",
        "SoA_f32": "score_and_refine_f32_soa_avx2",
    },
    "baseline": {
        "AoS_f64": "score_and_refine_f64_sse41",
        "SoA_f64": "score_and_refine_f64_soa_sse41",
        "AoS_f32": "score_and_refine_f32_sse41",
        "SoA_f32": "score_and_refine_f32_soa_sse41",
    },
}


def gen_data(ng, seed=42, tol=0.05):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "score_and_refine"))
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
    return ubis, gv, tol


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    args = p.parse_args()

    import c2ImageD11
    fn = c2ImageD11.score_and_refine
    mod = c2ImageD11._cImageD11
    rebind = getattr(mod, "_rebind_score_and_refine", None)
    n_cores = 2

    f2py = {}
    for ng in args.sizes:
        ubis, gv, tol = gen_data(ng)
        nc = max(5, int(2e8 / ng))
        try:
            import ImageD11._cImageD11 as old
            old.cimaged11_omp_set_num_threads(1)
            for _ in range(5): old.score_and_refine(ubis[0].copy(), gv, tol)
            t0 = time.perf_counter()
            for i in range(nc): old.score_and_refine(ubis[i % N_UBIS].copy(), gv, tol)
            t1 = time.perf_counter()
            f2py[ng] = ng * nc / (t1 - t0) / 1e6
            print("f2py ng={:>8d} {:>7.0f}M".format(ng, f2py[ng]))
        except ImportError:
            f2py[ng] = 0
            print("f2py ng={:>8d} (not found)".format(ng))

    header = "{:>8s}  {:>5s}  {:>8s}  {:>8s}  {:>9s}  {:>6s}  {:>4s}  {:s}".format(
        "ng", "nthr", "tier", "layout", "M_gv/s", "xf2py", "gve", "variant")
    print()
    print(header)
    print("-" * 110)

    defaults = {}
    for ng in args.sizes[:1]:
        ubis, gv_f64, tol = gen_data(ng)
        for label, gv in [("AoS_f64", gv_f64), ("SoA_f64", gv_f64.T.copy()),
                           ("AoS_f32", gv_f64.astype(np.float32)), ("SoA_f32", gv_f64.T.copy().astype(np.float32))]:
            if rebind: rebind(None)
            mod._c2py_perf_set_enabled(1)
            try: fn(ubis[0].copy(), gv, tol)
            except: pass
            mod._c2py_perf_set_enabled(0)
            for a in sorted(dir(mod)):
                if "_c2py_ol_ptr_score_and_refine__" in a:
                    ptr = int(getattr(mod, a))
                    buf = bytearray(128)
                    mod._c2py_perf_read(ptr, buf)
                    if struct.unpack_from("Q", buf)[0] > 0:
                        defaults[label] = a.replace("_c2py_ol_ptr_score_and_refine__", "")
                        break

    available_tiers = {"baseline"}
    for v in defaults.values():
        if "avx512" in v:
            available_tiers.update(("avx512", "avx2"))
            break
        if "avx2" in v:
            available_tiers.add("avx2")

    for tier in ("avx512", "avx2", "baseline"):
        if tier not in available_tiers:
            print("{:>8s}  {:>5s}  {:>8s}  {:>8s}  {:>9s}  {:>6s}  {:>4s}  {:s}".format(
                "---", "---", tier, "---", "---", "---", "---", "not available on this CPU"), flush=True)
            continue
        tier_vars = TIER_VARIANTS.get(tier, {})

        for ng in args.sizes:
            ubis, gv_f64, tol = gen_data(ng)
            nc = max(5, int(2e8 / ng))
            gv_f32 = gv_f64.astype(np.float32)
            gv_s64 = gv_f64.T.copy()
            gv_s32 = gv_f64.T.copy().astype(np.float32)
            for nthr in [1, 2]:
                for label, gv in [("AoS_f64", gv_f64), ("SoA_f64", gv_s64),
                                   ("AoS_f32", gv_f32), ("SoA_f32", gv_s32)]:
                    vname = tier_vars.get(label)
                    if vname and rebind: rebind(vname)
                    c2ImageD11.cimaged11_omp_set_num_threads(nthr)
                    for _ in range(5): fn(ubis[0].copy(), gv, tol)
                    t0 = time.perf_counter()
                    for i in range(nc): fn(ubis[i % N_UBIS].copy(), gv, tol)
                    t1 = time.perf_counter()
                    thr = ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0
                    fp = f2py.get(ng, 0)
                    v1 = thr / fp if fp > 0 else 0
                    shape = "({},{})".format(ng, 3) if "AoS" in label else "(3,{})".format(ng)
                    mark = " *" if defaults.get(label) == vname else ""
                    print("{:>8d}  {:>5d}  {:>8s}  {:>8s}  {:>9.0f}  {:>5.1f}x  {:>4s}  {:s}{:s}".format(
                        ng, nthr, tier, label, thr, v1, shape, vname or "?", mark), flush=True)

    if rebind: rebind(None)


if __name__ == "__main__":
    main()
