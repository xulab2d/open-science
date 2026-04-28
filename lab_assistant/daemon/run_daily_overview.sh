#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${OPENSCIENCE_PYTHON:-/opt/homebrew/bin/python3}"
CODEX_BIN="${OPENSCIENCE_CODEX:-/opt/homebrew/bin/codex}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi
if [[ ! -x "$CODEX_BIN" ]]; then
  CODEX_BIN="$(command -v codex)"
fi

"$ROOT_DIR/lab_assistant/daemon/run_daily_check.sh" || true

PROMPT_PATH="$("$PYTHON_BIN" "$ROOT_DIR/lab_assistant/scripts/daily_reasoned_overview.py" \
  --config "$ROOT_DIR/lab_assistant/daemon/config.json")"

STAMP="$(date +%Y-%m-%d_%H%M%S_%Z)"
OUT_DIR="$ROOT_DIR/lab_assistant/daemon/overviews"
mkdir -p "$OUT_DIR"
OUT_PATH="$OUT_DIR/daily_overview_${STAMP}.md"

"$PYTHON_BIN" - "$CODEX_BIN" "$ROOT_DIR" "$OUT_PATH" "$PROMPT_PATH" "${OPENSCIENCE_CODEX_TIMEOUT_SECONDS:-1800}" <<'PY'
import subprocess
import sys
from pathlib import Path

codex_bin, root_dir, out_path, prompt_path, timeout_s = sys.argv[1:]
cmd = [
    codex_bin,
    "exec",
    "-C",
    root_dir,
    "--skip-git-repo-check",
    "-c",
    'model_reasoning_effort="medium"',
    "--sandbox",
    "danger-full-access",
    "--output-last-message",
    out_path,
    "-",
]
with Path(prompt_path).open("rb") as prompt:
    try:
        subprocess.run(cmd, stdin=prompt, check=True, timeout=int(timeout_s))
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"codex daily overview timed out after {timeout_s}s") from exc
PY

cp "$OUT_PATH" "$OUT_DIR/daily_summary_latest.md"

echo "daily_overview: $OUT_PATH"
