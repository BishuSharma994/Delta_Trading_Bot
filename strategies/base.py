# strategies/base.py
# Strategy interface (design-only)

class Strategy:
    name = "base"

    def vote(self, features: dict) -> dict:
        """
        Returns:
        {
          "bias": -1 | 0 | 1,        # short / neutral / long
          "confidence": 0.0 - 1.0,   # strategy certainty
          "reason": str             # human-readable explanation
        }
        """
        raise NotImplementedError
