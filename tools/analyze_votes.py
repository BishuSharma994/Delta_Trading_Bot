# tools/analyze_votes.py
# Offline analysis of strategy voting behavior
# Read-only. No API calls. No execution.

import json
from collections import defaultdict
from statistics import mean
from pathlib import Path

EVENT_FILE = Path("data/events/strategy_votes.jsonl")
REPORT_DIR = Path("tools/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_votes():
    votes = []
    if not EVENT_FILE.exists():
        raise FileNotFoundError(f"{EVENT_FILE} not found")

    with EVENT_FILE.open() as f:
        for line in f:
            try:
                votes.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return votes


def analyze_votes(votes):
    stats = defaultdict(lambda: {
        "total": 0,
        "non_neutral": 0,
        "abstain": 0,
        "bias_counts": defaultdict(int),
        "confidence_values": []
    })

    for v in votes:
        strategy = v.get("strategy")
        vote = v.get("vote", {})

        if not strategy or not vote:
            continue

        bias = vote.get("bias", 0)
        confidence = vote.get("confidence", 0.0)

        s = stats[strategy]
        s["total"] += 1
        s["bias_counts"][bias] += 1

        if bias == 0:
            s["abstain"] += 1
        else:
            s["non_neutral"] += 1
            if isinstance(confidence, (int, float)):
                s["confidence_values"].append(confidence)

    return stats


def build_report(stats):
    report = {}

    for strategy, s in stats.items():
        total = s["total"]
        if total == 0:
            continue

        report[strategy] = {
            "total_votes": total,
            "abstain_rate_pct": round(100 * s["abstain"] / total, 2),
            "non_neutral_rate_pct": round(100 * s["non_neutral"] / total, 2),
            "bias_distribution": dict(s["bias_counts"]),
            "avg_confidence": round(mean(s["confidence_values"]), 4)
            if s["confidence_values"] else 0.0
        }

    return report


def main():
    votes = load_votes()
    stats = analyze_votes(votes)
    report = build_report(stats)

    out_file = REPORT_DIR / "vote_distribution.json"
    with out_file.open("w") as f:
        json.dump(report, f, indent=2)

    print("Vote analysis complete")
    print(f"Total vote events: {len(votes)}")
    print(f"Report written to: {out_file}")

    for strategy, r in report.items():
        print("\n---", strategy, "---")
        for k, v in r.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
