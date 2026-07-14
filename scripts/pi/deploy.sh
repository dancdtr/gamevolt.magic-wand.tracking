#!/usr/bin/env bash
# deploy.sh — source-deploy wands_app to a Pi (run from the dev machine).
#
# rsyncs the working tree (minus build artifacts / logs / recordings) to
# ~/Code/gamevolt.magic-wand.tracking on the Pi, installs the systemd user
# unit + `wands` bash aliases, refreshes the venv, and restarts the service
# if it is running. Per-Pi config (wands_app/appsettings.env.yml) is excluded
# so a deploy never clobbers it.
#
# This is the run-from-source flow (see scripts/run.sh); the PyInstaller
# zip flow lives in scripts/workflow.sh.
#
# Usage:
#   scripts/pi/deploy.sh [host] [--no-sync] [--no-restart]
#
#   host          ssh target, default cdtr@172.30.1.114 (or $WANDS_PI)
#   --no-sync     skip `uv sync --no-dev` on the Pi
#   --no-restart  do not restart the wands service after deploy

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PI="${WANDS_PI:-cdtr@172.30.1.114}"
REMOTE_DIR="Code/gamevolt.magic-wand.tracking"
RUN_SYNC=1
RUN_RESTART=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-sync)    RUN_SYNC=0; shift ;;
    --no-restart) RUN_RESTART=0; shift ;;
    -*)           echo "ERROR: unknown flag $1" >&2; exit 1 ;;
    *)            PI="$1"; shift ;;
  esac
done

info() { echo "▶ $*"; }

GIT_SHA="$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
GIT_DESC="$(git -C "$PROJECT_ROOT" log -1 --oneline 2>/dev/null || echo unknown)"
DIRTY=""
[[ -n "$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null)" ]] && DIRTY=" (dirty working tree)"

DEPLOY_INFO="$(mktemp)"
trap 'rm -f "$DEPLOY_INFO"' EXIT
cat > "$DEPLOY_INFO" <<EOF
commit:   ${GIT_DESC}${DIRTY}
deployed: $(date -u +"%Y-%m-%dT%H:%M:%SZ") by $(whoami)@$(hostname -s)
EOF

info "Deploying ${GIT_SHA}${DIRTY} to $PI:$REMOTE_DIR"
ssh "$PI" "mkdir -p '$REMOTE_DIR'"

rsync -az --delete \
  --exclude '.git' --exclude '.venv' --exclude '.dist' --exclude '.build' \
  --exclude 'Logs' --exclude '__pycache__' --exclude '.ruff_cache' \
  --exclude '.mypy_cache' --exclude '.pytest_cache' \
  --exclude 'wands_app/recordings' --exclude 'wands_app/appsettings.env.yml' \
  --exclude '*.log' --exclude '.DS_Store' \
  "$PROJECT_ROOT/" "$PI:$REMOTE_DIR/"

scp -q "$DEPLOY_INFO" "$PI:$REMOTE_DIR/.deploy_info"

info "Installing service unit + aliases"
ssh "$PI" "
  set -e
  mkdir -p ~/.config/systemd/user
  cp '$REMOTE_DIR/scripts/pi/wands.service' ~/.config/systemd/user/wands.service
  cp '$REMOTE_DIR/scripts/pi/bash_aliases.wands.sh' ~/.bash_aliases.wands.sh
  grep -q 'bash_aliases.wands.sh' ~/.bashrc 2>/dev/null || \
    printf '\n[ -f ~/.bash_aliases.wands.sh ] && source ~/.bash_aliases.wands.sh\n' >> ~/.bashrc
  systemctl --user daemon-reload
"

if [[ "$RUN_SYNC" == "1" ]]; then
  info "uv sync --no-dev on Pi"
  ssh "$PI" "cd '$REMOTE_DIR' && ~/.local/bin/uv sync --no-dev"
fi

if [[ "$RUN_RESTART" == "1" ]]; then
  if ssh "$PI" "systemctl --user is-active --quiet wands"; then
    info "Restarting wands service"
    ssh "$PI" "systemctl --user restart wands"
  else
    info "wands service not running - start with: wands start"
  fi
fi

info "Done. Deployed: $GIT_DESC$DIRTY"
