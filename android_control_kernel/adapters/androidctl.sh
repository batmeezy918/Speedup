#!/system/bin/sh
# Native Android capability probe.
set -eu
cmd="${1:-capabilities}"
case "$cmd" in
  capabilities)
    echo '{"capabilities":["packages","activities","filesystem.shared","intents","telemetry"]}'
    ;;
  packages)
    pm list packages -f 2>/dev/null | sed 's/^/PACKAGE /'
    ;;
  package)
    test -n "${2:-}" || { echo "usage: package <name>" >&2; exit 2; }
    dumpsys package "$2" 2>/dev/null
    ;;
  activity)
    dumpsys activity activities 2>/dev/null | head -120
    ;;
  memory)
    dumpsys meminfo 2>/dev/null | head -160
    ;;
  cpu)
    dumpsys cpuinfo 2>/dev/null | head -120
    ;;
  *)
    echo "commands: capabilities packages package activity memory cpu" >&2
    exit 2
    ;;
esac
