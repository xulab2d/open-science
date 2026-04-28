# Slack Integration Plan

Goal:
- Support future Slack interaction without coupling the whole workspace to Slack-specific behavior.

Channel-agnostic core:
- task interpretation
- file discovery
- project context retrieval
- activity summarization
- analysis support
- durable memory updates

Slack-specific layer:
- user/thread identity mapping
- mention and thread behavior
- message formatting constraints
- routing to DMs or channels
- optional background polling and digest delivery

Recommended future design:
1. Keep Slack adapters separate from core assistant files.
2. Store Slack identity and routing config in a dedicated integration config, not in `core/`.
3. Reuse `skills/` for the substantive work; Slack should mainly supply input, context, and output formatting.
4. Add a deterministic message-preparation helper before adding autonomous Slack loops.

Not carried over from legacy system:
- OpenClaw CLI messaging assumptions
- hard-coded mention behavior in core prompts
- Slack logic intertwined with ingest orchestration
