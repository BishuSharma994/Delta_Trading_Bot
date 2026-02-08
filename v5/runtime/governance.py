"""
V5 Governance Enforcement
NO EXECUTION
DISARM ONLY
"""

import yaml
from pathlib import Path

RUNTIME_CONFIG = Path("config/v5/runtime.yaml")

def is_armed():
    if not RUNTIME_CONFIG.exists():
        return False, "runtime_config_missing"

    with RUNTIME_CONFIG.open() as f:
        cfg = yaml.safe_load(f) or {}

    if cfg.get("armed") is not True:
        return False, "system_disarmed"

    return True, "armed"
