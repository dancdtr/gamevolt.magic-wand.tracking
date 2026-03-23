#!/usr/bin/env bash
# workflow.sh — build, deploy, install relay/wands

set -euo pipefail
IFS=$'\n\t'

[[ -n "${BASH_VERSION:-}" ]] || {
  echo "ERROR: workflow.sh must be run under bash" >&2
  exit 1
}

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
load_env

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DOCKERFILE="${DOCKERFILE:-Dockerfile.dev}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-gamevolt.magic-wand.tracking}"
DIST_DIR="${DIST_DIR:-$PROJECT_ROOT/.dist}"

SSH_KEY="${SSH_KEY:-}"
SSH_KEY="${SSH_KEY/#\~/$HOME}"
SSH_PORT="${SSH_PORT:-}"

USE_VPN="${USE_VPN:-auto}"   # false|true|auto
OPENVPN_PROFILE_ID="${OPENVPN_PROFILE_ID:-}"
OPENVPN_BIN="${OPENVPN_BIN:-/Applications/OpenVPN Connect/OpenVPN Connect.app/Contents/MacOS/OpenVPN Connect}"

VPN_STARTED_BY_SCRIPT=false

usage() {
  cat <<EOF
Usage:
  ./workflow.sh --app <relay|wands> --version <version> [--build] [--deploy] [--install]

Examples:
  ./workflow.sh --app relay --version v0.1.0 --build
  ./workflow.sh --app wands --version v0.1.0 --build
  ./workflow.sh --app relay --version v0.1.0
  ./workflow.sh --app relay --version v0.1.0 --deploy --install

Notes:
  - With no step flags, runs build, deploy, install.
  - Must be run with bash, not sh.
EOF
  exit 1
}

APP_KEY=""
VERSION=""
run_build=false
run_deploy=false
run_install=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)
      [[ $# -ge 2 ]] || die "Missing value for --app"
      APP_KEY="$2"
      shift 2
      ;;
    --app=*)
      APP_KEY="${1#*=}"
      shift
      ;;
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

[[ -n "$APP_KEY" ]] || die "Missing required argument: --app"
[[ -n "$VERSION" ]] || die "Missing required argument: --version"

case "$APP_KEY" in
  relay)
    APPLICATION_NAME="relay"
    INSTALL_SCRIPT="${INSTALL_SCRIPT:-install.sh}"
    ;;
  wands)
    APPLICATION_NAME="wands"
    INSTALL_SCRIPT="${INSTALL_SCRIPT:-install.sh}"
    ;;
  *)
    die "Unknown app '$APP_KEY'. Expected: relay or wands"
    ;;
esac

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

require_build_vars() {
  for var in DOCKERFILE DIST_DIR AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY; do
    require_var "$var"
  done
}

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
  require_build_vars
  require_commands docker

  info "Building app=$APP_KEY version=$VERSION"
  export DOCKER_BUILDKIT=1

  docker build \
    --platform linux/arm64 \
    --file "$DOCKERFILE" \
    --target export \
    --build-arg APP_KEY="$APP_KEY" \
    --build-arg CONDA_ENV_NAME="$CONDA_ENV_NAME" \
    --build-arg BUILD_VERSION="$VERSION" \
    --build-arg AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    --build-arg AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    --output "type=local,dest=$DIST_DIR" \
    "$PROJECT_ROOT"

  info "Artifacts exported to $DIST_DIR"
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
      "bash '$PI_DIR/$INSTALL_SCRIPT' '$APPLICATION_NAME' '$VERSION'"
}

$run_build && build_step
$run_deploy && deploy_step
$run_install && install_step

info "Workflow complete."