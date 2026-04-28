"""
monitor — real-time monitoring of active experimental runs.

Triggered when someone announces an experiment is running (via Slack/OpenClaw).
Polls the local Dropbox cache for new data files, analyzes them as they arrive,
and feeds condensed summaries to the LLM so it can decide what to alert about.

Entry points (called by the OpenClaw agent):
  tools/start_monitor_run.py  — register a new active run
  tools/poll_monitor.py       — poll once; print LLM-ready summary of anything new
  tools/replay_monitor.py     — replay a past run for evaluation/testing
"""
