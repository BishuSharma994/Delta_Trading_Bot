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

CONFIDENCE_THRESHOLD = 0.65
MAX_FUNDING_WINDOW_SEC = 900  # 15 minute window


def load_latest_by_symbol(path):
    latest = {}
    if not path.exists():
        return latest

    with path.open() as f:
        for line in f:
            row = json.loads(line)
            latest[row["symbol"]] = row
    return latest


def _extract_direction(v):
    return v if v in ("LONG", "SHORT") else None


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

            # -------- EVIDENCE (LOCKED V4 ARTIFACTS) --------
            # These MUST come from V4.
            # If missing, validator will DENY (correct behavior).
            "evidence": {
                "hypothesis_id": vote.get("hypothesis_id"),
                "rarity_index": vote.get("rarity_index"),
                "scenario_concurrence": vote.get("scenario_concurrence"),
                "confidence_calibration": vote.get("confidence_calibration"),
            },
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

        vol_confidence = float(vote.get("confidence", 0.0)) if isinstance(vote.get("confidence"), (int, float)) else 0.0
        funding_confidence = min(float(funding.get("funding_rate_abs", 0.0)) * 25, 0.60)
        computed_confidence = round((vol_confidence + funding_confidence) / 2, 4)

        if computed_confidence < 0.50:
            alignment["reason"] = "confidence_below_threshold"
            write_alignment(alignment)
            continue

        vol_direction = _extract_direction(vol_vote)
        funding_direction = _extract_direction(funding_vote)
        if vol_direction is None or funding_direction is None or vol_direction != funding_direction:
            alignment["reason"] = "vote_misalignment"
            write_alignment(alignment)
            continue

        if ttf is None or abs(ttf) > MAX_FUNDING_WINDOW_SEC:
            alignment["reason"] = "funding_outside_window"
            write_alignment(alignment)
            continue

        alignment.update({
            "alignment_state": "ALIGNED",
            "direction": vol_direction,
            "confidence": computed_confidence,
            "reason": "volatility_funding_aligned",
        })

        write_alignment(alignment)


def write_alignment(row):
    with ALIGNMENT_OUT.open("a") as f:
        f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
