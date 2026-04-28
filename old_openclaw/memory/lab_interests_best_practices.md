# Lab interests & best practices (living synthesis)

Purpose: capture recurring guidance from Isaac + lab members about what matters (scientific framing), how to present results, and what analysis conventions are “standard” in the Xu Lab. This is intended to prevent repeating mistakes and to make future decks more aligned with the lab’s expectations.

## How to use
- When you receive feedback (DM or channel), add a short bullet under the relevant section with:
  - date
  - who said it
  - the specific recommendation
  - (optional) an example slide/plot path that illustrates the recommended style
- When starting a new analysis/deck update, skim the “Presentation norms” + “Analysis norms” sections.

---

## Presentation norms (decks, Slack summaries)
- **Academic tone over corporate tone** (2026-03-11, Isaac): avoid corporate phrasing like “hero plot”; use “key figures”, “core result plots”, “representative panels”.
- **Science-first**: emphasize results, interpretation, and next experiments; avoid file-change accounting (recurring directive).
- **Interestingness filter** (2026-03-11, Isaac): prioritize what is *interesting* in the data and explain why; connect to relevant prior literature when helpful.
- **Natural-language project references**: refer to projects by human names + experiment context, not by filesystem paths (2026-03-04, Isaac; see #open-science channel history).
- **Put text on the slide (not speaker notes)** (2026-03-17, Isaac): substantive commentary/takeaways should be readable on-slide. If layout is too dense, generate a PDF (markdown/LaTeX) instead of hiding content in notes.
- **What counts as “most interesting” (tMoTe2 2+2 transport)** (2026-03-13, Xiaodong): for Shuai’s twisted double bilayer device summaries, foreground the Landau fan / “fan diagram” features in the filling window −1→0 (often discussed as “below −1”) when present, and attach the specific fan panel(s) (not fixed-D slices) alongside the text.

## Collaboration / process norms
- **Maintain dialogue with project owners** (2026-03-11, Isaac): DM relevant people with plots + interpretation; ask 1–2 concrete questions to validate the story.
- **Record feedback when off** (2026-03-11, Isaac): explicitly note when a plot/analysis is off the mark and what was learned.
- **Proactively build a lab-knowledge network** (2026-03-17, Isaac): maintain systems so I can draw on accumulated lab context (preferences, norms, ownership) and reduce repeated mistakes + trivial questions over time.

## Analysis norms (conventions, quantitative observables)

- **Infer conventions from existing corpus** (2026-03-11, Isaac): before waiting on replies, look at older decks/scripts from the same people/project to recover plotting/analysis conventions; use DMs for confirmation/nuance.
- **Prefer the project’s established quantitative observable** (2026-03-11, open question): for reflectance/PL, confirm whether the lab wants peak-fit energy, derivative extrema, fixed-energy slices, or polarization contrasts like (L−R)/(L+R).
- **Calibrations must be verified**: gate→(n,D) conversion constants should be confirmed with the owners for each dataset.

## Where feedback is recorded
- Daily log: `memory/YYYY-MM-DD.md`
- Slide-deck feedback (recommendations/criticism): `memory/slide_deck_feedback_log.md`
- People-specific notes: `memory/people/<name>.md`
- Project-specific notes: `memory/projects/<project>.md`
- Expert routing map: `memory/slack_expert_handles.md`

## Open items (to refine)
- Define a standard “interpretation ladder” for new datasets (sanity plot → quantitative extraction → literature connection → proposed next step).
- Create short templates for DMing owners: {plot} + {claim} + {uncertainty} + {question}.
