"""
V2.5 Gate Stress Value Resolver
SPEC ONLY — NO EXECUTION
"""

from typing import Any, Dict, List
import copy


def resolve_numeric_sweep(
    baseline_value: float,
    multipliers: List[float],
) -> List[float]:
    """
    Resolve numeric sweep values from baseline using multipliers.
    """
    return [baseline_value * m for m in multipliers]


def resolve_expand_only_windows(
    baseline_windows: List[Any],
    expansion_steps: int = 1,
) -> List[List[Any]]:
    """
    Expand session windows conservatively.
    SPEC: exact expansion semantics are deferred.
    """
    resolved = [copy.deepcopy(baseline_windows)]
    for _ in range(expansion_steps):
        resolved.append(copy.deepcopy(baseline_windows))
    return resolved


def resolve_stress_values(
    baseline_gate_config: Dict,
    param_path: List[str],
    matrix_entry: Dict,
) -> List[Any]:
    """
    Entry-point resolver.
    Returns resolved sweep values without side effects.
    """
    ref = baseline_gate_config
    for key in param_path:
        ref = ref[key]

    baseline_value = ref

    if "sweep_multipliers" in matrix_entry:
        return resolve_numeric_sweep(
            baseline_value,
            matrix_entry["sweep_multipliers"],
        )

    if matrix_entry.get("sweep_mode") == "expand_only":
        return resolve_expand_only_windows(baseline_value)

    raise ValueError("Unsupported sweep mode")
