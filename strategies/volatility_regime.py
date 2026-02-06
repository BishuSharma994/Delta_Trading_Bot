# strategies/volatility_regime.py
# V2.2 — Volatility Regime Strategy (Vote Only)

from statistics import median
from data.memory import get_recent_feature_values


class VolatilityRegimeStrategy:
    """
    Junior analyst:
    Detects volatility regime transitions.
    Emits votes only. Never trades.
    """

    name = "volatility_regime"

    def __init__(self, lookback=60):
        self.lookback = lookback

    def vote(self, features: dict) -> dict:
        current_vol = features.get("pre_volatility_5m")

        if current_vol is None:
            return {"state": "NO_DATA", "confidence": 0.0}

        history = get_recent_feature_values(
            feature_name="pre_volatility_5m",
            limit=self.lookback
        )

        if not history or len(history) < 10:
            return {"state": "INSUFFICIENT_HISTORY", "confidence": 0.0}

        baseline = median(history)

        if current_vol < 0.7 * baseline:
            return {"state": "COMPRESSED", "confidence": 0.4}

        if current_vol > 1.5 * baseline:
            return {
                "state": "EXPANSION_DETECTED",
                "confidence": round(min(1.0, current_vol / baseline), 2)
            }

        return {"state": "NEUTRAL", "confidence": 0.5}
