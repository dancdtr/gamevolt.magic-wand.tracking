# wands CLI - service management for the Magic Wand Tracking app on the Pi.
# Installed to ~/.bash_aliases.wands.sh (and sourced from ~/.bashrc) by
# scripts/pi/deploy.sh, or manually:
#   cat bash_aliases.wands.sh >> ~/.bash_aliases && source ~/.bash_aliases
#
# The service is a systemd *user* unit (GUI app needs the Wayland session),
# so no sudo anywhere.

wands() {
  local repo="$HOME/Code/gamevolt.magic-wand.tracking"
  case "$1" in
    start)    systemctl --user start wands ;;
    stop)     systemctl --user stop wands ;;
    restart)  systemctl --user restart wands ;;
    status)   systemctl --user status wands ;;
    enable)   systemctl --user enable wands ;;
    disable)  systemctl --user disable wands ;;
    # NB: --user-unit (reads system journal), not --user -u (needs persistent user journal)
    logs)     shift; journalctl --user-unit wands -f "$@" ;;
    edit)
      nano ~/.config/systemd/user/wands.service && systemctl --user daemon-reload
      echo "run 'wands restart' to apply"
      ;;
    run)
      # foreground run in this terminal (stop the service first to avoid two instances)
      systemctl --user is-active --quiet wands && { echo "service running - 'wands stop' first"; return 1; }
      UV_NO_DEV=1 "$repo/scripts/run.sh" "${@:2}"
      ;;
    sync)     (cd "$repo" && "$HOME/.local/bin/uv" sync --no-dev) ;;
    settings) nano "$repo/wands_app/appsettings.env.yml" && echo "run 'wands restart' to apply" ;;
    version)
      if [ -f "$repo/.deploy_info" ]; then cat "$repo/.deploy_info"; else echo "no .deploy_info (not deployed via deploy.sh)"; fi
      ;;
    help|*)
      cat <<'EOF'
wands <command>
  start | stop | restart | status    manage the systemd user service
  enable | disable                   boot persistence on/off
  logs [-n N]                        follow journalctl --user -u wands
  edit                               edit unit file, daemon-reload on save
  run [args]                         run in foreground from source (service must be stopped)
  sync                               uv sync --no-dev (refresh venv)
  settings                           edit per-Pi appsettings.env.yml
  version                            deployed commit info (.deploy_info)
  help                               this table
EOF
      ;;
  esac
}
