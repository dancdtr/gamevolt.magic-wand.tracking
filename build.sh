#!/usr/bin/env bash
# build.sh

set -euo pipefail
IFS=$'\n\t'

[[ -n "${BASH_VERSION:-}" ]] || {
  echo "ERROR: build.sh must be run under bash" >&2
  exit 1
}

die()   { echo "ERROR: $*" >&2; exit 1; }
info()  { echo "▶ $*"; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_ROOT/.build"
WORK_DIR="$BUILD_DIR/work"
OUTPUT_DIR="$BUILD_DIR/dist"
DIST_DIR="$PROJECT_ROOT/.dist"

usage() {
  echo "Usage: $0 <relay|wands> [version]"
  exit 1
}

[[ $# -ge 1 ]] || usage

APP_KEY="$1"
VERSION="${2:-$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo dev)}"

case "$APP_KEY" in
  relay)
    APPLICATION_NAME="relay"
    SPEC_FILE="$PROJECT_ROOT/relay.spec"
    ;;
  wands)
    APPLICATION_NAME="wands"
    SPEC_FILE="$PROJECT_ROOT/wands.spec"
    ;;
  *)
    die "Unknown app '$APP_KEY'. Expected: relay or wands"
    ;;
esac

[[ -f "$SPEC_FILE" ]] || die "Spec file not found: $SPEC_FILE"

info "Starting build"
info "Project root: $PROJECT_ROOT"
info "App key: $APP_KEY"
info "Application name: $APPLICATION_NAME"
info "Version: $VERSION"

rm -rf "$BUILD_DIR"
mkdir -p "$WORK_DIR" "$OUTPUT_DIR" "$DIST_DIR"

GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
BUILD_TIME_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

info "Generating build_info.py"
cat > "$PROJECT_ROOT/build_info.py" <<EOF
# Auto-generated at build time. Do not edit.
VERSION = "${VERSION}"
GIT_SHA = "${GIT_SHA}"
BUILD_TIME_UTC = "${BUILD_TIME_UTC}"
APPLICATION_NAME = "${APPLICATION_NAME}"
APP_KEY = "${APP_KEY}"
EOF

info "Running PyInstaller with $SPEC_FILE"
pyinstaller \
  --workpath "$WORK_DIR" \
  --distpath "$OUTPUT_DIR" \
  --noconfirm \
  "$SPEC_FILE" \
  --log-level WARN

info "Contents of $OUTPUT_DIR:"
ls -la "$OUTPUT_DIR"

if [[ -d "$OUTPUT_DIR/$APPLICATION_NAME" ]]; then
  APP_OUTPUT="$OUTPUT_DIR/$APPLICATION_NAME"
elif [[ -f "$OUTPUT_DIR/$APPLICATION_NAME" ]]; then
  APP_OUTPUT="$OUTPUT_DIR"
else
  die "Cannot find built output for '$APPLICATION_NAME' in $OUTPUT_DIR"
fi

ZIP_FILE="${APPLICATION_NAME}-${VERSION}.zip"
ZIP_PATH="$DIST_DIR/$ZIP_FILE"

info "Creating zip: $ZIP_PATH"
(
  cd "$APP_OUTPUT"
  zip -r -q "$ZIP_PATH" .
)

[[ -f "$ZIP_PATH" ]] || die "Failed to create zip: $ZIP_PATH"

info "✅ Build complete: $ZIP_PATH"