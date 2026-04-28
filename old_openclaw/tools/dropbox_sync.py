#!/usr/bin/env python3
"""
Cursor-based Dropbox sync (deterministic; fast on large trees).

Goal:
  - Avoid remote full-tree walks by using the Dropbox "delta" cursor.
  - Download only changed files into the local cache root.
  - Write `state/delta_manifest.json` for deterministic ingestion.

Token source:
  - Prefer env `DROPBOX_ACCESS_TOKEN` if set.
  - Else read the current access_token from the configured rclone remote's `token` field.
    If the token is expired, this script will try to trigger an rclone refresh and re-read it.
"""

from __future__ import annotations

import argparse
import configparser
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any
import fnmatch


STATE_VERSION = 3
MANIFEST_VERSION = 1


def _iso_now() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _norm_rel(value: str) -> str:
    s = value.strip().replace("\\", "/")
    while s.startswith("./"):
        s = s[2:]
    return s.strip("/")


def _parse_iso(value: str) -> dt.datetime | None:
    try:
        d = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
        return d
    except Exception:
        return None


def _remote_name_from_rclone_remote(remote: str) -> str:
    # "dropbox:" or "dropbox:/OpenScience" -> "dropbox"
    r = remote.strip()
    if ":" not in r:
        return r
    return r.split(":", 1)[0]


def _default_rclone_config_path() -> Path:
    # rclone uses the RCLONE_CONFIG env var if set, else ~/.config/rclone/rclone.conf typically.
    env = os.environ.get("RCLONE_CONFIG")
    if env:
        return Path(env).expanduser()
    return Path("~/.config/rclone/rclone.conf").expanduser()


def _read_rclone_access_token(remote_name: str, rclone_config: Path) -> str | None:
    if not rclone_config.exists():
        return None
    cp = configparser.ConfigParser()
    cp.read(rclone_config, encoding="utf-8")
    if not cp.has_section(remote_name):
        return None
    token_raw = cp.get(remote_name, "token", fallback="").strip()
    if not token_raw:
        return None
    try:
        token_obj = json.loads(token_raw)
    except json.JSONDecodeError:
        return None
    tok = token_obj.get("access_token") if isinstance(token_obj, dict) else None
    return str(tok) if isinstance(tok, str) and tok.strip() else None


