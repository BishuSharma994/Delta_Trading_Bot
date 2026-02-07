"""
V3.x — Rarity Index Analysis
READ-ONLY | OFFLINE ONLY

Defines rarity as inverse frequency of 'eligible' windows:
- All required features are hot
- At least one non-neutral strategy vote exists in the window

No thresholds. No decisions. Pure measurement.
"""

import json
from collections import defaultdict
from pathlib import Path

EVENTS_DIR = Path("data/events")
REPORTS_DIR = Path("tools/reports/analysis")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DECISIONS_FILE = EVENTS_DIR / "decision.jsonl"
VOTES_FILE = EVENTS_DIR / "strategy_votes.jsonl"
OUTPUT_FILE = REPORTS_DIR / "rarity_index.json"

REQUIRED_FEATURES = [
    "funding_rate_abs",
    "time_to_funding_sec",
    "pre_volatility_5m",
]


def load_events(path):
    events = []
    if not path.exists():
        return events
    with open(path, "r") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def main():
    decisions = load_events(DECISIONS_FILE)
    votes = load_events(VOTES_FILE)

    # Index votes by (timestamp, symbol)
    votes_by_window = defaultdict(list)
    for v in votes:
        key = (v.get("timestamp_utc"), v.get("symbol"))
        votes_by_window[key].append(v)

    totals = defaultdict(int)
    eligible = defaultdict(int)

    for d in decisions:
        symbol = d.get("symbol")
        ts = d.get("timestamp_utc")
        feature_states = d.get("feature_states", {})

        totals[symbol] += 1

        # Check feature readiness
        if not all(feature_states.get(f) == "hot" for f in REQUIRED_FEATURES):
            continue

        # Check for any non-neutral vote in this window
        window_votes = votes_by_window.get((ts, symbol), [])
        has_non_neutral = any(
            v.get("vote", {}).get("bias", 0) != 0 for v in window_votes
        )

        if has_non_neutral:
            eligible[symbol] += 1

    report = {}
    for symbol in totals:
        freq = eligible[symbol] / totals[symbol] if totals[symbol] else 0.0
        rarity = float("inf") if freq == 0 else round(1 / freq, 6)

        report[symbol] = {
            "total_windows": totals[symbol],
            "eligible_windows": eligible[symbol],
            "eligibility_frequency": round(freq, 6),
            "rarity_index": rarity,
        }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print("Rarity analysis complete.")
    print(f"Report written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
