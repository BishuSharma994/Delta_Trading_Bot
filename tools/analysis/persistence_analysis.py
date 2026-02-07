"""
V3.x — Persistence & Confluence Analysis
READ-ONLY | OFFLINE ONLY

Measures:
- Consecutive non-neutral vote streaks (persistence)
- Cross-strategy agreement per symbol
"""

import json
from collections import defaultdict
from pathlib import Path

EVENTS_DIR = Path("data/events")
REPORTS_DIR = Path("tools/reports/analysis")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

VOTES_FILE = EVENTS_DIR / "strategy_votes.jsonl"
OUTPUT_FILE = REPORTS_DIR / "persistence_report.json"


def main():
    if not VOTES_FILE.exists():
        raise FileNotFoundError("strategy_votes.jsonl not found")

    # Data structures
    streaks = defaultdict(list)          # symbol -> list of streak lengths
    agreement = defaultdict(int)          # symbol -> count
    total_windows = defaultdict(int)      # symbol -> count

    # Organize votes by timestamp and symbol
    events = []
    with open(VOTES_FILE, "r") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    events.sort(key=lambda e: (e["timestamp_utc"], e["symbol"]))

    current_streak = defaultdict(int)

    for event in events:
        symbol = event["symbol"]
        bias = event.get("vote", {}).get("bias", 0)

        if bias != 0:
            current_streak[symbol] += 1
        else:
            if current_streak[symbol] > 0:
                streaks[symbol].append(current_streak[symbol])
            current_streak[symbol] = 0

    # Capture any trailing streaks
    for symbol, length in current_streak.items():
        if length > 0:
            streaks[symbol].append(length)

    # Cross-strategy agreement
    window = defaultdict(lambda: defaultdict(list))

    for event in events:
        ts = event["timestamp_utc"]
        symbol = event["symbol"]
        strategy = event["strategy"]
        bias = event.get("vote", {}).get("bias", 0)

        window[(ts, symbol)][strategy].append(bias)

    for (ts, symbol), votes in window.items():
        total_windows[symbol] += 1
        non_zero = [b for v in votes.values() for b in v if b != 0]
        if non_zero and len(set(non_zero)) == 1:
            agreement[symbol] += 1

    # Build report
    report = {}

    for symbol in set(list(streaks.keys()) + list(total_windows.keys())):
        report[symbol] = {
            "max_consecutive_non_neutral": max(streaks[symbol]) if streaks[symbol] else 0,
            "average_streak_length": round(
                sum(streaks[symbol]) / len(streaks[symbol]), 6
            ) if streaks[symbol] else 0.0,
            "total_non_neutral_streaks": len(streaks[symbol]),
            "agreement_windows": agreement.get(symbol, 0),
            "total_windows": total_windows.get(symbol, 0),
            "agreement_rate": round(
                agreement.get(symbol, 0) / total_windows.get(symbol, 1), 6
            ),
        }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print("Persistence analysis complete.")
    print(f"Report written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
