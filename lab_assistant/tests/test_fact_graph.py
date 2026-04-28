from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import fact_graph  # noqa: E402
import fact_graph_daily_summary  # noqa: E402


def load_nodes() -> dict[str, dict]:
    path = ROOT / "graph" / "nodes.jsonl"
    return {
        row["id"]: row
        for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    }


def load_edges() -> list[dict]:
    path = ROOT / "graph" / "edges.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_fact_graph_validates():
    assert fact_graph.validate() == 0


def test_foundational_semiconductor_moire_papers_present():
    nodes = load_nodes()
    expected = {
        "paper:hubbard_model_physics_in_transition_metal_dichalcogenide_moire_bands",
        "paper:simulation_of_hubbard_model_physics_in_wse2_ws2_moire_superlattices",
        "paper:semiconductor_moire_materials",
        "paper:excitons_in_semiconductor_moire_superlattices",
        "paper:spontaneous_fractional_chern_insulators_in_transition_metal_dichalcogenide_moire",
        "paper:moire_heterostructures_as_a_condensed_matter_quantum_simulator",
        "paper:a_tunable_bilayer_hubbard_model_in_twisted_wse2",
        "paper:atomic_reconstruction_in_twisted_bilayers_of_transition_metal_dichalcogenides",
    }
    missing = expected - set(nodes)
    assert not missing


def test_search_surfaces_foundational_semiconductor_moire_context(capsys):
    fact_graph.search("semiconductor moire Hubbard WSe2 WS2 review", limit=20)
    out = capsys.readouterr().out
    assert "paper:semiconductor_moire_materials" in out
    assert (
        "paper:hubbard_model_physics_in_transition_metal_dichalcogenide_moire_bands" in out
        or "claim:hubbard_model_physics_in_transition_metal_dichalcogenide_moire_bands" in out
    )
    assert "paper:simulation_of_hubbard_model_physics_in_wse2_ws2_moire_superlattices" in out


def test_search_surfaces_mote2_frontier_context(capsys):
    fact_graph.search("twisted MoTe2 superconductivity optical switching valley-degenerate", limit=20)
    out = capsys.readouterr().out
    assert "paper:arxiv_2508_19602v1" in out or "claim:promoted_2508_optical_switching_domain_walls" in out
    assert "claim:promoted_2603_twist_angle_evolution_to_valley_degenerate_sc" in out


def test_search_surfaces_structural_wse2_bridge_context(capsys):
    fact_graph.search("reconstruction flat bands twisted WSe2 Gamma valley emergent lattice", limit=20)
    out = capsys.readouterr().out
    assert (
        "paper:flat_bands_in_twisted_bilayer_transition_metal_dichalcogenides" in out
        or "paper:lattice_reconstruction_induced_multiple_ultra_flat_bands_in_twisted_bilayer_wse2" in out
    )
    assert (
        "paper:valley_transition_metal_dichalcogenide_moire_bands" in out
        or "paper:observation_of_valley_moire_bands_and_emergent_hexagonal_lattice_in_twisted_tran" in out
    )


def test_search_surfaces_wse2_hubbard_bridge_context(capsys):
    fact_graph.search("field tunable twisted WSe2 bilayer Hubbard model electric field", limit=20)
    out = capsys.readouterr().out
    assert "paper:a_tunable_bilayer_hubbard_model_in_twisted_wse2" in out
    assert (
        "paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti" in out
        or "paper:quantum_criticality_in_twisted_transition_metal_dichalcogenides" in out
    )


def test_search_surfaces_review_level_semiconductor_moire_context(capsys):
    fact_graph.search("semiconductor moire review quantum simulator excitons correlated electrons", limit=20)
    out = capsys.readouterr().out
    assert "paper:moire_heterostructures_as_a_condensed_matter_quantum_simulator" in out
    assert "paper:excitons_and_emergent_quantum_phenomena_in_stacked_2d_semiconductors" in out


def test_neighborhood_captures_claim_structure():
    nodes, edges = fact_graph.collect_neighborhood(
        "claim:promoted_2603_twist_angle_evolution_to_valley_degenerate_sc",
        depth=1,
    )
    assert "paper:arxiv_2603_16412v1" in nodes
    assert "phenomenon:valley_degenerate_superconductivity" in nodes
    assert any(edge["relation"] == "supports_claim" for edge in edges)


def test_wse2_hubbard_bridge_neighborhood_has_semantic_links():
    nodes, edges = fact_graph.collect_neighborhood(
        "paper:a_tunable_bilayer_hubbard_model_in_twisted_wse2",
        depth=1,
    )
    assert "claim:a_tunable_bilayer_hubbard_model_in_twisted_wse2_twisted_ab_wse2_realizes_a_field_tunable_bilayer" in nodes
    assert "phenomenon:moire_magnetism" in nodes
    assert "observable:pl" in nodes
    assert any(edge["relation"] == "supports_claim" for edge in edges)


def test_daily_summary_network_figure_generation(tmp_path: Path):
    nodes = fact_graph_daily_summary.load_jsonl(fact_graph_daily_summary.NODES_PATH)
    edges = fact_graph_daily_summary.load_jsonl(fact_graph_daily_summary.EDGES_PATH)
    node_fig, coverage_fig, network_fig = fact_graph_daily_summary.render_figures(
        nodes,
        edges,
        tmp_path,
        "graph_test",
    )
    assert node_fig.exists()
    assert coverage_fig.exists()
    assert network_fig.exists()
    assert network_fig.stat().st_size > 50_000


def test_backbone_visual_is_structural_not_textual():
    nodes = list(load_nodes().values())
    edges = load_edges()
    markdown = fact_graph_daily_summary.render_markdown(
        nodes,
        edges,
        Path("/tmp/node.png"),
        Path("/tmp/coverage.png"),
        Path("/tmp/network.png"),
    )
    assert "spring embedding" in markdown
    assert "drops labels" in markdown
