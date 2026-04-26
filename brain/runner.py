"""
brain/runner.py
Master pipeline — runs the entire brain in one command.

Steps:
    1. Collect historical OHLCV data (skip if cached)
    2. Detect statistical patterns on all symbols + resolutions
    3. Log patterns to log book
    4. Load full pattern history
    5. Run drift monitor
    6. Print summary + recommendations

Usage:
    python -m brain.runner             # use cached data
    python -m brain.runner --refresh   # force fresh data from API
"""

import logging
import sys
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SYMBOLS = [
    "BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD",
    "GOOGLXUSD", "METAXUSD", "AAPLXUSD", "AMZNXUSD",
    "TSLAXUSD", "NVDAXUSD", "COINXUSD", "CRCLXUSD",
    "QQQXUSD", "SPYXUSD",
]
RESOLUTIONS = ["15m", "1h"]


def run(force_refresh: bool = False):
    from brain.data_collector import collect_all
    from brain.drift_monitor import run_drift_check
    from brain.log_book import (
        append_patterns,
        compute_pattern_stats,
        load_all_patterns,
        print_summary,
        save_stats_snapshot,
    )
    from brain.pattern_detector import run_all_detectors

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n{'=' * 60}")
    print(f"  BRAIN PIPELINE  —  {now_str}")
    print(f"{'=' * 60}")

    # Step 1 — data
    print("\n[1/4] Collecting historical data...")
    data = collect_all(force_refresh=force_refresh)
    total_candles = sum(len(value) for value in data.values())
    print(
        f"      {total_candles:,} candles across "
        f"{len(data)} symbol/resolution pairs"
    )

    # Step 2+3 — detect + log
    print("\n[2/4] Detecting patterns...")
    new_patterns = []
    for key, candles in data.items():
        if not candles:
            continue
        symbol, resolution = key.rsplit("_", 1)
        patterns = run_all_detectors(candles, symbol, resolution)
        if patterns:
            append_patterns(patterns, symbol, resolution)
            new_patterns.extend(patterns)
    print(f"      {len(new_patterns):,} new patterns detected and logged")

    # Step 4 — load all history
    print("\n[3/4] Loading full pattern history...")
    all_patterns = []
    for symbol in SYMBOLS:
        for resolution in RESOLUTIONS:
            all_patterns.extend(load_all_patterns(symbol, resolution))
    print(f"      {len(all_patterns):,} total patterns in log book")

    if all_patterns:
        stats = {}
        for symbol in SYMBOLS:
            for resolution in RESOLUTIONS:
                key = f"{symbol}_{resolution}"
                patterns = [
                    pattern
                    for pattern in all_patterns
                    if pattern["symbol"] == symbol
                    and pattern["resolution"] == resolution
                ]
                if patterns:
                    stats[key] = compute_pattern_stats(patterns)
        save_stats_snapshot(stats)

    # Step 5 — drift
    print("\n[4/4] Running drift monitor...")
    staging = run_drift_check(all_patterns)
    changes = staging.get("_changes", [])

    # Summary
    print(f"\n{'=' * 60}")
    print("  BRAIN PIPELINE COMPLETE")
    print(f"{'=' * 60}")

    if changes:
        print(f"\n  ⚠  {len(changes)} parameter change(s) recommended:")
        for change in changes:
            print(
                f"     {change['param']:<35} "
                f"{change['old_val']} → {change['new_val']}"
            )
            print(f"     Reason: {change['reason']}")
        print("\n  Review : python -m brain.config_writer")
        print("  Apply  : python -m brain.config_writer --approve")
    else:
        print("\n  ✅  All patterns stable — no changes recommended")

    print("\n  Log book : brain/data/log_book/")
    print("  Staging  : brain/data/staging/risk_staging.json\n")

    for symbol in SYMBOLS[:4]:
        print_summary(symbol, "1h")

    return staging


if __name__ == "__main__":
    run(force_refresh="--refresh" in sys.argv)
