"""
brain/log_book.py
Stores every detected pattern with full metadata.
Acts as the brain's permanent memory.
Computes win rate, avg outcome, expectancy per pattern type.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)
LOG_DIR = Path(__file__).parent / "data" / "log_book"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def append_patterns(patterns: list, symbol: str, resolution: str) -> Path:
    path = LOG_DIR / f"{symbol}_{resolution}_patterns.jsonl"
    with open(path, "a", encoding="utf-8") as handle:
        for pattern in patterns:
            pattern["logged_at"] = datetime.now(timezone.utc).isoformat()
            handle.write(json.dumps(pattern) + "\n")
    logger.info(f"LogBook: +{len(patterns)} → {path.name}")
    return path


def load_all_patterns(symbol: str, resolution: str) -> list:
    path = LOG_DIR / f"{symbol}_{resolution}_patterns.jsonl"
    if not path.exists():
        return []
    result = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                result.append(json.loads(line))
    return result


def compute_pattern_stats(patterns: list) -> dict:
    grouped = defaultdict(list)
    for pattern in patterns:
        grouped[pattern["pattern"]].append(pattern)

    stats = {}
    for name, items in grouped.items():
        wins = [pattern for pattern in items if pattern["success"]]
        losses = [pattern for pattern in items if not pattern["success"]]
        win_rate = len(wins) / len(items) if items else 0.0
        avg_win = (
            sum(pattern["outcome_pct"] for pattern in wins) / len(wins)
            if wins else 0.0
        )
        avg_loss = (
            sum(pattern["outcome_pct"] for pattern in losses) / len(losses)
            if losses else 0.0
        )
        expectancy = win_rate * avg_win - (1 - win_rate) * abs(avg_loss)
        stats[name] = {
            "pattern": name,
            "count": len(items),
            "win_count": len(wins),
            "win_rate": round(win_rate, 4),
            "avg_win": round(avg_win, 6),
            "avg_loss": round(avg_loss, 6),
            "expectancy": round(expectancy, 6),
        }
    return stats


def save_stats_snapshot(stats: dict, label: str = "latest") -> Path:
    path = LOG_DIR / f"stats_{label}.json"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "stats": stats,
            },
            handle,
            indent=2,
        )
    return path


def load_stats_snapshot(label: str = "latest") -> dict:
    path = LOG_DIR / f"stats_{label}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def print_summary(symbol: str, resolution: str):
    patterns = load_all_patterns(symbol, resolution)
    if not patterns:
        print(f"No patterns: {symbol} {resolution}")
        return
    stats = compute_pattern_stats(patterns)
    print(f"\n{'=' * 58}")
    print(f"LOG BOOK: {symbol} {resolution} ({len(patterns)} patterns)")
    print(f"{'=' * 58}")
    print(f"{'Pattern':<38} {'N':>5} {'WR':>7} {'Expect':>9}")
    print(f"{'-' * 58}")
    for name, stat in sorted(
        stats.items(),
        key=lambda item: -item[1]["expectancy"],
    ):
        print(
            f"{name:<38} {stat['count']:>5} "
            f"{stat['win_rate']:>6.1%} {stat['expectancy']:>+9.4%}"
        )
    print(f"{'=' * 58}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    from brain.data_collector import ALL_SYMBOLS, RESOLUTIONS

    for symbol in ALL_SYMBOLS:
        for resolution in RESOLUTIONS:
            print_summary(symbol, resolution)
