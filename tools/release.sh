#!/usr/bin/env bash
# ============================================================================
# tools/release.sh  --  gather CI-built wheels for manual PyPI upload
#
# Downloads pre-built wheels from GitHub Actions CI, computes SHA256
# checksums, and prints the `twine upload` command.
# Does NOT upload to PyPI.
#
# Usage:
#   ./tools/release.sh              # download latest from all workflows
#   ./tools/release.sh --list       # list recent CI runs
#   ./tools/release.sh --help       # show help
#
# Requirements:
#   - gh CLI authenticated to jonwright/c2ImageD11
#   - (your existing PAT is sufficient)
#
# Wheel matrix (all produced by CI except ppc64le):
#   Workflow              | Artifact              | Wheel
#   ---------------------|-----------------------|--------------------------
#   CI                   | dist-linux            | py3-none-manylinux_x86_64
#   CI                   | dist-windows          | py3-none-win_amd64
#   CI (aarch64)         | dist-linux-aarch64    | py3-none-manylinux_aarch64
#   CI (Python 2.7)      | dist-linux-py2        | py2-none-manylinux_x86_64
#   CI (Python 2.7)      | dist-windows-py2      | py2-none-win_amd64
#   (manual)             | ppc64le               | py3-none-manylinux_ppc64le
# ============================================================================

set -euo pipefail

REPO="jonwright/c2ImageD11"
OUTDIR="dist"

# workflow_name:artifact_name:description
WORKFLOWS=(
  "CI:dist-linux:linux_x86_64_py3"
  "CI:dist-windows:windows_amd64_py3"
  "CI (aarch64):dist-linux-aarch64:linux_aarch64_py3"
  "CI (Python 2.7):dist-linux-py2:linux_x86_64_py2"
  "CI (Python 2.7):dist-windows-py2:windows_amd64_py2"
)

usage() {
  sed -ne '/^# Usage:/,/^$/p' "$0"
  exit 0
}

get_latest_run() {
  local workflow="$1"
  gh run list --repo "$REPO" --workflow "$workflow" --branch master --limit 5 \
    --json databaseId,conclusion,displayTitle,createdAt \
    --jq '.[] | select(.conclusion == "success") | .databaseId' | head -1
}

# ---- Parse args -----------------------------------------------------------
if [ $# -gt 0 ]; then
  case "$1" in
    --help|-h) usage ;;
    --list|-l)
      echo "Recent CI runs (last 5 per workflow):"
      for entry in "${WORKFLOWS[@]}"; do
        wf="${entry%%:*}"
        echo ""
        echo "--- $wf ---"
        gh run list --repo "$REPO" --workflow "$wf" --branch master --limit 5 \
          --json databaseId,conclusion,displayTitle,createdAt \
          --jq '.[] | "  #\(.databaseId) [\(.conclusion)] \(.displayTitle) \(.createdAt)"'
      done
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
fi

# ---- Download wheels ------------------------------------------------------
mkdir -p "$OUTDIR"

for entry in "${WORKFLOWS[@]}"; do
  IFS=':' read -r wf artifact desc <<< "$entry"
  rid=$(get_latest_run "$wf")
  if [ -z "$rid" ]; then
    echo "WARNING: No successful run for '$wf'  --  skipping $desc"
    continue
  fi

  subdir="$OUTDIR/$desc"
  mkdir -p "$subdir"
  echo "Downloading $desc (run #$rid) ..."
  if gh run download "$rid" --repo "$REPO" --name "$artifact" --dir "$subdir" 2>/dev/null; then
    echo "  -> $subdir/"
  else
    echo "  Trying full run download for $artifact ..."
    tmpdir=$(mktemp -d)
    gh run download "$rid" --repo "$REPO" --dir "$tmpdir" 2>/dev/null || true
    if [ -d "$tmpdir/$artifact" ]; then
      mv "$tmpdir/$artifact"/*.whl "$subdir/" 2>/dev/null || true
      rm -rf "$tmpdir"
      echo "  -> $subdir/"
    else
      rm -rf "$tmpdir"
      echo "  WARNING: artifact '$artifact' not found in run #$rid  --  skipping"
    fi
  fi
done

# ---- Show inventory -------------------------------------------------------
echo ""
echo "=========================================="
echo "  Wheel inventory"
echo "=========================================="
wheels=()
while IFS= read -r w; do wheels+=("$w"); done < <(find "$OUTDIR" -name '*.whl' -type f | sort)
if [ ${#wheels[@]} -eq 0 ]; then
  echo "  (no wheels downloaded)"
  echo ""
  echo "Possible causes:"
  echo "  - CI runs may still be in progress"
  echo "  - No successful runs exist on the master branch"
  echo "  - You can check with: ./tools/release.sh --list"
  exit 1
fi
for w in "${wheels[@]}"; do
  echo "  $w"
done

# ---- Checksums ------------------------------------------------------------
echo ""
echo "=========================================="
echo "  SHA256 checksums"
echo "=========================================="
sha256sum "${wheels[@]}" | tee "$OUTDIR/SHA256SUMS"

# ---- Upload instructions --------------------------------------------------
echo ""
echo "=========================================="
echo "  Upload to PyPI (manual step)"
echo "=========================================="
echo ""
echo "First, register the PyPI project (one-time):"
echo "  1. Go to https://pypi.org/manage/projects/"
echo "  2. Create project 'c2ImageD11'"
echo ""
echo "Set up Trusted Publisher (OIDC  --  no token needed):"
echo "  1. Go to https://pypi.org/manage/account/publishing/"
echo "  2. Add a pending publisher:"
echo "       PyPI Project: c2ImageD11"
echo "       Owner: jonwright"
echo "       Repository: c2ImageD11"
echo "       Workflow name: publish.yml"
echo "       Environment: pypi-publish"
echo ""
echo "Then upload:"
echo ""
echo "  twine check $OUTDIR/*/*.whl"
echo "  twine upload $OUTDIR/*/*.whl"
echo ""
echo "Or upload per-arch:"
for w in "${wheels[@]}"; do
  echo "  twine upload $w"
done
echo ""
echo "=========================================="
echo "  ppc64le"
echo "=========================================="
echo ""
echo "No CI runner available for ppc64le."
echo "Build manually on a ppc64le machine:"
echo ""
echo "  git clone https://github.com/jonwright/c2ImageD11.git"
echo "  cd c2ImageD11"
echo "  pip install meson ninja numpy setuptools wheel auditwheel"
echo "  mkdir -p build/libc2ImageD11 && cd build/libc2ImageD11"
echo "  meson setup ../../lib && ninja"
echo "  cp _cImageD11.so ../../c2ImageD11/_cImageD11_ppc64le.so"
echo "  cd ../.."
echo "  python setup.py bdist_wheel"
echo "  auditwheel repair --plat manylinux_2_28_ppc64le dist/*.whl -w dist/"
echo "  twine upload dist/*ppc64le*.whl"
echo ""
