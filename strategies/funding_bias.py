# strategies/funding_bias.py
# Vote-only funding bias strategy (V2.1)

from Delta_Trading_Bot.strategies.base import Strategy



class FundingBiasStrategy(Strategy):
    name = "funding_bias"

    def vote(self, features: dict) -> dict:
        """
        Funding is contextual. This strategy emits a weak bias only
        when funding magnitude AND timing are informative.
        """

        fr = features.get("funding_rate_abs")
        ttf = features.get("time_to_funding_sec")

        # Default: no opinion
        vote = {
            "bias": 0,            # -1 short, 0 neutral, +1 long
            "confidence": 0.0,
            "reason": "No actionable funding context",
        }

        # Funding unavailable or stale
        if not isinstance(fr, (int, float)) or not isinstance(ttf, (int, float)):
            vote["reason"] = "Funding data incomplete"
            return vote

        # Ignore weak funding
        if fr < 0.0005:
            vote["reason"] = "Funding magnitude too small"
            return vote

        # Timing context: closer to funding = more relevant
        if ttf > 3600:  # more than 1 hour away
            vote["reason"] = "Funding too far in future"
            return vote

        # Directional bias (funding positive → short bias, negative → long bias)
        # Note: evaluator will later decide how to use sign
        vote["bias"] = -1  # short bias for positive funding
        vote["confidence"] = min(fr * 20, 0.4)  # capped, weak by design
        vote["reason"] = "High funding near settlement"

        return vote
