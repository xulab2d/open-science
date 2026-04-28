Canonicalized: `memory/compactions/2026-03-02_compacted_routing_and_paths.md`

# 2026-03-02 — Convention: tMoTe2_Measuring folder boundaries

Source: Slack DM from Christiano Wang Beach (timestamp Mon 2026-03-02 21:50 PST).

- Convention: different folders within `tMoTe2_Measuring` are typically **different projects**.

Implication for ingestion/routing:
- Avoid assuming shared metadata/calibrations across sibling folders under `tMoTe2_Measuring`; treat each top-level folder as a separate project unless explicitly linked.
