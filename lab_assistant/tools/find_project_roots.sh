#!/bin/zsh
set -eu

ROOT="/Volumes/Xu Lab/tMoTe2_Measuring"

if [[ ! -d "$ROOT" ]]; then
  echo "Project root not found: $ROOT" >&2
  exit 1
fi

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <pattern> [pattern...]"
  exit 1
fi

for pattern in "$@"; do
  echo "Pattern: $pattern"
  find "$ROOT" -maxdepth 1 -type d | rg -i "$pattern" || true
  echo
done
