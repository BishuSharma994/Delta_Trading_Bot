"""
V2.5 Gate Stress Test Runner
OFFLINE ONLY — REPO-ALIGNED
"""

import json
import copy
from typing import Dict, List
from pathlib import Path

from tools.replay.replay_runner import run_replay
from tools.replay.loaders import (
    load_votes,
    load_confluence,
    load_persistence,
)

REPORTS_DIR = Path("tools/reports")


class GateStressRunner:
    def __init__(self):
        self.votes = load_votes("data/events/strategy_votes.jsonl")
        self.confluence = load_confluence("tools/reports/confluence_events.json")
        self.persistence = load_persistence("tools/reports/persistence_report.json")

        with open("config/execution_gate.yaml", "r") as f:
            self.base_gate_config = json.loads(
                json.dumps(__import__("yaml").safe_load(f))
            )

    def _inject_param(
        self, gate_config: Dict, param_path: List[str], value
    ) -> Dict:
        cfg = copy.deepcopy(gate_config)
        ref = cfg
        for key in param_path[:-1]:
            ref = ref[key]
        ref[param_path[-1]] = value
        return cfg

    def run_single_param_sweep(
        self,
        param_path: List[str],
        sweep_values: List,
        label: str,
    ):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        for value in sweep_values:
            gate_cfg = self._inject_param(
                self.base_gate_config, param_path, value
            )

            summary = run_replay(
                votes=self.votes,
                confluence_events=self.confluence,
                persistence_report=self.persistence,
                gate_config=gate_cfg,
            )

            out_path = REPORTS_DIR / f"gate_stress_{label}_{value}.json"
            with out_path.open("w") as f:
                json.dump(
                    {
                        "parameter": ".".join(param_path),
                        "value": value,
                        "summary": summary,
                    },
                    f,
                    indent=2,
                )
