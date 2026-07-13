# Review Log

Purpose:
- Compact running log of repeated wins, misses, and maintenance candidates.

How to use:
- Keep entries short.
- Record only things that could improve future behavior.
- Prefer promoting mature lessons into `core/`, `context/`, `skills/`, or `knowledge/` rather than letting them sit here indefinitely.

Entry format:
- `Date | Type | Where it belongs next | Note`

Types:
- `success`
- `failure`
- `gap`
- `promotion`

Seed entries:
- `2026-04-08 | promotion | integrations/slack/context_files.json | Added fixed context bundle so Slack turns always load mission-critical directives and navigation.`
- `2026-04-08 | promotion | knowledge/ | Shifted from prescriptive retrieval notes toward linked paper shelves plus higher-level syntheses.`
- `2026-04-11 | correction | plans/knowledge_graph_direction.md | Knowledge graph should center subject-matter facts/claims/mechanisms/evidence, not data-location over a modest lab corpus.`
- `2026-04-11 | promotion | graph/ + skills/fact-graph.md | Built first scaled fact graph from curated paper shelves, summary decks, and arXiv metadata; low-confidence auto records should be promoted only after source review.`
- `2026-04-11 | promotion | graph/sources/promotions/ | First lead-to-fact curation pass promoted 9 arXiv papers and selected D93/D6/C5 deck observations; keep future promotions dated and auditable.`
- `2026-04-13 | promotion | scripts/fact_graph_ingest_arxiv.py + graph/sources/arxiv_queries.json + scripts/fact_graph_daily_summary.py | Added arXiv noise filtering, explicit prune workflow, and a reusable fact-graph summary figure generator for daily overviews.`
- `2026-04-13 | promotion | tests/test_fact_graph.py | Fact-graph tests should check retrieval usefulness for frontier, foundations, and semantic neighborhoods, not only schema validity or file existence.`
- `2026-04-16 | promotion | context/interaction_capabilities.md + integrations/context_files.json | Made OpenScience LaTeX rendering and file-backed image uploads explicit standing context so browser turns can reliably use equations and attached-image operations.`
- `2026-04-20 | correction | daemon/run_daily_overview.sh | Overnight Codex overviews need full networked access for Slack clarification; workspace-write sandbox blocked Slack API resolution/posting.`
- `2026-04-20 | correction | codexui-xulab/src/components/content/ThreadConversation.vue | Bare path auto-linking was too permissive because it allowed spaces in relative path matches; tightened regex to stop ordinary prose turning blue/clickable.`
- `2026-04-23 | correction | context/routing.md + skills/background-cataloguing.md + scripts/daily_reasoned_overview.py | Project-specific overnight clarification should default to owner DMs, not #open-science; the prior rule left too much discretion.`
- `2026-04-23 | promotion | integrations/slack/transcript_log.py + integrations/slack/logs/ | Record inbound DMs/#open-science messages and outbound replies/clarifications in append-only JSONL so Slack interactions remain auditable ground truth and can be revisited when promoting knowledge.`
- `2026-04-28 | promotion | scripts/fact_graph_ingest_xu_publications.py + scripts/fact_graph_reconcile_duplicate_papers.py + knowledge/papers/xu_group_*.md + scripts/fact_graph_benchmark.py | Graph growth should couple broad official-publication coverage to narrower curated Xu-group shelves, duplicate-paper cleanup, and an explicit retrieval benchmark, otherwise scale adds metadata but not usable scientific memory.`
- `2026-04-28 | correction | skills/fact-graph.md + graph/README.md | Deterministic publication ingest is only the breadth layer; the real value comes from reading papers, writing compressed summaries, and promoting reusable claims and syntheses into the graph.`
- `2026-04-28 | correction | scripts/fact_graph.py + scripts/fact_graph_retrieval_comparison.py | Generic all-node graph search is the wrong interface for direct literature lookup; paper-finding should use a paper-first search path and be evaluated separately from richer claim/context retrieval.`
- `2026-07-07 | correction | context/people.md + project summaries | NAS/Dropbox presence is evidence for project/file activity, not current Xu Lab membership; use the lab current-members page plus direct user correction as roster ground truth.`
- `2026-07-07 | promotion | context/storage_layout.md + context/nas_guide.md | Lab searches should distinguish personal folders for fabrication/provenance from shared roots for complete measurements/results and instrument roots for setup/control context.`
- `2026-07-07 | gap | context/plot_preferences.md + skills/plot-generation.md + context/interaction_capabilities.md | Plot/code/artifact generation and preference recall need to be first-class: first-run refinements should become project/person memory, later runs should start from accepted conventions, and serious-science deliberation should be queued, auditable, and candidate-gated rather than pasted ad hoc into an external UI.`
