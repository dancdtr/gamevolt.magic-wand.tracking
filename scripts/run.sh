#!/usr/bin/env bash
# run.sh — launch wands_app from source on a Pi.
#
# Runs locally on the Pi's desktop (double-click via the .desktop launcher, a
# terminal, or a Pi Connect screen share). Resolves the repo root from the
# script's own location, so the working directory of the caller does not matter:
# it always cd's to the repo root before launching so cwd-relative paths
# (./Logs/, the uv project + .venv) resolve correctly. appsettings.yml /
# appsettings.env.yml resolve relative to wands_app/ (via the entry path), so
# per-Pi config lives in wands_app/appsettings.env.yml.
#
# Usage:
#   scripts/run.sh [--sync] [--hold] [-- <extra args passed to python>]
#
#   --sync   run `uv sync` before launching (refresh the venv)
#   --hold   after the app exits, print the exit code and wait for Enter
#            (used by the .desktop launcher so the terminal stays open on crash)
#
# Override the entry with WANDS_ENTRY (default: wands_app.main). A value ending
# in .py runs as a script (python <path>); anything else runs as a module
# (python -m <module>). Paths are relative to the repo root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ENTRY="${WANDS_ENTRY:-wands_app.main}"
SYNC=0
HOLD=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sync) SYNC=1; shift ;;
    --hold) HOLD=1; shift ;;
    --) shift; break ;;
    *) break ;;
  esac
done

command -v uv >/dev/null || { echo "ERROR: uv not found on PATH" >&2; exit 1; }

cd "$PROJECT_ROOT"

if [[ "$SYNC" == "1" ]]; then
  echo "▶ uv sync"
  uv sync
fi

if [[ "$ENTRY" == *.py ]]; then
  RUN=(uv run python "$ENTRY")
else
  RUN=(uv run python -m "$ENTRY")
fi

echo "▶ launching $ENTRY from $PROJECT_ROOT"

if [[ "$HOLD" == "1" ]]; then
  set +e
  "${RUN[@]}" "$@"
  code=$?
  set -e
  echo
  echo "▶ $ENTRY exited with code $code"
  read -rp "Press Enter to close..." _
  exit "$code"
fi

exec "${RUN[@]}" "$@"
