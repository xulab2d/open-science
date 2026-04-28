# Skill: Fact Graph

Use when:
- A question depends on specialized, recent, or lab-specific subject-matter knowledge.
- You need provenance-backed claims rather than general model recall.
- You are connecting papers, mechanisms, observables, project interpretations, or open questions.
- A lab-member correction should become durable scientific memory.

Procedure:
1. Search the graph before relying on memory:
- `python3 lab_assistant/scripts/fact_graph.py search "<topic>"`
 - if the task is explicitly paper-finding, prefer `python3 lab_assistant/scripts/fact_graph.py search-papers "<topic>"`
2. Load the neighborhood around the best node:
- `python3 lab_assistant/scripts/fact_graph.py neighborhood <node_id>`
3. Read the cited Markdown/paper/project sources for any claim that matters.
4. Answer from the graph plus source context, separating observation, inference, and uncertainty.
5. If the interaction creates a durable fact, claim, contradiction, convention, or open question, add it with provenance and confidence.
6. Rebuild graph views after graph edits:
- `python3 lab_assistant/scripts/fact_graph.py build-views`

Graph stance:
- The graph is not a data locator.
- File paths are evidence pointers, not the ontology.
- Prefer a few high-confidence, provenance-backed claims over many vague triples.
- Human-readable Markdown remains the explanation layer; graph neighborhoods are retrieval context.
- Low-confidence nodes from arXiv metadata or automatic deck extraction are discovery leads, not settled facts.
- Promote useful low-confidence records by reading the source and rewriting the claim with stronger provenance.
- Deterministic publication ingest is the breadth layer, not the understanding layer.
- Real utility comes from reading important papers, compressing them into reusable claims and syntheses, and linking those claims to observables, mechanisms, and project questions.

Useful targets:
- concepts
- mechanisms
- observables
- claims
- evidence
- contradictions
- open questions
- conventions

Maintenance commands:
- `python3 lab_assistant/scripts/fact_graph_ingest_paper_shelves.py`
- `python3 lab_assistant/scripts/fact_graph_ingest_xu_publications.py`
- `python3 lab_assistant/scripts/fact_graph_reconcile_duplicate_papers.py`
- `python3 lab_assistant/scripts/fact_graph_ingest_summary_decks.py`
- `python3 lab_assistant/scripts/fact_graph_ingest_arxiv.py`
- `python3 lab_assistant/scripts/fact_graph_apply_promotions.py`
- `python3 lab_assistant/scripts/fact_graph_benchmark.py`
- `python3 lab_assistant/scripts/fact_graph_retrieval_comparison.py`
- `python3 lab_assistant/scripts/fact_graph.py validate`

Promotion rule:
- Keep lead-to-fact curation in dated JSON files under `graph/sources/promotions/`.
- Promote a lead only when the source supports a reusable scientific claim, useful open question, or durable concept.
- Do not promote every low-confidence node; deletion or leaving it as a search lead is acceptable.
