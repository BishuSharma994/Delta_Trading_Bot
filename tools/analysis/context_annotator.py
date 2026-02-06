"""
Context Annotator — V3.0 Associate Analyst
READ-ONLY | NO EXECUTION | NO DECISION AUTHORITY
"""

from typing import Dict, Any


def annotate_with_context(
    event: Dict[str, Any],
    regime_output: Dict[str, Any],
    rarity_output: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Attach contextual metadata to an existing event.

    - Does not modify original fields
    - Adds a 'context' namespace only
    """

    context = {
        "regime": regime_output.get("regime"),
        "regime_confidence": regime_output.get("confidence"),
    }

    if rarity_output:
        context["rarity_score"] = rarity_output.get("rarity_score")
        context["historical_frequency"] = rarity_output.get("historical_frequency")

    annotated = dict(event)
    annotated["context"] = context
    return annotated
