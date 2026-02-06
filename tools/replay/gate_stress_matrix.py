"""
V2.5 Gate Stress Parameter Matrix
SPEC ONLY — NO EXECUTION
"""

GATE_STRESS_MATRIX = [
    {
        "label": "volatility_cap",
        "param_path": ["volatility", "max_allowed"],
        "sweep_multipliers": [0.5, 0.75, 1.0, 1.25, 1.5],
    },
    {
        "label": "liquidity_floor",
        "param_path": ["liquidity", "min_depth"],
        "sweep_multipliers": [0.5, 0.75, 1.0, 1.25],
    },
    {
        "label": "spread_cap",
        "param_path": ["spread", "max_spread_bps"],
        "sweep_multipliers": [0.5, 0.8, 1.0, 1.2],
    },
    {
        "label": "slippage_tolerance",
        "param_path": ["slippage", "max_expected"],
        "sweep_multipliers": [0.5, 1.0, 1.5, 2.0],
    },
    {
        "label": "session_window",
        "param_path": ["session", "allowed_windows"],
        "sweep_mode": "expand_only",
    },
]
