"""
V5 Kill-Switch Enforcement
NO EXECUTION
IMMEDIATE DISARM
"""

import yaml
from pathlib import Path

KILL_SWITCH_CONFIG = Path("config/v5/kill_switch.yaml")

def kill_switch_triggered():
    if not KILL_SWITCH_CONFIG.exists():
        return False, None

    with KILL_SWITCH_CONFIG.open() as f:
        cfg = yaml.safe_load(f) or {}

    for key, value in cfg.items():
        if value is True:
            return True, key

    return False, None
