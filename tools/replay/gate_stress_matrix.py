"""
V2.5 Gate Stress Parameter Matrix
REPO-ALIGNED — SPEC ONLY
"""

GATE_STRESS_MATRIX = [
    {
        "label": "min_strategies",
        "param_path": ["requirements", "confluence", "min_strategies"],
        "sweep_values": [1, 2, 3, 4],
    },
    {
        "label": "confluence_window",
        "param_path": ["requirements", "confluence", "window_seconds"],
        "sweep_values": [30, 60, 120, 300],
    },
    {
        "label": "confidence_threshold",
        "param_path": ["requirements", "confidence", "min_average"],
        "sweep_values": [0.4, 0.5, 0.6, 0.7],
    },
    {
        "label": "persistence_votes",
        "param_path": ["requirements", "persistence", "min_consecutive_votes"],
        "sweep_values": [1, 2, 3],
    },
    {
        "label": "cooldown_seconds",
        "param_path": ["safety", "cooldown_seconds"],
        "sweep_values": [0, 30, 60, 120],
    },
]
