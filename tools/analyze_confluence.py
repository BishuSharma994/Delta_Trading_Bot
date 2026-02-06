# tools/analyze_confluence.py
# Offline confluence analysis across strategy votes
# Read-only. No execution.

import json
from collections import defaultdict
from pathlib import Path

EVENT_FILE = Path("data/events/strategy_votes.jsonl")
REPORT_DIR = Path("tools/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# minimum number of agreeing strategies
MIN_STRATEGIES = 2


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


def group_by_timestamp(votes):
    grouped = defaultdict(list)
    for v in votes:
        ts = v.get("timestamp_utc")
        if ts:
            grouped[ts].append(v)
    return grouped


def analyze_confluence(grouped_votes):
    confluences = []

    for ts, events in grouped_votes.items():
        by_symbol = defaultdict(list)

        for e in events:
            symbol = e.get("symbol")
            vote = e.get("vote", {})
            bias = vote.get("bias", 0)

            if bias != 0:
                by_symbol[symbol].append({
                    "strategy": e.get("strategy"),
                    "bias": bias,
                    "confidence": vote.get("confidence", 0.0)
                })

        for symbol, votes in by_symbol.items():
            if len(votes) < MIN_STRATEGIES:
                continue

            biases = {v["bias"] for v in votes}
            if len(biases) == 1:
                confluences.append({
                    "timestamp_utc": ts,
                    "symbol": symbol,
                    "bias": biases.pop(),
                    "strategies": votes
                })

    return confluences


def summarize(confluences):
    summary = defaultdict(int)
    for c in confluences:
        key = f"{c['symbol']}_{c['bias']}"
        summary[key] += 1
    return dict(summary)


def main():
    votes = load_votes()
    grouped = group_by_timestamp(votes)
    confluences = analyze_confluence(grouped)
    summary = summarize(confluences)

    out_file = REPORT_DIR / "confluence_events.json"
    with out_file.open("w") as f:
        json.dump(confluences, f, indent=2)

    print("Confluence analysis complete")
    print(f"Total vote events: {len(votes)}")
    print(f"Total confluence events: {len(confluences)}")
    print(f"Report written to: {out_file}")

    print("\nSummary:")
    for k, v in summary.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
