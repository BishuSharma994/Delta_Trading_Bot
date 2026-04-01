# strategies/funding_bias.py
# Vote-only funding bias strategy (V2.2)

from Delta_Trading_Bot.config.risk import RISK
from Delta_Trading_Bot.strategies.base import Strategy


class FundingBiasStrategy(Strategy):
    name = "funding_bias"

    def vote(self, features: dict) -> dict:
        """
        Funding emits directional context only when:
        - magnitude meaningful
        - timing relevant
        """

        raw_fr = features.get("funding_rate")
        fr = features.get("funding_rate_abs")
        ttf = features.get("time_to_funding_sec")

        # -------------------------------------------------
        # HARD NO DATA
        # -------------------------------------------------
        if (
            not isinstance(raw_fr, (int, float))
            or not isinstance(fr, (int, float))
            or not isinstance(ttf, (int, float))
        ):
            return {
                "state": "NO_DATA",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Funding data incomplete",
            }

        # -------------------------------------------------
        # WEAK FUNDING
        # -------------------------------------------------
        if fr < RISK.min_funding_rate_abs:
            return {
                "state": "NEUTRAL",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Funding magnitude too small",
            }

        # -------------------------------------------------
        # TOO FAR FROM SETTLEMENT
        # -------------------------------------------------
        if ttf > RISK.funding_signal_window_sec:
            return {
                "state": "NEUTRAL",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Funding too far in future",
            }

        # -------------------------------------------------
        # ACTIONABLE FUNDING
        # -------------------------------------------------
        bias = -1 if raw_fr > 0 else 1

        return {
            "state": "BIAS_DETECTED",
            "bias": bias,
            "side": "SHORT" if bias < 0 else "LONG",
            "confidence": min(fr * 25, 0.6),
            "reason": "High funding near settlement",
        }
