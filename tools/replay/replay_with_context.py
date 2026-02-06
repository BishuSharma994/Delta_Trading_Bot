"""
Offline Replay with Context — V3.0
READ-ONLY | OFFLINE ONLY
"""

from typing import List, Dict, Any

from tools.analysis.regime_classifier import classify_regime
from tools.analysis.context_annotator import annotate_with_context
from tools.analysis.conditional_stats import (
    compute_abstention_rate_by_regime,
    compute_confidence_distribution_by_regime,
)


def replay_with_context(
    events: List[Dict[str, Any]],
    feature_provider,
) -> Dict[str, Any]:
    """
    Offline replay that:
    - classifies regime
    - annotates events with context
    - computes conditional statistics

    feature_provider(event) -> Dict[str, float]
    """

    annotated_events: List[Dict[str, Any]] = []

    for event in events:
        features = feature_provider(event)
        regime_out = classify_regime(features)
        annotated = annotate_with_context(event, regime_out)
        annotated_events.append(annotated)

    stats = {
        "abstention_rate_by_regime": compute_abstention_rate_by_regime(annotated_events),
        "confidence_by_regime": compute_confidence_distribution_by_regime(annotated_events),
    }

    return {
        "annotated_events": annotated_events,
        "conditional_statistics": stats,
    }
