# Legacy Assessment

Legacy system summary:
- The old OpenClaw workspace combined prompt files, long-term memory, routing notes, Dropbox ingestion, Slack plans, active-run monitoring, and a large pile of generated outputs.
- Its intended role was stronger than its architecture: it was trying to be a lab notebook, context retriever, summarizer, analyst, and communication aide.

Conceptually worth preserving:
- provenance-aware reasoning
- project and people memory
- concise science-facing summaries
- targeted clarification questions
- awareness of recurring lab naming conventions

Needs rewriting:
- nearly all instructions, because authority was split across too many overlapping files
- all Dropbox-first assumptions
- all OpenClaw-specific messaging and session machinery
- most operational guidance, which was too coupled to a nightly heartbeat model

Should be dropped:
- redundant root-level prompt files with partial overlap
- framework-specific state and agent-session directories
- most generated `out/`, `reports/`, and cached state as architectural inputs
- any policy that only made sense for the prior platform

Structural problems in the old implementation:
- too many “canonical” files
- too much dated operational detail embedded in primary guidance
- coupling between core assistant behavior and transport layers like Slack
- heavy Dropbox/cron bias despite the real task being broader lab assistance
- mixed durable knowledge and transient artifacts in the same workspace
