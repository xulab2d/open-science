#!/bin/zsh
set -eu

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

python3 lab_assistant/scripts/build_reference_inventory.py \
  --manifest lab_assistant/knowledge/sources/summary_sources.json \
  --out-jsonl lab_assistant/knowledge/index/summary_inventory.jsonl \
  --out-md lab_assistant/knowledge/index/summary_inventory.md

python3 lab_assistant/scripts/build_reference_inventory.py \
  --manifest lab_assistant/knowledge/sources/literature_sources.json \
  --out-jsonl lab_assistant/knowledge/index/literature_inventory.jsonl \
  --out-md lab_assistant/knowledge/index/literature_inventory.md

python3 lab_assistant/scripts/build_reference_overview.py \
  --inventory lab_assistant/knowledge/index/summary_inventory.jsonl \
  --out lab_assistant/knowledge/canon/summary_collections.md

python3 lab_assistant/scripts/build_reference_overview.py \
  --inventory lab_assistant/knowledge/index/literature_inventory.jsonl \
  --out lab_assistant/knowledge/canon/literature_collections.md

echo "Knowledge inventories refreshed."
