#!/usr/bin/env bash
# ============================================================================
# tools/upload.sh  --  download CI-built wheels and upload to PyPI
#
# Downloads the latest successful wheel artifacts from GitHub Actions CI,
# checks them with twine, then uploads to PyPI.
#
# Usage:
#   ./tools/upload.sh                    # harvest + upload (needs TWINE_PASSWORD)
#   TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-xxx ./tools/upload.sh
#   ./tools/upload.sh --dry-run          # harvest + check but don't upload
#   ./tools/upload.sh --list             # list recent CI runs
#
# Requirements:
#   - gh CLI authenticated to jonwright/c2ImageD11
#   - pip install twine
#   - PyPI API token (upload requires authentication)
#
# One-time setup:
#   1. pip install twine
#   2. Create a PyPI API token at https://pypi.org/manage/account/token/
#   3. Export it or pass via environment:
#        export TWINE_USERNAME=__token__
#        export TWINE_PASSWORD=pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ============================================================================

set -euo pipefail

cd "$(dirname "$0")/.."  # project root

RELEASE_SCRIPT="tools/release.sh"

usage() {
  sed -ne '/^# Usage:/,/^$/p' "$0"
  exit 0
}

# ---- Parse args -----------------------------------------------------------
DRY_RUN=false
if [ $# -gt 0 ]; then
  case "$1" in
    --help|-h) usage ;;
    --list|-l) exec "$RELEASE_SCRIPT" --list ;;
    --dry-run|-n) DRY_RUN=true ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
fi

# ---- Harvest wheels -------------------------------------------------------
echo "=== Harvesting wheels from CI ==="
"$RELEASE_SCRIPT"

# ---- Check wheels ---------------------------------------------------------
echo ""
echo "=== Checking wheels with twine ==="
wheels=(dist/*/*.whl)
if [ ${#wheels[@]} -eq 0 ]; then
  echo "ERROR: no wheels found in dist/"
  exit 1
fi
python3 -m twine check "${wheels[@]}"
echo "All wheels look good."

# ---- Upload ---------------------------------------------------------------
if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "=== Dry-run mode  --  skipping upload ==="
  echo "Would upload:"
  for w in "${wheels[@]}"; do
    echo "  $w"
  done
  exit 0
fi

# Verify credentials
if [ -z "${TWINE_USERNAME:-}" ]; then
  export TWINE_USERNAME="__token__"
fi
if [ -z "${TWINE_PASSWORD:-}" ]; then
  echo ""
  echo "ERROR: TWINE_PASSWORD not set."
  echo ""
  echo "Upload requires a PyPI API token. Either:"
  echo "  export TWINE_USERNAME=__token__"
  echo "  export TWINE_PASSWORD=pypi-xxxx"
  echo ""
  echo "Or run with --dry-run to just harvest and check:"
  echo "  ./tools/upload.sh --dry-run"
  exit 1
fi

echo ""
echo "=== Uploading to PyPI ==="
echo "User: $TWINE_USERNAME"
echo "Wheels: ${#wheels[@]}"
echo ""
python3 -m twine upload "${wheels[@]}"
echo ""
echo "=== Done ==="
