"""Versioned deterministic rubrics for scientific synthesis objects."""

from __future__ import annotations


SYNTHESIS_RUBRIC_VERSION = "synthesis_rubric_v1"


SYNTHESIS_RUBRIC = {
    "groundedness": "0-5: support and contradiction fields cite concrete graph or source ids.",
    "falsifiability": "0-5: prediction, minimal test, and falsifying observation are concrete.",
    "mechanism_clarity": "0-5: mechanism links observation to predicted outcome.",
    "contradiction_awareness": "0-5: contradicting claims or risks are explicitly represented.",
    "novelty_proxy": "0-5: novelty rationale states what gap the hypothesis addresses.",
    "actionability": "0-5: minimal test is experimentally or analytically actionable.",
    "provenance_completeness": "0-5: every support/contradiction has provenance or graph id.",
}
