#!/bin/zsh
set -eu

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT_DIR="$ROOT/lab_assistant/integrations/slack"

"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/socket_mode_bridge.py"
