"""
V3.x — Abstention Analysis
READ-ONLY | OFFLINE ONLY

Measures abstention discipline per symbol and strategy.
"""

import json
from collections import defaultdict
from pathlib import Path

EVENTS_DIR = Path("data/events")
REPORTS_DIR = Path("tools/reports/analysis")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

VOTES_FILE = EVENTS_DIR / "strategy_votes.jsonl"
OUTPUT_FILE = REPORTS_DIR / "abstention_report.json"


def main():
    totals = defaultdict(int)
    non_neutral = defaultdict(int)
    by_strategy = defaultdict(lambda: defaultdict(int))

    if not VOTES_FILE.exists():
        raise FileNotFoundError("strategy_votes.jsonl not found")

    with open(VOTES_FILE, "r") as f:
        for line in f:
            if not line.strip():
                continue

            event = json.loads(line)
            symbol = event.get("symbol")
            strategy = event.get("strategy")
            vote = event.get("vote", {})

            bias = vote.get("bias", 0)

            totals[symbol] += 1
            by_strategy[(symbol, strategy)]["total"] += 1

            if bias != 0:
                non_neutral[symbol] += 1
                by_strategy[(symbol, strategy)]["non_neutral"] += 1

    report = {
        "summary": {},
        "by_symbol_strategy": {}
    }

    for symbol in totals:
        abstention_rate = 1.0
        if totals[symbol] > 0:
            abstention_rate = 1 - (non_neutral[symbol] / totals[symbol])

        report["summary"][symbol] = {
            "total_votes": totals[symbol],
            "non_neutral_votes": non_neutral[symbol],
            "abstention_rate": round(abstention_rate, 6)
        }

    for (symbol, strategy), stats in by_strategy.items():
        total = stats.get("total", 0)
        nn = stats.get("non_neutral", 0)
        abst = 1.0 if total == 0 else 1 - (nn / total)

        report["by_symbol_strategy"].setdefault(symbol, {})[strategy] = {
            "total_votes": total,
            "non_neutral_votes": nn,
            "abstention_rate": round(abst, 6)
        }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print("Abstention analysis complete.")
    print(f"Report written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
