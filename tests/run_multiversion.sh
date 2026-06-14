#!/usr/bin/env bash
# run_multiversion.sh - Build and test c2ImageD11 INSIDE a snakepit container
# Usage: bash run_multiversion.sh pythonX.Y
#
# Minimal test: builds c2ImageD11 .so and runs ctypes-only verification.
# No numpy, no ImageD11 — just the bare C extension.
set -e

PYTHON="${1:-python3}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
C2PY23_DIR="${C2PY23_DIR:-/workspace/c2py23}"
if [ ! -d "$C2PY23_DIR" ]; then
    C2PY23_DIR="/home/worker/c2py23"
fi

echo "=== c2ImageD11 test ($($PYTHON --version 2>&1)) ==="

VENV_DIR="$SCRIPT_DIR/.test_venv"
rm -rf "$VENV_DIR"

MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info[0])" 2>/dev/null || echo "3")
if [ "$MAJOR" = "2" ]; then
    virtualenv -p "$PYTHON" "$VENV_DIR" || exit 1
else
    "$PYTHON" -m venv "$VENV_DIR" || exit 1
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel -q 2>&1 | tail -1
pip install -e "$C2PY23_DIR" -q 2>&1 | tail -1
pip install --no-build-isolation -e "$PROJECT_DIR" -q 2>&1 | tail -1

echo "Running ctypes-only tests..."
cd "$PROJECT_DIR"
python -c "
from __future__ import print_function
import sys, ctypes, math

# Load the module via ctypes to avoid any import issues
sys.path.insert(0, '.')
import c2ImageD11._cImageD11 as M

ok = 0
fail = 0

def t(name, cond):
    global ok, fail
    if cond:
        ok += 1
    else:
        print('FAIL: ' + name)
        fail += 1

# basic scalar
t('verify_rounding', M.verify_rounding(20) == 0)
t('omp_max_threads', M.cimaged11_omp_get_max_threads() >= 0)

# score: identity ubi, orthogonal g-vectors -> 3 indexed peaks
ubi = (ctypes.c_double * 9)(1,0,0, 0,1,0, 0,0,1)
gv = (ctypes.c_double * 9)(1,0,0, 0,2,0, 0,0,3)
mv_ubi = memoryview(ubi).cast('B').cast('d', [3,3]) if sys.version_info[0] >= 3 else ubi
mv_gv = memoryview(gv).cast('B').cast('d', [3,3]) if sys.version_info[0] >= 3 else gv
t('score', M.score(mv_ubi, mv_gv, 0.001) == 3)

# misori: identity -> trace 3.0
u2 = (ctypes.c_double * 9)(1,0,0, 0,1,0, 0,0,1)
mv2 = memoryview(u2).cast('B').cast('d', [3,3]) if sys.version_info[0] >= 3 else u2
r = M.misori_cubic(mv_ubi, mv2)
t('misori_cubic', abs(r - 3.0) < 1e-10)

# closest: find nearest
x = (ctypes.c_double * 5)(1.0, 2.0, 3.0, 4.0, 5.0)
v = (ctypes.c_double * 2)(1.5, 4.2)
ib = (ctypes.c_int * 1)(0)
best = (ctypes.c_double * 1)(0.0)
M.closest(x, v, ib, best)
t('closest', ib[0] >= 0 and best[0] >= 0)

# array_stats
img_arr = (ctypes.c_float * 10)(1,2,3,4,5,6,7,8,9,10)
mn = (ctypes.c_float * 1)(); mx = (ctypes.c_float * 1)()
me = (ctypes.c_float * 1)(); va = (ctypes.c_float * 1)()
M.array_stats(img_arr, mn, mx, me, va)
t('array_stats', mn[0] <= me[0] <= mx[0] and va[0] >= 0)

# connectedpixels - 2D only on py3
if sys.version_info[0] >= 3:
    data = (ctypes.c_float * 16)(0.1, 0.2, 0.9, 0.1,
                                  0.1, 0.9, 0.9, 0.1,
                                  0.1, 0.9, 0.9, 0.1,
                                  0.1, 0.2, 0.9, 0.1)
    labels = (ctypes.c_int * 16)(*([0]*16))
    mv_d = memoryview(data).cast('B').cast('f', [4,4])
    mv_l = memoryview(labels).cast('B').cast('i', [4,4])
    n = M.connectedpixels(mv_d, mv_l, 0.5, 0, 1)
    t('connectedpixels', n > 0)

# optional defaults - use random-ish values to avoid degenerate cases
import random
random.seed(42)
vals = []
for _ in range(100):
    vals.append(random.random() * 10 + 1)
img2 = (ctypes.c_float * 100)(*vals)
me2 = (ctypes.c_float * 1)(); va2 = (ctypes.c_float * 1)()
M.array_mean_var_cut(img2, me2, va2)
t('optional_defaults', me2[0] > 0 and math.isfinite(me2[0]))

print('Results: %d passed, %d failed' % (ok, fail))
sys.exit(1 if fail > 0 else 0)
"
echo "=== Done ==="
