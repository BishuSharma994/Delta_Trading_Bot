import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent

if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.risk import RISK
from app.strategy.exit_manager import get_vol_trailing_stop, handle_vol_timeout
from core import state_engine as state_engine_module
from core.state_engine import StateEngine, SymbolState
from Delta_Trading_Bot.strategies.funding_bias import FundingBiasStrategy


class RuntimeRiskTests(unittest.TestCase):
    def setUp(self):
        self.events = []

        self.save_patch = patch.object(state_engine_module.StateEngine, "_save", autospec=True)
        self.write_patch = patch.object(
            state_engine_module,
            "write_event",
            side_effect=lambda filename, payload: self.events.append((filename, payload.copy())),
        )

        self.save_patch.start()
        self.write_patch.start()
        self.engine = StateEngine()

    def tearDown(self):
        self.write_patch.stop()
        self.save_patch.stop()

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

    def test_funding_rate_filter_rejects_extreme_funding(self):
        now = datetime(2026, 4, 1, 2, 0, tzinfo=timezone.utc)

        self.engine.process(
            "BTCUSD",
            decision={"score": 1.0},
            features={
                "funding_rate": 0.004,
                "funding_rate_abs": RISK.max_funding_rate_abs + 0.0001,
                "time_to_funding_sec": 120,
                "pre_volatility_5m": 0.001,
                "bid_ask_spread_pct": 0.0005,
            },
            price=100.0,
            funding_vote={"state": "BIAS_DETECTED", "bias": -1, "side": "SHORT", "confidence": 0.6},
            vol_vote={},
            now=now,
        )

        self.assertEqual(self.engine.symbols["BTCUSD"].state, "FLAT")
        self.assertEqual(self.events[-1][1]["reason"], "funding_rate_filter")

    def test_position_sizing_scales_with_symbol_volatility(self):
        now = datetime(2026, 4, 1, 3, 0, tzinfo=timezone.utc)
        decision = {"score": 1.0}
        vol_vote = {
            "state": "STRUCTURE_CONFIRMED",
            "signal": "LONG",
            "confidence": 0.90,
            "reason": "trend_follow",
            "ob": {"low": 99.0, "high": 101.0},
            "expansion": {"displacement_ratio": 1.2},
        }

        self.engine.process(
            "BTCUSD",
            decision=decision,
            features={
                "pre_volatility_5m": 0.0010,
                "bid_ask_spread_pct": 0.0005,
            },
            price=100.0,
            funding_vote={},
            vol_vote=vol_vote,
            now=now,
        )

        self.engine.process(
            "ETHUSD",
            decision=decision,
            features={
                "pre_volatility_5m": 0.0040,
                "bid_ask_spread_pct": 0.0005,
            },
            price=100.0,
            funding_vote={},
            vol_vote={**vol_vote, "signal": "SHORT"},
            now=now,
        )

        btc_state = self.engine.symbols["BTCUSD"]
        eth_state = self.engine.symbols["ETHUSD"]

        self.assertEqual(btc_state.state, "IN_VOL_TRADE")
        self.assertEqual(eth_state.state, "IN_VOL_TRADE")
        self.assertGreater(btc_state.position_notional_usd, eth_state.position_notional_usd)
        self.assertGreater(btc_state.volatility_scale, eth_state.volatility_scale)

    def test_volatility_reject_logs_for_structure_confirmed_setup(self):
        now = datetime(2026, 4, 1, 3, 30, tzinfo=timezone.utc)

        self.engine.process(
            "TSLAXUSD",
            decision={"score": 1.0},
            features={
                "pre_volatility_5m": RISK.max_vol_pre_volatility_5m + 0.001,
                "bid_ask_spread_pct": 0.0005,
            },
            price=100.0,
            funding_vote={},
            vol_vote={
                "state": "STRUCTURE_CONFIRMED",
                "signal": "SHORT",
                "confidence": 0.95,
                "reason": "breakdown",
                "ob": {"low": 99.0, "high": 101.0},
                "expansion": {"displacement_ratio": 1.2},
            },
            now=now,
        )

        self.assertEqual(self.engine.symbols["TSLAXUSD"].state, "FLAT")
        self.assertEqual(self.events[-1][1]["reason"], "volatility_too_high")

    def test_xstock_structure_confirmed_can_enter_24x7(self):
        now = datetime(2026, 4, 1, 3, 45, tzinfo=timezone.utc)

        self.engine.process(
            "TSLAXUSD",
            decision={"score": 1.0},
            features={
                "pre_volatility_5m": 0.0010,
                "bid_ask_spread_pct": 0.0005,
            },
            price=100.0,
            funding_vote={},
            vol_vote={
                "state": "STRUCTURE_CONFIRMED",
                "signal": "SHORT",
                "confidence": 0.95,
                "reason": "breakdown",
                "ob": {"low": 99.0, "high": 101.0},
                "expansion": {"displacement_ratio": 1.2},
            },
            now=now,
        )

        self.assertEqual(self.engine.symbols["TSLAXUSD"].state, "IN_VOL_TRADE")
        self.assertEqual(self.events[-1][1]["action"], "ENTRY")
        self.assertEqual(self.events[-1][1]["side"], "SHORT")

    def test_cooldown_active_logs_reject_for_structure_confirmed_setup(self):
        now = datetime(2026, 4, 1, 3, 50, tzinfo=timezone.utc)
        state = SymbolState()
        state.trade_date = now.date().isoformat()
        state.cooldown_until = (now + timedelta(minutes=15)).isoformat()
        self.engine.symbols["BTCUSD"] = state

        self.engine.process(
            "BTCUSD",
            decision={"score": 1.0},
            features={
                "pre_volatility_5m": 0.0010,
                "bid_ask_spread_pct": 0.0005,
            },
            price=100.0,
            funding_vote={},
            vol_vote={
                "state": "STRUCTURE_CONFIRMED",
                "signal": "LONG",
                "confidence": 0.90,
                "reason": "trend_follow",
                "ob": {"low": 99.0, "high": 101.0},
                "expansion": {"displacement_ratio": 1.2},
            },
            now=now,
        )

        self.assertEqual(self.engine.symbols["BTCUSD"].state, "FLAT")
        self.assertEqual(self.events[-1][1]["reason"], "cooldown_active")

    def test_portfolio_drawdown_kill_switch_blocks_new_entries(self):
        now = datetime(2026, 4, 1, 4, 0, tzinfo=timezone.utc)
        losing_state = SymbolState()
        losing_state.trade_date = now.date().isoformat()
        losing_state.daily_realized_return = -RISK.portfolio_max_daily_drawdown_pct
        self.engine.symbols["BTCUSD"] = losing_state

        self.engine.process(
            "ETHUSD",
            decision={"score": 1.0},
            features={
                "pre_volatility_5m": 0.0010,
                "bid_ask_spread_pct": 0.0005,
            },
            price=100.0,
            funding_vote={},
            vol_vote={
                "state": "STRUCTURE_CONFIRMED",
                "signal": "LONG",
                "confidence": 0.90,
                "reason": "trend_follow",
                "ob": {"low": 99.0, "high": 101.0},
                "expansion": {"displacement_ratio": 1.2},
            },
            now=now,
        )

        self.assertEqual(self.engine.symbols["ETHUSD"].state, "FLAT")
        self.assertFalse(self.events)

    def test_trailing_stop_uses_configured_activation_threshold(self):
        state = SymbolState()
        state.side = "LONG"
        state.entry_price = 100.0
        state.peak_price = 100.05
        state.trough_price = 100.0

        self.assertIsNone(get_vol_trailing_stop(state))

        state.peak_price = 100.20
        self.assertIsNotNone(get_vol_trailing_stop(state))

    def test_profitable_timeout_switches_to_buffered_trailing_stop(self):
        state = SymbolState()
        state.side = "LONG"
        state.entry_price = 100.0
        state.vol_context = {}

        should_exit = handle_vol_timeout(state, current_pnl_pct=0.0020, log_func=lambda *_: None)

        self.assertFalse(should_exit)
        self.assertAlmostEqual(
            state.vol_context["timeout_trailing_stop"],
            100.0 * (1 + RISK.vol_timeout_trailing_buffer_pct),
        )


if __name__ == "__main__":
    unittest.main()
