#!/usr/bin/env bash
# Run the headless harness with Anki's own Python (has anki, aqt, PyQt6 + WebEngine).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ANKI_PY="${ANKI_PY:-$HOME/Library/Application Support/AnkiProgramFiles/.venv/bin/python}"
[ -x "$ANKI_PY" ] || { echo "Anki python not found: $ANKI_PY (set ANKI_PY)"; exit 1; }
exec env QT_QPA_PLATFORM=offscreen "$ANKI_PY" "$HERE/harness.py" "$@"
