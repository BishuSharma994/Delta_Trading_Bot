"""
Pattern Rarity Index — V3.0 Associate Analyst
READ-ONLY | DESCRIPTIVE ONLY
"""

from typing import Dict, Any, List
from collections import Counter


def compute_pattern_signature(event: Dict[str, Any]) -> str:
    """
    Create a simple signature of the event configuration.
    """
    vote = event.get("vote", {})
    bias = vote.get("bias")
    confidence_bucket = int((vote.get("confidence", 0.0) or 0.0) * 10)
    regime = event.get("context", {}).get("regime", "unknown")

    return f"{regime}|bias:{bias}|conf:{confidence_bucket}"


def compute_rarity_index(
    annotated_events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute historical frequency and rarity score for each event.
    """

    signatures = [compute_pattern_signature(e) for e in annotated_events]
    counts = Counter(signatures)
    total = len(signatures)

    results = []

    for event, sig in zip(annotated_events, signatures):
        freq = counts[sig] / total if total else 0.0
        rarity = 1.0 - freq

        results.append({
            "pattern_signature": sig,
            "historical_frequency": freq,
            "rarity_score": rarity,
        })

    return results
