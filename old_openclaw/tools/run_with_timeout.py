#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Run a command with a hard timeout in seconds.")
    ap.add_argument("--seconds", type=int, required=True, help="Timeout in seconds")
    ap.add_argument("command", nargs=argparse.REMAINDER, help="Command to execute")
    args = ap.parse_args(argv)

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        raise SystemExit("Missing command. Usage: run_with_timeout.py --seconds 120 -- <cmd> ...")

    try:
        proc = subprocess.run(cmd, timeout=max(1, int(args.seconds)))
        return int(proc.returncode)
    except subprocess.TimeoutExpired:
        print(f"timeout: exceeded {args.seconds}s", file=sys.stderr)
        return 124


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
