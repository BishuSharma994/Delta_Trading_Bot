# tools/analyze_persistence.py
# Offline temporal persistence analysis of strategy votes
# Read-only. No execution.

import json
from collections import defaultdict
from pathlib import Path

EVENT_FILE = Path("data/events/strategy_votes.jsonl")
REPORT_DIR = Path("tools/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

MIN_STREAK = 2  # consecutive non-neutral votes required


def load_votes():
    if not EVENT_FILE.exists():
        raise FileNotFoundError(f"{EVENT_FILE} not found")

    votes = []
    with EVENT_FILE.open() as f:
        for line in f:
            try:
                votes.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return votes


def analyze_persistence(votes):
    # key: (strategy, symbol)
    streams = defaultdict(list)

    for v in votes:
        strategy = v.get("strategy")
        symbol = v.get("symbol")
        vote = v.get("vote", {})
        bias = vote.get("bias", 0)

        if strategy and symbol:
            streams[(strategy, symbol)].append(bias)

    results = {}

    for key, biases in streams.items():
        longest = 0
        current = 0
        streaks = []

        for b in biases:
            if b != 0:
                current += 1
                longest = max(longest, current)
            else:
                if current >= MIN_STREAK:
                    streaks.append(current)
                current = 0

        if current >= MIN_STREAK:
            streaks.append(current)

        results[f"{key[0]}::{key[1]}"] = {
            "total_votes": len(biases),
            "longest_streak": longest,
            "streaks_detected": streaks,
            "num_persistent_events": len(streaks)
        }

    return results


def main():
    votes = load_votes()
    results = analyze_persistence(votes)

    out_file = REPORT_DIR / "persistence_report.json"
    with out_file.open("w") as f:
        json.dump(results, f, indent=2)

    print("Persistence analysis complete")
    print(f"Strategies analyzed: {len(results)}")
    print(f"Report written to: {out_file}")

    for k, v in results.items():
        if v["longest_streak"] > 0:
            print("\n---", k, "---")
            for m, val in v.items():
                print(f"{m}: {val}")


if __name__ == "__main__":
    main()
