"""
V2.5 Gate Stress Orchestrator
OFFLINE ONLY — REPO-ALIGNED
"""

import json
from tools.replay.gate_stress_runner import GateStressRunner
from tools.replay.gate_stress_matrix import GATE_STRESS_MATRIX
from tools.replay.gate_stress_resolver import resolve_stress_values


class GateStressOrchestrator:
    """
    Wires matrix → resolver → runner.
    Explicit invocation only.
    """

    def __init__(self):
        self.runner = GateStressRunner()
        with open("config/execution_gate.yaml", "r") as f:
            self.base_gate_config = json.loads(
                json.dumps(__import__("yaml").safe_load(f))
            )

    def prepare_and_run(self):
        for entry in GATE_STRESS_MATRIX:
            param_path = entry["param_path"]
            label = entry["label"]

            sweep_values = resolve_stress_values(
                baseline_gate_config=self.base_gate_config,
                param_path=param_path,
                matrix_entry=entry,
            )

            self.runner.run_single_param_sweep(
                param_path=param_path,
                sweep_values=sweep_values,
                label=label,
            )
