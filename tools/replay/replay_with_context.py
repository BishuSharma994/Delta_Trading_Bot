"""
Offline Replay with Context + Rarity — V3.0
READ-ONLY | OFFLINE ONLY | NO DECISION AUTHORITY
"""

from typing import List, Dict, Any

from tools.analysis.regime_classifier import classify_regime
from tools.analysis.context_annotator import annotate_with_context
from tools.analysis.conditional_stats import (
    compute_abstention_rate_by_regime,
    compute_confidence_distribution_by_regime,
)
from tools.analysis.pattern_rarity import compute_rarity_index


def replay_with_context(
    events: List[Dict[str, Any]],
    feature_provider,
) -> Dict[str, Any]:
    """
    Offline replay that:
    - classifies regime
    - annotates events with context
    - computes rarity index
    - computes conditional statistics

    feature_provider(event) -> Dict[str, float]
    """

    annotated_events: List[Dict[str, Any]] = []

    # 1. Regime classification + context annotation
    for event in events:
        features = feature_provider(event)
        regime_out = classify_regime(features)
        annotated = annotate_with_context(event, regime_out)
        annotated_events.append(annotated)

    # 2. Pattern rarity computation
    rarity_results = compute_rarity_index(annotated_events)

    # 3. Attach rarity to events (non-intrusive)
    enriched_events: List[Dict[str, Any]] = []
    for event, rarity in zip(annotated_events, rarity_results):
        e = dict(event)
        context = dict(e.get("context", {}))
        context["rarity_score"] = rarity["rarity_score"]
        context["historical_frequency"] = rarity["historical_frequency"]
        e["context"] = context
        enriched_events.append(e)

    # 4. Conditional statistics (descriptive only)
    stats = {
        "abstention_rate_by_regime": compute_abstention_rate_by_regime(enriched_events),
        "confidence_by_regime": compute_confidence_distribution_by_regime(enriched_events),
    }

    return {
        "annotated_events": enriched_events,
        "conditional_statistics": stats,
    }
