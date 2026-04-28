#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


STATE_VERSION = 1


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


def _sha1_hex(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


def _parse_digest_id(content: str) -> str:
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("- digest_id:"):
            # "- digest_id: `abc...`"
            a = s.find("`")
            b = s.rfind("`")
            if 0 <= a < b:
                return s[a + 1 : b].strip()
    return _sha1_hex(content)[:12]


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


def _run_openclaw_send(*, openclaw_bin: str, target: str, message: str, dry_run: bool) -> dict[str, Any]:
    cmd = [
        openclaw_bin,
        "message",
        "send",
        "--channel",
        "slack",
        "--target",
        target,
        "--message",
        message,
        "--json",
    ]
    if dry_run:
        cmd.append("--dry-run")

    if dry_run:
        return {
            "command": cmd,
            "ran": False,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "json": None,
        }

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


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Post Slack clarifications digest via OpenClaw CLI (no Slack API).")
    ap.add_argument("--digest", default="out/slack_clarifications_digest.md", help="Digest markdown to post")
    ap.add_argument("--target", default=None, help="Slack channel id to post into (e.g., C0123...)")
    ap.add_argument("--state", default="state/slack_state.json", help="State JSON path")
    ap.add_argument("--openclaw-bin", default="openclaw", help="OpenClaw CLI binary name/path (default: openclaw)")
    ap.add_argument("--config", default=None, help="OpenClaw config path (default: OPENCLAW_CONFIG_PATH or ~/.openclaw/openclaw.json)")
    ap.add_argument("--force", action="store_true", help="Post even if digest_id already posted")
    ap.add_argument("--dry-run", action="store_true", help="Do not send; record what would happen")
    args = ap.parse_args(argv)

    cwd = Path.cwd().resolve()
    digest_path = (cwd / args.digest).resolve()
    state_path = (cwd / args.state).resolve()
    config_path = Path(args.config).expanduser() if args.config else _default_openclaw_config_path()

    if not digest_path.exists():
        raise SystemExit(f"Digest not found: {digest_path}")
    content = digest_path.read_text(encoding="utf-8", errors="replace")
    digest_id = _parse_digest_id(content)

    if state_path.exists():
        state = _load_json(state_path)
        if not isinstance(state, dict):
            state = {}
    else:
        state = {}

    now = _iso_now()
    state.setdefault("version", STATE_VERSION)
    state.setdefault("created_at", now)
    state.setdefault("last_post", {"digest_id": None, "posted_at": None, "target": None, "message_id": None})
    state.setdefault("last_error", None)

    last_post = state.get("last_post")
    if not isinstance(last_post, dict):
        last_post = {"digest_id": None, "posted_at": None, "target": None, "message_id": None}
        state["last_post"] = last_post

    if not args.force and last_post.get("digest_id") == digest_id:
        print(f"skip: digest_id already posted: {digest_id}")
        return 0

    target = args.target or os.environ.get("OPENCLAW_SLACK_TARGET") or _detect_slack_target_from_config(config_path)
    if not target:
        raise SystemExit("Missing Slack --target (or set OPENCLAW_SLACK_TARGET, or allowlist a channel in openclaw.json).")

    openclaw_bin = args.openclaw_bin
    if not shutil.which(openclaw_bin) and not args.dry_run:
        raise SystemExit(f"OpenClaw CLI not found in PATH: {openclaw_bin!r}")

    result = _run_openclaw_send(openclaw_bin=openclaw_bin, target=target, message=content, dry_run=args.dry_run)
    ok = (result.get("returncode") == 0) or bool(args.dry_run)

    message_id = None
    payload = result.get("json")
    if isinstance(payload, dict):
        for k in ("messageId", "id", "ts"):
            v = payload.get(k)
            if isinstance(v, str) and v:
                message_id = v
                break

    if ok:
        last_post["digest_id"] = digest_id
        last_post["posted_at"] = now
        last_post["target"] = target
        last_post["message_id"] = message_id
        state["last_error"] = None
    else:
        state["last_error"] = {"at": now, "action": "post_digest", "digest_id": digest_id, "returncode": result.get("returncode")}

    wrote_state = _write_text_if_changed(state_path, _dump_json(state), dry_run=args.dry_run)

    print(f"digest_id: {digest_id}")
    print(f"target: {target}")
    print(f"ok: {ok}")
    print(f"message_id: {message_id}")
    print(f"state_written: {wrote_state} -> {state_path}")
    if args.dry_run:
        print("openclaw_command:", " ".join(result.get("command") or []))
    if not ok:
        print("stderr:", (result.get("stderr") or "")[-4000:])
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
