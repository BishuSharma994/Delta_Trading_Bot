# strategies/funding_bias.py
# Vote-only funding bias strategy (V2.2)

from Delta_Trading_Bot.strategies.base import Strategy


class FundingBiasStrategy(Strategy):
    name = "funding_bias"

    def vote(self, features: dict) -> dict:
        """
        Funding emits directional context only when:
        - magnitude meaningful
        - timing relevant
        """

        fr = features.get("funding_rate_abs")
        ttf = features.get("time_to_funding_sec")

        # -------------------------------------------------
        # HARD NO DATA
        # -------------------------------------------------
        if not isinstance(fr, (int, float)) or not isinstance(ttf, (int, float)):
            return {
                "state": "NO_DATA",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Funding data incomplete",
            }

        # -------------------------------------------------
        # WEAK FUNDING
        # -------------------------------------------------
        if fr < 0.0005:
            return {
                "state": "NEUTRAL",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Funding magnitude too small",
            }

        # -------------------------------------------------
        # TOO FAR FROM SETTLEMENT
        # -------------------------------------------------
        if ttf > 3600:
            return {
                "state": "NEUTRAL",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Funding too far in future",
            }

        # -------------------------------------------------
        # ACTIONABLE FUNDING
        # -------------------------------------------------
        return {
            "state": "BIAS_DETECTED",
            "bias": -1,  # positive funding → short bias
            "confidence": min(fr * 20, 0.4),
            "reason": "High funding near settlement",
        }
