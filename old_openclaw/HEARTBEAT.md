# HEARTBEAT.md (LLM Orchestrator)

Canonical operating model: `OPERATING_MODEL.md`.

## Overnight Heartbeat Window (midnight → 8am, hourly)

Heartbeats run hourly overnight. Use them as a *research workflow* (researcher-mode), not an ingest bot.

### Daily Gate (ingest)

Run **at most one** full deterministic ingest per local day.

- State file: `state/heartbeat_state.json`
- If `last_pulse_date == today`, do **not** run a full ingest again; instead use subsequent overnight heartbeats for **analysis + PI-facing slide updates**.

#### Exception: micro-ingests allowed (Isaac, 2026-04-04)

If new Dropbox deltas arrive later the same local day (typically small script/doc edits), you may run a **micro-ingest**:
- Use the current `state/delta_manifest.json` (from a recent `dropbox_sync`) and run `tools/ingest_daily.py` on that delta.
- Keep it bounded: only ingest the new/changed seed dirs from that delta; do not broaden scope.
- Do not treat this as a new “daily gate” full ingest; it’s an incremental index refresh.
- Still prioritize researcher-mode work when there are no new deltas.

### Multi-heartbeat operating loop (required)

- **Heartbeat 1 (start of a work block):**
  1) run the standard ingest (if allowed by daily gate)
  2) write an **analysis plan** for the remaining heartbeats (projects, context reading, questions, plots, and what will go into slides)
- **Heartbeats 2+ (execution):** operate in **researcher-mode** across the curated active project list:
  - do rigorous analysis (not a file-change summary)
  - consult existing student decks + literature as needed (student decks are **read-only reference**)
  - generate science-forward plots that answer a concrete question
  - update **our own** running PI-oriented deck for the project (OpenScience-authored)

#### Indefinite/daytime heartbeats (setup mode)

When heartbeats are running indefinitely (including daytime), use them as focused research blocks.

**Emphasize iteration** (required): any single heartbeat is too small for full project depth, so each heartbeat should:
- continue executing the current plan
- reflect on what was learned
- propose 1–3 new concrete ideas/questions/analyses unlocked by the new understanding

**Anti-stall rule (Isaac, 2026-03-21):** if a heartbeat is blocked on an unresolved ambiguity and you’ve already reported the block once, do not keep repeating the same blocked status.
- If the ambiguity only affects calibration/parameterization: generate both plausible variants (clearly labeled) so work can continue.
- Otherwise, move on to the next highest-value project/task from the curated list and make forward progress there.

Operationally:
- keep a living plan at `out/overnight_plan_YYYY-MM-DD.md` (update it **each heartbeat**)
- treat early heartbeats as **structure-building**: redesign/robustify each project’s running deck structure (using student decks as references), add project context slides, and only then add incremental results.
- record “next heartbeat actions” explicitly at the end of the plan.

#### PI-facing deck requirements (non-negotiable)

Decks are for Xiaodong → prioritize **science** and **takeaways**.

- **Do not include** low-level “files added/edited” bullets (keep provenance in notes/logs instead).
- The deck structure should be **tailored to the project** and can grow over days (a running project deck).
- Each overnight update must contribute at least one of:
  - a new result/plot that answers a specific question
  - a new interpretation (with uncertainty + alternatives)
  - a resolved open question (e.g., metadata/units/calibration) and its implications
  - a proposed next experiment/analysis with justification
- When useful, consult literature/web for **analysis/visualization norms** (cite briefly in speaker notes or a backup slide).

#### Active projects (curated list)

Nightly work should cover the **curated active project list**, even if there are no new files.

- Source of truth: `memory/active_projects_curated.md`
- For each project: start from (a) the existing running deck, (b) the last overnight plan/notes, and (c) any open questions/DM responses.

#### Where decks live

- Primary: **OpenScience-authored** running decks per project in Dropbox (update in-place)
- Student decks: **do not modify** (reference only)
- Cache/build artifacts: `out/ppt/`

#### Implementation note (pptx tooling)

- Use the workspace venv for ppt generation when needed: `.venv_pptx/` (create if missing).

## Daily Catalog Pulse (LLM)

