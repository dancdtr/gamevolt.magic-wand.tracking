#!/usr/bin/env bash
# lib.sh

die()   { echo "ERROR: $*" >&2; exit 1; }
info()  { echo "▶ $*"; }

require_var() {
  local varname=$1
  [[ -n "${!varname:-}" ]] || die "Missing required var: $varname"
}

assert_command() {
  command -v "$1" >/dev/null || die "Command not found: $1"
}

# Usage: extract_artifact <image:tag> <path_in_container> <dest_host_path>
extract_artifact() {
  local img=$1 src=$2 dst=$3
  local tmp="tmp_extract_$$"
  info "Extracting $src from $img → $dst"
  docker create --name "$tmp" "$img"
  docker cp "$tmp:$src" "$dst"
  docker rm "$tmp" >/dev/null
}

load_env() {
  local f="$(dirname "${BASH_SOURCE[0]}")/.env"
  [[ -f $f ]] && {
    set -o allexport
    # shellcheck disable=SC1090
    source "$f"
    set +o allexport
  }
}
