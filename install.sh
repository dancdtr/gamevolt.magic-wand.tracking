#!/usr/bin/env bash
# install.sh — unpack wand_demo on the Pi (no systemd service)

set -euo pipefail
IFS=$'\n\t'

die()  { echo "ERROR: $*" >&2; exit 1; }
info() { echo "$*"; }

# ─── Don’t run as root ────────────────────────────────────────────────────────
if [[ $EUID -eq 0 ]]; then
  die "Run this script as the target user (not with sudo)."
fi

# ─── Configuration ────────────────────────────────────────────────────────────
APPLICATION_NAME="wand_demo"

USER="$(id -un)"
GROUP="$(id -gn)"
DEPLOY_BASE="${DEPLOY_BASE:-/home/$USER/CDTR}"

CURRENT_DIR="$DEPLOY_BASE/Current"
INSTALL_DIR="$CURRENT_DIR"
ENV_FILE="appsettings.env.yml"

# ─── Args ─────────────────────────────────────────────────────────────────────
[[ $# -eq 1 ]] || die "Usage: $0 <version>"
VERSION=$1
ZIP_FILE="$APPLICATION_NAME-$VERSION.zip"
ZIP_PATH="$DEPLOY_BASE/$ZIP_FILE"

# ─── Sanity ───────────────────────────────────────────────────────────────────
info "Installing $APPLICATION_NAME version $VERSION"
[[ -f "$ZIP_PATH" ]] || die "Cannot find zip at $ZIP_PATH"
command -v unzip >/dev/null || die "unzip not found"

# ─── Preserve environment file ────────────────────────────────────────────────
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

if [[ -f "$INSTALL_DIR/$ENV_FILE" ]]; then
  info "Preserving $ENV_FILE"
  mv "$INSTALL_DIR/$ENV_FILE" "$TEMP_DIR/$ENV_FILE"
else
  info "No existing $INSTALL_DIR/$ENV_FILE to preserve"
fi

# ─── Deploy new version ───────────────────────────────────────────────────────
info "Preparing $DEPLOY_BASE"
mkdir -p "$DEPLOY_BASE"
mkdir -p "$CURRENT_DIR"

info "Extracting $ZIP_FILE into $CURRENT_DIR"
rm -rf "$CURRENT_DIR"/*
unzip -o -q "$ZIP_PATH" -d "$CURRENT_DIR"

# restore environment file
if [[ -f "$TEMP_DIR/$ENV_FILE" ]]; then
  info "Restoring $ENV_FILE"
  mv "$TEMP_DIR/$ENV_FILE" "$INSTALL_DIR/$ENV_FILE"
fi

# ─── Ownership & permissions ──────────────────────────────────────────────────
EXECUTABLE="$INSTALL_DIR/$APPLICATION_NAME"

if [[ -f "$EXECUTABLE" ]]; then
  info "Marking $EXECUTABLE as executable"
  chmod +x "$EXECUTABLE"
else
  info "WARNING: Expected executable not found at $EXECUTABLE"
fi

info "Fixing permissions under $DEPLOY_BASE"
sudo chown -R "$USER:$GROUP" "$DEPLOY_BASE"
sudo mkdir -p "$DEPLOY_BASE/Logs"
sudo chown -R "$USER:$GROUP" "$DEPLOY_BASE/Logs"
sudo chmod 755 "$DEPLOY_BASE/Logs"

info "Install complete."
info "You can run the app with:"
echo "  $EXECUTABLE"
