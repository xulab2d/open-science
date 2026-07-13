"""Task-routed context compiler for OpenScience work."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
import re
import time
from pathlib import Path
from typing import Any

from .snapshot import (
    PACKAGE_ROOT,
    estimate_tokens,
    file_sha256,
    read_jsonish,
    relative_id,
    resolve_lab_path,
    stable_hash,
)


POLICY_DIR = PACKAGE_ROOT / "context_policy"
DEFAULT_POLICY_PATH = POLICY_DIR / "default.yaml"
TASK_ROUTES_PATH = POLICY_DIR / "task_routes.yaml"


@dataclass
class ContextItem:
    kind: str
    id: str
    hash: str
    reason: str
    chars: int
    path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    content: str = ""

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("content", None)
        return data


@dataclass
class ExcludedItem:
    id: str
    reason: str
    path: str | None = None
    chars: int | None = None


@dataclass
class ContextPack:
    context_pack_id: str
    task_type: str
    query: str
    project_id: str | None
    latency_tier: str
    memory_snapshot_id: str | None
    items: list[ContextItem]
    excluded: list[ExcludedItem]
    metrics: dict[str, Any]

    def to_trajectory_dict(self) -> dict[str, Any]:
        return {
            "context_pack_id": self.context_pack_id,
            "items": [item.public_dict() for item in self.items],
            "excluded": [asdict(item) for item in self.excluded],
        }

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "context_pack_id": self.context_pack_id,
            "task_type": self.task_type,
            "query": self.query,
            "project_id": self.project_id,
            "latency_tier": self.latency_tier,
            "memory_snapshot_id": self.memory_snapshot_id,
            "items": [item.public_dict() for item in self.items],
            "excluded": [asdict(item) for item in self.excluded],
            "metrics": self.metrics,
        }


def _default_policy() -> dict[str, Any]:
    if DEFAULT_POLICY_PATH.exists():
        return read_jsonish(DEFAULT_POLICY_PATH)
    return {
        "char_budgets": {"direct": 3000, "fast": 6000, "normal": 12000, "deep": 22000, "self_improve": 26000},
        "legacy_always_include": "integrations/context_files.json",
        "fallback_include": [
            {"path": "core/identity.md", "kind": "core", "reason": "minimal core identity", "max_chars": 1200},
            {"path": "core/directives.md", "kind": "core", "reason": "minimal core directives", "max_chars": 1600},
        ],
    }


def _task_routes() -> dict[str, Any]:
    if TASK_ROUTES_PATH.exists():
        return read_jsonish(TASK_ROUTES_PATH)
    return {}


def _read_text_limited(path: Path, max_chars: int | None = None) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars].rstrip() + "\n[truncated]\n"
    return text


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[A-Za-z0-9_]+", text.lower()) if len(token) > 1}


def _node_text(node: dict[str, Any]) -> str:
    aliases = " ".join(str(item) for item in node.get("aliases", []))
    provenance = " ".join(
        f"{item.get('source', '')} {item.get('method', '')}"
        for item in node.get("provenance", [])
        if isinstance(item, dict)
    )
    return f"{node.get('id', '')} {node.get('type', '')} {node.get('label', '')} {aliases} {node.get('summary', '')} {provenance}"


def _load_graph() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    def load_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    nodes = {node["id"]: node for node in load_jsonl(PACKAGE_ROOT / "graph" / "nodes.jsonl")}
    edges = load_jsonl(PACKAGE_ROOT / "graph" / "edges.jsonl")
    return nodes, edges


def _graph_search(query: str, node_types: set[str] | None, limit: int) -> list[dict[str, Any]]:
    nodes, edges = _load_graph()
    degree: dict[str, int] = {}
    for edge in edges:
        degree[edge.get("source", "")] = degree.get(edge.get("source", ""), 0) + 1
        degree[edge.get("target", "")] = degree.get(edge.get("target", ""), 0) + 1
    qtokens = _tokenize(query)
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for node_id, node in nodes.items():
        if node_types is not None and node.get("type") not in node_types:
            continue
        text = _node_text(node)
        tokens = _tokenize(text)
        score = 3 * len(qtokens & _tokenize(str(node.get("label", "")))) + len(qtokens & tokens)
        if query.lower() in text.lower():
            score += 8
        if node.get("confidence") == "high":
            score += 2
        elif node.get("confidence") == "medium":
            score += 1
        if score > 0:
            scored.append((score, node_id, node))
    scored.sort(key=lambda item: (-item[0], -degree.get(item[1], 0), item[1]))
    return [node for _score, _node_id, node in scored[:limit]]


def _graph_neighbors(node_ids: list[str], limit: int = 8) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes, edges = _load_graph()
    selected_edges = []
    selected_nodes: dict[str, dict[str, Any]] = {}
    starts = set(node_ids)
    for edge in edges:
        if edge.get("source") in starts or edge.get("target") in starts:
            selected_edges.append(edge)
            for node_id in (edge.get("source"), edge.get("target")):
                if node_id in nodes:
                    selected_nodes[node_id] = nodes[node_id]
        if len(selected_edges) >= limit:
            break
    return list(selected_nodes.values()), selected_edges


def _render_node(node: dict[str, Any]) -> str:
    provenance = "; ".join(
        f"{item.get('source', 'unknown')} ({item.get('method', 'unknown')})"
        for item in node.get("provenance", [])
        if isinstance(item, dict)
    )
    return (
        f"### {node.get('label', node.get('id'))}\n"
        f"- ID: `{node.get('id')}`\n"
        f"- Type: {node.get('type')}\n"
        f"- Confidence: {node.get('confidence')}\n"
        f"- Summary: {node.get('summary')}\n"
        f"- Provenance: {provenance}\n"
    )


def _render_edge(edge: dict[str, Any]) -> str:
    return (
        f"- `{edge.get('source')}` -{edge.get('relation')}-> `{edge.get('target')}` "
        f"[{edge.get('confidence')}]: {edge.get('claim')}\n"
    )


def load_skill_metadata() -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for path in sorted((PACKAGE_ROOT / "skills").glob("*.yaml")):
        data = read_jsonish(path)
        skill_id = data.get("skill_id")
        if not skill_id:
            continue
        data["_metadata_path"] = str(path.relative_to(PACKAGE_ROOT))
        md_path = PACKAGE_ROOT / "skills" / f"{skill_id}.md"
        if md_path.exists():
            data["_skill_path"] = str(md_path.relative_to(PACKAGE_ROOT))
        registry[skill_id] = data
    return registry


class ContextBuilder:
    def __init__(self, char_budget: int):
        self.char_budget = char_budget
        self.items: list[ContextItem] = []
        self.excluded: list[ExcludedItem] = []
        self.used_chars = 0
        self._seen_ids: set[str] = set()

    def add_content(
        self,
        *,
        kind: str,
        item_id: str,
        content: str,
        reason: str,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if item_id in self._seen_ids:
            return
        chars = len(content)
        if self.used_chars + chars > self.char_budget:
            self.excluded.append(ExcludedItem(id=item_id, reason="budget", path=path, chars=chars))
            return
        self._seen_ids.add(item_id)
        self.used_chars += chars
        self.items.append(
            ContextItem(
                kind=kind,
                id=item_id,
                path=path,
                hash=stable_hash({"id": item_id, "content": content}),
                reason=reason,
                chars=chars,
                metadata=metadata or {},
                content=content,
            )
        )

    def add_file(self, entry: dict[str, Any]) -> None:
        path = resolve_lab_path(entry["path"])
        rel = relative_id(path)
        item_id = entry.get("id", rel)
        if not path.exists():
            self.excluded.append(ExcludedItem(id=item_id, reason="missing", path=rel))
            return
        max_chars = entry.get("max_chars")
        content = _read_text_limited(path, max_chars=max_chars)
        self.add_content(
            kind=entry.get("kind", "core"),
            item_id=item_id,
            path=rel,
            content=content,
            reason=entry.get("reason", "policy include"),
            metadata={"file_sha256": file_sha256(path), "max_chars": max_chars},
        )


def _legacy_entries() -> list[dict[str, Any]]:
    policy = _default_policy()
    legacy_path = resolve_lab_path(policy.get("legacy_always_include", "integrations/context_files.json"))
    if not legacy_path.exists():
        return policy.get("fallback_include", [])
    data = json.loads(legacy_path.read_text(encoding="utf-8"))
    entries = []
    for item in data.get("always_include", []):
        entries.append(
            {
                "path": item["path"],
                "kind": "core" if "/core/" in item["path"] else "skill" if "/skills/" in item["path"] else "knowledge_index",
                "reason": f"legacy always_include: {item.get('label', item['path'])}",
                "max_chars": item.get("max_chars"),
            }
        )
    return entries


def _add_skills(builder: ContextBuilder, skill_ids: list[str], reason: str) -> None:
    registry = load_skill_metadata()
    for skill_id in skill_ids:
        metadata = registry.get(skill_id)
        if not metadata:
            builder.excluded.append(ExcludedItem(id=f"skill:{skill_id}", reason="missing"))
            continue
        skill_path = metadata.get("_skill_path")
        if skill_path:
            builder.add_file(
                {
                    "path": skill_path,
                    "kind": "skill",
                    "reason": reason,
                    "max_chars": metadata.get("context_max_chars", 2200),
                    "id": f"skill:{skill_id}",
                }
            )
        builder.add_content(
            kind="skill",
            item_id=f"skill_metadata:{skill_id}",
            path=metadata.get("_metadata_path"),
            content=json.dumps({k: v for k, v in metadata.items() if not k.startswith("_")}, indent=2, sort_keys=True),
            reason=f"machine-readable skill metadata for {skill_id}",
            metadata={"skill_id": skill_id},
        )


def _add_graph_context(builder: ContextBuilder, route: dict[str, Any], query: str) -> None:
    graph = route.get("graph", {})
    if not graph:
        return
    type_names = graph.get("node_types")
    node_types = set(type_names) if type_names else None
    limit = int(graph.get("limit", 5))
    nodes = _graph_search(query, node_types=node_types, limit=limit)
    for node in nodes:
        builder.add_content(
            kind="graph_node",
            item_id=node["id"],
            path="lab_assistant/graph/nodes.jsonl",
            content=_render_node(node),
            reason=graph.get("reason", "task-routed graph retrieval"),
            metadata={"type": node.get("type"), "confidence": node.get("confidence")},
        )
    if graph.get("include_neighbors") and nodes:
        neighbor_nodes, edges = _graph_neighbors([node["id"] for node in nodes[: int(graph.get("neighbor_seed_limit", 2))]])
        for edge in edges:
            builder.add_content(
                kind="graph_edge",
                item_id=edge["id"],
                path="lab_assistant/graph/edges.jsonl",
                content=_render_edge(edge),
                reason="one-hop graph neighborhood",
                metadata={"relation": edge.get("relation"), "confidence": edge.get("confidence")},
            )
        for node in neighbor_nodes:
            if node["id"] in {item.id for item in builder.items}:
                continue
            builder.add_content(
                kind="graph_node",
                item_id=node["id"],
                path="lab_assistant/graph/nodes.jsonl",
                content=_render_node(node),
                reason="one-hop graph neighborhood",
                metadata={"type": node.get("type"), "confidence": node.get("confidence")},
            )


def _route_for(task_type: str) -> dict[str, Any]:
    routes = _task_routes()
    return routes.get(task_type, {})


def render_markdown(pack: ContextPack) -> str:
    lines = [
        f"# Context Pack: {pack.context_pack_id}",
        "",
        f"- Task type: `{pack.task_type}`",
        f"- Query: {pack.query}",
        f"- Items: {len(pack.items)}",
        f"- Chars: {pack.metrics['chars']}",
        f"- Token estimate: {pack.metrics['token_estimate']}",
        "",
    ]
    for item in pack.items:
        lines.extend(
            [
                f"## {item.kind}: {item.id}",
                f"Reason: {item.reason}",
                "",
                item.content.rstrip(),
                "",
            ]
        )
    if pack.excluded:
        lines.extend(["## Excluded", ""])
        for item in pack.excluded:
            lines.append(f"- `{item.id}`: {item.reason}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_context_pack(
    *,
    task_type: str,
    query: str,
    project_id: str | None = None,
    latency_tier: str = "normal",
    char_budget: int | None = None,
    memory_snapshot: Any | None = None,
    write: bool = False,
    output_dir: Path | None = None,
    legacy_fallback: bool = False,
) -> tuple[ContextPack, str]:
    started = time.perf_counter()
    policy = _default_policy()
    budgets = policy.get("char_budgets", {})
    budget = char_budget or int(budgets.get(latency_tier, budgets.get("normal", 12000)))
    builder = ContextBuilder(budget)
    route = _route_for(task_type)
    if legacy_fallback or not route:
        route = {
            "include": _legacy_entries(),
            "skills": [],
            "graph": {},
            "fallback": True,
        }
    else:
        for entry in policy.get("minimal_core", []):
            builder.add_file(entry)

    for entry in route.get("include", []):
        builder.add_file(entry)
    for glob_entry in route.get("include_globs", []):
        paths = sorted(PACKAGE_ROOT.glob(glob_entry["glob"]))
        max_items = int(glob_entry.get("max_items", len(paths)))
        for path in paths[:max_items]:
            builder.add_file(
                {
                    "path": str(path.relative_to(PACKAGE_ROOT)),
                    "kind": glob_entry.get("kind", "knowledge_index"),
                    "reason": glob_entry.get("reason", "policy glob include"),
                    "max_chars": glob_entry.get("max_chars"),
                }
            )
        for path in paths[max_items:]:
            builder.excluded.append(ExcludedItem(id=relative_id(path), reason="glob_limit", path=relative_id(path)))
    _add_skills(builder, route.get("skills", []), reason="task route skill")
    _add_graph_context(builder, route, query)

    snapshot_id = getattr(memory_snapshot, "snapshot_id", None)
    item_records = [item.public_dict() for item in builder.items]
    excluded_records = [asdict(item) for item in builder.excluded]
    context_pack_id = stable_hash(
        {
            "task_type": task_type,
            "query": " ".join(query.lower().split()),
            "project_id": project_id,
            "latency_tier": latency_tier,
            "memory_snapshot_id": snapshot_id,
            "items": item_records,
            "excluded": excluded_records,
        }
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    chars = sum(item.chars for item in builder.items)
    metrics = {
        "chars": chars,
        "token_estimate": estimate_tokens(chars),
        "item_count": len(builder.items),
        "excluded_count": len(builder.excluded),
        "cacheability_hash": stable_hash(item_records),
        "latency_ms": elapsed_ms,
    }
    pack = ContextPack(
        context_pack_id=context_pack_id,
        task_type=task_type,
        query=query,
        project_id=project_id,
        latency_tier=latency_tier,
        memory_snapshot_id=snapshot_id,
        items=builder.items,
        excluded=builder.excluded,
        metrics=metrics,
    )
    markdown = render_markdown(pack)
    if write:
        target_dir = output_dir or (PACKAGE_ROOT / "runs" / "context_packs")
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / f"{context_pack_id}.json").write_text(
            json.dumps(pack.to_summary_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (target_dir / f"{context_pack_id}.md").write_text(markdown, encoding="utf-8")
    return pack, markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile a deterministic task-routed context pack.")
    parser.add_argument("--task-type", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--project-id", default=None)
    parser.add_argument("--latency-tier", default="normal", choices=["direct", "fast", "normal", "deep", "self_improve"])
    parser.add_argument("--char-budget", type=int, default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--legacy-fallback", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pack, _markdown = build_context_pack(
        task_type=args.task_type,
        query=args.query,
        project_id=args.project_id,
        latency_tier=args.latency_tier,
        char_budget=args.char_budget,
        write=not args.no_write,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        legacy_fallback=args.legacy_fallback,
    )
    print(json.dumps(pack.to_summary_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
