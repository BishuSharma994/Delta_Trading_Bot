"""
V4 — Confidence Calibration Engine
READ-ONLY | OFFLINE ONLY

Measures confidence behavior vs. realized outcomes in a descriptive manner.
- No signals
- No thresholds for execution
- No optimization
"""

import json
from pathlib import Path
from collections import defaultdict

EVENTS_DIR = Path("data/events")
REPORTS_DIR = Path("tools/reports/analysis")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

VOTES_FILE = EVENTS_DIR / "strategy_votes.jsonl"
DECISIONS_FILE = EVENTS_DIR / "decision.jsonl"
OUTPUT_FILE = REPORTS_DIR / "confidence_calibration.json"


def load_events(path):
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    votes = load_events(VOTES_FILE)
    decisions = load_events(DECISIONS_FILE)

    # Index decisions by (timestamp, symbol)
    decision_index = {
        (d.get("timestamp_utc"), d.get("symbol")): d for d in decisions
    }

    # Aggregates
    confidence_bins = defaultdict(list)  # bin -> list of outcomes
    per_strategy = defaultdict(lambda: defaultdict(list))

    for v in votes:
        ts = v.get("timestamp_utc")
        symbol = v.get("symbol")
        strategy = v.get("strategy")
        vote = v.get("vote", {})
        conf = vote.get("confidence", 0.0)
        bias = vote.get("bias", 0)

        # Bin confidence (descriptive)
        bin_key = round(conf, 2)

        d = decision_index.get((ts, symbol))
        outcome_state = None
        if d:
            outcome_state = d.get("decision", {}).get("state")

        record = {
            "bias": bias,
            "outcome_state": outcome_state
        }

        confidence_bins[bin_key].append(record)
        per_strategy[strategy][bin_key].append(record)

    # Build report
    report = {
        "overall": {},
        "by_strategy": {}
    }

    for bin_key, records in confidence_bins.items():
        total = len(records)
        non_neutral = sum(1 for r in records if r["bias"] != 0)

        report["overall"][str(bin_key)] = {
            "total_votes": total,
            "non_neutral_votes": non_neutral,
            "non_neutral_rate": round(non_neutral / total, 6) if total else 0.0
        }

    for strategy, bins in per_strategy.items():
        report["by_strategy"][strategy] = {}
        for bin_key, records in bins.items():
            total = len(records)
            non_neutral = sum(1 for r in records if r["bias"] != 0)

            report["by_strategy"][strategy][str(bin_key)] = {
                "total_votes": total,
                "non_neutral_votes": non_neutral,
                "non_neutral_rate": round(non_neutral / total, 6) if total else 0.0
            }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print("Confidence calibration complete.")
    print(f"Results written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
