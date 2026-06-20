#!/usr/bin/env bash
# test_build_once.sh - Verify c2py23 dlopen runtime: build one .so, test everywhere.
#
# Builds c2ImageD11 with Python 2.7 in manylinux2014, producing an untagged
# _cImageD11.so.  Then tests importing that single .so from every Python
# version available in snakepit containers (cp38-315, including free-threaded).
#
# Usage:  bash tools/test_build_once.sh [--quick] [your-python ...]
#
#   --quick       import-only check (skip buffer tests)
#   py3.9 py3.14  test only listed Python versions
#
# Requirements:
#   - Apptainer installed
#   - ../c2py23 sibling directory
#   - snakepit SIF files in ../snakepit/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE="$(cd "$PROJECT_DIR/.." && pwd)"
BUILD_DIR="$WORKSPACE/c2build_single"
SNAKEPIT="$WORKSPACE/snakepit"
MANYLINUX_SIF="$SNAKEPIT/manylinux2014.sif"
C2PY23_DIR="${C2PY23_DIR:-$WORKSPACE/c2py23}"

red()    { echo -e "\033[31m$*\033[0m"; }
green()  { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }

QUICK=0
SELECTED_VERSIONS=()
for arg in "$@"; do
    case "$arg" in
        --quick) QUICK=1 ;;
        *) SELECTED_VERSIONS+=("$arg") ;;
    esac
done

# ---- Version matrix (SIF, python_binary, label) ----
ALL_VERSIONS=(
    "$SNAKEPIT/ubuntu20.04.sif python3.8"
    "$SNAKEPIT/ubuntu24.04.sif python3.9"
    "$SNAKEPIT/ubuntu24.04.sif python3.10"
    "$SNAKEPIT/ubuntu24.04.sif python3.11"
    "$SNAKEPIT/ubuntu24.04.sif python3.12"
    "$SNAKEPIT/ubuntu24.04.sif python3.13"
    "$SNAKEPIT/ubuntu24.04.sif python3.14"
    "$SNAKEPIT/ubuntu24.04.sif python3.14t"
    "$SNAKEPIT/ubuntu26.04.sif python3.15"
    "$SNAKEPIT/ubuntu26.04.sif python3.15t"
)

