# TOOLS.md (Workspace Tool Boundaries)

Canonical operating model: `OPERATING_MODEL.md`.

## Inputs (read-only)

- `data/` (especially `data/dropbox_cache/`)

## Outputs (derived)

- `state/`: sync + ingestion checkpoints
- `index/`: durable, queryable memory (`*.jsonl`, routing rules)
- `out/`: generated artifacts for humans/Slack
- `reports/`: dated run logs/audits
- `memory/`: narrative notes/decisions

## Dropbox (cursor + local cache)

- Daily sync: `python3 tools/dropbox_sync.py`
  - Uses Dropbox cursor delta (fast; avoids full remote tree walk)
  - Downloads only changed files, writes `state/delta_manifest.json`
  - State: `state/dropbox_cursor_state.json`
  - Token source:
    - prefer `DROPBOX_ACCESS_TOKEN`, else read from rclone remote token (and trigger rclone refresh on expiry)
- Extra context fetch (heartbeat only, bounded):
  - Write paths to `out/extra_context_paths.txt`
  - Run: `python3 tools/dropbox_sync.py --paths-only --paths-file out/extra_context_paths.txt`


## Active run monitoring

Triggered when an experimenter announces a run on Slack. Runs at file-level granularity during active measurements, independent of the nightly ingest pipeline.

- Register a new run (call when a Slack trigger fires):
  - `python3 tools/start_monitor_run.py --dropbox-dir "tMoTe2_Measuring/..." --modality RMCD --sample D93 --experimenter Yifan --context "..."`
  - Writes to: `state/active_runs.json`
- Poll active runs (call after targeted sync, each heartbeat while runs are active):
  - `python3 tools/poll_monitor.py --no-dry-run --json`
  - Output: JSON with `decision` (alert/suppress/watch) and `slack_message` for alerts
- Stop monitoring a run:
  - `python3 tools/start_monitor_run.py --stop --run-id <id>`
- Back-test / replay a past run:
  - `python3 tools/replay_monitor.py --dir "data/dropbox_cache/..." --modality RMCD --sample D93 -v`
- Plot a single file (PL spectrum, RMCD loop/gate map, or reflectance dR/R) — auto-detects type:
  - `python3 tools/quick_plot.py <path_to_mat_file>`
  - Output: `out/plots/<stem>_<modality>_plot.png` (path printed to stdout; attach via Slack filePath)
- Compact run status — file counts, quality distribution, flag summary, metric trends:
  - `python3 tools/inspect_run.py [--run-id <id>] [--n 5]`
  - Output: <200 tokens of plain text, optimized for LLM reading
- Timeline health plot — anomaly score per file across the full run directory:
  - `python3 tools/plot_run_health.py --dir "data/dropbox_cache/..." --modality RMCD`
  - Output: `out/plots/<stem>_health.png` with score bars + key physics metric trend

## Physics corpus (state/corpus/)

A growing reference library of physics feature vectors extracted from known-good data.
New files are compared against the corpus at analysis time; statistically unusual files
get `corpus_outlier_feature` or `corpus_globally_unusual` flags (score += 0.2).

Collections and their feature keys:
- `PL` — peak_energy_eV, peak_snr, integrated_intensity, background_level, nan_gate_fraction
- `RMCD_hysteresis` — coercive_field_T, saturation_contrast, saturation_high/low_B, loop_area, B range
- `RMCD_gate_map` — rmcd_mean/std/range, fill_fraction, gate voltage ranges
- `Reflectance` — resonance_center_eV, dRR_amplitude, resonance_dip_depth

- Seed/update corpus from historical data:
  - `python3 tools/build_corpus.py --dir "data/dropbox_cache/..." --modality RMCD --sample D93`
  - Only adds files with no hard errors; bad files are skipped to keep corpus clean
- Query corpus for a specific file:
  - `python3 tools/query_corpus.py <path_to_mat_file> --modality RMCD [--sample D93]`
  - Output: nearest neighbors + z-scores for each feature (~15 lines)
- Corpus is automatically queried during `poll_monitor.py` and `replay_monitor.py`

## Cataloging / Ingestion

- Deterministic, batch-level ingest of changed dirs:
  - `python3 tools/ingest_daily.py --delta-manifest state/delta_manifest.json ...`

## Plots

- Generated plots go to `out/plots/`
- Naming convention: `{sample}_{measurement}_{description}.png`
- Examples: `C7_spot1_dualgate_PL_integrated.png`
- Use `dpi=150` for Slack-friendly file sizes
- Send via `message` tool with `filePath`

## Slack

- Heartbeat writes Slack payload to `out/slack_daily_update.md` and posts via OpenClaw CLI:
  - `openclaw message send --channel slack --target $OPENCLAW_SLACK_TARGET --message "$(cat out/slack_daily_update.md)" --json`
- Optional helper (same effect):
  - `python3 tools/post_digest_to_slack.py --digest out/slack_daily_update.md`
- Apply clarifications back to indices:
  - `python3 tools/apply_clarification.py --question-id q_... --resolution "..." --resolver "..."`
