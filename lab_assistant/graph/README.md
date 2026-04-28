# Fact Graph

Purpose:
- Subject-matter memory for OpenScience.
- Organize facts, claims, mechanisms, observables, contradictions, conventions, and evidence.
- Improve Codex reasoning by retrieving a relevant graph neighborhood into context.

Non-goal:
- This is not primarily a data locator. NAS search, project roots, and catalog pulses handle file discovery.

How this interfaces with Codex:
- Codex receives the graph rules through `skills/fact-graph.md`.
- For a question, Codex searches the graph for relevant concepts/claims.
- Codex loads a small neighborhood of matching nodes and edges into context.
- Codex reasons over that structured evidence alongside Markdown syntheses, project notes, papers, and lab-member context.
- When a durable subject-matter lesson emerges, Codex adds or updates graph records with provenance and confidence.

Files:
- `schema.json`: allowed node/edge types and required fields.
- `nodes.jsonl`: append-friendly node records.
- `edges.jsonl`: append-friendly edge records.
- `sources/`: deterministic source configs, currently including arXiv query seeds.
- `staging/`: raw metadata fetched from external sources before promotion.
- `views/`: generated Markdown graph views for humans and Codex.

Rules:
- Every claim-like edge needs provenance.
- Keep the graph sparse and high-signal.
- Prefer a few reliable facts over many low-confidence triples.
- File/data nodes are evidence pointers only.
- Human-readable Markdown remains the explanation layer; the graph is the retrieval and relation layer.
- Deterministic publication metadata is useful for coverage and recall, but it is not a substitute for reading papers and promoting durable scientific takeaways.
- The highest-value graph growth comes from curated paper shelves, syntheses, and claim promotion after source reading.

Basic commands:
```bash
python3 lab_assistant/scripts/fact_graph.py validate
python3 lab_assistant/scripts/fact_graph.py search "RMCD hysteresis"
python3 lab_assistant/scripts/fact_graph.py search-papers "moire exciton optical signatures"
python3 lab_assistant/scripts/fact_graph.py neighborhood claim:optical_probes_primary_evidence
python3 lab_assistant/scripts/fact_graph.py build-views
```

Ingestion commands:
```bash
python3 lab_assistant/scripts/fact_graph_ingest_paper_shelves.py
python3 lab_assistant/scripts/fact_graph_ingest_xu_publications.py
python3 lab_assistant/scripts/fact_graph_reconcile_duplicate_papers.py
python3 lab_assistant/scripts/fact_graph_ingest_summary_decks.py
python3 lab_assistant/scripts/fact_graph_ingest_arxiv.py
python3 lab_assistant/scripts/fact_graph_apply_promotions.py
```

Evaluation command:
```bash
python3 lab_assistant/scripts/fact_graph_benchmark.py
python3 lab_assistant/scripts/fact_graph_retrieval_comparison.py
```

Confidence model:
- `high`: human-confirmed or directly maintained canonical fact.
- `medium`: curated paper/deck/project summary with clear provenance.
- `low`: arXiv metadata, automatically extracted deck claims, or weak/ambiguous interpretation.

Current scale:
- The initial graph is seeded from curated Markdown paper shelves, curated summary-deck text, targeted arXiv metadata, and a small manual core ontology.
- As of the first promotion pass: 296 nodes and 606 edges.
- Deck claims are intentionally conservative and should be promoted, rewritten, or removed as they are used.
- Curated promotions live in `graph/sources/promotions/` so lead-to-fact decisions remain auditable.
- Official Xu-group publication metadata can be ingested at broad coverage, but low-confidence paper nodes are only the breadth layer; curated paper shelves remain the main path to reusable claim-level facts.
