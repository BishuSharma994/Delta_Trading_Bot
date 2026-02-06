"""
Regime Classifier — V3.0 Associate Analyst
READ-ONLY | NO EXECUTION | NO DECISION AUTHORITY
"""

from typing import Dict, Literal

Regime = Literal[
    "trend_up",
    "trend_down",
    "range",
    "volatility_expansion",
    "volatility_compression",
    "transition",
]


def classify_regime(features: Dict[str, float]) -> Dict[str, object]:
    """
    Classify market regime based on precomputed features.

    This function is:
    - Deterministic
    - Stateless
    - Non-actionable
    """

    volatility = features.get("volatility", 0.0)
    trend_strength = features.get("trend_strength", 0.0)

    if trend_strength > 0.7 and volatility > 0.4:
        regime: Regime = "trend_up"
        confidence = 0.75
    elif trend_strength < -0.7 and volatility > 0.4:
        regime = "trend_down"
        confidence = 0.75
    elif volatility < 0.2:
        regime = "range"
        confidence = 0.7
    elif volatility > 0.6:
        regime = "volatility_expansion"
        confidence = 0.7
    else:
        regime = "transition"
        confidence = 0.5

    return {
        "regime": regime,
        "confidence": confidence,
    }
