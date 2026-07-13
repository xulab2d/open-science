#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.xulab.openscience.codexui"
PLIST_SOURCE="$ROOT_DIR/launchd/${LABEL}.plist.template"
PLIST_TARGET="$HOME/Library/LaunchAgents/${LABEL}.plist"

mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SOURCE" "$PLIST_TARGET"

launchctl bootout "gui/$(id -u)" "$PLIST_TARGET" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_TARGET"
launchctl enable "gui/$(id -u)/$LABEL"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "Installed and started $LABEL"
echo "Plist: $PLIST_TARGET"
