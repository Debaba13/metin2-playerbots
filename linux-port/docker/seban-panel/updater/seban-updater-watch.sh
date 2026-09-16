#!/bin/sh
set -eu
SPOOL=${SEBAN_UPDATE_SPOOL:-/var/lib/docker/volumes/metin2_update-spool/_data}
OVR=${SEBAN_OVERRIDE_DIR:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}
ROOT=${SEBAN_M2_ROOT:-/opt/metin2-mt2009/mt2009-r41023-base}
mkdir -p "$SPOOL"
touch "$SPOOL/watcher"
status() {
  tmp="$SPOOL/update.status.new"
  ver=$(cat "$ROOT/VERSION" 2>/dev/null || echo unknown)
  printf 'state=%s\ntime=%s\nstep=%s\nsteps=%s\nmessage=%s\nversion=%s\n' "$1" "$(date +%s)" "$2" "$3" "$4" "$ver" > "$tmp"
  mv "$tmp" "$SPOOL/update.status"
}
status idle 0 5 'Seban updater is ready.'
while :; do
  touch "$SPOOL/watcher"
  if [ -f "$SPOOL/request" ]; then
    id=$(sed -n 's/^id=//p' "$SPOOL/request" | head -1)
    last=$(cat "$SPOOL/last-id" 2>/dev/null || true)
    if [ -n "$id" ] && [ "$id" != "$last" ]; then
      update_panel=$(sed -n 's/^update_seban_panel=//p' "$SPOOL/request" | head -1)
      case "$update_panel" in 1) ;; *) update_panel=0 ;; esac
      printf '%s\n' "$id" > "$SPOOL/last-id"
      status running 1 5 'Creating a world backup before the update.'
      : > "$SPOOL/update.log"
      printf 'Request: update_seban_panel=%s\n' "$update_panel" >> "$SPOOL/update.log"
      if SEBAN_UPDATE_PANEL="$update_panel" "$OVR/update-with-backup.sh" >> "$SPOOL/update.log" 2>&1; then
        if [ "$update_panel" = 1 ]; then
          status ok 5 5 'Playerbots updated. Seban Panel option processed; see the log for its version decision.'
        else
          status ok 5 5 'Playerbots updated. Seban Panel kept unchanged. Backup created first.'
        fi
      else
        status failed 5 5 'Update failed; see the updater log. Existing world was not removed.'
      fi
    fi
  fi
  sleep 5
done
