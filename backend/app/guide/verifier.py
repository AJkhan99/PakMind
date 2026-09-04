"""Cross-LLM answer verification.

Compares the primary LLM's draft answer against the source context using a
secondary LLM, producing warnings and adjusting confidence.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.ai.llm_router import call_llm_json

logger = logging.getLogger(__name__)


def verify_and_refine(
    context: str,
    draft: dict[str, Any],
) -> dict[str, Any]:
    """Verify the draft answer and merge corrections.

    Returns the refined answer dict with updated confidence and warnings.
    """
    draft_text = json.dumps(draft, ensure_ascii=False, indent=2)

    try:
        from app.guide.prompts import build_verification_prompt
        messages = build_verification_prompt(context, draft_text)
        verification = call_llm_json(messages, provider="groq")
    except Exception as exc:
        logger.warning("Verification LLM call failed: %s — returning draft as-is", exc)
        draft.setdefault("warnings", []).append(
            "Cross-verification was unavailable; answer relies on a single LLM."
        )
        draft["confidence"] = draft.get("confidence", "medium")
        return draft

    # If verification found issues, apply corrections
    if verification.get("issues"):
        draft.setdefault("warnings", []).extend(verification["issues"])

    if verification.get("corrected_fields"):
        for field, value in verification["corrected_fields"].items():
            if field in draft:
                draft[field] = value

    # Adjust confidence
    verified = verification.get("verified", False)
    conf_adj = verification.get("confidence_adjustment", "medium")

    if verified:
        draft["confidence"] = "high"
    else:
        draft["confidence"] = conf_adj

    return draft
