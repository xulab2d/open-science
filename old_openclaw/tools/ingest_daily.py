#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
STATE_VERSION = 1

IGNORED_NAMES = {
    ".DS_Store",
    "Thumbs.db",
}

SCRIPT_EXTS = {
    ".m",
    ".py",
    ".ipynb",
    ".sh",
    ".zsh",
    ".bash",
    ".jl",
    ".r",
}

NOTE_EXTS = {
    ".md",
    ".txt",
    ".rtf",
    ".pdf",
}

QUESTION_CATEGORIES = {
    "naming",
    "ownership",
    "instrument",
    "schema",
    "analysis",
}


@dataclasses.dataclass(frozen=True)
class BatchSpec:
    key: str
    family: str
    rel_dir: str
    kind: str  # leaf_dir | dir_files | coarse_dir
    dir_path: Path
    depth: int


def _local_tz() -> dt.tzinfo:
    tz = dt.datetime.now().astimezone().tzinfo
    if tz is None:
        raise RuntimeError("Failed to determine local timezone")
    return tz


def _iso_now() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def _today_str() -> str:
    return dt.date.today().isoformat()


def _sha1_hex_str(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="replace")).hexdigest()


def _stable_batch_id(batch_key: str) -> str:
    return f"batch_{_sha1_hex_str(batch_key)[:16]}"


def _path_for_record(path: Path, workspace_root: Path) -> str:
    """
    Prefer workspace-relative paths for portability; fall back to absolute paths when
    the data root is outside the workspace.
    """
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError:
        return path.as_posix()


def _parse_since(value: str) -> dt.datetime:
    value = value.strip()
    try:
        if len(value) == 10:
            d = dt.date.fromisoformat(value)
            return dt.datetime(d.year, d.month, d.day, tzinfo=_local_tz())
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=_local_tz())
        return parsed
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid --since value: {value!r}. Use YYYY-MM-DD or an ISO datetime (optionally timezone-aware)."
        ) from e


def _norm_rel_subpath(value: str) -> str:
    s = value.strip().replace("\\", "/")
    while s.startswith("./"):
        s = s[2:]
    s = s.strip("/")
    return s


def _dedupe_watched_roots(paths: list[str]) -> list[str]:
    cleaned = sorted({_norm_rel_subpath(p) for p in paths if _norm_rel_subpath(p)})
    out: list[str] = []
    for p in cleaned:
        if any(p == root or p.startswith(root + "/") for root in out):
            continue
        out.append(p)
    return out


def _looks_like_json_path(value: str) -> bool:
    p = Path(value).expanduser()
    return p.suffix.lower() == ".json" or "/" in value or value.startswith(".")


def _load_watched_from_config(config_path: Path) -> tuple[str | None, list[str], str | None]:
    if not config_path.exists():
        raise argparse.ArgumentTypeError(f"Watched config JSON not found: {config_path}")
    try:
        obj = _load_json(config_path)
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Failed to load watched config JSON: {config_path}") from e
    if not isinstance(obj, dict):
        raise argparse.ArgumentTypeError(f"Watched config JSON must be an object: {config_path}")

    root = obj.get("dropbox_root") if isinstance(obj.get("dropbox_root"), str) else None
    watched_raw = obj.get("watched_roots")
    watched = [str(x) for x in watched_raw] if isinstance(watched_raw, list) else []
    inbox = obj.get("inbox_root") if isinstance(obj.get("inbox_root"), str) else None
    return root, watched, inbox


def _load_delta_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise argparse.ArgumentTypeError(f"Delta manifest not found: {path}")
    try:
        obj = _load_json(path)
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Failed to load delta manifest: {path}") from e
    if not isinstance(obj, dict):
        raise argparse.ArgumentTypeError(f"Delta manifest must be an object: {path}")
    return obj


def _seed_dirs_from_manifest(
    *,
    manifest: dict[str, Any],
    data_root: Path,
) -> tuple[Path, list[tuple[str, Path]]]:
    root = data_root
    root_raw = manifest.get("dropbox_root")
    if isinstance(root_raw, str) and root_raw.strip():
        root = Path(root_raw).expanduser().resolve()

    changed = manifest.get("changed_directories")
    if not isinstance(changed, list):
        return root, []

    seed: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for item in changed:
        if not isinstance(item, dict):
            continue
        path_value = item.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            continue

        # Delta manifests are intended to seed *directories* for ingestion.
        # However, some manifests (especially older ones) may contain file paths.
        # Be defensive: normalize to a directory by promoting file paths → parent dirs.
        raw = path_value.strip().replace("\\", "/")
        p = Path(raw).expanduser()
        if p.is_absolute():
            abs_path = p.resolve()
            try:
                rel = abs_path.relative_to(root).as_posix()
            except ValueError:
                rel = _norm_rel_subpath(abs_path.as_posix())
        else:
            rel = _norm_rel_subpath(raw)
            abs_path = (root / rel).resolve()

        # Promote to parent directory if this is a file path (heuristic via suffix or existing file).
        rel_dir = rel
        abs_dir = abs_path
        try:
            looks_like_file = bool(Path(rel).suffix)
        except Exception:
            looks_like_file = False
        if looks_like_file or (abs_dir.exists() and abs_dir.is_file()):
            rel_dir = _norm_rel_subpath(str(Path(rel_dir).parent).replace("\\", "/"))
            abs_dir = abs_dir.parent

        if not rel_dir or rel_dir in seen:
            continue
        seen.add(rel_dir)
        seed.append((rel_dir, abs_dir))

    seed.sort(key=lambda x: x[0])
    return root, seed


