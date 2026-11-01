#!/usr/bin/env bash
# Dev helper for AnkiPdffer.
#
#   dev/dev.sh sync       copy this working tree into your real Anki add-ons folder
#   dev/dev.sh watch      sync on every change (needs `fswatch`, falls back to polling)
#   dev/dev.sh check      headless regression checks (real add-on code, temp collection)
#   dev/dev.sh preview    render dialog screenshots + sample PDFs -> dev/out/index.html
#   dev/dev.sh sandbox    start Anki with a throw-away profile + sample deck + this add-on
#   dev/dev.sh sandbox-reset   same, but re-create the sample data first
#   dev/dev.sh status     show what is installed vs. this tree
#
# `sync` never deletes anything in the target and never touches your user data
# (settings.json, meta.json, last_export_log.txt). Restart Anki after syncing.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ANKI_BASE="${ANKI_BASE:-$HOME/Library/Application Support/Anki2}"
TARGET="${TARGET:-$ANKI_BASE/addons21/anki-pdffer-dev}"
SANDBOX="${SANDBOX:-$REPO/dev/out/sandbox}"
ANKI_APP="${ANKI_APP:-/Applications/Anki.app/Contents/MacOS/Anki}"

EXCLUDES=(
  --exclude ".git" --exclude ".gitignore" --exclude "dev/" --exclude "dist/"
  --exclude "__pycache__/" --exclude "*.pyc" --exclude ".DS_Store"
  --exclude "settings.json" --exclude "meta.json" --exclude "last_export_log.txt"
)

version() { python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['human_version'])" "$1/manifest.json" 2>/dev/null || echo "?"; }

do_sync() {
  if pgrep -x Anki >/dev/null 2>&1; then
    echo "note: Anki is running - restart it to load the new code."
  fi
  mkdir -p "$TARGET"
  rsync -a "${EXCLUDES[@]}" "$REPO/" "$TARGET/"
  # Anki's own add-on manager rewrites meta.json; only keep its version label current.
  if [ -f "$TARGET/meta.json" ]; then
    python3 - "$TARGET/meta.json" "$(version "$REPO")" <<'PY'
import json, sys
path, ver = sys.argv[1:3]
try:
    meta = json.load(open(path))
    meta["human_version"] = ver
    json.dump(meta, open(path, "w"))
except (OSError, ValueError):
    pass
PY
  fi
  echo "synced $(version "$REPO") -> $TARGET"
}

case "${1:-status}" in
  sync) do_sync ;;

  watch)
    do_sync
    if command -v fswatch >/dev/null 2>&1; then
      echo "watching (fswatch) - Ctrl+C to stop"
      fswatch -o -e '/\.git/' -e '/dev/out/' -e '__pycache__' "$REPO" | while read -r _; do do_sync; done
    else
      echo "watching (polling every 2s, install fswatch for instant sync) - Ctrl+C to stop"
      last=""
      while sleep 2; do
        now="$(find "$REPO" -path "$REPO/.git" -prune -o -path "$REPO/dev/out" -prune -o -path '*/__pycache__' -prune -o \
               -type f \( -name '*.py' -o -name '*.json' \) -newer "$TARGET/manifest.json" -print 2>/dev/null | head -1)"
        if [ -n "$now" ] && [ "$now" != "$last" ]; then do_sync; last="$now"; fi
      done
    fi
    ;;

  check) exec "$REPO/dev/run-harness.sh" check ;;

  preview)
    "$REPO/dev/run-harness.sh" shots html pdf gallery
    echo "open: $REPO/dev/out/index.html"
    ;;

  sandbox|sandbox-reset)
    [ "${1}" = "sandbox-reset" ] && rm -rf "$SANDBOX"
    [ -x "$ANKI_APP" ] || { echo "Anki not found at $ANKI_APP (set ANKI_APP)"; exit 1; }
    if [ ! -f "$SANDBOX/prefs21.db" ] || [ ! -f "$SANDBOX/User 1/collection.anki2" ]; then
      echo "seeding sandbox profile + sample collection..."
      rm -rf "$SANDBOX"
      "$REPO/dev/run-harness.sh" seed "$SANDBOX"
    fi
    # a copy, not a symlink: the add-on writes settings.json next to itself and the repo's is tracked
    mkdir -p "$SANDBOX/addons21/anki-pdffer-dev"
    rsync -a "${EXCLUDES[@]}" "$REPO/" "$SANDBOX/addons21/anki-pdffer-dev/"
    echo "starting Anki with isolated base: $SANDBOX"
    exec "$ANKI_APP" -b "$SANDBOX" -p "User 1"
    ;;

  status)
    echo "repo      $(version "$REPO")   $REPO"
    echo "installed $(version "$TARGET")   $TARGET"
    changed="$(rsync -ain "${EXCLUDES[@]}" "$REPO/" "$TARGET/" | grep -c '^>f' || true)"
    echo "files out of date in installed copy: $changed"
    ;;

  *) sed -n '2,10p' "$0"; exit 1 ;;
esac
