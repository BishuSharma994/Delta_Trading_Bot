import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent

if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from config.risk import RISK
from core import state_engine as state_engine_module
from core.state_engine import StateEngine, SymbolState
from Delta_Trading_Bot.strategies.funding_bias import FundingBiasStrategy


class RuntimeRiskTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "execution_state.json"
        self.events = []

        self.state_patch = patch.object(state_engine_module, "STATE_FILE", self.state_file)
        self.write_patch = patch.object(
            state_engine_module,
            "write_event",
            side_effect=lambda filename, payload: self.events.append((filename, payload.copy())),
        )

        self.state_patch.start()
        self.write_patch.start()
        self.engine = StateEngine()

    def tearDown(self):
        self.write_patch.stop()
        self.state_patch.stop()
        self.temp_dir.cleanup()

    def test_funding_bias_uses_signed_direction(self):
        strategy = FundingBiasStrategy()

        vote = strategy.vote({
            "funding_rate": -0.0012,
            "funding_rate_abs": 0.0012,
            "time_to_funding_sec": 30,
        })

        self.assertEqual(vote["state"], "BIAS_DETECTED")
        self.assertEqual(vote["bias"], 1)
        self.assertEqual(vote["side"], "LONG")

    def test_stale_gap_forces_exit_and_blocks_immediate_reentry(self):
        now = datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc)
        symbol = "BTCUSD"
        state = SymbolState()
        state.state = "IN_FUNDING_TRADE"
        state.trade_type = "FUNDING"
        state.side = "SHORT"
        state.entry_time = (now - timedelta(minutes=2)).isoformat()
        state.entry_price = 100.0
        state.exit_funding_ts = (now + timedelta(seconds=30)).isoformat()
        state.trade_date = now.date().isoformat()
        state.last_observed_at = (now - timedelta(minutes=10)).isoformat()
        self.engine.symbols[symbol] = state

        funding_features = {
            "funding_rate": 0.001,
            "funding_rate_abs": 0.001,
            "time_to_funding_sec": 60,
            "pre_volatility_5m": 0.001,
            "bid_ask_spread_pct": 0.0005,
        }
        funding_vote = {"state": "BIAS_DETECTED", "bias": -1, "side": "SHORT"}

        self.engine.process(
            symbol,
            decision={},
            features=funding_features,
            price=101.0,
            funding_vote=funding_vote,
            vol_vote={},
            now=now,
        )

        saved_state = self.engine.symbols[symbol]
        self.assertEqual(saved_state.state, "FLAT")
        self.assertEqual(saved_state.warmup_loops_remaining, RISK.warmup_loops_after_stale_gap)
        self.assertEqual(self.events[-1][1]["reason"], "stale_recovery_exit")

        self.engine.process(
            symbol,
            decision={},
            features=funding_features,
            price=100.0,
            funding_vote=funding_vote,
            vol_vote={},
            now=now + timedelta(minutes=1),
        )

        self.assertEqual(self.engine.symbols[symbol].state, "FLAT")
        event_reasons = [payload["reason"] for _, payload in self.events]
        self.assertEqual(event_reasons.count("funding_entry"), 0)

    def test_high_volatility_blocks_funding_entry(self):
        now = datetime(2026, 4, 1, 1, 0, tzinfo=timezone.utc)

        self.engine.process(
            "ETHUSD",
            decision={},
            features={
                "funding_rate": 0.0015,
                "funding_rate_abs": 0.0015,
                "time_to_funding_sec": 45,
                "pre_volatility_5m": RISK.max_funding_pre_volatility_5m + 0.001,
                "bid_ask_spread_pct": 0.0005,
            },
            price=2000.0,
            funding_vote={"state": "BIAS_DETECTED", "bias": -1, "side": "SHORT"},
            vol_vote={},
            now=now,
        )

        self.assertEqual(self.engine.symbols["ETHUSD"].state, "FLAT")
        self.assertFalse(self.events)


if __name__ == "__main__":
    unittest.main()
