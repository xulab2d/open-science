# SOP: PI-facing project deck updates (overnight)

Goal: each active project gets a **science-first** update, not an ingest report.

## Audience
Xiaodong Xu (PI): wants **what’s new**, **why it matters**, **how confident**, **what next**.

## Minimum deck update structure (per project)

**Slide 1 — Project framing (stable / slowly changing)**
- Device / run / modality (transport, PL, reflectance, RMCD)
- One-sentence project question (e.g., “map magnetic signatures vs (n, D, B)”)
- Current status (1 bullet)

**Slide 2 — Overnight result (hero figure)**
- 1 large plot (clean axes/units)
- 2–3 bullets:
  - what the plot shows
  - key regime/parameter values
  - what changed vs previous expectation

**Slide 3 — Interpretation**
- 2–4 bullets: hypothesis + alternatives
- Call out confounds (drift, normalization, background subtraction, sweep-rate artifacts)

**Slide 4 — Next steps (actionable)**
- 3–6 items, each concrete ("re-run at n=..., D=... with sweep rate ...", "compare to transport channel ...")
- If blocked on metadata: one question + who to ask

Optional backup:
- literature-style comparison figure, fitting details, pipeline notes.

## Plot standards
- Units on axes; label sweep direction if relevant.
- Prefer consistent colormaps + dynamic range across comparable panels.
- Avoid tiny multi-panel grids unless they *tell a story* (use a grid as backup; pick a hero panel for the main slide).

## Provenance
- Put file paths + script names in **speaker notes** or a backup slide, not in the main narrative.

## Where to save
- `OpenScience/Summaries/PPT/<project>/` (primary)
- `out/ppt/` (cache)
