#!/usr/bin/env bash
# workflow.sh — build (locally), deploy, install wands on the Pi

set -euo pipefail
IFS=$'\n\t'

[[ -n "${BASH_VERSION:-}" ]] || {
  echo "ERROR: workflow.sh must be run under bash" >&2
  exit 1
}

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
load_env

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DIST_DIR="${DIST_DIR:-$PROJECT_ROOT/.dist}"

SSH_KEY="${SSH_KEY:-}"
SSH_KEY="${SSH_KEY/#\~/$HOME}"
SSH_PORT="${SSH_PORT:-}"

USE_VPN="${USE_VPN:-auto}"   # false|true|auto
OPENVPN_PROFILE_ID="${OPENVPN_PROFILE_ID:-}"
OPENVPN_BIN="${OPENVPN_BIN:-/Applications/OpenVPN Connect/OpenVPN Connect.app/Contents/MacOS/OpenVPN Connect}"

VPN_STARTED_BY_SCRIPT=false

APPLICATION_NAME="wands"
BUILD_SCRIPT="${BUILD_SCRIPT:-$SCRIPT_DIR/build.sh}"
INSTALL_SCRIPT="${INSTALL_SCRIPT:-$SCRIPT_DIR/install.sh}"

usage() {
  cat <<EOF
Usage:
  ./workflow.sh --version <version> [--build] [--deploy] [--install]

Examples:
  ./workflow.sh --version v0.1.0 --build
  ./workflow.sh --version v0.1.0 --deploy --install
  ./workflow.sh --version v0.1.0

Notes:
  - With no step flags, runs build, deploy, install.
  - --build runs scripts/build.sh locally (Pi cross-build via Docker is deferred until a uv-based Dockerfile is added back).
  - Must be run with bash, not sh.
EOF
  exit 1
}

VERSION=""
run_build=false
run_deploy=false
run_install=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      [[ $# -ge 2 ]] || die "Missing value for --version"
      VERSION="$2"
      shift 2
      ;;
    --version=*)
      VERSION="${1#*=}"
      shift
      ;;
    --build)
      run_build=true
      shift
      ;;
    --deploy)
      run_deploy=true
      shift
      ;;
    --install)
      run_install=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

[[ -n "$VERSION" ]] || die "Missing required argument: --version"

if ! $run_build && ! $run_deploy && ! $run_install; then
  run_build=true
  run_deploy=true
  run_install=true
fi

SSH_OPTS=()
if [[ -n "$SSH_KEY" ]]; then
  SSH_OPTS+=( -i "$SSH_KEY" -o IdentitiesOnly=yes )
fi
if [[ -n "$SSH_PORT" ]]; then
  SSH_OPTS+=( -o Port="$SSH_PORT" )
fi

RSYNC_SSH="ssh"
if (( ${#SSH_OPTS[@]} > 0 )); then
  RSYNC_SSH+=" ${SSH_OPTS[*]}"
fi

vpn_can_reach_pi() {
  ssh "${SSH_OPTS[@]}" \
      -o BatchMode=yes \
      -o ConnectTimeout=2 \
      "$PI" "true" >/dev/null 2>&1
}

vpn_connect() {
  [[ -n "$OPENVPN_PROFILE_ID" ]] || die "OPENVPN_PROFILE_ID is not set (needed for USE_VPN=$USE_VPN)"
  [[ -x "$OPENVPN_BIN" ]] || die "OpenVPN Connect CLI not found/executable at: $OPENVPN_BIN"

  info "VPN: connecting (profile id: $OPENVPN_PROFILE_ID)..."
  "$OPENVPN_BIN" --accept-gdpr --skip-startup-dialogs --minimize \
                 --connect-shortcut="$OPENVPN_PROFILE_ID" >/dev/null 2>&1 || true

  VPN_STARTED_BY_SCRIPT=true
}

vpn_disconnect() {
  [[ -x "$OPENVPN_BIN" ]] || return 0
  info "VPN: disconnecting..."
  "$OPENVPN_BIN" --disconnect-shortcut="$OPENVPN_PROFILE_ID" >/dev/null 2>&1 || true
  "$OPENVPN_BIN" --quit >/dev/null 2>&1 || true
}

vpn_ensure_for_remote() {
  case "$USE_VPN" in
    false) return 0 ;;
    true|auto) ;;
    *) die "USE_VPN must be one of: false|true|auto (got: $USE_VPN)" ;;
  esac

  if vpn_can_reach_pi; then
    info "VPN: not needed (Pi reachable without VPN)."
    return 0
  fi

  vpn_connect

  info "VPN: waiting for remote to become reachable..."
  for _ in {1..30}; do
    if vpn_can_reach_pi; then
      info "VPN: remote reachable."
      return 0
    fi
    sleep 1
  done

  die "VPN connected but Pi still not reachable via SSH (after 30s)."
}

cleanup() {
  if $VPN_STARTED_BY_SCRIPT; then
    vpn_disconnect
  fi
}
trap cleanup EXIT INT TERM

require_remote_vars() {
  for var in PI PI_DIR SSH_KEY; do
    require_var "$var"
  done
  [[ -f "$SSH_KEY" ]] || die "Private key file not found: $SSH_KEY"
}

require_commands() {
  local cmds=("$@")
  for cmd in "${cmds[@]}"; do
    assert_command "$cmd"
  done
}

build_step() {
  info "Building $APPLICATION_NAME version=$VERSION via $BUILD_SCRIPT"
  bash "$BUILD_SCRIPT" "$VERSION"
}

deploy_step() {
  require_remote_vars
  require_commands rsync ssh scp

  vpn_ensure_for_remote

  ARTIFACT="$APPLICATION_NAME-$VERSION.zip"
  ZIP_PATH="$DIST_DIR/$ARTIFACT"

  [[ -f "$ZIP_PATH" ]] || die "Artifact not found: $ZIP_PATH"

  info "Deploying $ARTIFACT to $PI:$PI_DIR"
  ssh "${SSH_OPTS[@]}" "$PI" "mkdir -p '$PI_DIR'"

  rsync -av --progress -e "$RSYNC_SSH" \
        "$ZIP_PATH" "${PI}:${PI_DIR}/"

  scp "${SSH_OPTS[@]}" "$INSTALL_SCRIPT" "$PI:$PI_DIR"
}

install_step() {
  require_remote_vars
  require_commands ssh

  vpn_ensure_for_remote

  info "Running install script on Pi..."
  ssh "${SSH_OPTS[@]}" "$PI" -t \
      "bash '$PI_DIR/$(basename "$INSTALL_SCRIPT")' '$APPLICATION_NAME' '$VERSION'"
}

$run_build && build_step
$run_deploy && deploy_step
$run_install && install_step

info "Workflow complete."