def _discover_batches(
    data_root: Path,
    *,
    watched_roots: list[str],
    seed_dirs: list[tuple[str, Path]] | None,
    max_depth: int,
    max_subdirs: int,
    open_questions: list[dict[str, Any]],
) -> list[BatchSpec]:
    batches: list[BatchSpec] = []

    if seed_dirs is not None:
        for rel, abs_dir in seed_dirs:
            if not abs_dir.exists():
                open_questions.append(
                    {
                        "key": f"missing_delta_dir:{rel}",
                        "text": f"Delta-manifest directory is missing locally and was skipped: {rel}",
                        "evidence": {"rel_dir": rel},
                    }
                )
                continue
            if not abs_dir.is_dir():
                open_questions.append(
                    {
                        "key": f"invalid_delta_dir:{rel}",
                        "text": f"Delta-manifest path is not a directory and was skipped: {rel}",
                        "evidence": {"rel_dir": rel},
                    }
                )
                continue

            family = rel.split("/", 1)[0] if rel else abs_dir.name
            batches.extend(
                _split_dir_into_batches(
                    abs_dir,
                    rel_dir=rel,
                    family=family,
                    depth=1,
                    max_depth=max_depth,
                    max_subdirs=max_subdirs,
                    open_questions=open_questions,
                )
            )
        return batches

    if not watched_roots:
        for fam_dir in sorted(data_root.iterdir()):
            if not fam_dir.is_dir():
                continue
            family = fam_dir.name
            batches.extend(
                _split_dir_into_batches(
                    fam_dir,
                    rel_dir=family,
                    family=family,
                    depth=1,
                    max_depth=max_depth,
                    max_subdirs=max_subdirs,
                    open_questions=open_questions,
                )
            )
        return batches

    for rel in watched_roots:
        watched_dir = (data_root / rel).resolve()
        if not watched_dir.exists():
            open_questions.append(
                {
                    "key": f"missing_watched:{rel}",
                    "text": f"Configured watched root is missing locally (likely not synced yet): {rel}",
                    "evidence": {"rel_dir": rel, "family": rel.split('/')[0] if rel else rel},
                }
            )
            continue
        if not watched_dir.is_dir():
            open_questions.append(
                {
                    "key": f"invalid_watched:{rel}",
                    "text": f"Configured watched root is not a directory and was skipped: {rel}",
                    "evidence": {"rel_dir": rel, "family": rel.split('/')[0] if rel else rel},
                }
            )
            continue

        family = rel.split("/", 1)[0] if rel else watched_dir.name
        batches.extend(
            _split_dir_into_batches(
                watched_dir,
                rel_dir=rel,
                family=family,
                depth=1,
                max_depth=max_depth,
                max_subdirs=max_subdirs,
                open_questions=open_questions,
            )
        )
    return batches


def _iter_dir_entries(dir_path: Path) -> tuple[list[os.DirEntry[str]], list[os.DirEntry[str]]]:
    files: list[os.DirEntry[str]] = []
    dirs: list[os.DirEntry[str]] = []
    with os.scandir(dir_path) as it:
        for entry in it:
            if entry.name in IGNORED_NAMES or entry.name.startswith("."):
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    dirs.append(entry)
                elif entry.is_file(follow_symlinks=False):
                    files.append(entry)
            except FileNotFoundError:
                continue
    files.sort(key=lambda e: e.name)
    dirs.sort(key=lambda e: e.name)
    return files, dirs

def _split_dir_into_batches(
    dir_path: Path,
    *,
    rel_dir: str,
    family: str,
    depth: int,
    max_depth: int,
    max_subdirs: int,
    open_questions: list[dict[str, Any]],
) -> list[BatchSpec]:
    files, subdirs = _iter_dir_entries(dir_path)
    has_loose_files = len(files) > 0
    has_subdirs = len(subdirs) > 0

    # Depth only matters if we would recurse further.
    too_deep = depth >= max_depth and has_subdirs
    too_wide = len(subdirs) > max_subdirs
    if too_deep or too_wide:
        key = f"{'deep' if too_deep else 'wide'}_dir:{rel_dir}"
        why = "depth" if too_deep else "subdir-count"
        open_questions.append(
            {
                "key": key,
                "text": (
                    f"Directory exceeds v1 batching limit ({why}); ingest_daily is treating it as a single coarse batch. "
                    "Consider adding a more specific batching rule here."
                ),
                "evidence": {
                    "rel_dir": rel_dir,
                    "family": family,
                    "depth": depth,
                    "max_depth": max_depth,
                    "subdir_count": len(subdirs),
                    "max_subdirs": max_subdirs,
                },
            }
        )
        return [
            BatchSpec(
                key=rel_dir,
                family=family,
                rel_dir=rel_dir,
                kind="coarse_dir",
                dir_path=dir_path,
                depth=depth,
            )
        ]

    if has_subdirs:
        batches: list[BatchSpec] = []
        if has_loose_files:
            batches.append(
                BatchSpec(
                    key=f"{rel_dir}::files",
                    family=family,
                    rel_dir=rel_dir,
                    kind="dir_files",
                    dir_path=dir_path,
                    depth=depth,
                )
            )
        for sub in subdirs:
            batches.extend(
                _split_dir_into_batches(
                    Path(sub.path),
                    rel_dir=f"{rel_dir}/{sub.name}",
                    family=family,
                    depth=depth + 1,
                    max_depth=max_depth,
                    max_subdirs=max_subdirs,
                    open_questions=open_questions,
                )
            )
        return batches

    if has_loose_files:
        return [
            BatchSpec(
                key=rel_dir,
                family=family,
                rel_dir=rel_dir,
                kind="leaf_dir",
                dir_path=dir_path,
                depth=depth,
            )
        ]

    return []


