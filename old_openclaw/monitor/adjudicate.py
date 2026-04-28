"""
LLM adjudication of a RunSummary.

The LLM receives a plain-text summary (no arrays) and returns a structured
AlertDecision via tool_use. It also drafts a Slack message when alerting.

Requires: pip install anthropic
Set ANTHROPIC_API_KEY before use.
Pass dry_run=True to skip the API call (for testing).
"""

from __future__ import annotations

from datetime import datetime, timezone

from .schemas import AlertDecision, RunSummary
from .summarize import format_summary_for_llm

_DECISION_TOOL = {
    "name": "record_alert_decision",
    "description": (
        "Record your decision about this active experimental run. "
        "Decide whether to alert the lab, suppress (nothing notable), or watch (check again next poll)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["alert", "suppress", "watch"],
                "description": (
                    "alert: post to Slack now — something needs attention. "
                    "suppress: all normal, no action. "
                    "watch: slightly suspicious, check again next poll."
                ),
            },
            "likely_cause": {
                "type": "string",
                "enum": [
                    "instrument_issue",
                    "data_quality",
                    "interesting_physics",
                    "routine_pause",
                    "run_complete",
                    "unknown",
                ],
            },
            "reasoning": {
                "type": "string",
                "description": "1–3 sentences explaining the decision.",
            },
            "suggested_action": {
                "type": "string",
                "description": "Concrete next step for the experimenter.",
            },
            "slack_message": {
                "type": "string",
                "description": (
                    "Only if decision == 'alert': a ready-to-send Slack message "
                    "(plain text, no Markdown, ≤3 short bullets). "
                    "Empty string if not alerting."
                ),
            },
            "confidence": {
                "type": "number",
                "description": "Your confidence in this decision, 0 to 1.",
            },
        },
        "required": [
            "decision", "likely_cause", "reasoning",
            "suggested_action", "slack_message", "confidence",
        ],
    },
}

_SYSTEM_PROMPT = """\
You are OpenScience, the AI assistant for the Xu Lab at UW. \
The lab studies twisted transition-metal dichalcogenides (tMoTe₂, alternating-twist trilayer, θ≈3.9°) \
and related materials using PL, reflectance, and RMCD spectroscopy on attodry cryostats and dilution refrigerators.

You are monitoring an active experiment in real time as data files arrive from the cryostat.
Your job: decide whether anything needs immediate attention from the experimenter.

## Decision criteria

Suppress (say nothing) unless there is a concrete, actionable problem:
- First few files of a run: normal.
- Files arriving in bursts: cryostats write in batches.
- RMCD coercive field near zero at some gate voltages: this is EXPECTED PHYSICS — at paramagnetic filling \
factors (e.g., between ν=-1 and ν=-2 in the hole-doped regime) the hysteresis loop collapses. \
Do NOT flag this as an instrument problem. Only consider alerting if Hc is zero across ALL conditions \
when the experimenter explicitly expects ferromagnetism.
- Low SNR in reflectance at specific gate voltages: normal when sweeping off-resonance.
- Occasional NaN points in a gate sweep: normal from incomplete gate equilibration.
- PL intensity dropping at certain (n, D): expected at exciton-quenching filling factors \
(ν ≈ -2, -3 in tMoTe₂). Only flag if ALL spectra simultaneously drop to noise.

Alert (immediate Slack message) for:
- Load failure on multiple consecutive files: DAQ, disk, or instrument issue.
- All-zeros arrays in primary data variables: detector or lock-in dropout.
- Complete loss of dR/R contrast in reflectance (was working, then all files show near-zero signal): \
laser alignment drift, temperature excursion, or sample damage.
- PL peak energy shifting by >10 meV between consecutive files at identical gate conditions: \
temperature instability or laser drift.
- RMCD gate map entirely NaN when previous files were fine: DAQ connection issue.
- Gap >30 min with no new files when experimenter indicated sweep is running continuously.

Watch (log, no Slack) for:
- A few isolated bad files (1–2 out of a batch) surrounded by clean ones.
- RMCD saturation contrast dropping gradually (could be temperature rising).
- Integration time or file size inconsistent with other files in the same sweep.

## Slack message style
Plain text, no Markdown. Address the experimenter by name from the context.
3 bullets max: (1) what was observed, (2) why it matters, (3) what to check.
Keep it under 5 lines total. Example:
  Yifan — RMCD files 15–17 failed to load (scipy error).
  - May indicate a partial write from the DAQ or a cryostat network hiccup.
  - Check the LabOne connection and re-save those gate points if possible.
"""


def adjudicate(
    summary: RunSummary,
    model: str = "claude-haiku-4-5-20251001",
    dry_run: bool = False,
) -> AlertDecision:
    """
    Ask the LLM whether to alert, suppress, or watch.

    dry_run=True: skip API call, return suppress/unknown.
    """
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    if dry_run:
        return AlertDecision(
            run_id=summary.run_id,
            decided_at=now_iso,
            decision="suppress",
            likely_cause="unknown",
            reasoning="[dry_run] LLM call skipped.",
            suggested_action="No action (dry run).",
            slack_message="",
            confidence=0.0,
            llm_model="dry_run",
            prompt_tokens=0,
            completion_tokens=0,
        )

    try:
        import anthropic  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "anthropic package not installed. Run: pip install anthropic\n"
            "Or use --dry-run to skip LLM calls."
        ) from exc

    client = anthropic.Anthropic()
    user_msg = format_summary_for_llm(summary)

    response = client.messages.create(
        model=model,
        max_tokens=600,
        system=_SYSTEM_PROMPT,
        tools=[_DECISION_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": user_msg}],
    )

    tool_result: dict | None = None
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "record_alert_decision":
            tool_result = block.input
            break

    if tool_result is None:
        return AlertDecision(
            run_id=summary.run_id,
            decided_at=now_iso,
            decision="watch",
            likely_cause="unknown",
            reasoning="LLM did not return a structured decision.",
            suggested_action="Review manually.",
            slack_message="",
            confidence=0.0,
            llm_model=model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
        )

    return AlertDecision(
        run_id=summary.run_id,
        decided_at=now_iso,
        decision=str(tool_result["decision"]),
        likely_cause=str(tool_result["likely_cause"]),
        reasoning=str(tool_result["reasoning"]),
        suggested_action=str(tool_result["suggested_action"]),
        slack_message=str(tool_result.get("slack_message", "")),
        confidence=float(tool_result.get("confidence", 0.5)),
        llm_model=model,
        prompt_tokens=response.usage.input_tokens,
        completion_tokens=response.usage.output_tokens,
    )
