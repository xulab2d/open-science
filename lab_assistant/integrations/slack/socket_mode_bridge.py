#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from transcript_log import append_transcript_entry


ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_DIR = Path(__file__).resolve().parent
ENV_PATH = INTEGRATION_DIR / ".env.local"
ROUTING_PATH = INTEGRATION_DIR / "routing.template.json"
CONTEXT_FILES_PATH = INTEGRATION_DIR.parent / "context_files.json"
CODEX_TIMEOUT_S = int(os.environ.get("SLACK_CODEX_TIMEOUT_S", "600"))
THREAD_HISTORY_LIMIT = int(os.environ.get("SLACK_THREAD_HISTORY_LIMIT", "8"))
DM_HISTORY_LIMIT = int(os.environ.get("SLACK_DM_HISTORY_LIMIT", "6"))
STATUS_TEXT = os.environ.get("SLACK_WORKING_TEXT", "Working on it.")


@dataclass
class SlackRouting:
    project_data_root: str
    summary_root: str
    fallback_channel: str
    raw: dict[str, Any]


@dataclass
class ContextFileSpec:
    path: Path
    label: str
    max_chars: int


def load_env() -> None:
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_routing() -> SlackRouting:
    with ROUTING_PATH.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return SlackRouting(
        project_data_root=str(raw.get("project_data_root", "")),
        summary_root=str(raw.get("summary_root", "")),
        fallback_channel=str(raw.get("fallback_channel", "")),
        raw=raw,
    )


def load_context_specs() -> tuple[list[ContextFileSpec], int]:
    with CONTEXT_FILES_PATH.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)

    specs: list[ContextFileSpec] = []
    for item in raw.get("always_include", []):
        specs.append(
            ContextFileSpec(
                path=ROOT / str(item["path"]),
                label=str(item["label"]),
                max_chars=int(item.get("max_chars", 1600)),
            )
        )
    max_total_chars = int(raw.get("max_total_chars", 10000))
    return specs, max_total_chars


def sanitize_text(value: str | None) -> str:
    if not value:
        return ""
    return value.replace("\r", "").strip()


def clip_text(value: str, max_chars: int) -> str:
    text = sanitize_text(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 15].rstrip() + "\n[truncated]"


def render_context_bundle() -> str:
    specs, max_total_chars = load_context_specs()
    sections: list[str] = []
    used = 0

    for spec in specs:
        if not spec.path.exists():
            continue
        text = clip_text(spec.path.read_text(encoding="utf-8", errors="replace"), spec.max_chars)
        section = f"[{spec.label} | {spec.path.relative_to(ROOT)}]\n{text}"
        projected = used + len(section) + 2
        if projected > max_total_chars:
            break
        sections.append(section)
        used = projected

    return "\n\n".join(sections) if sections else "(no workspace context bundle loaded)"


def should_ignore_message(event: dict[str, Any], bot_user_id: str) -> bool:
    if event.get("subtype"):
        return True
    if event.get("bot_id"):
        return True
    if event.get("user") == bot_user_id:
        return True
    if not sanitize_text(event.get("text")):
        return True
    return False


def should_monitor(event: dict[str, Any], routing: SlackRouting) -> bool:
    channel_type = event.get("channel_type")
    if channel_type == "im":
        return True
    if event.get("channel") == routing.fallback_channel:
        return True
    return False


def fetch_context_messages(client: Any, event: dict[str, Any]) -> list[dict[str, str]]:
    channel = event["channel"]
    thread_ts = event.get("thread_ts") or event.get("ts")
    channel_type = event.get("channel_type")

    if event.get("thread_ts"):
        resp = client.conversations_replies(channel=channel, ts=thread_ts, limit=THREAD_HISTORY_LIMIT)
        messages = resp.get("messages", [])[-THREAD_HISTORY_LIMIT:]
    elif channel_type == "im":
        resp = client.conversations_history(channel=channel, limit=DM_HISTORY_LIMIT)
        history = list(reversed(resp.get("messages", [])[-DM_HISTORY_LIMIT:]))
        messages = history
    else:
        messages = [event]

    out: list[dict[str, str]] = []
    for msg in messages:
        text = sanitize_text(msg.get("text"))
        if not text:
            continue
        role = "assistant" if msg.get("bot_id") else "user"
        sender = msg.get("user") or msg.get("bot_id") or "unknown"
        out.append({"role": role, "sender": sender, "text": text})
    return out


def log_inbound_message(event: dict[str, Any]) -> None:
    append_transcript_entry(
        {
            "source": "socket_mode_bridge",
            "direction": "inbound",
            "channel_id": event.get("channel"),
            "channel_type": event.get("channel_type"),
            "thread_ts": event.get("thread_ts"),
            "slack_ts": event.get("ts"),
            "sender_id": event.get("user"),
            "text": sanitize_text(event.get("text")),
            "subtype": event.get("subtype"),
        }
    )


def log_outbound_message(
    *,
    event: dict[str, Any],
    text: str,
    slack_ts: str | None,
    route: str,
) -> None:
    append_transcript_entry(
        {
            "source": "socket_mode_bridge",
            "direction": "outbound",
            "route": route,
            "channel_id": event.get("channel"),
            "channel_type": event.get("channel_type"),
            "thread_ts": event.get("thread_ts") or event.get("ts"),
            "slack_ts": slack_ts,
            "text": sanitize_text(text),
        }
    )


def log_bridge_error(event: dict[str, Any], error_text: str) -> None:
    append_transcript_entry(
        {
            "source": "socket_mode_bridge",
            "direction": "error",
            "channel_id": event.get("channel"),
            "channel_type": event.get("channel_type"),
            "thread_ts": event.get("thread_ts") or event.get("ts"),
            "slack_ts": event.get("ts"),
            "text": sanitize_text(error_text),
        }
    )


