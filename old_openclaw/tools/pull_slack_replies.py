#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


STATE_VERSION = 1

QID_RE = re.compile(r"\b(q_[0-9a-fA-F]{8,64})\b")


def _iso_now() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def _write_text_if_changed(path: Path, content: str, *, dry_run: bool) -> bool:
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace")
        if existing == content:
            return False
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _default_openclaw_config_path() -> Path:
    return Path(os.environ.get("OPENCLAW_CONFIG_PATH") or (Path.home() / ".openclaw" / "openclaw.json")).expanduser()


def _detect_slack_target_from_config(config_path: Path) -> str | None:
    if not config_path.exists():
        return None
    try:
        cfg = _load_json(config_path)
    except Exception:
        return None
    slack = ((cfg.get("channels") or {}).get("slack") or {}) if isinstance(cfg, dict) else {}
    channels = slack.get("channels") if isinstance(slack.get("channels"), dict) else {}
    for chan_id, rule in channels.items():
        if isinstance(rule, dict) and rule.get("allow") is True and isinstance(chan_id, str) and chan_id:
            return chan_id
    return None


def _run_openclaw_read(
    *,
    openclaw_bin: str,
    target: str,
    limit: int,
    after: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    cmd = [
        openclaw_bin,
        "message",
        "read",
        "--channel",
        "slack",
        "--target",
        target,
        "--limit",
        str(limit),
        "--json",
    ]
    if after:
        cmd.extend(["--after", after])
    if dry_run:
        cmd.append("--dry-run")

    if dry_run:
        return {"command": cmd, "ran": False, "returncode": 0, "stdout": "", "stderr": "", "json": []}

    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    parsed: Any | None = None
    if out:
        try:
            parsed = json.loads(out)
        except json.JSONDecodeError:
            parsed = None
    return {
        "command": cmd,
        "ran": True,
        "returncode": proc.returncode,
        "stdout": out[-4000:],
        "stderr": err[-4000:],
        "json": parsed,
    }


def _iter_messages(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        # common wrappers
        for k in ("messages", "items", "data"):
            v = payload.get(k)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        # single message?
        return [payload]
    return []


def _msg_id(msg: dict[str, Any]) -> str | None:
    for k in ("id", "messageId", "ts", "timestamp"):
        v = msg.get(k)
        if isinstance(v, str) and v:
            return v
        if isinstance(v, (int, float)):
            return str(v)
    return None


def _msg_text(msg: dict[str, Any]) -> str:
    for k in ("text", "message", "body", "content"):
        v = msg.get(k)
        if isinstance(v, str) and v:
            return v
    # nested forms
    v = msg.get("text")
    if isinstance(v, dict):
        inner = v.get("text")
        if isinstance(inner, str):
            return inner
    return ""


def _msg_author(msg: dict[str, Any]) -> str:
    for k in ("authorId", "userId", "from"):
        v = msg.get(k)
        if isinstance(v, str) and v:
            return v
    author = msg.get("author")
    if isinstance(author, dict):
        for k in ("id", "userId", "slack_user_id"):
            v = author.get(k)
            if isinstance(v, str) and v:
                return v
        name = author.get("name")
        if isinstance(name, str) and name:
            return name
    return "unknown"


def _looks_like_resolution(text: str) -> bool:
    s = text.strip().lower()
    if not s:
        return False
    if s.startswith("resolve ") or s.startswith("resolved "):
        return True
    if " resolved" in s or "resolve" in s:
        return True
    if "answer:" in s:
        return True
    if re.match(r"^q_[0-9a-f]{8,64}\\s*[:\\-]", s):
        return True
    return False


def _run_apply_clarification(
    *,
    workspace_root: Path,
    question_id: str,
    resolution: str,
    resolver: str,
    dry_run: bool,
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str((workspace_root / "tools" / "apply_clarification.py").resolve()),
        "--question-id",
        question_id,
        "--resolution",
        resolution,
        "--resolver",
        resolver,
    ]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=workspace_root)
    return {"command": cmd, "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Pull Slack replies via OpenClaw CLI and resolve q_<id> items (no Slack API).")
    ap.add_argument("--target", default=None, help="Slack channel id to read from")
    ap.add_argument("--state", default="state/slack_state.json", help="State JSON path")
    ap.add_argument("--openclaw-bin", default="openclaw", help="OpenClaw CLI binary name/path (default: openclaw)")
    ap.add_argument("--config", default=None, help="OpenClaw config path (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json)")
    ap.add_argument("--limit", type=int, default=50, help="Max messages to read per run (default: 50)")
    ap.add_argument("--dry-run", action="store_true", help="Do not modify indices/state; print actions")
    ap.add_argument("--input-json", default=None, help="Offline mode: path to JSON payload to process instead of calling OpenClaw CLI")
    args = ap.parse_args(argv)

    workspace_root = Path.cwd().resolve()
    state_path = (workspace_root / args.state).resolve()
    config_path = Path(args.config).expanduser() if args.config else _default_openclaw_config_path()

    now = _iso_now()

    if state_path.exists():
        state = _load_json(state_path)
        if not isinstance(state, dict):
            state = {}
    else:
        state = {}

    state.setdefault("version", STATE_VERSION)
    state.setdefault("created_at", now)
    state.setdefault("last_post", {})
    state.setdefault("last_read", {"target": None, "after": None, "processed_message_ids": []})
    state.setdefault("last_error", None)

    last_read = state.get("last_read")
    if not isinstance(last_read, dict):
        last_read = {"target": None, "after": None, "processed_message_ids": []}
        state["last_read"] = last_read

    target = args.target or os.environ.get("OPENCLAW_SLACK_TARGET") or _detect_slack_target_from_config(config_path) or last_read.get("target")
    if not target:
        raise SystemExit("Missing Slack --target (or set OPENCLAW_SLACK_TARGET, or allowlist a channel in openclaw.json).")

    after = last_read.get("after") if isinstance(last_read.get("after"), str) else None
    processed = last_read.get("processed_message_ids") if isinstance(last_read.get("processed_message_ids"), list) else []
    processed_set = {str(x) for x in processed if str(x)}

    payload: Any | None = None
    read_result: dict[str, Any] | None = None

    if args.input_json:
        payload = _load_json(Path(args.input_json).expanduser())
    else:
        openclaw_bin = args.openclaw_bin
        if not shutil.which(openclaw_bin) and not args.dry_run:
            raise SystemExit(f"OpenClaw CLI not found in PATH: {openclaw_bin!r}")
        read_result = _run_openclaw_read(
            openclaw_bin=openclaw_bin,
            target=target,
            limit=max(1, args.limit),
            after=after,
            dry_run=args.dry_run,
        )
        if read_result.get("returncode") not in (0, None) and not args.dry_run:
            state["last_error"] = {"at": now, "action": "read_messages", "returncode": read_result.get("returncode")}
            _write_text_if_changed(state_path, _dump_json(state), dry_run=args.dry_run)
            raise SystemExit("openclaw message read failed")
        payload = read_result.get("json")

    messages = _iter_messages(payload)
    applied = 0
    skipped = 0
    max_seen_id: str | None = after

    for msg in messages:
        mid = _msg_id(msg)
        if mid and mid in processed_set:
            skipped += 1
            continue
        text = _msg_text(msg)
        if not text:
            skipped += 1
            continue
        qids = [m.group(1) for m in QID_RE.finditer(text)]
        if not qids:
            skipped += 1
            continue
        if not _looks_like_resolution(text):
            skipped += 1
            continue

        resolver = "slack:" + _msg_author(msg)
        # Apply once per message (first qid); multi-qid messages are rare and ambiguous.
        qid = qids[0]
        res = _run_apply_clarification(
            workspace_root=workspace_root,
            question_id=qid,
            resolution=text.strip(),
            resolver=resolver,
            dry_run=args.dry_run,
        )
        if res.get("returncode") == 0:
            applied += 1
        else:
            state["last_error"] = {"at": now, "action": "apply_clarification", "question_id": qid, "returncode": res.get("returncode")}

        if mid:
            processed_set.add(mid)
        if mid and (max_seen_id is None or str(mid) > str(max_seen_id)):
            max_seen_id = str(mid)

    # Update state
    last_read["target"] = target
    last_read["after"] = max_seen_id or after
    last_read["processed_message_ids"] = list(sorted(processed_set))[-2000:]

    wrote_state = _write_text_if_changed(state_path, _dump_json(state), dry_run=args.dry_run)

    print(f"target: {target}")
    print(f"after: {after}")
    print(f"messages_seen: {len(messages)}")
    print(f"applied: {applied}")
    print(f"skipped: {skipped}")
    print(f"state_written: {wrote_state} -> {state_path}")
    if args.dry_run and read_result is not None:
        print("openclaw_command:", " ".join(read_result.get("command") or []))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
