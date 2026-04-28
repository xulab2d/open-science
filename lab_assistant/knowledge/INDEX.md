# Knowledge Index

Purpose:
- Main navigation page for the lab-assistant knowledge web.

Use this when:
- you need to move between project context and field context
- you want the fastest entrypoint into the right part of the knowledge base

## Start By Question Type

If the question is mainly about:
- a current lab project:
  - start in [projects/](/Users/xulab/openscience/lab_assistant/knowledge/projects)
- a scientific topic or result class:
  - start in [syntheses/](/Users/xulab/openscience/lab_assistant/knowledge/syntheses)
- a niche fact, claim, mechanism, observable, contradiction, or open question:
  - search the [fact graph](/Users/xulab/openscience/lab_assistant/graph) with `python3 lab_assistant/scripts/fact_graph.py search "<topic>"`
- a specific paper family:
  - start in [papers/](/Users/xulab/openscience/lab_assistant/knowledge/papers)
- internal lab conventions, decks, or history:
  - start in [canon/](/Users/xulab/openscience/lab_assistant/knowledge/canon)
- plotting style or visualization conventions:
  - start with [context/plotting_practices.md](/Users/xulab/openscience/lab_assistant/context/plotting_practices.md) and [canon/plotting_reference_map.md](/Users/xulab/openscience/lab_assistant/knowledge/canon/plotting_reference_map.md)

## Domain Entry Points

- Moire MoTe2 frontier:
  - [moire_tmote2_research_frontier.md](/Users/xulab/openscience/lab_assistant/knowledge/syntheses/moire_tmote2_research_frontier.md)
- Displacement-field control:
  - [displacement_field_and_phase_control.md](/Users/xulab/openscience/lab_assistant/knowledge/syntheses/displacement_field_and_phase_control.md)
- Moire magnetism and competing orders:
  - [moire_magnetism_and_competing_orders.md](/Users/xulab/openscience/lab_assistant/knowledge/syntheses/moire_magnetism_and_competing_orders.md)
- Optical readout of correlated states:
  - [optical_readout_of_correlated_states.md](/Users/xulab/openscience/lab_assistant/knowledge/syntheses/optical_readout_of_correlated_states.md)
- Xu-group optical probe lineage:
  - [xu_group_optical_probe_and_control_ladder.md](/Users/xulab/openscience/lab_assistant/knowledge/syntheses/xu_group_optical_probe_and_control_ladder.md)
- Probe logic across modalities:
  - [optical_magnetism_and_probes.md](/Users/xulab/openscience/lab_assistant/knowledge/syntheses/optical_magnetism_and_probes.md)
- Evidence hierarchy:
  - [evidence_hierarchy_for_correlated_states.md](/Users/xulab/openscience/lab_assistant/knowledge/syntheses/evidence_hierarchy_for_correlated_states.md)
- Xu-group publication map:
  - [xu_group_publications.md](/Users/xulab/openscience/lab_assistant/knowledge/index/xu_group_publications.md)
- Xu-group optical foundations:
  - [xu_group_valley_and_exciton_foundations.md](/Users/xulab/openscience/lab_assistant/knowledge/papers/xu_group_valley_and_exciton_foundations.md)
- Xu-group magnetism and proximity:
  - [xu_group_vdw_magnetism_and_proximity.md](/Users/xulab/openscience/lab_assistant/knowledge/papers/xu_group_vdw_magnetism_and_proximity.md)
- Xu-group recent moire states:
  - [xu_group_recent_moire_states.md](/Users/xulab/openscience/lab_assistant/knowledge/papers/xu_group_recent_moire_states.md)
- Xu-group WTe2 and topological edges:
  - [xu_group_wte2_and_topological_edges.md](/Users/xulab/openscience/lab_assistant/knowledge/papers/xu_group_wte2_and_topological_edges.md)

## Project Entry Points

- [shuai_mt43.md](/Users/xulab/openscience/lab_assistant/knowledge/projects/shuai_mt43.md)
- [d93_run2.md](/Users/xulab/openscience/lab_assistant/knowledge/projects/d93_run2.md)
- [d88.md](/Users/xulab/openscience/lab_assistant/knowledge/projects/d88.md)
- [a5_dot.md](/Users/xulab/openscience/lab_assistant/knowledge/projects/a5_dot.md)
- [b79.md](/Users/xulab/openscience/lab_assistant/knowledge/projects/b79.md)
- [c7.md](/Users/xulab/openscience/lab_assistant/knowledge/projects/c7.md)

## Working Rule

This is a web, not a tree:
- project pages should point to the domain syntheses they touch
- syntheses should point to the paper shelves that support them
- canon should stay focused on lab-specific memory and conventions
