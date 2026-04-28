# Interaction Capabilities

Purpose:
- Keep channel/UI-facing capabilities explicit so Codex can rely on them during Slack/OpenScience interactions.

Current confirmed capabilities:
- New image uploads from the OpenScience UI are stored as local files and arrive to Codex as `localImage` inputs, not only as browser previews.
- Codex can inspect uploaded image pixels and operate on those local image files when asked to crop, annotate, compare, or extract information.
- Chat and summary Markdown support LaTeX-style math rendering in the OpenScience UI.
- Inline math like `$...$` and display math like `$$...$$` are valid in user-facing responses when equations help clarity.

Usage rules:
- When an image is attached in a new OpenScience turn, treat it as actionable input, not merely as visual context.
- If an image-dependent answer matters, prefer direct inspection or transformation of the attached image over asking the user to restate what is visible.
- Use equations when they materially improve scientific precision, but keep them concise and readable.
- Do not assume Slack itself renders LaTeX; keep Slack equations plain-text unless the destination clearly supports rendered math.

Limits and caveats:
- The file-backed image guarantee applies to new OpenScience uploads, not necessarily to old legacy thread attachments.
- UI rendering support is separate from transport: OpenScience renders LaTeX; Slack replies should remain plain text.
