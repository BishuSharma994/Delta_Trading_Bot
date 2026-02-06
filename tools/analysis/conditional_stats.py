"""
Conditional Statistics — V3.0 Associate Analyst
DESCRIPTIVE ONLY | NO FEEDBACK | NO DECISION AUTHORITY
"""

from typing import Dict, List, Any
from collections import defaultdict
from statistics import mean


def compute_abstention_rate_by_regime(
    annotated_events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute abstention rate conditioned on regime.
    Assumes event contains:
      - event['vote']['bias']  (0 == abstention)
      - event['context']['regime']
    """

    totals = defaultdict(int)
    abstentions = defaultdict(int)

    for e in annotated_events:
        regime = e.get("context", {}).get("regime", "unknown")
        totals[regime] += 1
        if e.get("vote", {}).get("bias") == 0:
            abstentions[regime] += 1

    results = []
    for regime, total in totals.items():
        rate = abstentions[regime] / total if total else 0.0
        results.append({
            "metric_name": "abstention_rate",
            "regime": regime,
            "value": rate,
            "sample_size": total,
        })

    return results


def compute_confidence_distribution_by_regime(
    annotated_events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute mean confidence conditioned on regime.
    Assumes event['vote']['confidence'] exists.
    """

    buckets = defaultdict(list)

    for e in annotated_events:
        regime = e.get("context", {}).get("regime", "unknown")
        conf = e.get("vote", {}).get("confidence")
        if conf is not None:
            buckets[regime].append(conf)

    results = []
    for regime, values in buckets.items():
        results.append({
            "metric_name": "mean_confidence",
            "regime": regime,
            "value": mean(values) if values else 0.0,
            "sample_size": len(values),
        })

    return results