def build_prompt(
    *,
    event: dict[str, Any],
    context_messages: list[dict[str, str]],
    routing: SlackRouting,
) -> str:
    context_bundle = render_context_bundle()
    thread_lines = []
    for item in context_messages:
        thread_lines.append(f"{item['role']} ({item['sender']}): {item['text']}")
    thread_block = "\n".join(thread_lines) if thread_lines else "(no prior context)"

    thread_ts = event.get("thread_ts") or event.get("ts")
    channel = event.get("channel")
    channel_type = event.get("channel_type")
    return textwrap.dedent(
        f"""
        You are replying through the Xu Lab Slack bridge.

        Use the workspace under `lab_assistant/` as the primary source of directives, preferences, routing, and project context.
        The following context bundle is always in scope and should outrank generic assistant habits.

        Slack response requirements:
        - Output plain text suitable for Slack.
        - Be concise, direct, and science-oriented.
        - Do not mention hidden bridge mechanics, env vars, or internal plumbing.
        - If the answer is uncertain, say what is known and what remains uncertain.
        - If the message is in a shared channel, prefer replying as a thread response rather than broad channel chatter.
        - If a lab member answers a prior scientific clarification or corrects project context, update the smallest relevant durable file under `lab_assistant/` before replying.
        - For project-owner answers, preserve the scientific content in `knowledge/projects/`, `knowledge/syntheses/`, `context/`, or `memory/project_pulse.md` as appropriate.

        Confirmed workspace roots:
        - project data root: {routing.project_data_root}
        - assistant summary root: {routing.summary_root}

        Always-loaded workspace context:
        {context_bundle}

        Slack event context:
        - channel_id: {channel}
        - channel_type: {channel_type}
        - thread_ts: {thread_ts}

        Recent conversation context:
        {thread_block}

        Latest inbound message:
        {sanitize_text(event.get("text"))}

        Respond only with the message body to send back to Slack.
        """
    ).strip()


def run_codex(prompt: str) -> str:
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as fh:
        output_path = Path(fh.name)

    cmd = [
        "codex",
        "exec",
        "--ephemeral",
        "--color",
        "never",
        "-C",
        str(ROOT),
        "-o",
        str(output_path),
        prompt,
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=CODEX_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return "I hit the local Codex timeout before producing a response."

    try:
        if output_path.exists():
            content = output_path.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                return content
    finally:
        output_path.unlink(missing_ok=True)

    stderr = sanitize_text(proc.stderr)
    stdout = sanitize_text(proc.stdout)
    diagnostic = stderr or stdout or f"codex exited with status {proc.returncode}"
    return f"I could not complete the Codex handoff.\n\nDiagnostic: {diagnostic[:1200]}"


def post_reply(client: Any, event: dict[str, Any], text: str) -> None:
    channel = event["channel"]
    thread_ts = event.get("thread_ts")
    if event.get("channel_type") != "im":
        thread_ts = thread_ts or event.get("ts")

    payload: dict[str, Any] = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    client.chat_postMessage(**payload)


def post_status_message(client: Any, event: dict[str, Any]) -> dict[str, str]:
    channel = event["channel"]
    thread_ts = event.get("thread_ts")
    if event.get("channel_type") != "im":
        thread_ts = thread_ts or event.get("ts")

    payload: dict[str, Any] = {"channel": channel, "text": STATUS_TEXT}
    if thread_ts:
        payload["thread_ts"] = thread_ts

    resp = client.chat_postMessage(**payload)
    return {"channel": resp["channel"], "ts": resp["ts"]}


def update_status_message(client: Any, status_ref: dict[str, str], text: str) -> None:
    client.chat_update(channel=status_ref["channel"], ts=status_ref["ts"], text=text)


def process_message(client: Any, event: dict[str, Any], routing: SlackRouting) -> None:
    log_inbound_message(event)
    status_ref = post_status_message(client, event)
    context_messages = fetch_context_messages(client, event)
    prompt = build_prompt(event=event, context_messages=context_messages, routing=routing)
    reply = run_codex(prompt)
    update_status_message(client, status_ref, reply)
    log_outbound_message(
        event=event,
        text=reply,
        slack_ts=status_ref.get("ts"),
        route="dm" if event.get("channel_type") == "im" else "open-science-thread",
    )


def main() -> None:
    load_env()
    app_token = require_env("SLACK_APP_TOKEN")
    bot_token = require_env("SLACK_BOT_TOKEN")
    require_env("SLACK_SIGNING_SECRET")
    routing = load_routing()

    app = App(token=bot_token)
    bot_user_id = app.client.auth_test()["user_id"]

    @app.event("message")
    def handle_message_events(body: dict[str, Any], event: dict[str, Any], logger: Any, ack: Any) -> None:
        ack()

        if should_ignore_message(event, bot_user_id):
            return
        if not should_monitor(event, routing):
            return

        def worker() -> None:
            try:
                process_message(app.client, event, routing)
            except Exception as exc:  # pragma: no cover
                logger.exception("Slack bridge failure")
                fallback = f"I hit an internal bridge error before I could finish: {exc}"
                log_bridge_error(event, fallback)
                try:
                    status_ref = post_status_message(app.client, event)
                    update_status_message(app.client, status_ref, fallback)
                    log_outbound_message(
                        event=event,
                        text=fallback,
                        slack_ts=status_ref.get("ts"),
                        route="dm" if event.get("channel_type") == "im" else "open-science-thread",
                    )
                except Exception:
                    logger.exception("Failed to post Slack bridge error")

        threading.Thread(target=worker, daemon=True).start()

    handler = SocketModeHandler(app, app_token)
    handler.start()


if __name__ == "__main__":
    main()
