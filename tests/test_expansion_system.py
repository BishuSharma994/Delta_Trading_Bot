import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent

if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.strategy.expansion_validator import validate_expansion
from app.strategy.exit_manager import evaluate_vol_exit
from app.strategy.htf_bias import detect_htf_bias
from app.strategy.regime_filter import evaluate_regime_filter
from config.asset_rules import get_asset_rules


def _candle(open_price: float, high_price: float, low_price: float, close_price: float) -> dict:
    return {
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
    }


class ExpansionSystemTests(unittest.TestCase):
    def test_expansion_validator_accepts_displacement_break(self):
        rules = get_asset_rules("BTCUSD")
        candles = [
            _candle(100.0, 100.8, 99.6, 100.2),
            _candle(100.2, 100.9, 99.9, 100.4),
            _candle(100.4, 101.0, 100.0, 100.5),
            _candle(100.5, 101.1, 100.1, 100.6),
            _candle(100.6, 101.2, 100.2, 100.7),
            _candle(100.7, 101.3, 100.3, 100.8),
            _candle(100.8, 104.8, 100.6, 104.5),
        ]

        result = validate_expansion("LONG", candles, structure_level=101.0, asset_rules=rules)

        self.assertTrue(result["is_valid"])
        self.assertGreater(result["displacement_ratio"], 1.0)
        self.assertGreaterEqual(result["body_ratio"], rules.min_body_ratio)
        self.assertTrue(result["close_beyond_structure"])

    def test_regime_filter_classifies_choppy_market_as_range(self):
        rules = get_asset_rules("BTCUSD")
        candles = []

        for index in range(20):
            if index % 2 == 0:
                candles.append(_candle(100.0, 101.6, 99.4, 101.0))
            else:
                candles.append(_candle(101.0, 101.6, 99.4, 100.0))

        result = evaluate_regime_filter(candles, rules)

        self.assertTrue(result["allow_trade"])
        self.assertEqual(result["regime"], "RANGE")

    def test_htf_bias_detects_uptrend(self):
        rules = get_asset_rules("BTCUSD")
        candles = []
        price = 100.0

        for _ in range(30):
            open_price = price
            close_price = price + 0.4
            candles.append(_candle(open_price, close_price + 0.2, open_price - 0.1, close_price))
            price = close_price

        result = detect_htf_bias(candles, rules)

        self.assertEqual(result["bias"], "LONG")
        self.assertGreater(result["trend_pct"], 0.0)

    def test_exit_manager_flags_no_expansion_inside_validation_window(self):
        rules = get_asset_rules("BTCUSD")
        state = SimpleNamespace(
            side="LONG",
            entry_price=100.0,
            peak_price=100.1,
            trough_price=100.0,
            vol_context={
                "validation_remaining": 1,
                "validation_passed": False,
                "entry_atr_pct": 0.01,
                "structure_invalidation": 99.0,
            },
        )

        reason, context = evaluate_vol_exit(
            symbol="BTCUSD",
            state=state,
            price=100.05,
            vol_vote={},
            asset_rules=rules,
        )

        self.assertEqual(reason, "no_expansion")
        self.assertEqual(context["validation_remaining"], 0)


if __name__ == "__main__":
    unittest.main()
