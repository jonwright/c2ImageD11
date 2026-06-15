#!/usr/bin/env bash
# run_ci.sh - Local CI equivalent for c2ImageD11
#
# Mirrors the GitHub Actions workflow steps:
#   1. Install test dependencies (numpy, pytest)
#   2. Install c2py23 from sibling directory
#   3. Build and install c2ImageD11
#   4. Run buffer tests and equivalence tests
#
# Usage:
#   bash run_ci.sh                          # uses default python3
#   bash run_ci.sh /path/to/python3.12      # use specific Python version
#   bash run_ci.sh --no-venv                # install into current environment
#   bash run_ci.sh --image             # use ImageD11 from sibling folder
#
# ImageD11 is auto-detected from ../ImageD11 if available.
# Equivalence tests are skipped if ImageD11 is not importable.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
WORKSPACE="$(cd "$PROJECT_DIR/.." && pwd)"
C2PY23_DIR="${C2PY23_DIR:-$WORKSPACE/c2py23}"
TIMEOUT_SEC=300

# ---- Parse args ----
PYTHON=""
USE_VENV=1
INSTALL_IMAGED11=1

for arg in "$@"; do
    case "$arg" in
        --no-venv)
            USE_VENV=0
            ;;
        --no-imaged11)
            INSTALL_IMAGED11=0
            ;;
        *)
            if [ -z "$PYTHON" ]; then
                PYTHON="$arg"
            fi
            ;;
    esac
done

PYTHON="${PYTHON:-python3}"

# ---- Logging ----
red()    { echo -e "\033[31m$*\033[0m"; }
green()  { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }
blue()   { echo -e "\033[34m$*\033[0m"; }

banner() {
    echo ""
    echo "============================================================"
    echo "  $*"
    echo "============================================================"
}

fail() {
    red "FAIL: $*"
    exit 1
}

# ---- Validate environment ----
if [ ! -d "$C2PY23_DIR" ]; then
    fail "c2py23 not found at $C2PY23_DIR. Set C2PY23_DIR or clone into sibling dir."
fi

$PYTHON --version >/dev/null 2>&1 || fail "Python not found: $PYTHON"

# ---- Setup venv (optional) ----
if [ "$USE_VENV" = "1" ]; then
    VENV_DIR="$PROJECT_DIR/.ci_venv"
    blue "Creating clean virtualenv at $VENV_DIR ..."
    rm -rf "$VENV_DIR"
    if "$PYTHON" -c "import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)" 2>/dev/null; then
        "$PYTHON" -m venv "$VENV_DIR"
    else
        virtualenv -p "$PYTHON" "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
fi

banner "c2ImageD11 CI ($($PYTHON --version 2>&1))"

# ---- Step 1: Install test dependencies ----
banner "Installing test dependencies"
pip install --upgrade pip setuptools wheel -q
pip install numpy pytest -q 2>/dev/null || {
    # Python 2.7 fallback: install compatible versions
    pip install "numpy==1.16.6" -q 2>/dev/null || true
    pip install "pytest>=4.6,<5" -q 2>/dev/null || true
}

# ---- Step 2: Install c2py23 ----
banner "Installing c2py23 from $C2PY23_DIR"
pip install --no-build-isolation -e "$C2PY23_DIR" -q

# ---- Step 3: Build and install c2ImageD11 ----
banner "Building c2ImageD11"
pip install --no-build-isolation -e "$PROJECT_DIR" -q

# ---- Step 4: Install ImageD11 (--no-deps, only C code needed) ----
IMAGED11_AVAILABLE=0
if [ "$INSTALL_IMAGED11" = "1" ]; then
    banner "Installing ImageD11 from git (--no-deps --no-build-isolation)"
    if pip install "git+https://github.com/jonwright/ImageD11.git" \
        --no-deps --no-build-isolation 2>&1 | tail -3; then
        IMAGED11_AVAILABLE=1
        green "ImageD11 installed (no deps)"
    else
        yellow "ImageD11 install failed (equivalence tests will be skipped)"
    fi
elif ! python -c "import ImageD11._cImageD11" 2>/dev/null; then
    yellow "ImageD11 not available (equivalence tests will be skipped)"
fi

# ---- Step 5: Run tests ----
banner "Running tests (timeout: ${TIMEOUT_SEC}s)"

cd "$PROJECT_DIR"
TEST_CMD="python -m pytest tests/test_buffer.py tests/test_equivalence.py -v --tb=short -W ignore::DeprecationWarning"

if timeout "$TIMEOUT_SEC" bash -c "$TEST_CMD" 2>&1; then
    green ""
    green "============================================================"
    green "  ALL TESTS PASSED"
    green "============================================================"
    green ""
    exit 0
else
    rc=$?
    if [ $rc -eq 124 ]; then
        red "TIMEOUT: tests exceeded ${TIMEOUT_SEC}s"
    else
        red ""
        red "============================================================"
        red "  TESTS FAILED (exit code $rc)"
        red "============================================================"
        red ""
    fi
    exit $rc
fi
