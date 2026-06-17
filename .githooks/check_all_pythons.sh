#!/bin/bash
# Check all .py files for Python 2.7-3.14 syntax compatibility via snakepit.
# Usage: bash .githooks/check_all_pythons.sh [files...]
#   If no files given, checks all non-submodule .py files in the repo.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SNAKEPIT_DIR="$HOME/snakepit"

# Container -> Python versions
# ubuntu20.04.sif has python2.7, python3.8
# ubuntu24.04.sif has python3.9..3.14
CONTAINERS=(
    "ubuntu20.04.sif:python2.7:python2"
    "ubuntu20.04.sif:python3.8:python3.8"
    "ubuntu24.04.sif:python3.9:python3.9"
    "ubuntu24.04.sif:python3.10:python3.10"
    "ubuntu24.04.sif:python3.11:python3.11"
    "ubuntu24.04.sif:python3.12:python3.12"
    "ubuntu24.04.sif:python3.13:python3.13"
    "ubuntu24.04.sif:python3.14:python3.14"
)

if [ $# -gt 0 ]; then
    FILES=("$@")
else
    # All non-submodule, non-build, non-thirdparty .py files
    cd "$REPO_DIR"
    FILES=()
    while IFS= read -r f; do
        case "$f" in
            lz4/*|bitshuffle/*|kcb/*|zstd/*|build/*|venv/*|.eggs/*|__pycache__/*) ;;
            *) FILES+=("$f") ;;
        esac
    done < <(find . -name '*.py' -not -path '*/.venv/*' -not -path '*/build/*' -not -path '*/__pycache__/*' -not -path '*/lz4/*' -not -path '*/bitshuffle/*' -not -path '*/kcb/*' -not -path '*/zstd/*')
fi

echo "Checking ${#FILES[@]} Python files across 8 Python versions..."
echo

HAD_ERROR=0

for entry in "${CONTAINERS[@]}"; do
    IFS=':' read -r sif pyver pybin <<< "$entry"
    sif_path="$SNAKEPIT_DIR/$sif"
    if [ ! -f "$sif_path" ]; then
        echo "SKIP $pyver: SIF not found at $sif_path"
        continue
    fi

    errors=0
    for f in "${FILES[@]}"; do
        f_abs="$(cd "$REPO_DIR" && realpath "$f" 2>/dev/null || echo "$f")"
        f_rel="${f#./}"
        output=$(apptainer exec -e -B "$REPO_DIR:$REPO_DIR" "$sif_path" \
            "$pybin" -m py_compile "$f_abs" 2>&1) || {
            echo "FAIL $pyver: $f_rel"
            echo "$output"
            errors=1
            HAD_ERROR=1
        }
    done
    if [ $errors -eq 0 ]; then
        echo "PASS $pyver (${#FILES[@]} files)"
    fi
done

echo
if [ "$HAD_ERROR" -eq 0 ]; then
    echo "All files pass all Python versions."
else
    echo "Some files have syntax errors. See above."
    exit 1
fi
