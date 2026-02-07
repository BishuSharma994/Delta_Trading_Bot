"""
V4 — Hypothesis Stress Tester
READ-ONLY | OFFLINE ONLY

Stress-tests HYP-001 for robustness.
"""

import json
import random
from pathlib import Path
from collections import defaultdict

EVENTS_DIR = Path("data/events")
REPORTS_DIR = Path("tools/reports/analysis")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DECISIONS_FILE = EVENTS_DIR / "decision.jsonl"
OUTPUT_FILE = REPORTS_DIR / "hypothesis_stress_HYP_001.json"

FEATURES = ["funding_rate_abs", "pre_volatility_5m"]


def load_events(path):
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    decisions = load_events(DECISIONS_FILE)
    total = len(decisions)

    stress_results = {}

    # 1. Feature removal stress
    for removed in FEATURES:
        satisfied = 0
        for d in decisions:
            fs = d.get("feature_states", {})
            active = [f for f in FEATURES if f != removed]
            if all(fs.get(f) == "hot" for f in active):
                satisfied += 1

        stress_results[f"remove_{removed}"] = {
            "windows_satisfying": satisfied,
            "frequency": round(satisfied / total, 6) if total else 0.0
        }

    # 2. Random baseline stress
    random_hits = 0
    sample = random.sample(decisions, min(1000, total))
    for d in sample:
        fs = d.get("feature_states", {})
        if random.random() < 0.01:
            if all(fs.get(f) == "hot" for f in FEATURES):
                random_hits += 1

    stress_results["random_baseline"] = {
        "random_hits": random_hits,
        "sample_size": len(sample)
    }

    # 3. Symbol isolation
    by_symbol = defaultdict(int)
    for d in decisions:
        fs = d.get("feature_states", {})
        if all(fs.get(f) == "hot" for f in FEATURES):
            by_symbol[d.get("symbol")] += 1

    stress_results["symbol_isolation"] = dict(by_symbol)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(stress_results, f, indent=2)

    print("Stress test complete.")
    print(f"Results written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
