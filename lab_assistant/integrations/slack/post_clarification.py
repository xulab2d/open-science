#!/usr/bin/env python3
"""Post a targeted OpenScience clarification question to Slack."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from transcript_log import append_transcript_entry


INTEGRATION_DIR = Path(__file__).resolve().parent
ENV_PATH = INTEGRATION_DIR / ".env.local"
ROUTING_PATH = INTEGRATION_DIR / "routing.template.json"


def load_routing() -> dict:
    with ROUTING_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_local_env() -> None:
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def slack_api(method: str, token: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(f"Slack API request failed: {exc}") from exc
    if not data.get("ok"):
        raise SystemExit(f"Slack API error from {method}: {data.get('error', 'unknown_error')}")
    return data


def resolve_target(routing: dict, person: str | None, channel: str | None) -> tuple[str, str]:
    if channel:
        if channel == "open-science":
            return str(routing["fallback_channel"]), "#open-science"
        return channel, channel

    if not person:
        raise SystemExit("Provide --person or --channel.")

    people = routing.get("people", {})
    record = people.get(person)
    if not record:
        known = ", ".join(sorted(people))
        raise SystemExit(f"Unknown person key: {person}. Known keys: {known}")

    user_id = str(record.get("slack_user_id", "")).strip()
    if not user_id:
        raise SystemExit(f"No Slack user id configured for {person}.")
    return user_id, str(record.get("display_name", person))


def main() -> int:
    parser = argparse.ArgumentParser(description="Post a targeted clarification request to Slack.")
    parser.add_argument("--person", help="Person key from routing.template.json, e.g. christiano_wang_beach")
    parser.add_argument("--channel", help='Channel id, or "open-science" for the configured fallback channel')
    parser.add_argument("--message", required=True, help="Plain-text clarification question to send")
    parser.add_argument("--thread-ts", help="Optional Slack thread timestamp for channel replies")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved target without posting")
    args = parser.parse_args()

    load_local_env()
    routing = load_routing()
    target, label = resolve_target(routing, args.person, args.channel)

    if args.dry_run:
        print(json.dumps({"target": target, "label": label, "message": args.message}, indent=2))
        return 0

    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing SLACK_BOT_TOKEN in environment or .env.local.")

    channel_id = target
    if args.person:
        opened = slack_api("conversations.open", token, {"users": target})
        channel_id = opened["channel"]["id"]

    payload = {
        "channel": channel_id,
        "text": args.message,
    }
    if args.thread_ts and not args.person:
        payload["thread_ts"] = args.thread_ts

    try:
        resp = slack_api("chat.postMessage", token, payload)
    except SystemExit as exc:
        append_transcript_entry(
            {
                "source": "post_clarification",
                "direction": "error",
                "route": "dm" if args.person else "channel",
                "target": label,
                "channel_id": channel_id,
                "thread_ts": args.thread_ts if not args.person else None,
                "slack_ts": None,
                "text": args.message,
                "error": str(exc),
            }
        )
        raise

    append_transcript_entry(
        {
            "source": "post_clarification",
            "direction": "outbound",
            "route": "dm" if args.person else "channel",
            "target": label,
            "channel_id": resp["channel"],
            "thread_ts": args.thread_ts if not args.person else None,
            "slack_ts": resp["ts"],
            "text": args.message,
        }
    )
    print(json.dumps({"channel": resp["channel"], "ts": resp["ts"], "target": label}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
