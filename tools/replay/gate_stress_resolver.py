"""
V2.5 Gate Stress Value Resolver
REPO-ALIGNED — SPEC ONLY
"""

from typing import Any, Dict, List


def resolve_stress_values(
    baseline_gate_config: Dict,
    param_path: List[str],
    matrix_entry: Dict,
) -> List[Any]:
    """
    Resolve sweep values directly from matrix.
    """
    return matrix_entry["sweep_values"]
