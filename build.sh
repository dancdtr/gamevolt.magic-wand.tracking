#!/usr/bin/env bash
# build.sh

set -euo pipefail
IFS=$'\n\t'

# ─── Ensure Bash ──────────────────────────────────────────────────────────────
[[ -n "${BASH_VERSION:-}" ]] || {
  echo "ERROR: build.sh must be run under bash" >&2
  exit 1
}

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

# ─── Paths ───────────────────────────────────────────────────────────────────
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLICATION_NAME="wand_demo"

BUILD_DIR="$PROJECT_ROOT/.build"
WORK_DIR="$BUILD_DIR/work"
OUTPUT_DIR="$BUILD_DIR/dist"
DIST_DIR="$PROJECT_ROOT/.dist"

# ─── Version ─────────────────────────────────────────────────────────────────
VERSION=${1:-$(git describe --tags --always 2>/dev/null || git rev-parse --abbrev-ref HEAD)}
[[ -n "$VERSION" ]] || die "Could not determine version; pass it explicitly."
info "Starting Build for version $VERSION"

# ─── Prepare directories ───────────────────────────────────────────────────────
info "Resetting build dirs → $WORK_DIR, $OUTPUT_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$WORK_DIR" "$OUTPUT_DIR"

info "Ensuring dist dir exists → $DIST_DIR (old ZIPs kept)"
mkdir -p "$DIST_DIR"

# ─── Run PyInstaller ───────────────────────────────────────────────────────────
info "Running PyInstaller → workpath=$WORK_DIR, distpath=$OUTPUT_DIR"
pyinstaller \
  --workpath "$WORK_DIR" \
  --distpath "$OUTPUT_DIR" \
  --noconfirm \
  "$PROJECT_ROOT/$APPLICATION_NAME.spec" \
  --log-level WARN

# ─── Inspect what landed in OUTPUT_DIR ─────────────────────────────────────────
info "Contents of $OUTPUT_DIR:"
ls -l "$OUTPUT_DIR"

# ─── Find the actual app output (folder or single exe) ────────────────────────
# If PyInstaller made a folder named $APPLICATION_NAME, use that; otherwise use OUTPUT_DIR directly
if [[ -d "$OUTPUT_DIR/$APPLICATION_NAME" ]]; then
  APP_OUTPUT="$OUTPUT_DIR/$APPLICATION_NAME"
elif [[ -f "$OUTPUT_DIR/$APPLICATION_NAME" ]]; then
  APP_OUTPUT="$OUTPUT_DIR"
else
  die "Cannot find built application in $OUTPUT_DIR"
fi
info "Detected application output at → $APP_OUTPUT"

# ─── Patch version in appsettings.yml (if present) ───────────────────────────
APP_SETTINGS="$APP_OUTPUT/appsettings.yml"
if [[ -f "$APP_SETTINGS" ]]; then
  info "Updating version in appsettings.yml to $VERSION"
  jq --arg version "$VERSION" \
     '.version = $version' \
     "$APP_SETTINGS" > "$APP_SETTINGS.tmp" \
  && mv "$APP_SETTINGS.tmp" "$APP_SETTINGS"
else
  info "No appsettings.yml at $APP_SETTINGS; skipping version bump"
fi

# ─── Zip up into .dist ─────────────────────────────────────────────────────────
ZIP_FILE="${APPLICATION_NAME}-${VERSION}.zip"
ZIP_PATH="$DIST_DIR/$ZIP_FILE"
info "Zipping up $APP_OUTPUT → $ZIP_PATH"
(
  cd "$APP_OUTPUT"
  zip -r -q "$ZIP_PATH" .
)

[[ -f "$ZIP_PATH" ]] \
  && info "✅ Build ZIP created at $ZIP_PATH" \
  || die "❌ Failed to create ZIP at $ZIP_PATH"

info "Build task complete."
