# strategies/volatility_regime.py

from statistics import median
from strategies.base import Strategy
from data.memory import get_recent_feature_values


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

        raw_values = get_recent_feature_values(
            symbol=symbol,
            feature="pre_volatility_5m",
            lookback=30
        )

        # --- HARD SANITIZATION ---
        history = []
        for v in raw_values:
            if isinstance(v, (int, float)):
                history.append(float(v))
            else:
                # try last-resort coercion
                try:
                    history.append(float(v))
                except Exception:
                    continue

        # --- explicit abstention ---
        if len(history) < 5:
            return {
                "bias": 0,
                "confidence": 0.0,
                "reason": "Insufficient clean volatility history"
            }

        baseline = median(history)
        latest = history[-1]

        if baseline <= 0:
            return {
                "bias": 0,
                "confidence": 0.0,
                "reason": "Invalid baseline volatility"
            }

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
