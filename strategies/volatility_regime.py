# strategies/volatility_regime.py

from statistics import median
from data.memory import get_recent_feature_values
from strategies.base import Strategy


class VolatilityRegimeStrategy(Strategy):
    name = "volatility_regime"

    def vote(self, features: dict) -> dict:
        symbol = features.get("symbol")
        if not symbol:
            return {
                "bias": 0,
                "confidence": 0.0,
                "reason": "Missing symbol"
            }

        # --- pull raw history from memory ---
        raw_history = get_recent_feature_values(
            symbol=symbol,
            feature="pre_volatility_5m",
            lookback=30
        )

        # --- sanitize: enforce numeric only ---
        history = []
        for v in raw_history:
            try:
                history.append(float(v))
            except (TypeError, ValueError):
                continue

        # --- explicit abstention if insufficient data ---
        if len(history) < 5:
            return {
                "bias": 0,
                "confidence": 0.0,
                "reason": "Insufficient numeric volatility history"
            }

        # --- regime detection ---
        baseline = median(history)
        latest = history[-1]

        if latest > baseline * 1.5:
            return {
                "bias": 1,
                "confidence": min(1.0, (latest / baseline) - 1),
                "reason": "Volatility expansion detected"
            }

        if latest < baseline * 0.7:
            return {
                "bias": -1,
                "confidence": min(1.0, (baseline / latest) - 1),
                "reason": "Volatility compression detected"
            }

        return {
            "bias": 0,
            "confidence": 0.0,
            "reason": "Volatility neutral"
        }
