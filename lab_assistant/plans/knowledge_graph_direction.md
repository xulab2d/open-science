# Knowledge Graph Direction

Date: 2026-04-11

Question:
- Should OpenScience build a knowledge graph from lab data, project notes, literature, and lab-member interactions?

Clarification from lab feedback:
- The goal is not primarily finding experimental data. NAS search, project roots, catalog pulses, and Codex exploration are already flexible enough for a lab-scale corpus.
- The graph should organize subject-matter knowledge: facts, claims, mechanisms, observables, conventions, open questions, contradictions, and evidence links that are deep, specialized, novel, or underrepresented in general model training.
- The graph should augment scientific reasoning and discovery, not replace normal file search.

Short answer:
- Yes, but not as a heavy ontology-first graph database at the start.
- The useful first product should be a lightweight, provenance-backed fact graph that improves subject-matter recall, project interpretation, and cross-domain synthesis.
- Discovery-oriented graph analytics should come later, after extraction quality and schemas stabilize.

Relevant literature patterns:

1. Scholarly knowledge graphs
- ORKG frames papers as machine-actionable research contributions and supports comparison, templated descriptions, and community curation.
- Lesson for Xu Lab: graph value comes from structured comparison and reusable claims, not just storing disconnected triples.

2. Materials literature knowledge graphs
- MatKG and related materials KGs extract entities such as materials, properties, applications, synthesis methods, characterization methods, descriptors, and phase labels from large literature corpora.
- LLM-based materials KG work shows that extraction can support filtering by performance metrics, synthesis conditions, and application-relevant properties.
- Lesson for Xu Lab: literature KGs are useful for background retrieval and analogy, but the local value is a focused field/lab fact graph, not a global materials KG.

3. Experimental provenance graphs
- The Materials Experiment Knowledge Graph represents experiments and associated metadata/provenance in graph form.
- Lesson for Xu Lab: provenance still matters, but mainly as evidence for facts and claims. File/sample links should support scientific assertions, not become the center of the graph.

4. ELN and research data-management systems
- ELN/RDM systems emphasize automatic metadata capture to reduce manual documentation effort and link notes/files/experiments.
- Lesson for Xu Lab: if graph maintenance requires manual triple entry, it will fail. It must grow from papers, summaries, project notes, selected analysis outputs, Slack/OpenScience interactions, and Codex syntheses.

5. Latent knowledge and prediction from literature
- Materials-science embedding work showed that large corpora can encode useful latent relationships and even support prospective materials suggestions.
- Lesson for Xu Lab: discovery claims are plausible but should be treated as a long-horizon goal. Reliable discovery will more likely come from retrieval plus synthesis over high-quality claim/mechanism/evidence neighborhoods.

Recommended local architecture:

Phase 1: source-grounded fact graph
- Keep Markdown canon as the human-readable layer.
- Add a machine-readable graph store derived from papers, syntheses, decks, project notes, lab-member interactions, and selected analysis summaries.
- Every fact/edge must carry provenance: source file/message/paper, timestamp, extraction method, confidence, and whether it was human-confirmed.
- File paths should appear as evidence pointers, not as the main organizing principle.

Phase 2: concept and claim graph
- Model the graph around scientific understanding:
- `Concept`
- `Mechanism`
- `MaterialSystem`
- `Phenomenon`
- `Observable`
- `ExperimentalCondition`
- `Claim`
- `Evidence`
- `Contradiction`
- `OpenQuestion`
- `Interpretation`
- `Assumption`
- `Convention`
- `Paper`
- `Project`
- `Person`
- `Figure/Plot`
- `Dataset/File` only when needed as evidence
- Keep relation types small:
- `mentions`
- `is_a`
- `part_of`
- `causes`
- `suppresses`
- `enhances`
- `measured_by`
- `has_observable`
- `has_condition`
- `supports_claim`
- `contradicts_claim`
- `qualifies_claim`
- `analogous_to`
- `similar_to`
- `explains`
- `predicts`
- `open_question_for`
- `needs_followup`
- `preferred_for`

Phase 3: query and synthesis
- Build deterministic queries first:
- What do we know about phenomenon X, and what is the evidence?
- Which observables diagnose mechanism Y?
- What claims about moire MoTe2 magnetism are supported by Xu Lab projects versus literature?
- Which papers/projects disagree about interpretation Z?
- What experimental conditions enhance or suppress feature W?
- What unresolved questions connect A5, B79/C7, D88, and D93?
- Which plotting/analysis convention is trusted for observable Q?
- Use Codex to turn graph neighborhoods into concise summaries.

Phase 4: discovery support
- Add graph embeddings or similarity only after enough high-quality edges exist.
- Candidate use cases:
- find analogies across projects
- flag contradictory interpretations
- identify underexplored parameter regimes
- suggest which mechanisms or observables should be checked for a new feature
- surface recurring features that lab members repeatedly mark as interesting

Expected efficacy:
- High for subject-matter recall, provenance-backed answers, project interpretation, and avoiding repeated conceptual mistakes.
- High for linking lab observations to field context when facts are too niche, recent, or specialized to rely on model priors.
- Medium-high for cross-project analogy and synthesis.
- Medium for suggesting analyses or follow-up measurements.
- Low initially for autonomous scientific discovery unless the graph accumulates high-quality claims, mechanisms, observables, and contradictions.

Main risks:
- Ontology overbuild.
- Low-confidence automatic triples polluting context.
- Treating source/file lookup as the goal rather than subject-matter reasoning.
- Duplicate names for concepts, phenomena, samples, and project aliases.
- Encoding vague claims without evidence or confidence.
- Building a graph UI before the extraction/schema loop is useful.

Recommended first build:
- Start with append-only JSONL node/edge records plus generated Markdown graph summaries.
- Delay Neo4j/RDF until query needs justify it.
- Use deterministic extraction for existing Markdown papers/syntheses/project notes.
- Use Codex/LLM extraction for `Claim`, `Mechanism`, `Observable`, `Evidence`, `Contradiction`, `OpenQuestion`, and `Convention`, with confidence and provenance.
- Surface graph knowledge through normal OpenScience context files and skills, not a separate heavyweight interface.

Decision:
- Build a lightweight fact graph if the goal is durable subject-matter memory and better scientific synthesis.
- Do not start with a global literature-scale KG, graph neural networks, or a complex ontology.

First design target:
- A graph that helps answer: "What specific scientific facts and claims should OpenScience know, why do we believe them, where did they come from, and what do they imply?"
