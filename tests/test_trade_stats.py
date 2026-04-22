import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trade_stats import (
    ClosedTrade,
    build_equity_curve,
    crypto_vs_xstock,
    pair_trades,
    render_weekly,
)


class TradeStatsTests(unittest.TestCase):
    def test_pair_trades_handles_short_returns_and_schema_drift(self):
        events = [
            {
                "symbol": "TESTUSD",
                "action": "ENTRY",
                "trade_type": "VOL",
                "price": 100.0,
                "reason": "old_schema_missing_side",
                "timestamp_utc": "2026-04-01T00:00:00+00:00",
            },
            {
                "symbol": "BTCUSD",
                "action": "ENTRY",
                "trade_type": "VOL",
                "side": "SHORT",
                "price": 100.0,
                "reason": "short_entry",
                "timestamp_utc": "2026-04-01T00:01:00+00:00",
            },
            {
                "symbol": "BTCUSD",
                "action": "EXIT",
                "trade_type": "VOL",
                "side": "SHORT",
                "price": 95.0,
                "reason": "take_profit",
                "timestamp_utc": "2026-04-01T00:06:00+00:00",
            },
            {
                "symbol": "ETHUSD",
                "action": "ENTRY",
                "trade_type": "VOL",
                "side": "LONG",
                "price": 200.0,
                "reason": "long_entry",
                "timestamp_utc": "2026-04-01T01:00:00+00:00",
            },
            {
                "symbol": "ETHUSD",
                "action": "EXIT",
                "trade_type": "VOL",
                "side": "LONG",
                "price": 210.0,
                "reason": "take_profit",
                "timestamp_utc": "2026-04-01T01:10:00+00:00",
            },
            {
                "symbol": "SOLUSD",
                "action": "EXIT",
                "trade_type": "FUNDING",
                "side": "SHORT",
                "price": 80.0,
                "reason": "orphan_exit",
                "timestamp_utc": "2026-04-01T02:00:00+00:00",
            },
        ]

        closed, open_trades, skipped_rows, reject_counts = pair_trades(events)

        self.assertEqual(len(closed), 2)
        self.assertEqual(len(open_trades), 0)
        self.assertEqual(skipped_rows, 2)
        self.assertEqual(sum(reject_counts.values()), 0)
        self.assertAlmostEqual(closed[0].return_pct, 0.05)
        self.assertAlmostEqual(closed[1].return_pct, 0.05)

def _make_trade(symbol, side, return_pct, exit_ts, exit_reason="take_profit", trade_type="VOL"):
    entry_price = 100.0
    if side == "LONG":
        exit_price = entry_price * (1 + return_pct)
    else:
        exit_price = entry_price * (1 - return_pct)
    return ClosedTrade(
        symbol=symbol, trade_type=trade_type, side=side,
        entry_reason="entry", exit_reason=exit_reason,
        entry_price=entry_price, exit_price=exit_price,
        entry_ts="2026-04-01T00:00:00+00:00", exit_ts=exit_ts,
        return_pct=return_pct, duration_min=10.0,
    )


class EquityCurveTests(unittest.TestCase):
    def test_equity_curve_tracks_drawdown(self):
        trades = [
            _make_trade("BTCUSD", "LONG", 0.05, "2026-04-01T00:00:00+00:00"),
            _make_trade("ETHUSD", "LONG", 0.05, "2026-04-02T00:00:00+00:00"),
            _make_trade("SOLUSD", "LONG", -0.08, "2026-04-03T00:00:00+00:00"),
        ]

        points = build_equity_curve(trades)

        self.assertEqual(len(points), 3)
        self.assertEqual(points[0]["drawdown_pct"], 0.0)
        self.assertEqual(points[1]["drawdown_pct"], 0.0)
        self.assertGreater(points[2]["drawdown_pct"], 0)

    def test_equity_curve_sorted_by_exit_ts(self):
        trades = [
            _make_trade("BTCUSD", "LONG", 0.01, "2026-04-03T00:00:00+00:00"),
            _make_trade("ETHUSD", "LONG", 0.01, "2026-04-01T00:00:00+00:00"),
            _make_trade("SOLUSD", "LONG", 0.01, "2026-04-02T00:00:00+00:00"),
        ]

        points = build_equity_curve(trades)

        self.assertEqual(
            [point["exit_ts"] for point in points],
            [
                "2026-04-01T00:00:00+00:00",
                "2026-04-02T00:00:00+00:00",
                "2026-04-03T00:00:00+00:00",
            ],
        )

    def test_crypto_vs_xstock_split(self):
        trades = [
            _make_trade("BTCUSD", "LONG", 0.05, "2026-04-01T00:00:00+00:00"),
            _make_trade("BTCUSD", "LONG", 0.05, "2026-04-02T00:00:00+00:00"),
            _make_trade("GOOGLXUSD", "LONG", -0.03, "2026-04-03T00:00:00+00:00"),
            _make_trade("GOOGLXUSD", "LONG", -0.03, "2026-04-04T00:00:00+00:00"),
        ]

        result = crypto_vs_xstock(trades)

        self.assertEqual(result["crypto"]["count"], 2)
        self.assertEqual(result["xstock"]["count"], 2)
        self.assertGreater(result["crypto"]["avg_bps"], 0)
        self.assertLess(result["xstock"]["avg_bps"], 0)

    def test_weekly_filters_by_date(self):
        trades = [
            _make_trade("BTCUSD", "LONG", 0.05, "2026-04-18T00:00:00+00:00"),
            _make_trade("ETHUSD", "LONG", 0.02, "2026-04-21T00:00:00+00:00"),
            _make_trade("SOLUSD", "SHORT", 0.01, "2026-04-22T00:00:00+00:00"),
        ]
        week_start = datetime(2026, 4, 20, 0, 0, 0, tzinfo=timezone.utc)

        report = render_weekly(trades, week_start)

        self.assertIn("Closed trades: 2", report)


if __name__ == "__main__":
    unittest.main()
