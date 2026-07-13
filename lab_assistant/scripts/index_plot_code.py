#!/usr/bin/env python3
"""Index prior plotting code as precise retrieval context.

The index is intentionally lightweight: JSON for machines, Markdown for Codex
and humans. Source code remains the ground truth.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = PACKAGE_ROOT / "knowledge" / "canon" / "plot_code_index.json"
DEFAULT_OUTPUT_MD = PACKAGE_ROOT / "knowledge" / "canon" / "plot_code_index.md"

PLOT_PATTERNS = (
    "matplotlib",
    "plt.",
    "savefig",
    "exportgraphics",
    "imshow",
    "pcolormesh",
    "plot(",
    "colorbar",
    "xlabel",
    "ylabel",
    "caxis",
    "colormap",
)

TAG_PATTERNS = {
    "rmcd": r"\brmcd\b|\bmcd\b",
    "pl": r"\bpl\b|photoluminescence|lifetime|trpl",
    "reflectance": r"reflectance|\bdr\b|dR/R",
    "hysteresis": r"hysteresis|up sweep|down sweep",
    "magnetic_field": r"\bbfield\b|currentB|B \(T\)|magnetic",
    "density": r"\bdensity\b|\bnn\b|\bn \(",
    "displacement": r"displacement|\bD\b|V/nm",
    "filling": r"filling|\\nu|nu\b|moire filling",
    "energy": r"energy|eV|wavelength",
    "gate_map": r"dualgate|gate|Vt|Vb",
    "a5": r"\ba5\b|dot1|dot3|Zengde_Weijie_A5",
    "d88": r"\bd88\b",
    "d93": r"\bd93\b",
    "c7": r"\bc7\b",
    "mt43": r"\bmt43\b",
}


@dataclass
class PlotCodeRecord:
    path: str
    language: str
    sha256: str
    line_count: int
    chars: int
    tags: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    libraries: list[str] = field(default_factory=list)
    data_paths: list[str] = field(default_factory=list)
    output_paths: list[str] = field(default_factory=list)
    axis_labels: list[str] = field(default_factory=list)
    colormaps: list[str] = field(default_factory=list)
    plot_calls: list[str] = field(default_factory=list)
    constants: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PACKAGE_ROOT))
    except ValueError:
        return str(path)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_plot_code(path: Path, text: str) -> bool:
    if path.name == "index_plot_code.py":
        return False
    if path.suffix.lower() not in {".py", ".m", ".ipynb"}:
        return False
    lowered = text.lower()
    return any(pattern.lower() in lowered for pattern in PLOT_PATTERNS)


def extract_strings(text: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return re.findall(r"['\"]([^'\"]{3,220})['\"]", text)
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


def extract_python(text: str) -> tuple[list[str], list[str], dict[str, str]]:
    functions: list[str] = []
    libraries: set[str] = set()
    constants: dict[str, str] = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return functions, sorted(libraries), constants
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                libraries.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            libraries.add(node.module.split(".")[0])
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    try:
                        constants[target.id] = ast.unparse(node.value)[:180]
                    except Exception:
                        pass
    return sorted(functions), sorted(libraries), constants


def extract_matlab(text: str) -> tuple[list[str], list[str], dict[str, str]]:
    functions = re.findall(r"^\s*function\s+(?:\[?.*?\]?\s*=\s*)?([A-Za-z]\w*)", text, flags=re.MULTILINE)
    libraries = ["matlab"]
    constants: dict[str, str] = {}
    for name, value in re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*([^;\n]+)", text, flags=re.MULTILINE):
        constants[name] = value.strip()[:180]
    return sorted(set(functions)), libraries, constants


def unique_sorted(values: Iterable[str], limit: int = 20) -> list[str]:
    clean = []
    seen = set()
    for value in values:
        value = " ".join(str(value).split())
        if not value or value in seen:
            continue
        seen.add(value)
        clean.append(value)
    return sorted(clean)[:limit]


def find_axis_labels(strings: list[str]) -> list[str]:
    candidates = []
    for value in strings:
        if len(value) > 90 or "\n" in value or value.startswith(("-", "#")):
            continue
        lower = value.lower()
        if any(token in lower for token in ("eV".lower(), " cm", "v/nm", "b (t)", "rmcd", "pl", "intensity", "filling", "\\nu", "energy")):
            candidates.append(value)
    return unique_sorted(candidates, limit=16)


def find_paths(strings: list[str], text: str) -> tuple[list[str], list[str]]:
    data_terms = ("data", "/Volumes", ".mat", ".csv", ".txt", ".h5", ".hdf5", ".zarr")
    out_terms = (".png", ".pdf", ".svg")
    data_paths = [
        value
        for value in strings
        if len(value) <= 180 and any(term in value for term in data_terms) and ("/" in value or "." in value or value == "data")
    ]
    output_paths = [
        value
        for value in strings
        if len(value) <= 180 and (any(term in value for term in out_terms) or value in {"out", "plots"})
    ]
    output_paths.extend(re.findall(r"[\w./ -]+\.(?:png|pdf|svg)", text))
    return unique_sorted(data_paths, limit=20), unique_sorted(output_paths, limit=20)


def find_colormaps(text: str, strings: list[str]) -> list[str]:
    known = {"viridis", "magma", "inferno", "plasma", "RdBu_r", "coolwarm", "turbo", "jet", "parula"}
    values = [value for value in strings if value in known]
    for match in re.findall(r"colormap\(([^)]+)\)|cmap\s*=\s*['\"]([^'\"]+)['\"]", text):
        for item in match:
            for part in re.split(r"[, ]+", item):
                if part in known:
                    values.append(part)
    return unique_sorted(values, limit=12)


def find_plot_calls(text: str) -> list[str]:
    calls = []
    for pattern in ("imshow", "pcolormesh", "plot", "scatter", "errorbar", "imagesc", "contourf", "exportgraphics", "savefig"):
        if re.search(rf"\b{pattern}\b", text):
            calls.append(pattern)
    return calls


def infer_tags(path: Path, text: str) -> list[str]:
    haystack = f"{path} {text}".lower()
    tags = [tag for tag, pattern in TAG_PATTERNS.items() if re.search(pattern, haystack, flags=re.IGNORECASE)]
    return sorted(tags)


def summarize_notes(record: PlotCodeRecord) -> list[str]:
    notes = []
    if "jet" in record.colormaps or "turbo" in record.colormaps:
        notes.append("uses rainbow-like colormap; treat as legacy unless project convention requires it")
    if "filling" in record.tags:
        notes.append("contains filling-axis logic; inspect conversion constants before reuse")
    if "hysteresis" in record.tags:
        notes.append("hysteresis-related plot; preserve sweep direction rather than averaging")
    if "rmcd" in record.tags:
        notes.append("signed magnetic/contrast observable; check whether zero-centered diverging bounds are appropriate")
    if record.output_paths:
        notes.append("script emits reusable figure artifacts")
    return notes


def index_file(path: Path) -> PlotCodeRecord | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not is_plot_code(path, text):
        return None
    language = path.suffix.lower().lstrip(".")
    if language == "py":
        functions, libraries, constants = extract_python(text)
    elif language == "m":
        functions, libraries, constants = extract_matlab(text)
    else:
        functions, libraries, constants = [], [], {}
    strings = extract_strings(text)
    data_paths, output_paths = find_paths(strings, text)
    record = PlotCodeRecord(
        path=relpath(path),
        language=language,
        sha256=sha256_text(text),
        line_count=text.count("\n") + 1,
        chars=len(text),
        tags=infer_tags(path, text),
        functions=functions,
        libraries=libraries,
        data_paths=data_paths,
        output_paths=output_paths,
        axis_labels=find_axis_labels(strings),
        colormaps=find_colormaps(text, strings),
        plot_calls=find_plot_calls(text),
        constants=constants,
    )
    record.notes = summarize_notes(record)
    return record


def iter_code_files(roots: list[Path]) -> Iterable[Path]:
    suffixes = {".py", ".m", ".ipynb"}
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix.lower() in suffixes:
            yield root
        elif root.is_dir():
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.suffix.lower() in suffixes and "__pycache__" not in path.parts:
                    yield path


def write_markdown(records: list[PlotCodeRecord], path: Path) -> None:
    lines = [
        "# Plot Code Index",
        "",
        "Purpose:",
        "- Retrieve prior plotting implementations as precise context for future figure generation.",
        "- Source code remains the ground truth; this file is a compact navigation layer.",
        "",
        f"Indexed records: {len(records)}",
        "",
    ]
    tag_counts: dict[str, int] = {}
    for record in records:
        for tag in record.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    if tag_counts:
        lines.extend(["## Tags", ""])
        for tag, count in sorted(tag_counts.items()):
            lines.append(f"- `{tag}`: {count}")
        lines.append("")

    lines.extend(["## Records", ""])
    for record in records:
        lines.append(f"### `{record.path}`")
        lines.append(f"- language: `{record.language}`")
        if record.tags:
            lines.append(f"- tags: {', '.join(f'`{tag}`' for tag in record.tags)}")
        if record.functions:
            lines.append(f"- functions: {', '.join(f'`{name}`' for name in record.functions[:10])}")
        if record.plot_calls:
            lines.append(f"- plot calls: {', '.join(f'`{name}`' for name in record.plot_calls)}")
        if record.colormaps:
            lines.append(f"- colormaps: {', '.join(f'`{name}`' for name in record.colormaps)}")
        if record.axis_labels:
            lines.append("- labels: " + "; ".join(f"`{label}`" for label in record.axis_labels[:8]))
        if record.data_paths:
            lines.append("- data/source hints: " + "; ".join(f"`{item}`" for item in record.data_paths[:6]))
        if record.output_paths:
            lines.append("- output hints: " + "; ".join(f"`{item}`" for item in record.output_paths[:6]))
        if record.notes:
            lines.append("- notes: " + "; ".join(record.notes))
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index plotting code for retrieval.")
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        help="Root file/directory to scan. Defaults to scripts/ and tools/plotting/.",
    )
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    roots = [PACKAGE_ROOT / "scripts", PACKAGE_ROOT / "tools" / "plotting"]
    roots.extend(Path(root) if Path(root).is_absolute() else PACKAGE_ROOT / root for root in args.root)
    records = [record for path in iter_code_files(roots) if (record := index_file(path))]
    records.sort(key=lambda record: record.path)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "purpose": "plot_code_retrieval",
        "roots": [relpath(root) for root in roots],
        "record_count": len(records),
        "records": [asdict(record) for record in records],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(records, args.output_md)
    print(args.output_json)
    print(args.output_md)
    print(f"records={len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
