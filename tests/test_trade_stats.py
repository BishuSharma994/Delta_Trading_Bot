import unittest

from trade_stats import pair_trades


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

        closed, open_trades, skipped_rows = pair_trades(events)

        self.assertEqual(len(closed), 2)
        self.assertEqual(len(open_trades), 0)
        self.assertEqual(skipped_rows, 2)
        self.assertAlmostEqual(closed[0].return_pct, 0.05)
        self.assertAlmostEqual(closed[1].return_pct, 0.05)


if __name__ == "__main__":
    unittest.main()