if [ ${#SELECTED_VERSIONS[@]} -gt 0 ]; then
    FILTERED=()
    for py in "${SELECTED_VERSIONS[@]}"; do
        # Accept "3.8", "py3.8", or "python3.8"
        ver="$(echo "$py" | sed 's/^python//; s/^py//')"
        for entry in "${ALL_VERSIONS[@]}"; do
            read -r _ bin <<< "$entry"
            [ "$bin" = "python$ver" ] && FILTERED+=("$entry")
        done
    done
    ALL_VERSIONS=("${FILTERED[@]}")
fi

# ---- Step 1: Build ----
echo "============================================================"
echo "  Step 1: Building with Python 2.7 in manylinux2014"
echo "============================================================"
echo "Target: $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

if [ ! -f "$MANYLINUX_SIF" ]; then
    red "manylinux2014.sif not found at $MANYLINUX_SIF"
    exit 1
fi

apptainer exec -B "$WORKSPACE:/workspace" "$MANYLINUX_SIF" /bin/bash -c "
set -e
# Python 2.7.5 in manylinux2014 has no pip; install it
if ! python2.7 -m pip --version 2>/dev/null; then
    python2.7 -m ensurepip --user --default-pip 2>/dev/null || {
        curl -sS https://bootstrap.pypa.io/pip/2.7/get-pip.py -o /tmp/gp.py
        python2.7 /tmp/gp.py --no-setuptools --no-wheel --user -q
    }
fi
export PATH=\"\$HOME/.local/bin:\$PATH\"
python2.7 -m pip install wheel setuptools -q --user
python2.7 -m pip install --no-build-isolation -e /workspace/c2py23 -q --user
python2.7 -m pip install --target=/workspace/c2build_single --no-build-isolation /workspace/c2ImageD11 -q
"

# Clean up unwanted files from --target install
rm -rf "$BUILD_DIR/numpy" "$BUILD_DIR/bin" "$BUILD_DIR/"*.dist-info
find "$BUILD_DIR" -name '*.pyc' -delete

SO_FILE=$(find "$BUILD_DIR" -name '_cImageD11*.so' | head -1)
echo ""
echo "Built: $SO_FILE"
echo "Size:  $(du -h "$SO_FILE" | cut -f1)"
if echo "$SO_FILE" | grep -q 'cpython'; then
    yellow "WARNING: .so has ABI tag, other Python versions will NOT import it."
    yellow "The manylinux2014 Python 2.7 must produce untagged .so files."
    exit 1
fi
green ".so is untagged - good for cross-version imports."

# ---- Step 2: Test ----
echo ""
echo "============================================================"
echo "  Step 2: Testing across Python versions"
echo "============================================================"

PASSED=0; FAILED=0

for entry in "${ALL_VERSIONS[@]}"; do
    read -r sif python <<< "$entry"
    label="$(basename "$python") ($(basename "$sif" .sif))"

    echo ""
    echo "--- $label ---"

    # IMPORTANT: use --pwd that does NOT contain a c2ImageD11/ subdir,
    # otherwise CWD (sys.path[0]) wins over PYTHONPATH and the project's
    # own tagged .so is loaded instead of the c2build_single copy.
    SAFE_PWD="/workspace/c2build_single"

    if [ "$QUICK" = "1" ]; then
        # Quick import-only check
        if apptainer exec -e -B "$WORKSPACE:/workspace" --pwd "$SAFE_PWD" "$sif" /bin/bash -c "
            PYTHONPATH=/workspace/c2build_single $python -c '
import c2ImageD11
m = c2ImageD11._cImageD11
print(\"so:      \", m.__file__)
print(\"rounding:\", c2ImageD11.verify_rounding(20))'
        " 2>&1; then
            green "PASS $label"
            PASSED=$((PASSED+1))
        else
            red "FAIL $label"
            FAILED=$((FAILED+1))
        fi
    else
        # Full buffer tests with numpy+pytest
        if apptainer exec -e -B "$WORKSPACE:/workspace" --pwd "$SAFE_PWD" "$sif" /bin/bash -c "
            VDIR=/workspace/c2build_single/.test_venv
            rm -rf \"\$VDIR\"
            $python -m venv \"\$VDIR\" 2>/dev/null && {
                source \"\$VDIR/bin/activate\"
                pip install numpy pytest -q 2>&1 | tail -1
                PYTHONPATH=/workspace/c2build_single $python -c '
import c2ImageD11; m=c2ImageD11._cImageD11; print(\"so:\", m.__file__)'
                PYTHONPATH=/workspace/c2build_single python -m pytest \
                    /workspace/c2ImageD11/tests/test_buffer.py -v --tb=short 2>&1
            } || {
                # venv fails for free-threaded; fall back to --user
                $python -m pip install numpy pytest -q --user --break-system-packages 2>&1 | tail -1
                PYTHONPATH=/workspace/c2build_single $python -c '
import c2ImageD11; m=c2ImageD11._cImageD11; print(\"so:\", m.__file__)'
                PYTHONPATH=/workspace/c2build_single $python -m pytest \
                    /workspace/c2ImageD11/tests/test_buffer.py -v --tb=short 2>&1
            }
        " 2>&1; then
            green "PASS $label"
            PASSED=$((PASSED+1))
        else
            red "FAIL $label"
            FAILED=$((FAILED+1))
        fi
    fi
done

echo ""
echo "============================================================"
echo "  Results: $PASSED passed, $FAILED failed"
echo "============================================================"
echo ""
echo "Build output at: $BUILD_DIR"
echo "To run again:    bash tools/test_build_once.sh"
echo "Quick check:     bash tools/test_build_once.sh --quick"

[ "$FAILED" -eq 0 ] && exit 0 || exit 1
