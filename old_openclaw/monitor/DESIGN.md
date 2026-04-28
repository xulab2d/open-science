# Active-run monitor — design note

## What this is

A real-time monitoring subsystem for active experiments, triggered by a Slack
message and running alongside an ongoing measurement.  It is **completely
separate from the nightly heartbeat/ingest pipeline** — it runs at file
granularity, on-demand, while someone is in the lab taking data.

## How it fits into OpenClaw

```
Slack: "Starting RMCD run on D93 at D=0.375, v=-2 (Yifan)"
       ↓
OpenClaw agent receives message via Slack socket
       ↓
  python3 tools/start_monitor_run.py --dropbox-dir "..." --modality RMCD ...
  → writes state/active_runs.json
       ↓
  (OpenClaw schedules higher-frequency polls, e.g. every 2–5 min)
       ↓
  python3 tools/dropbox_sync.py --paths-only --path-dir <dir>
  python3 tools/poll_monitor.py
  → prints decision block; OpenClaw posts to Slack if decision == "alert"
       ↓
  (loop until experimenter says "done" or run is stopped)
       ↓
  python3 tools/start_monitor_run.py --stop --run-id <id>
```

## Files created

```
monitor/
  __init__.py           package marker
  schemas.py            ActiveRun, FileArrivedEvent, FileAnalysisResult,
                        RunSummary, AlertDecision, ReplayResult
  active_run.py         CRUD on state/active_runs.json
  poller.py             scan local_dir for new .mat files → FileArrivedEvents
  analyze/
    __init__.py         exports analyze_file()
    loader.py           .mat loading (scipy.io + h5py fallback)
    generic.py          file health checks (all_zeros, all_nan, tiny_file, etc.)
    pl.py               PL: peak wavelength, SNR, gate coverage
    rmcd.py             RMCD: hysteresis loop metrics + spatial map stats
    reflectance.py      Reflectance: dR/R amplitude, gate coverage, MCD
    dispatch.py         modality dispatch + anomaly scoring
  summarize.py          FileAnalysisResults → RunSummary → LLM-ready text
  adjudicate.py         LLM adjudication via tool_use → AlertDecision
  replay.py             replay a past run for back-testing

tools/
  start_monitor_run.py  register a new active run
  poll_monitor.py       one poll: detect new files, analyze, adjudicate, print
  replay_monitor.py     replay historical run for evaluation
```

## Data flow

```
New .mat file on disk
       ↓ poller.py
  FileArrivedEvent
       ↓ analyze/dispatch.py
  FileAnalysisResult   (loadable?, variables, quality_flags, modality metrics)
       ↓ summarize.py
  RunSummary           (condensed: counts, anomaly sentences, metric ranges)
       ↓ adjudicate.py
  AlertDecision        (LLM via tool_use: alert/suppress/watch + Slack draft)
       ↓ poll_monitor.py
  stdout block         (OpenClaw reads; posts slack_message if alert)
```

## Key design decisions

**File-level, not batch-level.**
Events are individual `.mat` files arriving on disk, not heartbeat snapshot
deltas.  This gives sub-minute detection latency instead of daily latency.

**The LLM is a filter, not a detector.**
All numerical detection is deterministic (quality flags, anomaly scores in
`dispatch.py`).  The LLM only adjudicates files that already have flags.
If everything looks clean, no LLM call is made → zero API cost for normal runs.

**Separation of concerns.**
Each analyzer (`pl.py`, `rmcd.py`, `reflectance.py`) knows about its modality.
`dispatch.py` routes to the right one and normalizes output.
`summarize.py` collapses multiple file results into a single human-readable
block.  The LLM never sees raw arrays.

**Dry-run default.**
All tools default to `dry_run=True`.  No API calls happen without
`--no-dry-run`, so the tools are safe to test without an API key.

**State is a simple JSON file.**
`state/active_runs.json` is a JSON list of run objects.  It is read and
written atomically by `active_run.py`.  No database needed.

---

## Quick start

```bash
# Register a run
python3 tools/start_monitor_run.py \
  --dropbox-dir "tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522/Data/Spot 3" \
  --modality RMCD --sample D93 --experimenter Yifan \
  --context "Curie-Weiss sweep. Watch for coercive field changes."

# Poll once (dry-run)
python3 tools/poll_monitor.py -v

# Poll with real LLM
ANTHROPIC_API_KEY=sk-... python3 tools/poll_monitor.py --no-dry-run

# Replay a past experiment (dry-run)
python3 tools/replay_monitor.py \
  --dir "data/dropbox_cache/tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522/Data/Spot 3" \
  --modality RMCD --sample D93 --experimenter Yifan -v
```

---

## What should come next

### Immediate (before real-time use)

1. **Install anthropic in the workspace venv**
   ```bash
   .venv/bin/pip install anthropic
   ```

2. **Add `--stop` flag to `start_monitor_run.py`** so the agent can stop a
   run when the experimenter says "done".

3. **Trigger higher-frequency sync in OpenClaw.**  When a run is active,
   the heartbeat (or a separate poller cron) should call:
   ```bash
   python3 tools/dropbox_sync.py --paths-only \
     --path-dir "<dropbox_dir>" --include-glob "*.mat"
   ```
   every 2–5 minutes, then immediately call `poll_monitor.py`.

4. **Wire Slack output.**  If `poll_monitor.py` output contains a
   `slack_message` field, the OpenClaw agent should post it to the relevant
   channel or DM.

### Near term

5. **Per-family expected parameter ranges.**  Add a
   `config/monitor_thresholds.json` that stores modality-specific ranges
   (e.g., expected PL peak 1050–1150 nm; expected RMCD coercive field
   0.1–2T for D93 at this condition).  The analyzer can then flag
   out-of-range values.

6. **Run-level context injection.**  Pass the relevant section of
   `memory/active_projects_curated.md` into the adjudication prompt so the
   LLM knows what the experimenter is *expecting* to see and can better
   distinguish "interesting physics" from "instrument problem".

7. **Parameter progression tracking.**  As files arrive with encoded
   parameters (D-field, gate voltage, temperature), track the sweep
   progression and flag if the sweep stalls at an unexpected point or
   reverses unexpectedly.

8. **Alert cooldown.**  Implement per-run cooldown (similar to the old
   alert.py) so a single bad file doesn't generate repeated alerts.

### Longer term

9. **Live Dropbox webhook** instead of polling — receive a push notification
   when a new file lands, trigger analysis immediately.

10. **Plot generation on alert.**  When a data-quality flag fires, generate
    a quick diagnostic plot (e.g., the RMCD loop, or the PL spectrum) and
    attach it to the Slack alert for immediate human verification.