def _trigger_rclone_token_refresh(rclone_remote: str, timeout_s: float = 30.0) -> None:
    # Best-effort: run a small rclone call that should refresh and update the config token.
    try:
        subprocess.run(
            ["rclone", "lsd", rclone_remote, "--max-depth", "1"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except Exception:
        return


def _looks_like_expired_token(body: str) -> bool:
    b = body.lower()
    return "expired_access_token" in b or "invalid_access_token" in b


def _dropbox_api_json(
    *,
    endpoint: str,
    token_getter: callable,
    payload: dict[str, Any],
    timeout_s: float,
    max_retries: int,
    refresh_hook: callable | None,
) -> dict[str, Any]:
    # Note: we construct the request per-attempt since token can change after refresh.
    body = json.dumps(payload).encode("utf-8")

    refreshed = False
    for attempt in range(max(1, max_retries)):
        token = token_getter()
        if not token:
            raise SystemExit("No Dropbox access token available (set DROPBOX_ACCESS_TOKEN or configure rclone remote token).")
        req = urllib.request.Request(
            endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            retry_after = int(e.headers.get("Retry-After", "2") or "2")

            # If token is expired, try one rclone refresh + retry immediately.
            if e.code == 401 and not refreshed and refresh_hook and _looks_like_expired_token(detail):
                refresh_hook()
                refreshed = True
                continue

            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                time.sleep(min(30, max(1, retry_after)))
                continue
            raise SystemExit(f"Dropbox API error {e.code}: {detail[:800]}") from e
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                time.sleep(min(30, 2 + attempt))
                continue
            raise SystemExit(f"Dropbox API network error: {e}") from e

    raise SystemExit("Dropbox API failed after retries")


def _dropbox_download(
    *,
    token_getter: callable,
    refresh_hook: callable | None,
    dropbox_path: str,
    local_path: Path,
    timeout_s: float,
    max_retries: int,
    dry_run: bool,
) -> bool:
    if dry_run:
        return True

    refreshed = False
    for attempt in range(max(1, max_retries)):
        token = token_getter()
        if not token:
            return False
        req = urllib.request.Request(
            "https://content.dropboxapi.com/2/files/download",
            data=b"",
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Dropbox-API-Arg": json.dumps({"path": dropbox_path}),
                # Dropbox expects a non-form Content-Type for download calls.
                "Content-Type": "text/plain; charset=utf-8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                data = resp.read()
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(data)
                return True
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            retry_after = int(e.headers.get("Retry-After", "2") or "2")

            if e.code == 401 and not refreshed and refresh_hook and _looks_like_expired_token(detail):
                refresh_hook()
                refreshed = True
                continue

            if e.code in (409,):
                # Missing file, revoked access, or path conflict. Treat as non-fatal skip.
                return False
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                time.sleep(min(30, max(1, retry_after)))
                continue
            raise SystemExit(f"Dropbox download error {e.code}: {detail[:800]}") from e
        except urllib.error.URLError:
            if attempt < max_retries - 1:
                time.sleep(min(30, 2 + attempt))
                continue
            return False

    return False


def _path_in_scope(rel_path: str, watched_roots: list[str]) -> bool:
    if not watched_roots:
        return True
    p = rel_path.lower().strip("/")
    for w in watched_roots:
        wl = str(w).lower().strip("/")
        if not wl:
            return True
        if p == wl or p.startswith(wl + "/"):
            return True
    return False


def _cluster_candidate(rel_path: str) -> str:
    parts = [p for p in rel_path.split("/") if p]
    if not parts:
        return rel_path
    markers = ("run", "spot", "scan", "sweep", "hysteresis", "curie", "inbox", "experiment")
    for i in range(len(parts), 0, -1):
        name = parts[i - 1].lower()
        if any(m in name for m in markers):
            return "/".join(parts[:i])
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0]


def _looks_like_file_path(rel_path: str) -> bool:
    """Heuristic: Dropbox cursor entries are files; ensure we cluster on directories.

    We treat any path whose final component has a non-empty suffix (".mat", ".pptx", etc.)
    as a file. This is intentionally conservative; directory names with dots are rare in our
    dataset and downstream ingest expects directories.
    """

    p = PurePosixPath(str(rel_path).strip("/"))
    return bool(p.suffix)


def _as_parent_dir(rel_path: str) -> str:
    p = PurePosixPath(str(rel_path).strip("/"))
    parent = p.parent.as_posix()
    return "" if parent == "." else parent


def _build_changed_dirs(changed_paths: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in changed_paths:
        rel = str(item.get("rel_path") or "")
        if not rel:
            continue

        # IMPORTANT: cursor changes are *files*, but the delta manifest is used to seed
        # directory-based ingestion. If we cluster on the full file path, downstream tools
        # will (correctly) skip it as "not a directory".
        rel_for_cluster = _as_parent_dir(rel) if _looks_like_file_path(rel) else rel
        if not rel_for_cluster:
            continue

        cluster = _cluster_candidate(rel_for_cluster)
        # Final guard: never emit a file-looking cluster path.
        if _looks_like_file_path(cluster):
            cluster = _as_parent_dir(cluster)
        if not cluster:
            continue

        mtime = item.get("mtime")
        change_type = item.get("change_type") or "modified"

        cur = grouped.get(cluster)
        if cur is None:
            grouped[cluster] = {
                "path": cluster,
                "mtime": mtime,
                "change_type": change_type,
                "confidence": 0.95,
                "evidence": {
                    "source": "dropbox_cursor",
                    "paths": [rel],
                    "raw_change_count": 1,
                },
            }
            continue

        cur["evidence"]["paths"].append(rel)
        cur["evidence"]["raw_change_count"] = int(cur["evidence"].get("raw_change_count") or 0) + 1
        if mtime and (not cur.get("mtime") or mtime > cur["mtime"]):
            cur["mtime"] = mtime
        if change_type == "modified":
            cur["change_type"] = "modified"

    # Deterministic ordering by mtime desc then path.
    items = list(grouped.values())
    items.sort(key=lambda x: (x.get("mtime") or "", x.get("path") or ""), reverse=True)
    return items


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Cursor-based Dropbox sync: fetch only changed files, write delta manifest.")
    ap.add_argument("--config", default="state/dropbox_config.json", help="Sync config JSON")
    ap.add_argument("--state", default="state/dropbox_cursor_state.json", help="Cursor state JSON")
    ap.add_argument("--manifest", default="state/delta_manifest.json", help="Delta manifest JSON")
    ap.add_argument("--since-hours", type=float, default=24.0, help="Only include changes within this window (safety cap)")
    ap.add_argument("--max-changed-dirs", type=int, default=200, help="Cap changed directory clusters written to manifest")
    ap.add_argument("--timeout-s", type=float, default=60.0, help="Dropbox API request timeout seconds")
    ap.add_argument("--max-retries", type=int, default=5)
    ap.add_argument("--bootstrap-latest", action="store_true", help="Initialize cursor without backfilling history")
    ap.add_argument("--no-download", action="store_true", help="Cursor mode: advance cursor + write manifest without downloading files")
    ap.add_argument("--paths-only", action="store_true", help="Download only explicit paths; do not use cursor")
    ap.add_argument("--path", action="append", default=[], help="Explicit Dropbox rel path to download (repeatable)")
    ap.add_argument(
        "--path-dir",
        action="append",
        default=[],
        help="Explicit Dropbox rel directory to download (repeatable; expands to files via list_folder)",
    )
    ap.add_argument("--paths-file", default=None, help="Text file with explicit paths to download (one per line)")
    ap.add_argument(
        "--include-glob",
        action="append",
        default=[],
        help="Optional glob(s) to include when expanding --path-dir (match against rel path). Repeatable.",
    )
    ap.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="Optional glob(s) to exclude when expanding --path-dir (match against rel path). Repeatable.",
    )
    ap.add_argument(
        "--max-files",
        type=int,
        default=5000,
        help="Safety cap: max files to download in --paths-only mode (default: 5000)",
    )
    ap.add_argument(
        "--max-total-mb",
        type=float,
        default=5000.0,
        help="Safety cap: max total MB to download in --paths-only mode (default: 5000MB)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    cwd = Path.cwd().resolve()
    config_path = (cwd / args.config).resolve()
    state_path = (cwd / args.state).resolve()
    manifest_path = (cwd / args.manifest).resolve()

    cfg = _load_json(config_path)
    dropbox_root = Path(cfg["dropbox_root"]).expanduser().resolve()
    watched_roots = [str(x) for x in (cfg.get("watched_roots") or [])]
    rclone_remote = str(cfg.get("rclone_remote") or "dropbox:")
    rclone_config = _default_rclone_config_path()
    remote_name = _remote_name_from_rclone_remote(rclone_remote)

    def token_getter() -> str | None:
        env_tok = os.environ.get("DROPBOX_ACCESS_TOKEN")
        if env_tok and env_tok.strip():
            return env_tok.strip()
        return _read_rclone_access_token(remote_name, rclone_config)

    def refresh_hook() -> None:
        _trigger_rclone_token_refresh(rclone_remote)

    # --- Paths-only mode (ad-hoc downloads) ---
    if args.paths_only:
        extra_files: list[str] = []
        extra_dirs: list[str] = []

        for p in args.path:
            if p and p.strip():
                extra_files.append(_norm_rel(p))
        for d in getattr(args, "path_dir", []) or []:
            if d and str(d).strip():
                extra_dirs.append(_norm_rel(str(d)))

        if args.paths_file:
            pf = Path(args.paths_file).expanduser()
            if not pf.is_absolute():
                pf = (cwd / pf).resolve()
            if pf.exists():
                for line in pf.read_text(encoding="utf-8", errors="replace").splitlines():
                    s = line.strip()
                    if s and not s.startswith("#"):
                        extra_files.append(_norm_rel(s))

        include_globs = [g.strip() for g in (getattr(args, "include_glob", []) or []) if str(g).strip()]
        exclude_globs = [g.strip() for g in (getattr(args, "exclude_glob", []) or []) if str(g).strip()]
        max_files = int(getattr(args, "max_files", 5000) or 5000)
        max_total_bytes = int(float(getattr(args, "max_total_mb", 5000.0) or 5000.0) * 1024 * 1024)

        def _glob_match(rel: str, globs: list[str]) -> bool:
            # Use PurePosixPath.match for pathname-aware glob semantics:
            # - `*` does NOT cross path separators
            # - `**` can match across directories
            from pathlib import PurePosixPath

            rp = PurePosixPath(_norm_rel(rel))
            return any(rp.match(pat) for pat in globs)

        def _allow(rel: str) -> bool:
            r = _norm_rel(rel)
            if exclude_globs and _glob_match(r, exclude_globs):
                return False
            if include_globs:
                return _glob_match(r, include_globs)
            return True

        # Expand directories via Dropbox list_folder (recursive)
        expanded_files: list[tuple[str, int]] = []  # (rel_path, size_bytes)
        failures = 0
        total_bytes = 0

        def _list_folder_recursive(dbx_dir: str) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
            payload = {
                "path": dbx_dir,
                "recursive": True,
                "include_deleted": False,
                "include_non_downloadable_files": False,
            }
            res = _dropbox_api_json(
                endpoint="https://api.dropboxapi.com/2/files/list_folder",
                token_getter=token_getter,
                payload=payload,
                timeout_s=args.timeout_s,
                max_retries=args.max_retries,
                refresh_hook=refresh_hook,
            )
            out.extend(res.get("entries") or [])
            cursor_l = res.get("cursor")
            has_more_l = bool(res.get("has_more"))
            while has_more_l and cursor_l:
                res2 = _dropbox_api_json(
                    endpoint="https://api.dropboxapi.com/2/files/list_folder/continue",
                    token_getter=token_getter,
                    payload={"cursor": cursor_l},
                    timeout_s=args.timeout_s,
                    max_retries=args.max_retries,
                    refresh_hook=refresh_hook,
                )
                out.extend(res2.get("entries") or [])
                cursor_l = res2.get("cursor") or cursor_l
                has_more_l = bool(res2.get("has_more"))
            return [e for e in out if isinstance(e, dict)]

        total_match_files = 0
        total_match_bytes = 0

        for rel_dir in extra_dirs:
            if not rel_dir:
                continue
            dbx_dir = "/" + rel_dir
            try:
                entries = _list_folder_recursive(dbx_dir)
            except Exception:
                failures += 1
                continue

            for e in entries:
                if e.get(".tag") != "file":
                    continue
                path_display = e.get("path_display")
                if not isinstance(path_display, str) or not path_display.strip():
                    continue
                rel = _norm_rel(path_display)
                if not _allow(rel):
                    continue
                size_b = int(e.get("size") or 0)

                total_match_files += 1
                total_match_bytes += size_b

                # Enqueue subject to safety caps
                if len(expanded_files) >= max_files:
                    continue
                if total_bytes + size_b > max_total_bytes:
                    continue

                expanded_files.append((rel, size_b))
                total_bytes += size_b

        # Add explicit files (size unknown until download; still cap by count)
        for rel in extra_files:
            if not rel:
                continue
            if not _allow(rel):
                continue
            if len(expanded_files) >= max_files:
                break
            expanded_files.append((rel, 0))

        # De-dup while preserving order
        seen: set[str] = set()
        final_files: list[str] = []
        for rel, _sz in expanded_files:
            if rel in seen:
                continue
            seen.add(rel)
            final_files.append(rel)

        downloaded = 0
        for rel in final_files:
            dbx_path = "/" + rel
            local_path = dropbox_root / rel
            ok = _dropbox_download(
                token_getter=token_getter,
                refresh_hook=refresh_hook,
                dropbox_path=dbx_path,
                local_path=local_path,
                timeout_s=args.timeout_s,
                max_retries=args.max_retries,
                dry_run=args.dry_run,
            )
            if ok:
                downloaded += 1
            else:
                failures += 1

        # In dry-run mode, "downloaded" means "would download".
        would_download = downloaded if args.dry_run else None

        print("mode: paths_only")
        print(f"dropbox_root: {dropbox_root}")
        print(f"paths_files: {len(extra_files)}")
        print(f"paths_dirs: {len(extra_dirs)}")
        print(f"expanded_to_files: {len(final_files)}")
        if extra_dirs:
            print(f"matched_files_total: {total_match_files}")
            print(f"matched_total_mb: {total_match_bytes / (1024*1024):.1f}")
        if include_globs:
            print("include_glob: " + ",".join(include_globs))
        if exclude_globs:
            print("exclude_glob: " + ",".join(exclude_globs))
        print(f"max_files: {max_files}")
        print(f"max_total_mb: {max_total_bytes / (1024*1024):.1f}")
        if args.dry_run:
            print(f"would_download_files: {downloaded}")
        else:
            print(f"downloaded_files: {downloaded}")
        print(f"failures: {failures}")
        if args.dry_run:
            print("dry_run: true")
        return 0 if failures == 0 else 2

    # --- Cursor bootstrap (no listing) ---
    if args.bootstrap_latest:
        payload = {
            "path": "",
            "recursive": True,
            "include_deleted": False,
            "include_non_downloadable_files": False,
        }
        res = _dropbox_api_json(
            endpoint="https://api.dropboxapi.com/2/files/list_folder/get_latest_cursor",
            token_getter=token_getter,
            payload=payload,
            timeout_s=args.timeout_s,
            max_retries=args.max_retries,
            refresh_hook=refresh_hook,
        )
        cursor = res.get("cursor")
        if not isinstance(cursor, str) or not cursor:
            raise SystemExit(f"Bootstrap failed: no cursor returned: {res}")
        st = {
            "version": STATE_VERSION,
            "cursor": cursor,
            "initialized_at": _iso_now(),
            "last_run": None,
            "notes": "Initialized with get_latest_cursor (no backfill).",
        }
        if not args.dry_run:
            _write_json(state_path, st)
        print("mode: bootstrap_latest")
        print("cursor_initialized: True")
        return 0

    # --- Normal cursor continue ---
    if not state_path.exists():
        raise SystemExit(f"Cursor state not found: {state_path}. Run with --bootstrap-latest first.")
    st = _load_json(state_path)
    cursor = st.get("cursor")
    if not isinstance(cursor, str) or not cursor.strip():
        raise SystemExit(f"Invalid cursor state: {state_path}")

    cutoff = dt.datetime.now().astimezone() - dt.timedelta(hours=float(args.since_hours))

    changed_entries = 0  # raw delta events

    # De-dupe by rel_path: cursor can emit multiple events for the same file.
    # We keep the latest mtime we see (server_modified/client_modified) for each path.
    latest_by_rel: dict[str, dict[str, Any]] = {}

    downloaded_files = 0
    deleted_local = 0

    has_more = True
    while has_more:
        res = _dropbox_api_json(
            endpoint="https://api.dropboxapi.com/2/files/list_folder/continue",
            token_getter=token_getter,
            payload={"cursor": cursor},
            timeout_s=args.timeout_s,
            max_retries=args.max_retries,
            refresh_hook=refresh_hook,
        )
        cursor = res.get("cursor") or cursor
        has_more = bool(res.get("has_more"))
        entries = res.get("entries") or []
        if not isinstance(entries, list):
            entries = []

        for e in entries:
            if not isinstance(e, dict):
                continue
            changed_entries += 1
            tag = e.get(".tag")
            if tag == "deleted":
                # We do not delete local cache; we only note it.
                deleted_local += 1
                continue
            if tag != "file":
                continue

            path_display = e.get("path_display")
            if not isinstance(path_display, str) or not path_display.strip():
                continue
            rel = _norm_rel(path_display)
            if not _path_in_scope(rel, watched_roots):
                continue

            mtime_raw = e.get("server_modified") or e.get("client_modified")
            mtime_dt = _parse_iso(mtime_raw) if isinstance(mtime_raw, str) else None
            if mtime_dt and mtime_dt < cutoff:
                continue

            local_path = dropbox_root / rel
            existed = local_path.exists()

            rec = {
                "rel_path": rel,
                "mtime": mtime_raw,
                "change_type": "modified" if existed else "new",
            }

            if args.no_download and not args.dry_run:
                ok = True
            else:
                # Download file
                ok = _dropbox_download(
                    token_getter=token_getter,
                    refresh_hook=refresh_hook,
                    dropbox_path="/" + rel,
                    local_path=local_path,
                    timeout_s=args.timeout_s,
                    max_retries=args.max_retries,
                    dry_run=args.dry_run,
                )

            if ok:
                if not (args.no_download and not args.dry_run):
                    downloaded_files += 1

                prev = latest_by_rel.get(rel)
                if prev is None:
                    latest_by_rel[rel] = rec
                else:
                    # Prefer later mtime when parseable; otherwise last-write-wins.
                    prev_dt = _parse_iso(prev.get("mtime") or "") if isinstance(prev.get("mtime"), str) else None
                    if mtime_dt and (prev_dt is None or mtime_dt >= prev_dt):
                        latest_by_rel[rel] = rec
                    elif prev_dt is None:
                        latest_by_rel[rel] = rec

        # Safety: do not spin forever on a bad cursor.
        if changed_entries > 200_000:
            raise SystemExit("Refusing to process >200k cursor entries in one run; investigate cursor state.")

    selected_paths: list[dict[str, Any]] = list(latest_by_rel.values())

    changed_dirs = _build_changed_dirs(selected_paths)
    if args.max_changed_dirs and args.max_changed_dirs > 0:
        changed_dirs = changed_dirs[: args.max_changed_dirs]

    manifest = {
        "schema_version": MANIFEST_VERSION,
        "generated_at": _iso_now(),
        "source": "dropbox_cursor",
        "dropbox_root": dropbox_root.as_posix(),
        "watched_roots": watched_roots,
        "since_hours": float(args.since_hours),
        "max_changed_dirs": int(args.max_changed_dirs),
        "changed_directories": changed_dirs,
        "stats": {
            "cursor_entries": changed_entries,
            "unique_paths": len(selected_paths),
            "downloaded_files": downloaded_files,
            "deleted_local": deleted_local,
            "selected_changed_dirs": len(changed_dirs),
        },
    }

    st["version"] = STATE_VERSION
    st["cursor"] = cursor
    st["last_run"] = _iso_now()
    st["since_hours"] = float(args.since_hours)
    st["stats"] = manifest["stats"]

    if not args.dry_run:
        _write_json(state_path, st)
        _write_json(manifest_path, manifest)

    print("source: dropbox_cursor")
    print(f"dropbox_root: {dropbox_root}")
    print(f"cursor_entries: {changed_entries}")
    print(f"unique_paths: {len(selected_paths)}")
    print(f"downloaded_files: {downloaded_files}")
    print(f"changed_directories: {len(changed_dirs)}")
    print(f"manifest: {manifest_path}")
    print(f"state: {state_path}")
    if args.dry_run:
        print("dry_run: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