def _dir_mtime_iso(path: Path) -> str:
    st = path.stat()
    return dt.datetime.fromtimestamp(st.st_mtime).astimezone().replace(microsecond=0).isoformat()


def _scan_batch_files(
    spec: BatchSpec,
    *,
    max_files_sampled: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (sig, stats) for a batch.

    - sig.value hashes only file *metadata* (name, size, mtime)
    - Never reads `.mat` contents.
    """

    ext_counts: Counter[str] = Counter()
    total_files = 0
    total_bytes = 0
    max_mtime: float | None = None

    script_files: list[str] = []
    note_files: list[str] = []
    sample_files: list[dict[str, Any]] = []

    hasher = hashlib.sha1()

    def consider(rel_name: str, st: os.stat_result) -> None:
        nonlocal total_files, total_bytes, max_mtime
        total_files += 1
        total_bytes += st.st_size
        if max_mtime is None or st.st_mtime > max_mtime:
            max_mtime = st.st_mtime

        ext = Path(rel_name).suffix.lower() or "<noext>"
        ext_counts[ext] += 1

        if ext in SCRIPT_EXTS:
            script_files.append(rel_name)
        if ext in NOTE_EXTS:
            note_files.append(rel_name)

        hasher.update(rel_name.encode("utf-8", errors="replace"))
        hasher.update(b"\x00")
        hasher.update(str(int(st.st_size)).encode("ascii"))
        hasher.update(b"\x00")
        hasher.update(str(int(st.st_mtime)).encode("ascii"))
        hasher.update(b"\n")

        if len(sample_files) < max_files_sampled:
            sample_files.append(
                {
                    "name": rel_name,
                    "bytes": st.st_size,
                    "mtime": dt.datetime.fromtimestamp(st.st_mtime)
                    .astimezone()
                    .replace(microsecond=0)
                    .isoformat(),
                }
            )

    if spec.kind in {"leaf_dir", "dir_files"}:
        files, _subdirs = _iter_dir_entries(spec.dir_path)
        for entry in files:
            try:
                st = entry.stat(follow_symlinks=False)
            except FileNotFoundError:
                continue
            consider(entry.name, st)
    elif spec.kind == "coarse_dir":
        for dirpath, dirnames, filenames in os.walk(spec.dir_path):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in IGNORED_NAMES]
            for fn in sorted(filenames):
                if fn.startswith(".") or fn in IGNORED_NAMES:
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    st = os.stat(fp, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                rel_name = os.path.relpath(fp, spec.dir_path).replace(os.sep, "/")
                consider(rel_name, st)
    else:
        raise ValueError(f"Unknown batch kind: {spec.kind}")

    sig = {
        "algo": "sha1(name,size,mtime)",
        "value": hasher.hexdigest(),
        "file_count": total_files,
        "total_bytes": total_bytes,
        "max_mtime": None
        if max_mtime is None
        else dt.datetime.fromtimestamp(max_mtime).astimezone().replace(microsecond=0).isoformat(),
    }

    stats = {
        "file_count": total_files,
        "file_count_by_ext": dict(ext_counts),
        "script_files": sorted(script_files),
        "note_files": sorted(note_files),
        "sample_files": sample_files,
    }
    return sig, stats


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def _write_text_if_changed(path: Path, content: str, *, dry_run: bool) -> bool:
    """Return True if a write would occur / occurred."""

    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace")
        if existing == content:
            return False
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _append_jsonl(path: Path, records: list[dict[str, Any]], *, dry_run: bool) -> int:
    if not records:
        return 0
    if dry_run:
        return len(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return len(records)


def _load_open_question_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s.startswith("<!-- key:") and s.endswith("-->"):
            keys.add(s[len("<!-- key:") : -len("-->")].strip())
    return keys


def _render_open_question_block(question: dict[str, Any]) -> str:
    key = str(question["key"]).strip()
    text = str(question["text"]).strip()
    evidence = question.get("evidence")

    lines: list[str] = []
    lines.append(f"<!-- key: {key} -->")
    lines.append(f"- [ ] {text}")
    if evidence is not None:
        lines.append("  - evidence: `" + json.dumps(evidence, sort_keys=True) + "`")
    lines.append("")
    return "\n".join(lines)


def _update_open_questions(path: Path, new_questions: list[dict[str, Any]], *, dry_run: bool) -> int:
    existing = _load_open_question_keys(path)
    to_add = [q for q in new_questions if q.get("key") and q["key"] not in existing]
    if not to_add:
        return 0
    if dry_run:
        return len(to_add)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for q in to_add:
            f.write(_render_open_question_block(q))
    return len(to_add)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            records.append(obj)
    return records


def _ensure_jsonl_header(path: Path, meta: dict[str, Any], *, dry_run: bool) -> bool:
    if path.exists():
        return False
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, sort_keys=True) + "\n", encoding="utf-8")
    return True


def _collapse_ws(s: str) -> str:
    return " ".join(s.split())


def _normalize_question_text(text: str) -> str:
    return _collapse_ws(text).strip().lower()


def _normalize_evidence_paths(paths: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for p in paths:
        s = str(p).strip().replace(os.sep, "/")
        if s.startswith("./"):
            s = s[2:]
        s = s.rstrip("/")
        if not s:
            continue
        if s not in seen:
            out.append(s)
            seen.add(s)
    out.sort()
    return out


def _question_dedupe_key(text: str, evidence_paths: list[str]) -> str:
    norm_text = _normalize_question_text(text)
    norm_paths = _normalize_evidence_paths(evidence_paths)
    return norm_text + "\n" + "\n".join(norm_paths)


def _question_id_from_dedupe(dedupe_key: str) -> str:
    return "q_" + _sha1_hex_str(dedupe_key)[:16]


def _infer_question_category(question: dict[str, Any]) -> str:
    key = str(question.get("key") or "")
    if key.startswith(("deep_dir:", "wide_dir:", "max_batches:")):
        return "schema"
    return "analysis"


def _evidence_paths_from_question(question: dict[str, Any]) -> list[str]:
    evidence = question.get("evidence") or {}
    if not isinstance(evidence, dict):
        return []
    rel_dir = evidence.get("rel_dir")
    if isinstance(rel_dir, str) and rel_dir.strip():
        rel = rel_dir.strip().replace(os.sep, "/").lstrip("/")
        return [f"data::{rel}"]
    return []


def _load_routing_rules(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = _load_json(path)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _route_question(
    *,
    category: str,
    family: str | None,
    routing_rules: dict[str, Any],
) -> tuple[list[str], Any | None]:
    people: list[str] = []
    slack_target: Any | None = None

    categories = routing_rules.get("categories") if isinstance(routing_rules.get("categories"), dict) else {}
    families = routing_rules.get("families") if isinstance(routing_rules.get("families"), dict) else {}

    cat_rule = categories.get(category) if isinstance(categories.get(category), dict) else {}
    fam_rule = families.get(family) if isinstance(families.get(family), dict) else {}

    for pk in (cat_rule.get("people_keys") or []):
        if isinstance(pk, str) and pk and pk not in people:
            people.append(pk)
    for pk in (fam_rule.get("people_keys") or []):
        if isinstance(pk, str) and pk and pk not in people:
            people.append(pk)

    slack_target = fam_rule.get("slack_target") or cat_rule.get("slack_target") or routing_rules.get("default_slack_target")
    return people, slack_target


def _upsert_questions_queue(
    queue_path: Path,
    questions: list[dict[str, Any]],
    *,
    routing_rules: dict[str, Any],
    run_started: str,
    dry_run: bool,
) -> tuple[int, int, bool]:
    """
    Upsert structured question items into a JSONL queue file.

    Dedupe key: normalized question_text + evidence_paths.
    Preserves manual status/resolution edits.

    Returns (added, updated, wrote_file).
    """
    meta_default = {
        "type": "meta",
        "schema_version": 1,
        "created_at": run_started,
        "notes": "Structured open-questions queue for automation. Edit status/resolution fields by hand.",
    }

    if not queue_path.exists():
        _ensure_jsonl_header(queue_path, {**meta_default, "created_at": run_started}, dry_run=dry_run)

    raw = _read_jsonl(queue_path)
    meta: dict[str, Any] | None = None
    items: list[dict[str, Any]] = []
    for rec in raw:
        if rec.get("type") == "meta" and meta is None:
            meta = rec
        else:
            items.append(rec)
    if meta is None:
        meta = meta_default

    existing_by_dedupe: dict[str, dict[str, Any]] = {}
    existing_by_text: dict[str, dict[str, Any]] = {}
    for rec in items:
        if not isinstance(rec, dict):
            continue
        text = rec.get("question_text")
        paths = rec.get("evidence_paths")
        if not isinstance(text, str) or not isinstance(paths, list):
            continue
        dedupe_key = _question_dedupe_key(text, [str(p) for p in paths])
        existing_by_dedupe.setdefault(dedupe_key, rec)
        existing_by_text.setdefault(_normalize_question_text(text), rec)

    added = 0
    updated = 0

    for q in questions:
        q_text = str(q.get("text") or "").strip()
        if not q_text:
            continue
        q_status = q.get("status")
        if q_status not in {"open", "resolved"}:
            q_status = "open"
        evidence_paths = _evidence_paths_from_question(q)
        dedupe_key = _question_dedupe_key(q_text, evidence_paths)
        q_id = _question_id_from_dedupe(dedupe_key)
        norm_text = _normalize_question_text(q_text)

        evidence = q.get("evidence") if isinstance(q.get("evidence"), dict) else {}
        family = evidence.get("family") if isinstance(evidence.get("family"), str) else None

        category = _infer_question_category(q)
        if category not in QUESTION_CATEGORIES:
            category = "analysis"

        suggested_assignees, slack_target = _route_question(
            category=category,
            family=family,
            routing_rules=routing_rules,
        )

        existing = existing_by_dedupe.get(dedupe_key) or existing_by_text.get(norm_text)
        if existing is None:
            items.append(
                {
                    "id": q_id,
                    "created_at": run_started,
                    "status": q_status,
                    "question_text": q_text,
                    "category": category,
                    "evidence_paths": evidence_paths,
                    "suggested_assignees": suggested_assignees,
                    "slack_target": slack_target,
                    "resolution": None,
                    "resolved_at": None,
                }
            )
            added += 1
            continue

        changed = False
        if (not isinstance(existing.get("id"), str) or not existing.get("id")) and existing.get("id") != q_id:
            existing["id"] = q_id
            changed = True
        if (not isinstance(existing.get("created_at"), str) or not existing.get("created_at")) and existing.get("created_at") != run_started:
            existing["created_at"] = run_started
            changed = True
        if existing.get("status") not in {"open", "resolved"}:
            existing["status"] = "open"
            changed = True

        if existing.get("category") not in QUESTION_CATEGORIES:
            existing["category"] = category
            changed = True

        existing_paths = existing.get("evidence_paths")
        if not isinstance(existing_paths, list):
            if existing_paths != evidence_paths:
                existing["evidence_paths"] = evidence_paths
                changed = True
        elif (not existing_paths) and evidence_paths:
            existing["evidence_paths"] = evidence_paths
            changed = True

        existing_suggested = existing.get("suggested_assignees")
        if not isinstance(existing_suggested, list):
            if existing_suggested != suggested_assignees:
                existing["suggested_assignees"] = suggested_assignees
                changed = True
        elif (not existing_suggested) and suggested_assignees:
            existing["suggested_assignees"] = suggested_assignees
            changed = True

        if existing.get("slack_target") in (None, "") and slack_target is not None:
            existing["slack_target"] = slack_target
            changed = True

        if changed:
            updated += 1

    if added == 0 and updated == 0 and meta.get("created_at") not in (None, ""):
        return 0, 0, False

    if meta.get("created_at") in (None, ""):
        meta["created_at"] = run_started

    content_lines = [json.dumps(meta, sort_keys=True)]
    for rec in items:
        content_lines.append(json.dumps(rec, sort_keys=True))
    content = "\n".join(content_lines) + "\n"
    wrote = _write_text_if_changed(queue_path, content, dry_run=dry_run)
    return added, updated, wrote


def _append_alias_candidates(
    aliases_path: Path,
    candidates: list[dict[str, Any]],
    *,
    dry_run: bool,
) -> int:
    meta_default = {
        "type": "meta",
        "schema_version": 1,
        "created_at": _iso_now(),
        "notes": "Append-only lab term/alias index. tools/ingest_daily.py may propose low-confidence candidates.",
    }
    if not aliases_path.exists():
        _ensure_jsonl_header(aliases_path, meta_default, dry_run=dry_run)

    existing_terms: set[str] = set()
    for rec in _read_jsonl(aliases_path):
        if rec.get("type") == "meta":
            continue
        term = rec.get("canonical_term")
        if isinstance(term, str) and term:
            existing_terms.add(term)

    to_add: list[dict[str, Any]] = []
    for c in candidates:
        term = c.get("canonical_term")
        if not isinstance(term, str) or not term:
            continue
        if term in existing_terms:
            continue
        to_add.append(c)
        existing_terms.add(term)

    if not to_add:
        return 0
    return _append_jsonl(aliases_path, to_add, dry_run=dry_run)


def _ensure_batches_header(path: Path, *, dry_run: bool) -> bool:
    if path.exists():
        return False
    meta = {
        "type": "meta",
        "schema_version": SCHEMA_VERSION,
        "created_at": _iso_now(),
        "notes": "Append-only batch snapshots written by tools/ingest_daily.py",
    }
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, sort_keys=True) + "\n", encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Incrementally index lab data runs into batch-level JSONL.")
    p.add_argument("--root", default="data", help="Root data directory (default: data)")
    p.add_argument(
        "--delta-manifest",
        default=None,
        help="Optional delta manifest JSON (ingest only changed_directories from this file)",
    )
    p.add_argument(
        "--watched",
        default=None,
        help=(
            "Comma-separated watched subpaths under --root, or path to dropbox_config.json "
            "(uses watched_roots and optionally dropbox_root/inbox_root)."
        ),
    )
    p.add_argument("--inbox", default=None, help="Optional inbox subpath under --root; included in watched scope")
    p.add_argument("--out", default="out", help="Generated artifacts directory (default: out)")
    p.add_argument("--index", default="index", help="Index directory (default: index)")
    p.add_argument("--state", default="state", help="State directory (default: state)")
    p.add_argument("--dry-run", action="store_true", help="Do not write files; print what would change")
    p.add_argument("--force", action="store_true", help="Re-scan + snapshot all batches")
    p.add_argument("--since", type=_parse_since, default=None, help="Only snapshot batches with max mtime >= since")
    p.add_argument("--max-batches", type=int, default=None, help="Cap number of batches processed")
    p.add_argument(
        "--max-files-sampled",
        type=int,
        default=25,
        help="Max sample filenames recorded per batch (default: 25)",
    )
    p.add_argument("--max-depth", type=int, default=6, help="Max directory depth for batching (default: 6)")
    p.add_argument(
        "--max-subdirs",
        type=int,
        default=150,
        help="Treat very wide directories as coarse batches (default: 150)",
    )

    args = p.parse_args(argv)

    cwd = Path.cwd().resolve()
    out_dir = (cwd / args.out).resolve()
    index_dir = (cwd / args.index).resolve()
    state_dir = (cwd / args.state).resolve()
    reports_dir = (cwd / "reports").resolve()

    root_arg_path = Path(args.root).expanduser()
    if root_arg_path.is_absolute():
        data_root = root_arg_path.resolve()
    else:
        data_root = (cwd / root_arg_path).resolve()

    watched_roots: list[str] = []
    seed_dirs: list[tuple[str, Path]] | None = None
    delta_mode = False
    inbox_root: str | None = _norm_rel_subpath(args.inbox) if args.inbox else None

    if args.watched:
        watched_arg = args.watched.strip()
        watched_path = Path(watched_arg).expanduser()
        config_path: Path | None = None
        if _looks_like_json_path(watched_arg):
            if watched_path.is_absolute():
                config_path = watched_path
            else:
                config_path = (cwd / watched_path).resolve()
            if config_path.exists():
                cfg_root, cfg_watched, cfg_inbox = _load_watched_from_config(config_path)
                watched_roots.extend(cfg_watched)
                if args.root == "data" and cfg_root:
                    data_root = Path(cfg_root).expanduser().resolve()
                if not inbox_root and cfg_inbox:
                    inbox_root = _norm_rel_subpath(cfg_inbox)
            else:
                # Fall back to CSV parsing for convenience when users pass simple labels.
                watched_roots.extend([x.strip() for x in watched_arg.split(",") if x.strip()])
        else:
            watched_roots.extend([x.strip() for x in watched_arg.split(",") if x.strip()])

    if inbox_root:
        watched_roots.append(inbox_root)
    watched_roots = _dedupe_watched_roots(watched_roots)

    if args.delta_manifest:
        delta_mode = True
        dm_path = Path(args.delta_manifest).expanduser()
        if not dm_path.is_absolute():
            dm_path = (cwd / dm_path).resolve()
        manifest = _load_delta_manifest(dm_path)
        # If the caller did not pass --watched, fall back to the manifest's watched_roots
        # (written by tools/dropbox_sync.py) so delta-mode runs stay properly scoped.
        if not watched_roots:
            dm_watched = manifest.get("watched_roots")
            if isinstance(dm_watched, list) and dm_watched:
                watched_roots = _dedupe_watched_roots([str(x) for x in dm_watched if str(x).strip()])
        manifest_root, seed_dirs = _seed_dirs_from_manifest(manifest=manifest, data_root=data_root)
        if args.root == "data":
            data_root = manifest_root

    if not data_root.exists() or not data_root.is_dir():
        raise SystemExit(f"Data root not found or not a directory: {data_root}")

    run_started = _iso_now()
    run_date = _today_str()

    state_path = state_dir / "ingestion_state.json"
    if state_path.exists():
        state = _load_json(state_path)
    else:
        state = {
            "version": STATE_VERSION,
            "created_at": run_started,
            "last_run": None,
            "roots": {},
            "batches": {},
        }

    state.setdefault("version", STATE_VERSION)
    if not state.get("created_at"):
        state["created_at"] = run_started
    state.setdefault("roots", {})
    state.setdefault("batches", {})

    state["roots"] = {
        "workspace": str(cwd),
        "data": str(data_root),
        "watched_roots": watched_roots,
        "delta_seed_dirs": [rel for rel, _abs in (seed_dirs or [])],
        "inbox_root": inbox_root,
        "out": str(out_dir),
        "index": str(index_dir),
        "state": str(state_dir),
        "reports": str(reports_dir),
    }

    open_questions: list[dict[str, Any]] = []
    batch_specs = _discover_batches(
        data_root,
        watched_roots=watched_roots,
        seed_dirs=seed_dirs,
        max_depth=args.max_depth,
        max_subdirs=args.max_subdirs,
        open_questions=open_questions,
    )

    if args.max_batches is not None and len(batch_specs) > args.max_batches:
        open_questions.append(
            {
                "key": f"max_batches:{run_date}",
                "text": f"Batch discovery produced {len(batch_specs)} entries; capped to --max-batches={args.max_batches}.",
                "evidence": {"discovered": len(batch_specs), "max_batches": args.max_batches},
            }
        )
        batch_specs = batch_specs[: args.max_batches]

    batches_path = index_dir / "batches.jsonl"
    openq_path = index_dir / "open_questions.md"
    queue_path = index_dir / "open_questions.jsonl"
    aliases_path = index_dir / "aliases.jsonl"
    routing_rules_path = index_dir / "routing_rules.json"
    digest_path = reports_dir / f"daily_digest_{run_date}.md"

    header_written = _ensure_batches_header(batches_path, dry_run=args.dry_run)
    routing_rules = _load_routing_rules(routing_rules_path)

    changed_records: list[dict[str, Any]] = []
    new_count = 0
    changed_count = 0
    unchanged_count = 0
    scanned_count = 0
    skipped_scan_count = 0

    total_files = 0
    total_exts: Counter[str] = Counter()

    changed_batch_keys: list[str] = []

    last_run = state.get("last_run")
    last_run_dt: dt.datetime | None = None
    if isinstance(last_run, str) and last_run:
        try:
            last_run_dt = dt.datetime.fromisoformat(last_run)
            if last_run_dt.tzinfo is None:
                last_run_dt = last_run_dt.replace(tzinfo=_local_tz())
        except ValueError:
            last_run_dt = None

    for spec in batch_specs:
        batch_id = _stable_batch_id(spec.key)
        prev = state["batches"].get(batch_id)

        dir_mtime = _dir_mtime_iso(spec.dir_path)
        if (
            not delta_mode
            and not args.force
            and isinstance(prev, dict)
            and prev.get("dir_mtime") == dir_mtime
        ):
            # Directory listing unchanged (best-effort); avoid rescanning.
            skipped_scan_count += 1
            unchanged_count += 1
            prev_stats = prev.get("stats") or {}
            total_files += int(prev_stats.get("file_count") or 0)
            total_exts.update(prev_stats.get("file_count_by_ext") or {})
            continue

        # If we have a last_run timestamp and this directory hasn't changed since then, skip.
        if (
            not delta_mode
            and not args.force
            and last_run_dt is not None
            and isinstance(prev, dict)
            and dt.datetime.fromisoformat(dir_mtime) < last_run_dt
        ):
            skipped_scan_count += 1
            unchanged_count += 1
            prev_stats = prev.get("stats") or {}
            total_files += int(prev_stats.get("file_count") or 0)
            total_exts.update(prev_stats.get("file_count_by_ext") or {})
            continue

        scanned_count += 1
        sig, stats = _scan_batch_files(spec, max_files_sampled=args.max_files_sampled)
        total_files += int(stats["file_count"])
        total_exts.update(stats["file_count_by_ext"])

        prev_sig = (prev or {}).get("sig", {}).get("value")
        is_new = prev is None
        sig_changed = prev_sig != sig["value"]

        since_ok = True
        if args.since is not None:
            max_mtime = sig.get("max_mtime")
            if not max_mtime:
                since_ok = False
            else:
                batch_mtime = dt.datetime.fromisoformat(max_mtime)
                if batch_mtime.tzinfo is None:
                    batch_mtime = batch_mtime.replace(tzinfo=_local_tz())
                since_ok = batch_mtime >= args.since

        should_snapshot = since_ok and (args.force or is_new or sig_changed)

        # Update state (dir_mtime helps incremental skipping).
        # Only advance last_changed when the signature changes (new/changed content).
        next_last_changed = (prev or {}).get("last_changed")
        if is_new or sig_changed or args.force:
            next_last_changed = run_started

        state["batches"][batch_id] = {
            "batch_key": spec.key,
            "family": spec.family,
            "rel_dir": spec.rel_dir,
            "kind": spec.kind,
            "depth": spec.depth,
            "path": _path_for_record(spec.dir_path, cwd),
            "dir_mtime": dir_mtime,
            "sig": sig,
            "stats": {
                "file_count": stats["file_count"],
                "file_count_by_ext": stats["file_count_by_ext"],
            },
            "last_changed": next_last_changed,
        }

        if should_snapshot:
            record = {
                "schema": SCHEMA_VERSION,
                "type": "batch",
                "recorded_at": run_started,
                "batch_id": batch_id,
                "batch_key": spec.key,
                "family": spec.family,
                "rel_dir": spec.rel_dir,
                "kind": spec.kind,
                "depth": spec.depth,
                "path": _path_for_record(spec.dir_path, cwd),
                "sig": sig,
                "stats": stats,
                "provenance": {
                    "root": str(data_root),
                    "dir_mtime": dir_mtime,
                },
                "confidence": {
                    "granularity": "high" if spec.kind != "coarse_dir" else "medium",
                },
            }
            changed_records.append(record)
            changed_batch_keys.append(spec.key)
            if is_new:
                new_count += 1
            else:
                changed_count += 1
        else:
            unchanged_count += 1

    appended = _append_jsonl(batches_path, changed_records, dry_run=args.dry_run)
    added_q = _update_open_questions(openq_path, open_questions, dry_run=args.dry_run)
    queue_added, queue_updated, queue_wrote = _upsert_questions_queue(
        queue_path,
        open_questions,
        routing_rules=routing_rules,
        run_started=run_started,
        dry_run=args.dry_run,
    )

    alias_candidates: list[dict[str, Any]] = []
    if delta_mode:
        families = sorted({rel.split("/", 1)[0] for rel, _abs in (seed_dirs or []) if rel})
    elif seed_dirs:
        families = sorted({rel.split("/", 1)[0] for rel, _abs in seed_dirs if rel})
    elif watched_roots:
        families = sorted({p.split("/", 1)[0] for p in watched_roots if p})
    else:
        families = [fam_dir.name for fam_dir in sorted(data_root.iterdir()) if fam_dir.is_dir()]
    for family in families:
        alias_candidates.append(
            {
                "canonical_term": family,
                "observed_terms": [family],
                "meaning": "",
                "confidence": 0.2,
                "evidence_paths": [f"data::{family}"],
                "confirmed_by": None,
                "notes": "Auto-proposed from top-level data/ folder name; fill meaning and raise confidence once confirmed.",
            }
        )
    aliases_added = _append_alias_candidates(aliases_path, alias_candidates, dry_run=args.dry_run)

    # Write digest only if this run changes anything OR the digest doesn't exist yet.
    changed_any = header_written or appended > 0 or added_q > 0 or queue_wrote or aliases_added > 0

    digest_lines: list[str] = []
    digest_lines.append(f"# OpenClaw daily ingest digest ({run_date})")
    digest_lines.append("")
    digest_lines.append(f"- workspace: `{cwd}`")
    digest_lines.append(f"- data root: `{data_root}`")
    digest_lines.append(f"- watched roots: `{len(watched_roots)}`")
    digest_lines.append(f"- delta manifest: `{args.delta_manifest}`")
    digest_lines.append(f"- delta seed dirs: `{len(seed_dirs or [])}`")
    if watched_roots:
        digest_lines.append("- watched root list: " + ", ".join(f"`{p}`" for p in watched_roots[:12]))
        if len(watched_roots) > 12:
            digest_lines.append(f"- watched root list: ... and `{len(watched_roots) - 12}` more")
    digest_lines.append(f"- inbox root: `{inbox_root}`")
    digest_lines.append(f"- run started: `{run_started}`")
    digest_lines.append(f"- dry run: `{args.dry_run}`")
    digest_lines.append("")
    digest_lines.append("## Summary")
    digest_lines.append("")
    digest_lines.append(f"- discovered batches: `{len(batch_specs)}`")
    digest_lines.append(f"- scanned: `{scanned_count}`")
    digest_lines.append(f"- skipped scan: `{skipped_scan_count}`")
    digest_lines.append(f"- snapshotted: `{appended}`")
    digest_lines.append(f"  - new: `{new_count}`")
    digest_lines.append(f"  - changed: `{changed_count}`")
    digest_lines.append(f"  - unchanged: `{unchanged_count}`")
    digest_lines.append(f"- open questions added: `{added_q}`")
    digest_lines.append(f"- structured questions (queue): `+{queue_added}` / `~{queue_updated}`")
    digest_lines.append(f"- alias candidates added: `{aliases_added}`")
    digest_lines.append(f"- files counted (metadata only): `{total_files}`")
    digest_lines.append("")

    if changed_batch_keys:
        digest_lines.append("## Changed batches")
        digest_lines.append("")
        for k in changed_batch_keys[:50]:
            digest_lines.append(f"- `{k}`")
        if len(changed_batch_keys) > 50:
            digest_lines.append(f"- ... and `{len(changed_batch_keys) - 50}` more")
        digest_lines.append("")

    digest_lines.append("## Extensions (top 10)")
    digest_lines.append("")
    for ext, cnt in total_exts.most_common(10):
        digest_lines.append(f"- `{ext}`: `{cnt}`")
    digest_lines.append("")

    digest = "\n".join(digest_lines) + "\n"

    wrote_digest = False
    if changed_any or not digest_path.exists():
        wrote_digest = _write_text_if_changed(digest_path, digest, dry_run=args.dry_run)

    # Persist state only if it actually changed (idempotent: a no-op run should not rewrite state).
    wrote_state = False
    state_content = _dump_json(state)
    existing_state = None
    if state_path.exists():
        existing_state = state_path.read_text(encoding="utf-8", errors="replace")
    if existing_state != state_content or not state_path.exists():
        state["last_run"] = run_started
        wrote_state = _write_text_if_changed(state_path, _dump_json(state), dry_run=args.dry_run)

    print(f"workspace: {cwd}")
    print(f"data_root: {data_root}")
    print(f"watched_roots: {len(watched_roots)}")
    print(f"delta_manifest: {args.delta_manifest}")
    print(f"delta_seed_dirs: {len(seed_dirs or [])}")
    if watched_roots:
        print("watched_root_list: " + ",".join(watched_roots))
    print(f"inbox_root: {inbox_root}")
    print(f"batches_discovered: {len(batch_specs)}")
    print(f"batches_scanned: {scanned_count}")
    print(f"batches_skipped_scan: {skipped_scan_count}")
    print(f"batches_snapshotted: {appended}")
    print(f"  new: {new_count}")
    print(f"  changed: {changed_count}")
    print(f"  unchanged: {unchanged_count}")
    print(f"open_questions_added: {added_q}")
    print(f"queue_added: {queue_added}")
    print(f"queue_updated: {queue_updated}")
    print(f"aliases_added: {aliases_added}")
    print(f"state_written: {wrote_state}")
    print(f"digest_written: {wrote_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
