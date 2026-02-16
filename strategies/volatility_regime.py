# strategies/volatility_regime.py
# Structured volatility regime strategy (V2.4)

from statistics import median
from Delta_Trading_Bot.strategies.base import Strategy
from Delta_Trading_Bot.data.memory import get_recent_feature_values


class VolatilityRegimeStrategy(Strategy):
    name = "volatility_regime"

    def vote(self, features: dict) -> dict:
        """
        Detect volatility expansion or compression.
        Memory layer already handles event context.
        No symbol dependency.
        """

        raw_values = get_recent_feature_values("pre_volatility_5m", 30)

        history = []
        for v in raw_values:
            if isinstance(v, (int, float)):
                history.append(float(v))

        if len(history) < 5:
            return {
                "state": "NO_DATA",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Insufficient volatility history",
            }

        baseline = median(history)
        latest = history[-1]

        if baseline <= 0:
            return {
                "state": "NO_DATA",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Invalid baseline volatility",
            }

        if latest > baseline * 1.5:
            return {
                "state": "EXPANSION_DETECTED",
                "bias": 1,
                "confidence": min(1.0, (latest / baseline) - 1),
                "reason": "Volatility expansion detected",
            }

        if latest < baseline * 0.7:
            return {
                "state": "COMPRESSION_DETECTED",
                "bias": -1,
                "confidence": min(1.0, (baseline / latest) - 1),
                "reason": "Volatility compression detected",
            }

        return {
            "state": "NEUTRAL",
            "bias": 0,
            "confidence": 0.0,
            "reason": "Volatility neutral",
        }