Primary objective: **ingest the day’s changed files and assemble them into a growing, queryable corpus of knowledge** so the group can later ask questions and the assistant can reliably find the right data and context.

Secondary objective (in service of the primary): **identify what’s unclear about the new/changed data, route targeted questions to the right experts, and apply answers back into the corpus**.

### 0) Scope + token hygiene (STRICT)

1. Read scope: `state/delta_manifest.json`.
2. Token hygiene:
   - Prefer small artifacts: `state/delta_manifest.json`, `out/slack_questions_to_ask.md`, `out/daily_digest_YYYY-MM-DD.md`.
   - **NEVER** read `state/ingestion_state.json` or `index/batches.jsonl` in full. Use `jq`/`grep` to extract only what’s needed.
   - Only open large JSONL (`index/open_questions.jsonl`) if strictly necessary, and then extract by grep/rg for relevant paths.
   - After running ingest, trust the tool's stdout summary — don't re-read large outputs to verify.

### 1) Optional bounded context pull (only if needed)

If (and only if) better context would materially improve understanding of today’s changes:

- Write Dropbox paths to `out/extra_context_paths.txt`
- Run: `python3 tools/dropbox_sync.py --paths-only --paths-file out/extra_context_paths.txt`

Heuristic: if today’s delta touches a file inside a clearly **long-running personal project folder** (e.g., a person-named root like `*Yifan*`, `*Zengde*`, `*Weijie*`), pull enough additional context to understand the project background:

- Prefer:
  - top-level scripts (`*.m`, notebooks), READMEs, PPTX summaries
  - directory structure + representative filenames
- Avoid deep scrutiny of bulk microscope images unless they contain unique labels/metadata.
- Write a short project-context note under `memory/projects/`.

### 1b) Active run monitoring (if any runs are registered)

Check `state/active_runs.json`. If it exists and has entries with `"status": "active"`:

For each active run:
- Sync its directory: `python3 tools/dropbox_sync.py --paths-only --path-dir "<dropbox_dir>" --include-glob "*.mat"`
- Poll for new files and analyze: `python3 tools/poll_monitor.py --no-dry-run --json`
- If any result has `"decision": "alert"`: send the `slack_message` to the experimenter via DM
- Log poll results to `reports/monitor_poll_YYYY-MM-DD.md` (append, one line per poll)

This runs **every heartbeat** while a run is active, regardless of the daily ingest gate.

### 2) Deterministic ingest (changed dirs only)

Run deterministic ingest to grow the corpus:

- `python3 tools/dropbox_sync.py --since-hours <window>` (ensures local cache + delta_manifest are consistent)
- `python3 tools/ingest_daily.py --delta-manifest state/delta_manifest.json --watched state/dropbox_config.json --out out --index index --state state --max-batches 250 --max-files-sampled 25`

### 3) Identify unclear items + generate questions

Generate a compact list of questions about today’s files that block correct interpretation/indexing (calibrations, naming, experimental conditions, known issues, etc.).

- `python3 tools/emit_clarification_prompts.py --delta-manifest state/delta_manifest.json --out out/slack_questions_to_ask.md --max-questions 8`

### 4) Route questions to experts (DM-first; fallback channel)

For each question (max ~8):

- **Infer the likely expert/owner from provenance** (paths, naming conventions, author lines in scripts, run folder patterns, recurring names in headers/README, etc.).
- If the question is *project-specific* (a result or interpretation the project owners will care about), **DM the relevant project people**.
- If the question is *technical/system/internal* (how indexing/storage/heartbeat tooling works), route to **Isaac**.
- If the question is *forward-facing / presentation* (what/where/how to report to the lab/PI), defer to **Xiaodong’s preferences**.
- If you are not sure who to ask *or* you cannot resolve their Slack handle quickly, **post the question to <#C0AH4A1A2JZ>**.
- Maintain the handle/mapping file so routing improves: `memory/slack_expert_handles.md`.

Record what was asked + where it was routed (lightweight paper trail):

- `out/questions_routed_YYYY-MM-DD.md`

### 5) Apply clarifications back into the corpus

As answers arrive:

