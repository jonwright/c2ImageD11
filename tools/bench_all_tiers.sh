#!/bin/bash
# bench_all_tiers.sh -- measure score_and_assign at all ISA levels
# Builds 3 .so files (avx512, avx2, baseline) and prints a comparison table.
set -euo pipefail

SIZES="${1:-50000 200000}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
SADIR="$PROJECT/lib/functions/score_and_assign"
BENCH="$SADIR/bench.py"

cd "$PROJECT"

restore_and_rebuild() {
    echo "  restoring all C2PY_BEGIN blocks..."
    for f in "$SADIR"/sa_*.c; do
        sed -i 's/C2PY_DISABLED_END/C2PY_END/g; s/C2PY_DISABLED/C2PY_BEGIN/g' "$f"
    done
    python3 tools/harvester.py --output-dir lib/interface > /dev/null 2>&1
    cd build/libc2ImageD11 && meson setup ../../lib --reconfigure -Dbuildtype=release -Doptimization=2 > /dev/null 2>&1
    ninja > /dev/null 2>&1
    cp _cImageD11.so ../../c2ImageD11/_cImageD11.so
    cp _cImageD11.so ../../c2ImageD11/_cImageD11_x86_64.so
    cd "$PROJECT"
}

measure() {
    local tier="$1"
    echo ">>> Measuring $tier..."
    python3 "$BENCH" --sizes $SIZES 2>&1 | tee "/tmp/bench_${tier}.txt"
}

# ── Tier 1: AVX-512 (default, all enabled) ──
echo "=== Tier 1: AVX-512 ==="
restore_and_rebuild
measure "avx512"

# ── Tier 2: AVX2 (disable avx512) ──
echo "=== Tier 2: AVX2 ==="
for f in "$SADIR"/sa_*avx512*.c; do
    sed -i 's/C2PY_BEGIN/C2PY_DISABLED/g; s/C2PY_END/C2PY_DISABLED_END/g' "$f"
done
# Also disable SSE4.1 .cpp fallbacks that have avx512 in when: conditions -- none exist for score_and_assign
restore_and_rebuild
measure "avx2"

# ── Tier 3: Baseline (disable all ISA) ──
echo "=== Tier 3: baseline (scalar) ==="
for f in "$SADIR"/sa_*.c; do
    sed -i 's/C2PY_BEGIN/C2PY_DISABLED/g; s/C2PY_END/C2PY_DISABLED_END/g' "$f"
done
restore_and_rebuild
measure "baseline"

# ── Restore defaults ──
echo "=== Restoring default build ==="
restore_and_rebuild

# ── Print summary ──
echo ""
echo "=============================================================="
echo "  Summary (1T, M gv/s)"
echo "=============================================================="
echo ""

# Extract the row for each size from each tier
python3 << PYEOF
import re, sys

tiers = ['avx512', 'avx2', 'baseline']
data = {}  # data[tier][ng][layout] = (thr_1t, thr_nt)

for tier in tiers:
    data[tier] = {}
    try:
        with open(f'/tmp/bench_{tier}.txt') as f:
            lines = f.readlines()
    except:
        continue
    for line in lines[1:]:
        if not line.strip() or line.startswith('---') or line.startswith('==='):
            continue
        parts = line.split()
        if len(parts) < 10:
            continue
        # Format: ng f2py A64_1T A64_nT spd S64_1T S64_nT spd A32_1T A32_nT spd S32_1T S32_nT spd
        try:
            ng = int(parts[0])
        except:
            continue
        # Skip header-like lines
        if ng < 100:
            continue
        off = 2 if 'f2py' in line or parts[1].endswith('M') or parts[1].startswith('f2py') else 1
        # Actually, just parse by fixed positions
        # Row: ng  f2py  A64_1T  A64_nT  spd  S64_1T  S64_nT  spd  A32_1T  A32_nT  spd  S32_1T  S32_nT  spd
        # After ng and optionally f2py, we have 12 fields
        fields = [p for p in parts if 'M' in p or 'x' in p or p == '-']
        # Find the M values
        speeds = []
        for p in parts:
            p = p.rstrip('M')
            try:
                speeds.append(float(p))
            except:
                pass
        if len(speeds) >= 8:
            data[tier][ng] = {
                'AoS_f64': (speeds[0], speeds[1]),
                'SoA_f64': (speeds[2], speeds[3]),
                'AoS_f32': (speeds[4], speeds[5]),
                'SoA_f32': (speeds[6], speeds[7]),
            }

# Find f2py reference
f2py = {}
try:
    with open('/tmp/bench_avx512.txt') as f:
        for line in f:
            if 'f2py reference' in line:
                break
        for line in f:
            m = re.search(r'ng=\s*(\d+)\s+(\d+)M', line)
            if m:
                f2py[int(m.group(1))] = int(m.group(2))
except:
    pass

# Print table
layouts = ['AoS_f64', 'SoA_f64', 'AoS_f32', 'SoA_f32']

for ng in sorted(data.get('avx512', {}).keys()):
    print(f"  ng={ng}")
    header = f"  {'Layout':<10s}"
    for t in tiers:
        header += f"  {t:>18s}"
    if f2py.get(ng):
        header += f"  {'f2py':>8s}"
    print(header)
    print("  " + "-" * (10 + 20*len(tiers) + 10))
    for lay in layouts:
        row = f"  {lay:<10s}"
        for t in tiers:
            d = data.get(t, {}).get(ng, {}).get(lay, (0, 0))
            row += f"  {d[0]:>7.0f}M /{d[1]:>7.0f}M"
        if f2py.get(ng) and lay == 'AoS_f64':
            row += f"  {f2py[ng]:>7}M"
        print(row)
    print()
PYEOF
