# Decision analysis
# Explains why trades are rejected
# No strategy changes. No execution.

import json
from collections import Counter
from pathlib import Path

EVENTS_DIR = Path("data/events")


def analyze_rejections(symbol: str = None):
    file = EVENTS_DIR / "decision.jsonl"
    if not file.exists():
        print("No decision log found")
        return

    rejection_counter = Counter()
    total = 0

    with open(file) as f:
        for line in f:
            event = json.loads(line)
            payload = event["payload"]

            if symbol and payload.get("symbol") != symbol:
                continue

            decision = payload.get("decision")
            if not decision:
                continue

            if not decision["allow"]:
                total += 1
                for reason in decision["reasons"]:
                    rejection_counter[reason] += 1

    print("=== DECISION REJECTION ANALYSIS ===")
    print(f"Total rejected decisions: {total}")
    print()

    for reason, count in rejection_counter.most_common():
        pct = (count / total) * 100 if total else 0
        print(f"{reason:40s} {count:5d}  ({pct:6.2f}%)")
