"""
V2.5 Gate Stress Orchestrator
OFFLINE ONLY — NO AUTO-EXECUTION
"""

from tools.replay.gate_stress_runner import GateStressRunner
from tools.replay.gate_stress_matrix import GATE_STRESS_MATRIX
from tools.replay.gate_stress_resolver import resolve_stress_values
from tools.replay.loaders import load_execution_gate_config


class GateStressOrchestrator:
    """
    Wires matrix → resolver → runner.
    Does nothing unless explicitly called.
    """

    def __init__(self, replay_config_path: str):
        self.runner = GateStressRunner(replay_config_path)
        self.base_gate_config = load_execution_gate_config(
            "config/execution_gate.yaml"
        )

    def prepare_and_run(self):
        """
        SPEC-COMPLETE wiring.
        Execution is still controlled by caller.
        """
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
