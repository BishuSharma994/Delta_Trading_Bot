"""
V4 — Integrated Stress Harness
READ-ONLY | OFFLINE ONLY

Generalized stress testing across:
- Features
- Time
- Symbols

Purpose: falsification, not validation.
"""

import json
import random
from pathlib import Path
from collections import defaultdict

EVENTS_DIR = Path("data/events")
REPORTS_DIR = Path("tools/reports/analysis")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DECISIONS_FILE = EVENTS_DIR / "decision.jsonl"
OUTPUT_FILE = REPORTS_DIR / "integrated_stress_results.json"


def load_decisions(path):
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    decisions = load_decisions(DECISIONS_FILE)
    total_windows = len(decisions)

    results = {
        "feature_removal": {},
        "time_randomization": {},
        "symbol_isolation": {}
    }

    FEATURES = ["funding_rate_abs", "pre_volatility_5m", "time_to_funding_sec"]

    # -------------------------
    # 1. Feature Removal Stress
    # -------------------------
    for removed in FEATURES:
        count = 0
        for d in decisions:
            fs = d.get("feature_states", {})
            active = [f for f in FEATURES if f != removed]
            if all(fs.get(f) == "hot" for f in active):
                count += 1

        results["feature_removal"][removed] = {
            "windows_satisfying": count,
            "frequency": round(count / total_windows, 6) if total_windows else 0.0
        }

    # -------------------------
    # 2. Time Randomization
    # -------------------------
    shuffled = decisions[:]
    random.shuffle(shuffled)

    random_hits = 0
    sample_size = min(1000, total_windows)

    for d in shuffled[:sample_size]:
        fs = d.get("feature_states", {})
        if all(fs.get(f) == "hot" for f in FEATURES):
            random_hits += 1

    results["time_randomization"] = {
        "random_hits": random_hits,
        "sample_size": sample_size
    }

    # -------------------------
    # 3. Symbol Isolation
    # -------------------------
    by_symbol = defaultdict(int)
    for d in decisions:
        fs = d.get("feature_states", {})
        if all(fs.get(f) == "hot" for f in FEATURES):
            by_symbol[d.get("symbol")] += 1

    results["symbol_isolation"] = dict(by_symbol)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print("Integrated stress harness complete.")
    print(f"Results written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
