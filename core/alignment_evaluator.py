# =========================
# V5.0 — ALIGNMENT EVALUATOR (SENIOR ANALYST)
# Capital Protection First
# NO EXECUTION
# =========================

import json
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data/events")

STRATEGY_VOTES = DATA_DIR / "strategy_votes.jsonl"
FUNDING_SNAPSHOTS = DATA_DIR / "funding_snapshot.jsonl"
ALIGNMENT_OUT = DATA_DIR / "alignment_state.jsonl"

CONFIDENCE_THRESHOLD = 0.30
MAX_FUNDING_WINDOW_SEC = 3600  # 1 hour pre/post funding


def load_latest_by_symbol(path):
    latest = {}
    if not path.exists():
        return latest

    with path.open() as f:
        for line in f:
            row = json.loads(line)
            latest[row["symbol"]] = row
    return latest


def main():
    now = datetime.now(timezone.utc)

    strategy_votes = load_latest_by_symbol(STRATEGY_VOTES)
    funding_data = load_latest_by_symbol(FUNDING_SNAPSHOTS)

    for symbol, vote in strategy_votes.items():
        alignment = {
            "timestamp_utc": now.isoformat(),
            "symbol": symbol,
            "alignment_state": "ABSTAIN",
            "direction": "NONE",
            "confidence": 0.0,
            "volatility_vote": None,
            "funding_vote": None,
            "time_to_funding_sec": None,
            "reason": "default_abstain",
        }

        vol_vote = vote.get("vote")
        alignment["volatility_vote"] = vol_vote

        funding = funding_data.get(symbol)
        if not funding:
            alignment["reason"] = "no_funding_data"
            write_alignment(alignment)
            continue

        funding_vote = funding.get("funding_bias")
        ttf = funding.get("time_to_funding_sec")

        alignment["funding_vote"] = funding_vote
        alignment["time_to_funding_sec"] = ttf

        if vol_vote != funding_vote:
            alignment["reason"] = "vote_misalignment"
            write_alignment(alignment)
            continue

        if ttf is None or abs(ttf) > MAX_FUNDING_WINDOW_SEC:
            alignment["reason"] = "funding_outside_window"
            write_alignment(alignment)
            continue

        confidence = CONFIDENCE_THRESHOLD
        alignment.update({
            "alignment_state": "ALIGNED",
            "direction": vol_vote,
            "confidence": confidence,
            "reason": "volatility_funding_aligned",
        })

        write_alignment(alignment)


def write_alignment(row):
    with ALIGNMENT_OUT.open("a") as f:
        f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
