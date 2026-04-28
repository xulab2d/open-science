# Slack Integration Staging Area

Purpose:
- Keep Slack-specific config and adapter code separate from the core assistant workspace.

What belongs here:
- Slack app credentials and environment-variable documentation
- user/channel routing config
- event adapter or webhook handler
- formatting helpers

Credential layout:
- checked-in template: `.env.example`
- local untracked secrets: `.env.local`
- routing config: `routing.template.json`

Current implementation:
- `socket_mode_bridge.py`: minimal Socket Mode bridge
- `context_files.json`: fixed list of workspace files always injected into Slack Codex prompts
- `run_bridge.sh`: local launcher using the integration virtualenv
- `post_clarification.py`: deterministic helper for OpenScience/Codex to send targeted clarification questions to project owners or `#open-science`
- `transcript_log.py`: append-only Slack transcript logger for inbound monitored messages and outbound replies/clarifications
- `.venv/`: local Python environment with Slack dependencies
- `logs/`: append-only JSONL transcript files; these are the transport-layer ground source of truth and should not be edited by hand

Response behavior:
- Native typing indicators are not available in this modern Events API / Socket Mode path.
- The bridge posts a short placeholder message immediately, then edits that message into the final Codex response.
- DMs get a direct placeholder; `#open-science` gets a threaded placeholder/reply.
- Replies in DMs and `#open-science` are routed back through Codex with recent conversation context.
- If a reply resolves a scientific ambiguity, Codex should update durable project/context knowledge before responding.
- Inbound monitored Slack messages and outbound bridge/helper messages are logged in full under `logs/slack_transcript_YYYY-MM.jsonl`.
- Treat the transcript log as raw source of truth; promote durable scientific content into canonical project/context files so it influences future reasoning directly.

Scientific clarification loop:
- Use Slack when a project-owner answer would materially improve interpretation.
- Prefer one narrow question with enough scientific context, relevant file/figure path, and a clear requested decision.
- Use a DM for targeted owner context and `#open-science` when the answer should be visible to the lab.
- Example:
```bash
python3 lab_assistant/integrations/slack/post_clarification.py \
  --person christiano_wang_beach \
  --message "D93 Run2: is the D = 0.375 V/nm hysteresis step the current lead result, and should I extract a coercive/transition field across D?"
```

What does not belong here:
- core reasoning rules
- project canon
- plot/analysis preferences
- durable lab memory unrelated to Slack transport

Prompt routing rule:
- Slack requests always include a small fixed context bundle drawn from the main workspace.
- The bundle is configured in `context_files.json`.
- Keep that list short, explicit, and limited to durable instructions that should apply on nearly every Slack turn.
- Include channel-specific capability notes when they affect behavior, for example that OpenScience can render LaTeX and pass new uploaded images as local files, while Slack replies should still remain plain text.

Next practical step:
- run `run_bridge.sh` in the normal machine environment
- verify the app is subscribed to DM and channel message events
- confirm replies appear in DMs and as thread replies in `#open-science`
