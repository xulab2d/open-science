#!/usr/bin/env python3
"""Build compact fact-graph summary figures and markdown for daily overviews."""

from __future__ import annotations

import argparse
import json
from collections import Counter
import math
from pathlib import Path
import sys

from fact_graph_common import EDGES_PATH, NODES_PATH, REPO_ROOT

LAB_ASSISTANT_ROOT = REPO_ROOT / "lab_assistant"
if str(LAB_ASSISTANT_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ASSISTANT_ROOT))


THEMES = {
    "Fractional topology": ["fractional", "fqah", "fci", "fractional quantum", "fractional chern", "fqsh", "anyon", "topological insulator"],
    "Optics / magneto-optics": ["optical", "photoluminescence", " trion", "rmcd", "mcd", "dichroism", "pump-probe"],
    "Superconductivity": ["superconduct", "pairing", "josephson", "holon metal"],
    "Field / twist control": ["displacement field", "electric-field", "gate", "twist-angle", "twist angle", "remote layer"],
    "Higher bands / multilayers": ["second moir", "higher-band", "multiband", "multilayer", "band reordering", "second flat chern band"],
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def theme_counts(papers: list[dict]) -> Counter:
    counts: Counter = Counter()
    for paper in papers:
        text = f"{paper.get('label', '')} {paper.get('summary', '')}".lower()
        for theme, terms in THEMES.items():
            if any(term in text for term in terms):
                counts[theme] += 1
    return counts


def medium_curated_arxiv(papers: list[dict]) -> list[dict]:
    return [
        paper
        for paper in papers
        if paper["id"].startswith("paper:arxiv_")
        and paper.get("confidence") == "medium"
    ]


def arxiv_year_counts(papers: list[dict]) -> Counter:
    counts: Counter = Counter()
    for paper in papers:
        published = paper.get("metadata", {}).get("published", "")
        if len(published) >= 4 and published[:4].isdigit():
            counts[published[:4]] += 1
    return counts


def render_figures(nodes: list[dict], edges: list[dict], out_dir: Path, stem: str) -> tuple[Path, Path, Path]:
    import matplotlib.pyplot as plt
    import networkx as nx

    from tools.plotting.openscience_plot_style import apply_style, figure_size, save_figure, style_axes

    out_dir.mkdir(parents=True, exist_ok=True)

    node_counts = Counter(node["type"] for node in nodes)
    node_order = [name for name, _count in node_counts.most_common()]
    node_values = [node_counts[name] for name in node_order]

    apply_style("deck")
    fig1, ax1 = plt.subplots(figsize=figure_size("wide"))
    colors = ["#1f3c88" if name in {"Paper", "Claim", "Evidence"} else "#7aa6c2" for name in node_order]
    ax1.bar(range(len(node_order)), node_values, color=colors)
    ax1.set_xticks(range(len(node_order)))
    ax1.set_xticklabels(node_order, rotation=35, ha="right")
    ax1.set_ylabel("Node count")
    ax1.set_title("Fact Graph Composition")
    style_axes(ax1)
    for idx, value in enumerate(node_values):
        ax1.text(idx, value + 2, str(value), ha="center", va="bottom", fontsize=9)
    node_fig = save_figure(fig1, out_dir / f"{stem}_node_composition", formats=("png",))[0]
    plt.close(fig1)

    papers = [node for node in nodes if node["type"] == "Paper"]
    curated = medium_curated_arxiv(papers)
    themed = theme_counts(curated)
    years = arxiv_year_counts(curated)

    fig2, (ax2, ax3) = plt.subplots(1, 2, figsize=(7.8, 2.9))
    theme_order = list(THEMES.keys())
    theme_values = [themed.get(name, 0) for name in theme_order]
    ax2.barh(theme_order, theme_values, color="#b44f3a")
    ax2.set_xlabel("Medium-confidence arXiv papers")
    ax2.set_title("Curated Frontier Coverage")
    style_axes(ax2)

    year_order = sorted(years)
    year_values = [years[year] for year in year_order]
    ax3.plot(year_order, year_values, marker="o", color="#2a7f62")
    ax3.set_ylabel("Medium-confidence arXiv papers")
    ax3.set_title("Curated arXiv by Year")
    style_axes(ax3)
    timeline_fig = save_figure(fig2, out_dir / f"{stem}_coverage", formats=("png",))[0]
    plt.close(fig2)

    keep_types = {"MaterialSystem", "Phenomenon", "Mechanism", "Observable", "Concept", "OpenQuestion", "Paper", "Claim"}
    graph = nx.Graph()
    for node in nodes:
        if node["type"] in keep_types:
            graph.add_node(node["id"], **node)
    for edge in edges:
        if edge["source"] in graph and edge["target"] in graph:
            graph.add_edge(edge["source"], edge["target"], relation=edge["relation"])

    if graph.number_of_nodes() == 0:
        backbone = graph
    else:
        largest_component = max(nx.connected_components(graph), key=len)
        largest = graph.subgraph(largest_component).copy()
        backbone = nx.k_core(largest, k=2)
        if backbone.number_of_nodes() == 0:
            backbone = largest

    communities = list(nx.algorithms.community.greedy_modularity_communities(backbone))
    community_index: dict[str, int] = {}
    for idx, community in enumerate(communities):
        for node_id in community:
            community_index[node_id] = idx

    apply_style("deck")
    fig3, ax4 = plt.subplots(figsize=(7.0, 7.0))
    ax4.set_title("Knowledge Graph Backbone")
    spectral = nx.spectral_layout(backbone)
    pos = nx.spring_layout(
        backbone,
        seed=7,
        pos=spectral,
        iterations=500,
        k=2.4 / math.sqrt(max(backbone.number_of_nodes(), 1)),
    )
    palette = list(plt.get_cmap("tab20").colors)
    edge_widths = [0.15 + 0.03 * min(backbone.degree[u], backbone.degree[v], 8) for u, v in backbone.edges()]
    nx.draw_networkx_edges(backbone, pos, width=edge_widths, alpha=0.09, edge_color="#334155", ax=ax4)

    node_order = sorted(backbone.nodes(), key=lambda node_id: backbone.degree[node_id])
    node_colors = [palette[community_index.get(node_id, 0) % len(palette)] for node_id in node_order]
    node_sizes = [8 + 5 * math.log1p(backbone.degree[node_id]) for node_id in node_order]
    nx.draw_networkx_nodes(
        backbone,
        pos,
        nodelist=node_order,
        node_color=node_colors,
        node_size=node_sizes,
        linewidths=0.0,
        alpha=0.9,
        ax=ax4,
    )
    ax4.set_axis_off()
    network_fig = save_figure(fig3, out_dir / f"{stem}_network", formats=("png",))[0]
    plt.close(fig3)

    return node_fig, timeline_fig, network_fig


def render_markdown(nodes: list[dict], edges: list[dict], node_fig: Path, coverage_fig: Path, network_fig: Path) -> str:
    papers = [node for node in nodes if node["type"] == "Paper"]
    curated = medium_curated_arxiv(papers)
    node_counts = Counter(node["type"] for node in nodes)
    themed = theme_counts(curated)

    top_themes = sorted(themed.items(), key=lambda item: (-item[1], item[0]))[:3]
    theme_text = ", ".join(f"{name.lower()} ({count})" for name, count in top_themes)

    return f"""### Knowledge graph update

Today’s literature-memory work expanded the MoTe2-focused fact graph to `{len(nodes)}` nodes and `{len(edges)}` edges, while keeping the emphasis on provenance-backed papers, claims, evidence, mechanisms, and open questions rather than keyword-only retrieval. The strongest current coverage is in {theme_text}.

![Fact graph node composition]({node_fig})

The graph is still claim-heavy by design, but the paper layer is now deeper and cleaner: `{node_counts.get('Paper', 0)}` paper nodes overall, `{len(curated)}` medium-confidence curated arXiv papers, `{node_counts.get('OpenQuestion', 0)}` open questions, and `{node_counts.get('Mechanism', 0)}` mechanism nodes. That makes retrieval more useful for interpretation tasks, especially when the question sits between optics, topology, and superconductivity.

![Fact graph frontier coverage]({coverage_fig})

Scientifically, the added depth now spans both frontier and foundation: twist-angle evolution into superconductivity, optical control and switching of Chern ferromagnets, displacement-field/twist-angle structure beyond the original first-band FQAH discovery papers, and the pre-2023 bridge literature on reconstruction, flat-band twisted WSe2, field-tunable Hubbard physics, and Gamma-valley emergent lattices. This is an internal knowledge update rather than a new experimental result, but it reduces the gap between the current field frontier and what the workspace can retrieve directly.

![Knowledge graph backbone spring layout]({network_fig})

This structure plot drops labels, keeps only the semantic backbone of the largest connected component, prunes leaf nodes with a 2-core filter, and lays the result out with a spring embedding. Node size scales gently with degree and color marks graph communities, so the point is to expose cluster structure rather than annotate individual records.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a fact-graph summary block for a daily overview.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--stem", default="fact_graph_summary")
    parser.add_argument("--markdown-out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    node_fig, coverage_fig, network_fig = render_figures(nodes, edges, args.out_dir, args.stem)
    markdown = render_markdown(nodes, edges, node_fig.resolve(), coverage_fig.resolve(), network_fig.resolve())
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(markdown + "\n", encoding="utf-8")
    print(args.markdown_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
