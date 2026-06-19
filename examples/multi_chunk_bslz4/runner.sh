#!/bin/bash
# Multi-chunk BSLZ4 CSC benchmark runner
#   bash runner.sh             # normal run (single core)
#   bash runner.sh --profile   # profile with py-spy
#   bash runner.sh --no-pin    # normal run, no core pinning

set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$DIR/bench_csc.py"

# Install py-spy if missing
if ! python3 -c "import py_spy" 2>/dev/null && ! command -v py-spy &>/dev/null; then
    echo "Installing py-spy..."
    pip3 install --user py-spy --break-system-packages 2>/dev/null || \
        pip3 install --user py-spy 2>/dev/null || \
        echo "WARNING: py-spy installation failed. Profile mode won't work."
fi

if [ "${1:-}" = "--profile" ]; then
    echo "Profiling with py-spy..."
    py-spy record -f flamegraph  -o "$DIR/profile_flame.svg"  -- python3 "$SCRIPT"
    py-spy record -f speedscope -o "$DIR/profile_speedscope.json" -- python3 "$SCRIPT"
    echo ""
    echo "Profile saved:"
    echo "  flamegraph:  $DIR/profile_flame.svg"
    echo "  speedscope:  $DIR/profile_speedscope.json"
elif [ "${1:-}" = "--no-pin" ]; then
    echo "Running benchmark (no core pinning)..."
    python3 "$SCRIPT"
    echo "Done. Plot: $DIR/benchmark.png"
else
    # Pin to CPU 0 to prevent core migration
    echo "Running benchmark (pinned to CPU 0)..."
    taskset -c 0 python3 "$SCRIPT"
    echo "Done. Plot: $DIR/benchmark.png"
fi
