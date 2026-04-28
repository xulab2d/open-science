#!/usr/bin/env python3
"""Watch a PPTX (or any file) and notify a Slack DM target when it changes.

Designed for OpenClaw workspace use.

Usage:
  python3 tools/watch_ppt_notify.py \
    --path out/ppt/running/.../file.pptx \
    --channel slack \
    --target UXXXXXXXX \
    --state state/watch_ppt_notify_state.json \
    --poll-seconds 60 \
    --cooldown-seconds 900 \
    --message "..."

Notes:
- Uses `openclaw message send ...` for delivery (matches workspace convention).
- State file tracks last mtime + last notification time.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class State:
    last_mtime: float = 0.0
    last_notified_ts: float = 0.0


def load_state(path: str) -> State:
    try:
        with open(path, "r") as f:
            d = json.load(f)
        return State(
            last_mtime=float(d.get("last_mtime", 0.0)),
            last_notified_ts=float(d.get("last_notified_ts", 0.0)),
        )
    except FileNotFoundError:
        return State()
    except Exception as e:
        print(f"[watch_ppt_notify] WARNING: failed to load state {path}: {e}", file=sys.stderr)
        return State()


def save_state(path: str, st: State) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"last_mtime": st.last_mtime, "last_notified_ts": st.last_notified_ts}, f)
    os.replace(tmp, path)


def send_message(channel: str, target: str, message: str) -> None:
    # Workspace convention uses OpenClaw CLI for Slack posts in automation.
    cmd = [
        "openclaw",
        "message",
        "send",
        "--channel",
        channel,
        "--target",
        target,
        "--message",
        message,
        "--json",
    ]
    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--channel", default="slack")
    ap.add_argument("--target", required=True, help="Slack user id (e.g. U09...) or channel id")
    ap.add_argument("--state", required=True)
    ap.add_argument("--poll-seconds", type=float, default=60.0)
    ap.add_argument("--cooldown-seconds", type=float, default=15 * 60.0)
    ap.add_argument("--message", required=True)
    args = ap.parse_args()

    st = load_state(args.state)

    # Initialize last_mtime if file exists.
    try:
        st.last_mtime = max(st.last_mtime, os.path.getmtime(args.path))
        save_state(args.state, st)
    except FileNotFoundError:
        pass

    while True:
        try:
            mtime = os.path.getmtime(args.path)
        except FileNotFoundError:
            time.sleep(args.poll_seconds)
            continue
        except Exception:
            time.sleep(args.poll_seconds)
            continue

        now = time.time()
        changed = mtime > st.last_mtime + 1e-6
        cooled = (now - st.last_notified_ts) >= args.cooldown_seconds

        if changed and cooled:
            send_message(args.channel, args.target, args.message)
            st.last_notified_ts = now
            st.last_mtime = mtime
            save_state(args.state, st)
        elif changed:
            # Update mtime even if we're in cooldown, so we notify on *next* new change.
            st.last_mtime = mtime
            save_state(args.state, st)

        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
