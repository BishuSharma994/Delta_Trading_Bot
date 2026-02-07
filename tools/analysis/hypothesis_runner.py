"""
V4 — Hypothesis Runner
READ-ONLY | OFFLINE ONLY

Evaluates hypotheses against historical logs.
Outputs descriptive research results only.
"""

import json
from pathlib import Path
from collections import defaultdict

EVENTS_DIR = Path("data/events")
REPORTS_DIR = Path("tools/reports/analysis")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DECISIONS_FILE = EVENTS_DIR / "decision.jsonl"
VOTES_FILE = EVENTS_DIR / "strategy_votes.jsonl"
OUTPUT_FILE = REPORTS_DIR / "hypothesis_results.json"


# -------------------------
# HYPOTHESIS REGISTRY (DESIGN-BOUND)
# -------------------------
HYPOTHESES = {
    "HYP-001": {
        "description": "Funding extreme + volatility compression precedes breakouts",
        "required_features": [
            "funding_rate_abs",
            "pre_volatility_5m",
        ],
        "min_hot_features": 2
    }
}


def load_events(path):
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    decisions = load_events(DECISIONS_FILE)

    results = {}

    for hyp_id, hyp in HYPOTHESES.items():
        tested = 0
        satisfied = 0

        for d in decisions:
            feature_states = d.get("feature_states", {})
            hot_count = sum(
                1 for f in hyp["required_features"]
                if feature_states.get(f) == "hot"
            )

            tested += 1
            if hot_count >= hyp["min_hot_features"]:
                satisfied += 1

        results[hyp_id] = {
            "description": hyp["description"],
            "windows_tested": tested,
            "windows_satisfying_preconditions": satisfied,
            "satisfaction_rate": round(
                satisfied / tested, 6
            ) if tested else 0.0,
            "interpretation": (
                "Rare or absent conditions"
                if satisfied == 0 else
                "Conditions observed (no outcome evaluation)"
            )
        }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print("Hypothesis runner complete.")
    print(f"Results written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
