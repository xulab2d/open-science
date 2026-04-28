# Org audit plan (workspace + Dropbox information architecture)

Date: 2026-03-13
Owner: OpenScience

## Goal
Reduce “where does this live?” friction by making folder roles explicit (measuring vs summaries vs running PI decks), and by consolidating conventions into a small number of canonical reference docs.

This is **report-only by default** (no moving/renaming in Dropbox unless Isaac explicitly approves specific actions).

## Scope
1) **Dropbox information architecture** (as mirrored in `data/dropbox_cache/`):
   - Identify summary/deck roots vs measurement roots.
   - Flag likely misplacements (e.g., a summary folder nested inside measurement folders).

2) **Workspace corpus structure** (`memory/`, `reports/`, `out/`, `state/`, `index/`):
   - Consolidate repeated conventions into canonical notes.
   - Ensure expert routing mappings exist for active projects.

## Non-goals / constraints
- Do not modify anything under `data/`.
- Do not move Dropbox folders/files automatically.
- Avoid large-file reads (JSONL/large MAT); use targeted `find/rg/jq` summaries.

## Canonical destinations (where knowledge should end up)
- **Conventions / “how to read our data”** → `memory/field_guide.md`
- **People + routing** → `memory/slack_expert_handles.md` (+ `memory/people/*.md` as needed)
- **Per-project context** → `memory/projects/<project>.md`
- **Audit reports (dated, immutable)** → `reports/org_audit_*.md`
- **Derived analysis artifacts** → `out/plots/`, `out/ppt/running/`

## Deliverables
### D1) Inventory report (weekly or as-needed)
`reports/org_audit_inventory_YYYY-MM-DD.md`
- Candidate “summary roots” and “measurement roots” (paths)
- Ambiguous/misplaced items (path, why it’s confusing, suggested canonical home)
- Confidence (high/med/low)

### D2) Recommended moves list (optional; requires approval)
`reports/org_audit_recommended_moves_YYYY-MM-DD.md`
- Proposed move operations (from → to)
- Rationale (discoverability, consistency)
- Risk notes (links/scripts that might break)

### D3) Compaction updates
- Update `memory/field_guide.md` with new conventions uncovered during inventory.
- Update/extend `memory/projects.md` index + per-project notes.

## Execution procedure (bounded)
1) **Snapshot structure** (no downloads beyond cache):
   - Use `find` maxdepth summaries to list top-level folders in:
     - `data/dropbox_cache/tMoTe2_Measuring/`
     - any known summaries root (if present in cache)
2) **Detect misplacements**:
   - Look for folders with names like `*summary*`, `*Summaries*`, `PPT`, `slides` nested under measurement roots.
3) **Write inventory report**:
   - Record path evidence + a minimal recommendation.
4) **(Only if approved)** execute moves via Dropbox UI/humans (not automated here).

## Current status (as of 2026-03-13)
- `memory/field_guide.md` drafted (v0.1) as the first compaction artifact.
- Cleanup audit completed separately: `reports/cleanup_audit_2026-03-13.md` (workspace tidying; report-only).
