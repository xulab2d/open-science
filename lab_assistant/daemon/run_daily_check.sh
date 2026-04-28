#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${OPENSCIENCE_PYTHON:-/opt/homebrew/bin/python3}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

"$PYTHON_BIN" "$ROOT_DIR/lab_assistant/scripts/daily_sanity_check.py" \
  --config "$ROOT_DIR/lab_assistant/daemon/config.json" \
  "$@"
