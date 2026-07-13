# Interaction Capabilities

Purpose:
- Keep channel/UI-facing capabilities explicit so Codex can rely on them during Slack/OpenScience interactions.

Current confirmed capabilities:
- New image uploads from the OpenScience UI are stored as local files and arrive to Codex as `localImage` inputs, not only as browser previews.
- Codex can inspect uploaded image pixels and operate on those local image files when asked to crop, annotate, compare, or extract information.
- Chat and summary Markdown support LaTeX-style math rendering in the OpenScience UI.
- Inline math like `$...$` and display math like `$$...$$` are valid in user-facing responses when equations help clarity.

Desired capabilities to design/build:
- Robust artifact delivery should be a first-class workflow: plots, figures, generated code, notebooks, processed tables, and reports should be produced as stable local artifacts with clear paths and provenance, not only described in chat.
- Serious scientific ideation may need an asynchronous high-reasoning model workflow. The safe shape is a queued, auditable "deliberation job": Codex compiles lab/project context and the question, sends it to an approved external/high-reasoning model interface when available, stores the transcript/outputs as artifacts, critiques the result against lab evidence, and only then proposes memory or analysis updates.
- As of the 2026-07-07 official OpenAI docs check, API access to Pro-capable models is technically available, but API billing is separate from ChatGPT Pro subscriptions. If the goal is to use the lab's existing ChatGPT Pro plan rather than per-token API spend, do not treat the API route as satisfying that requirement.
- For Pro-plan-based deliberation, keep the scope manual and auditable: Codex may prepare a context/prompt bundle and artifact packet; a lab member may run it inside ChatGPT Pro; the response can be saved back into OpenScience for critique, provenance checks, and candidate-gated promotion.
- External/high-reasoning model output should be treated as candidate evidence or hypothesis material, not durable lab memory by default. It must pass provenance, critique, and promotion gates before being folded into graph, skills, or summaries.

Usage rules:
- When an image is attached in a new OpenScience turn, treat it as actionable input, not merely as visual context.
- If an image-dependent answer matters, prefer direct inspection or transformation of the attached image over asking the user to restate what is visible.
- Use equations when they materially improve scientific precision, but keep them concise and readable.
- Do not assume Slack itself renders LaTeX; keep Slack equations plain-text unless the destination clearly supports rendered math.

Limits and caveats:
- The file-backed image guarantee applies to new OpenScience uploads, not necessarily to old legacy thread attachments.
- UI rendering support is separate from transport: OpenScience renders LaTeX; Slack replies should remain plain text.
- No automated high-reasoning external model bridge using ChatGPT Pro entitlements should be pursued unless OpenAI provides an explicit supported mechanism. Browser/UI automation is out of scope; a manual structured handoff bundle is the acceptable option if avoiding API token spend.
