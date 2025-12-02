#!/usr/bin/env bash
# workflow.sh — build, deploy, install wand_demo on Raspberry Pi (no service)

set -euo pipefail
IFS=$'\n\t'

# Ensure running under Bash
[[ -n "${BASH_VERSION:-}" ]] || { echo "ERROR: workflow.sh must be run under bash" >&2; exit 1; }

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
load_env

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Static config (from .env or defaults) ────────────────────────────────────
DOCKERFILE="${DOCKERFILE:-Dockerfile.dev}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-gamevolt.magic-wand.tracking}"
INSTALL_SCRIPT="${INSTALL_SCRIPT:-install.sh}"
DIST_DIR="${DIST_DIR:-$PROJECT_ROOT/.dist}"

# SSH key paths (expand ~) and optional port
SSH_KEY="${SSH_KEY:-}"
SSH_KEY="${SSH_KEY/#\~/$HOME}"
SSH_PORT="${SSH_PORT:-}"        # set this in .env if you need a non-standard port

# Build reusable SSH options
SSH_OPTS=( -i "$SSH_KEY" -o IdentitiesOnly=yes )
if [[ -n "$SSH_PORT" ]]; then
  SSH_OPTS+=( -o Port="$SSH_PORT" )
fi

# For rsync over SSH, include the same opts
RSYNC_SSH="ssh ${SSH_OPTS[@]}"

# Required env vars (no SSH_KEY_PUB / ssh-copy-id now)
for var in DOCKERFILE DIST_DIR AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY \
           PI PI_DIR SSH_KEY; do
  require_var "$var"
done

# Ensure SSH key file exists
[[ -f "$SSH_KEY" ]] || die "Private key file not found: $SSH_KEY"

# Required commands
for cmd in docker rsync ssh scp; do
  assert_command "$cmd"
done

APPLICATION_NAME="wand_demo"

# ─── Define step functions ────────────────────────────────────────────────────
build_step() {
  info "Building version $VERSION..."
  export DOCKER_BUILDKIT=1
  docker build \
    --file "$DOCKERFILE" \
    --target export \
    --build-arg CONDA_ENV_NAME="$CONDA_ENV_NAME" \
    --build-arg AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    --build-arg AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    --build-arg BUILD_VERSION="$VERSION" \
    --output "type=local,dest=$DIST_DIR" \
    .
  info "Artifacts exported to $DIST_DIR"
}

deploy_step() {
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
  info "Running install script on Pi..."
  ssh "${SSH_OPTS[@]}" "$PI" -t \
      "bash $PI_DIR/$INSTALL_SCRIPT $VERSION"
}

usage() {
  echo "Usage: $0 <version> [--build] [--deploy] [--install]"
  echo "Without flags, runs build, deploy, install in order."
  exit 1
}

# ─── Entrypoint ────────────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  usage
fi

# First argument must be version
if [[ "$1" == --* ]]; then
  usage
fi
VERSION=$1
shift

# Initialize step flags
run_build=false; run_deploy=false; run_install=false

if [[ $# -eq 0 ]]; then
  run_build=true; run_deploy=true; run_install=true
else
  for arg in "$@"; do
    case "$arg" in
      --build)   run_build=true   ;;
      --deploy)  run_deploy=true  ;;
      --install) run_install=true ;;
      *)         usage            ;;
    esac
  done
fi

# Execute steps
$run_build   && build_step
$run_deploy  && deploy_step
$run_install && install_step

info "Installed $VERSION on $PI."
info "To run the app on the Pi, SSH in and run:"
echo "  /home/CDTR/CDTR/Current/$APPLICATION_NAME"
info "Workflow complete."