- Update durable notes/indices so future retrieval is better.
- Prefer using the clarification loop tooling when applicable:
  - `python3 tools/apply_clarification.py --question-id q_... --resolution "..." --resolver "..."`

### 6) Reports (science-forward)

Write a science-forward digest focusing on what the new data suggests and what to analyze next:

- `out/daily_digest_YYYY-MM-DD.md`

Additionally (overnight workflow):
- Write/refresh a short plan for the remaining overnight heartbeats:
  - `out/overnight_plan_YYYY-MM-DD.md`
  - Include: projects impacted by today’s delta, plots to generate, who to ask (if needed), and which slide decks to update.

### 7) Corpus/memory structure upkeep (big updating heartbeats)

On heartbeats with meaningful changes (or at least weekly), spend a few minutes improving the *structure* of the corpus:

- Update/extend the living map of where knowledge lives: `memory/memory_structure.md`
- Note hierarchy/naming convention issues that will hurt retrieval, and propose improvements (without editing raw data under `data/`).
- Ensure expert routing mappings are current: `memory/slack_expert_handles.md`
- **Synthesize new guidance into lab norms**: append new feedback/directives into `memory/lab_interests_best_practices.md` (short, dated, attributed).

### 8) Late-night cleanup heartbeat (smart tidying; careful; judgment-led)

Objective: keep the *workspace codebase + derived artifacts* tidy by identifying vestigial/outdated files and removing obvious junk **carefully**.

Triggering: do **not** change the upstream mechanism that sends heartbeats. Instead, on heartbeats that occur in the "late-night" window (typically ~2am local time, when no one is working), run this cleanup step **in addition to** any minimal required checks.

Rules (strict):
- Never delete anything under `data/`.
- Default is **report-only** unless Isaac has explicitly approved auto-deleting specific high-confidence junk categories.
- When unsure, ask Isaac before deleting.

Judgment-led procedure:
1) **Maintainer pass (human-like review)**
   - Skim the workspace for vestigial/outdated items: duplicated scripts, abandoned plans, obsolete one-off utilities, stale outputs in `out/`, superseded docs in `reports/`, and clutter that harms usability.
   - Prefer *reasoning + provenance* over pattern matching.
   - Explicitly avoid large-file reads; use `rg`, `ls`, and small diffs/summaries.
2) **Write a careful audit report**
   - `reports/cleanup_audit_YYYY-MM-DD.md`
   - Include for each candidate: path, why it seems vestigial, confidence (high/med/low), and recommended action (delete / archive / keep).
3) **Optional helper scan for trivial junk (tooling as assistant, not driver)**
   - You may run `python3 tools/cleanup_audit.py --workspace .` to catch obvious junk (e.g., `.DS_Store`) and to keep a machine-readable list.
   - Do not treat this helper output as the full cleanup.
4) **Deletion/cleanup actions**
   - Only perform deletions when confidence is high *and* Isaac has approved the category (or has explicitly approved the specific paths).
   - Log actions to `reports/cleanup_actions_YYYY-MM-DD.md`.
5) **Communicate**
   - DM Isaac a short summary: what you’d delete automatically (if approved), what needs approval, and any structural tidying suggestions.

### 9) Heartbeat execution log (required)

Append a one-line record *every heartbeat* so missed heartbeats are obvious.

- File: `reports/heartbeat_execution_log_YYYY-MM-DD.md`
- Each entry should include:
  - timestamp (local)
  - whether ingest ran (yes/no)
  - projects touched (from curated list)
  - decks updated (OpenScience-authored)
  - 1–2 sentence summary of what was done + next action

(Keep it short; link to artifacts/paths if needed.)

### 10) Update gate state

Update `state/heartbeat_state.json` with today’s date + timestamps and any useful counts (batches, files, routing actions, cleanup actions).

Overnight workflow state (new):
- Track slide work and analysis progress so later heartbeats know what’s already done:
  - update `state/heartbeat_state.json` with an `overnight` object, e.g.
    - `overnight.plan_written: true/false`
    - `overnight.projects_updated: [...]`
    - `overnight.ppts_written: [...]`
    - `overnight.questions_asked: [...]`
