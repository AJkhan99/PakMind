"""Verification layer — secondary LLM cross-checks generated answers."""

from __future__ import annotations

import logging
from typing import Any

from app.watch.prompts import verify_answer

logger = logging.getLogger(__name__)


def verify_and_refine(context: str, draft: dict[str, Any]) -> dict[str, Any]:
    """Verify a draft answer against the source context.

    If the verifier identifies issues, merge corrections back into the draft.
    Returns the (possibly corrected) draft dict.
    """
    draft_answer = str(draft.get("answer", ""))
    if not draft_answer.strip():
        return draft

    try:
        verification = verify_answer(context, draft_answer)
    except Exception as exc:
        logger.warning("Verification LLM call failed: %s — using draft as-is", exc)
        draft.setdefault("warnings", []).append("Cross-verification was unavailable.")
        return draft

    if verification.get("error"):
        logger.warning("Verification returned error: %s", verification["error"])
        draft.setdefault("warnings", []).append("Cross-verification was unavailable.")
        return draft

    # Check if verification found issues
    if not verification.get("verified", True):
        issues = verification.get("issues", [])
        corrected_fields = verification.get("corrected_fields", {})

        if issues:
            logger.info("Verification found %d issues: %s", len(issues), issues[:3])
            draft.setdefault("warnings", []).extend(
                f"Verification note: {issue}" for issue in issues[:3]
            )

        # Apply corrections
        for field, corrected_value in corrected_fields.items():
            if field in draft and corrected_value is not None:
                draft[field] = corrected_value

    # Apply confidence adjustment
    adj = verification.get("confidence_adjustment")
    if adj and adj in ("high", "medium", "low"):
        draft["confidence"] = adj

    return draft
