#!/usr/bin/env bash
# run_health_all.sh — Re-run all health plots after corpus update.
# Run from workspace root: bash tools/run_health_all.sh
set -e
WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$WORKSPACE/out/reports/health_summary"
mkdir -p "$OUT"

echo "=== Re-running health plots ==="

python3 tools/plot_run_health.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522/Data/Spot 3" \
  --modality RMCD --sample D93 \
  --out "$OUT/D93_Spot3_RMCD_health.png"

python3 tools/plot_run_health.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/courtney_christiano_D88_run2_AAA_attodry522/Data" \
  --modality RMCD --sample D88 \
  --out "$OUT/D88_run2_RMCD_health.png"

python3 tools/plot_run_health.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/WJL_Zengde_B79_Attodry911" \
  --modality Reflectance --sample B79 \
  --out "$OUT/B79_Reflectance_health.png"

python3 tools/plot_run_health.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/Zengde_WJL_C7_Attodry911" \
  --modality PL --sample C7 \
  --out "$OUT/C7_PL_health.png"

python3 tools/plot_run_health.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/Shuai_CWB_MT48_attodry911" \
  --modality PL --sample MT48 \
  --out "$OUT/MT48_PL_health.png"

python3 tools/plot_run_health.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry" \
  --modality PL --sample A5 \
  --out "$OUT/A5_PL_health.png"

python3 tools/plot_run_health.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/courtney_christiano_D88_1+1+1_AAA_4deg_attodry911/Data" \
  --modality RMCD --sample D88 \
  --out "$OUT/D88_full_RMCD_health.png"

python3 tools/plot_run_health.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/courtney_christiano_D88_1+1+1_AAA_4deg_attodry911/Data" \
  --modality PL --sample D88 \
  --out "$OUT/D88_full_PL_health.png"

python3 tools/plot_run_health.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/courtney_christiano_D88_1+1+1_AAA_4deg_attodry911/Data" \
  --modality Reflectance --sample D88 \
  --out "$OUT/D88_full_Reflectance_health.png"

echo "=== All health plots written to $OUT ==="
ls -lh "$OUT"/*.png
