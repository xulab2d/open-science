# Fact Graph V1

Purpose:
- Build an accessible, interconnected subject-matter memory for OpenScience.
- Emphasize facts, claims, mechanisms, observables, and evidence that are too specialized, recent, or lab-specific to rely on model priors.

Non-goal:
- Do not build a graph primarily to locate experimental files. NAS search, project roots, catalog pulses, and Codex exploration already handle that well enough for the lab's data scale.

Core idea:
- Human-readable Markdown remains the canonical explanation layer.
- The graph is a compact machine-readable layer that connects concepts and claims across papers, projects, summaries, plots, and lab interactions.
- File/data nodes exist only as provenance for a claim or observation.

Candidate node types:
- `Concept`: moire filling, displacement field, valley polarization, Hund-like coupling
- `MaterialSystem`: twisted MoTe2, CrI3, WSe2/CrI3 heterostructure
- `Phenomenon`: RMCD hysteresis, PL peak splitting, Landau-fan-like structure
- `Mechanism`: moire magnetism, exchange coupling, charge transfer, optical selection rule
- `Observable`: RMCD, dR/R, PL intensity, peak energy, linewidth, coercive field
- `Condition`: temperature, magnetic field, density, displacement field, polarization, twist angle
- `Claim`: a provenance-backed scientific assertion
- `Evidence`: paper result, project plot, deck slide, analysis summary, lab-member correction
- `OpenQuestion`: unresolved interpretation or next-check item
- `Convention`: trusted conversion, plotting default, analysis preference
- `Paper`: literature source
- `Project`: local Xu Lab context

Candidate edge types:
- `supports`
- `contradicts`
- `qualifies`
- `measured_by`
- `has_condition`
- `has_observable`
- `explains`
- `predicts`
- `analogous_to`
- `derived_from`
- `preferred_for`
- `open_question_for`
- `mentioned_in`

Required provenance fields:
- source path, URL, paper key, or Slack/thread identifier
- source quote or compact paraphrase
- extraction method: deterministic, Codex, human-confirmed
- confidence: low, medium, high
- timestamp
- project scope, if local

Initial sources:
- `knowledge/papers/`
- `knowledge/syntheses/`
- `knowledge/projects/`
- `knowledge/canon/`
- curated summary decks in `/Volumes/Xu Lab/OpenScience/Summaries/PPT`
- daily overview outputs when they contain durable scientific claims
- lab-member corrections from Slack/OpenScience UI

Useful queries:
- What do we know about a concept, and what supports it?
- Which observables diagnose a proposed mechanism?
- What claims are supported by both literature and Xu Lab data?
- Where do project interpretations conflict?
- What open questions recur across multiple projects?
- Which plotting or analysis convention applies to this observable?

Build sequence:
1. Define `nodes.jsonl`, `edges.jsonl`, and a minimal schema. Done: `graph/schema.json`, `graph/nodes.jsonl`, `graph/edges.jsonl`.
2. Seed from existing Markdown knowledge files, not raw NAS data. Done for initial moire MoTe2, optical-readout, magnetism, D93, and curated paper shelves.
3. Add deterministic ingestion for summary decks. Done for curated extracted decks, with deck text as `Evidence` and conservative low/medium-confidence extracted claims.
4. Add targeted arXiv metadata discovery. Done as low-confidence `Paper` nodes and `mentions` edges only; reading/promoting papers remains a separate step.
5. Generate Markdown graph views by concept, project, evidence, paper, and claim. Done with `scripts/fact_graph.py build-views`.
6. Add lab-member interaction extraction only after Slack summaries are stable.
7. Add graph similarity/search after provenance quality is reliable.

Current first-scale build:
- 296 nodes.
- 606 edges.
- Sources include curated paper shelves, 40 curated summary-deck extracts, targeted arXiv metadata, and a small manual ontology.
- First promotion pass added dated curated facts from high-value arXiv and deck leads, including optical `nu=-1/3` FQAH, hidden transient-optical states, FQSH/TRSB nuance, putative FTI magnetic signatures, quantum-geometry remote-layer tuning, chiral superconductivity, multiband correlations, and selected D93/D6/C5 deck facts.

Next quality step:
- Use real questions to identify noisy low-confidence deck/arXiv records.
- Promote useful records into higher-confidence rewritten claims after source review.
- Add contradiction/open-question nodes when project and literature claims conflict.
