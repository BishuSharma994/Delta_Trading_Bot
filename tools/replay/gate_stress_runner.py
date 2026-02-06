"""
V2.5 Gate Stress Test Runner
OFFLINE ONLY
"""

from typing import Dict, List
from pathlib import Path
import json
import copy

from tools.replay.replay_runner import run_replay
from tools.replay.gate_evaluator import GateEvaluator
from tools.replay.loaders import (
    load_replay_config,
    load_market_data,
    load_execution_gate_config,
)

REPORTS_DIR = Path("tools/reports")


class GateStressRunner:
    def __init__(self, replay_config_path: str):
        self.replay_config = load_replay_config(replay_config_path)
        self.market_data = load_market_data(self.replay_config)
        self.base_gate_config = load_execution_gate_config(
            "config/execution_gate.yaml"
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

            evaluator = GateEvaluator(gate_cfg)

            gate_events = run_replay(
                market_data=self.market_data,
                replay_config=self.replay_config,
                gate_evaluator=evaluator,
            )

            summary = self._summarize(gate_events)

            report_path = REPORTS_DIR / f"gate_stress_{label}_{value}.json"
            with report_path.open("w") as f:
                json.dump(
                    {
                        "parameter": ".".join(param_path),
                        "value": value,
                        "summary": summary,
                    },
                    f,
                    indent=2,
                )

    @staticmethod
    def _summarize(gate_events: List[Dict]) -> Dict:
        counts = {"ALLOW": 0, "BLOCK": 0}
        for evt in gate_events:
            decision = evt.get("decision")
            if decision in counts:
                counts[decision] += 1
        return counts
