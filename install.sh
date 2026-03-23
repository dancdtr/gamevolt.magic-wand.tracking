#!/usr/bin/env bash
# install.sh — unpack relay/wands on the Pi

set -euo pipefail
IFS=$'\n\t'

die()  { echo "ERROR: $*" >&2; exit 1; }
info() { echo "▶ $*"; }

if [[ $EUID -eq 0 ]]; then
  die "Run this script as the target user (not with sudo)."
fi

[[ $# -eq 2 ]] || die "Usage: $0 <app_name> <version>"

APPLICATION_NAME="$1"
VERSION="$2"

USER="$(id -un)"
GROUP="$(id -gn)"
# DEPLOY_BASE="${DEPLOY_BASE:-/home/$USER/CDTR/$APPLICATION_NAME}"
DEPLOY_BASE="${DEPLOY_BASE:-/home/$USER/CDTR/}"

CURRENT_DIR="$DEPLOY_BASE/Current"
INSTALL_DIR="$CURRENT_DIR"

case "$APPLICATION_NAME" in
  relay)
    ENV_FILE="appsettings_relay.env.yml"
    ;;
  wands)
    ENV_FILE="appsettings.env.yml"
    ;;
  *)
    die "Unknown application: $APPLICATION_NAME"
    ;;
esac

ZIP_FILE="${APPLICATION_NAME}-${VERSION}.zip"
ZIP_PATH="$DEPLOY_BASE/$ZIP_FILE"

info "Installing $APPLICATION_NAME version $VERSION"
[[ -f "$ZIP_PATH" ]] || die "Cannot find zip at $ZIP_PATH"
command -v unzip >/dev/null || die "unzip not found"

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

if [[ -f "$INSTALL_DIR/$ENV_FILE" ]]; then
  info "Preserving $ENV_FILE"
  mv "$INSTALL_DIR/$ENV_FILE" "$TEMP_DIR/$ENV_FILE"
else
  info "No existing $ENV_FILE to preserve"
fi

mkdir -p "$DEPLOY_BASE"
mkdir -p "$CURRENT_DIR"

info "Extracting $ZIP_FILE into $CURRENT_DIR"
rm -rf "$CURRENT_DIR"/*
unzip -o -q "$ZIP_PATH" -d "$CURRENT_DIR"

if [[ -f "$TEMP_DIR/$ENV_FILE" ]]; then
  info "Restoring $ENV_FILE"
  mv "$TEMP_DIR/$ENV_FILE" "$INSTALL_DIR/$ENV_FILE"
fi

EXECUTABLE="$INSTALL_DIR/$APPLICATION_NAME"

if [[ -f "$EXECUTABLE" ]]; then
  chmod +x "$EXECUTABLE"
  info "Marked executable: $EXECUTABLE"
else
  info "WARNING: Expected executable not found at $EXECUTABLE"
fi

sudo chown -R "$USER:$GROUP" "$DEPLOY_BASE"
sudo mkdir -p "$DEPLOY_BASE/Logs"
sudo chown -R "$USER:$GROUP" "$DEPLOY_BASE/Logs"
sudo chmod 755 "$DEPLOY_BASE/Logs"

info "Install complete."
echo "Run with: $EXECUTABLE"