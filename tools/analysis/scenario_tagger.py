"""
V4 — Scenario Tagger
READ-ONLY | OFFLINE ONLY

Labels historical windows with descriptive market scenarios.
No signals. No execution. No thresholds.
"""

import json
from pathlib import Path
from collections import defaultdict

EVENTS_DIR = Path("data/events")
REPORTS_DIR = Path("tools/reports/analysis")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DECISIONS_FILE = EVENTS_DIR / "decision.jsonl"
OUTPUT_FILE = REPORTS_DIR / "scenario_labels.json"

# -------------------------
# SCENARIO DEFINITIONS (DESIGN-BOUND)
# -------------------------
SCENARIOS = {
    "VOLATILITY_COMPRESSION": {
        "required_features": ["pre_volatility_5m"],
    },
    "FUNDING_EXTREME": {
        "required_features": ["funding_rate_abs"],
    },
    "FUNDING_AND_VOL_COMPRESSION": {
        "required_features": ["funding_rate_abs", "pre_volatility_5m"],
    },
}


def load_events(path):
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    decisions = load_events(DECISIONS_FILE)

    labeled_windows = []
    scenario_counts = defaultdict(int)

    for d in decisions:
        symbol = d.get("symbol")
        ts = d.get("timestamp_utc")
        feature_states = d.get("feature_states", {})

        window_scenarios = []

        for name, spec in SCENARIOS.items():
            if all(feature_states.get(f) == "hot" for f in spec["required_features"]):
                window_scenarios.append(name)
                scenario_counts[name] += 1

        labeled_windows.append({
            "timestamp_utc": ts,
            "symbol": symbol,
            "scenarios": window_scenarios
        })

    report = {
        "total_windows": len(labeled_windows),
        "scenario_frequencies": dict(scenario_counts),
        "labels": labeled_windows
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print("Scenario tagging complete.")
    print(f"Results written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
