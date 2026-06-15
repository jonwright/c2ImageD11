#!/usr/bin/env bash
# run_ci_all.sh - Multi-version CI using snakepit Apptainer containers
#
# Tests c2ImageD11 across all Python versions matching GitHub Actions CI.
# Uses the snakepit SIF containers already present in ../snakepit/.
#
# Usage: bash run_ci_all.sh [--keep-going]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(cd "$SCRIPT_DIR/.." && pwd)"
SNAKEPIT="$WORKSPACE/snakepit"
LOGFILE="$SCRIPT_DIR/ci_all.log"

KEEP_GOING=""
for arg in "$@"; do
    [ "$arg" = "--keep-going" ] && KEEP_GOING=1
done

red()    { echo -e "\033[31m$*\033[0m"; }
green()  { echo -e "\033[32m$*\033[0m"; }
blue()   { echo -e "\033[34m$*\033[0m"; }

log() {
    echo "$*" | tee -a "$LOGFILE"
}

# Each entry: "SIF_path python_binary"
# ubuntu20.04: Python 2.7, 3.8
# ubuntu24.04: Python 3.9-3.14
VERSIONS=(
    "/home/worker/snakepit/ubuntu20.04.sif python2.7"
    "/home/worker/snakepit/ubuntu20.04.sif python3.8"
    "/home/worker/snakepit/ubuntu24.04.sif python3.9"
    "/home/worker/snakepit/ubuntu24.04.sif python3.10"
    "/home/worker/snakepit/ubuntu24.04.sif python3.11"
    "/home/worker/snakepit/ubuntu24.04.sif python3.12"
    "/home/worker/snakepit/ubuntu24.04.sif python3.13"
    "/home/worker/snakepit/ubuntu24.04.sif python3.14"
)

PASSED=0
FAILED=0

rm -f "$LOGFILE"

banner() {
    log ""
    log "============================================================"
    log "  $*"
    log "============================================================"
}

run_one() {
    local sif="$1"
    local python="$2"
    local label="$python"

    if [ ! -f "$sif" ]; then
        log "SKIP $label: SIF not found at $sif"
        FAILED=$((FAILED + 1))
        return 1
    fi

    log "RUN $label via $(basename "$sif") ..."

    local cmd=(
        apptainer exec -e
        -B "$WORKSPACE:/workspace"
        --pwd "/workspace/c2ImageD11"
        "$sif"
        /bin/bash -c "
            set -e
            C2PY23_DIR=/workspace/c2py23
            export C2PY23_DIR
            /workspace/c2ImageD11/run_ci.sh '$python'
        "
    )

    if timeout 600 "${cmd[@]}" >> "$LOGFILE" 2>&1; then
        log "PASS $label"
        PASSED=$((PASSED + 1))
        return 0
    else
        rc=$?
        if [ $rc -eq 124 ]; then
            log "TIMEOUT $label"
        else
            log "FAIL $label (rc=$rc)"
        fi
        FAILED=$((FAILED + 1))
        if [ -z "$KEEP_GOING" ]; then
            return 1
        fi
        return 1
    fi
}

# ---- Main ----
banner "c2ImageD11 Multi-Version CI"
log "Workspace: $WORKSPACE"
log ""

for entry in "${VERSIONS[@]}"; do
    run_one $entry
done

log ""
banner "Results: $PASSED passed, $FAILED failed"
[ "$FAILED" -eq 0 ] && exit 0 || exit 1
