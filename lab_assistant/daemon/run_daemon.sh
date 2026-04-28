#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INTERVAL_MINUTES="${OPENSCIENCE_PULSE_INTERVAL_MINUTES:-30}"

for arg in "$@"; do
  if [[ "$arg" == "--baseline-only" ]]; then
    echo "run_daemon.sh refuses --baseline-only; run one baseline with run_pulse.sh first." >&2
    exit 2
  fi
done

while true; do
  "$ROOT_DIR/lab_assistant/daemon/run_pulse.sh" "$@" || true
  sleep "$((INTERVAL_MINUTES * 60))"
done
