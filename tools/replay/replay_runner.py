import json
from typing import Dict, Any, List

from tools.replay.loaders import load_votes, load_confluence, load_persistence
from tools.replay.state import VirtualState
from tools.replay.timeutils import within_window
from tools.replay.gate_evaluator import evaluate_gate


def run_replay(
    votes: List[Dict[str, Any]],
    confluence_events: List[Dict[str, Any]],
    persistence_report: Dict[str, Any],
    gate_config: Dict[str, Any],
) -> Dict[str, Any]:

    decisions: List[Dict[str, Any]] = []
    allows: List[Dict[str, Any]] = []
    denys: List[Dict[str, Any]] = []

    virtual_state: VirtualState = {
        "open_position": False,
        "last_allow_ts": None,
        "cooldown_remaining_sec": 0,
    }

    window = gate_config["requirements"]["confluence"]["window_seconds"]

    for v in votes:
        ts = v["timestamp_utc"]
        symbol = v["symbol"]

        window_votes = within_window(ts, votes, window)

        inputs = {
            "timestamp_utc": ts,
            "symbol": symbol,
            "confluence": {},
            "persistence": persistence_report,
            "votes": window_votes,
            "virtual_state": virtual_state,
        }

        decision = evaluate_gate(inputs, gate_config)
        decisions.append(decision)

        if decision["state"] == gate_config["outputs"]["allow_state"]:
            allows.append(decision)
            virtual_state["last_allow_ts"] = ts
            virtual_state["cooldown_remaining_sec"] = gate_config["safety"]["cooldown_seconds"]
        else:
            denys.append(decision)

    return {
        "total_events": len(votes),
        "allow_count": len(allows),
        "deny_count": len(denys),
        "first_allow_ts": allows[0]["timestamp_utc"] if allows else None,
    }


def main():
    with open("config/execution_gate.yaml", "r") as f:
        gate_config = json.loads(json.dumps(__import__("yaml").safe_load(f)))

    votes = load_votes("data/events/strategy_votes.jsonl")
    confluence = load_confluence("tools/reports/confluence_events.json")
    persistence = load_persistence("tools/reports/persistence_report.json")

    summary = run_replay(votes, confluence, persistence, gate_config)

    with open("tools/reports/gate_summary.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
