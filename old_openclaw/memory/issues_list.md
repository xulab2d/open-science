# Issues list (system not working signals)

Purpose: when something feels brittle/confusing (for me or for lab members), log it here so I can fix structure/tooling rather than forgetting.

Format:
- id: i_YYYYMMDD_NN
- issue: short description
- impact: what breaks / who it affects
- evidence: path(s) and/or Slack timestamp
- proposed fix: concrete next action
- status: open | in_progress | done

---

- id: i_20260313_01
  issue: Audit/compaction plan lived in Slack DM thread and was not retrievable via memory_search (I answered “can’t find it” before re-reading Slack).
  impact: I risk re-asking/redoing work; Isaac loses confidence I’m tracking directives.
  evidence: Slack DM thread D0AGSG41Q6B (messages around 2026-03-13 13:13 PDT).
  proposed fix: Create a canonical audit plan doc and ensure START_HERE links to it; when a plan is agreed in Slack, immediately write it down.
  status: in_progress

- id: i_20260313_02
  issue: Lab member confusion about summary deck location ("tMoTe2summary" hard to find if moved under measurement folder).
  impact: People can’t find summaries; higher entropy in Dropbox structure.
  evidence: Slack DM from Isaac relaying Weijie message (2026-03-13 12:28 PDT).
  proposed fix: Add a "Where summaries live" section to field_guide + START_HERE; propose a stable top-level summaries root and document it.
  status: open

- id: i_20260317_01
  issue: Feedback about slide/deck style and lab expectations not being captured in a way that reliably reduces repeated mistakes/trivial questions.
  impact: I keep proposing arbitrary formatting rules; I re-ask questions that should be answered by accumulated lab norms.
  evidence: Slack thread #open-science (Isaac feedback 2026-03-17 ~10:50–10:54 PDT).
  proposed fix: Maintain persistent feedback logs (slide decks + lab norms) and consult them before posting summaries; explicitly record what changed in response to feedback.
  status: in_progress
