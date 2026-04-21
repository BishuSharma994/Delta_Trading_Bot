"""
V5 Kill-Switch Enforcement
NO EXECUTION
IMMEDIATE DISARM
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

KILL_SWITCH_CONFIG = Path("config/v5/kill_switch.yaml")


def kill_switch_triggered():
    if not KILL_SWITCH_CONFIG.exists():
        return True, "config_missing"

    with KILL_SWITCH_CONFIG.open() as f:
        cfg = yaml.safe_load(f) or {}

    for key, value in cfg.items():
        if value is True:
            return True, key

    return False, None


def arm_kill_switch(reason: str) -> None:
    KILL_SWITCH_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        reason: True,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "triggered_reason": reason,
    }
    with KILL_SWITCH_CONFIG.open("w") as f:
        yaml.safe_dump(payload, f, sort_keys=False)
    logger.critical(f"KILL SWITCH ARMED — reason: {reason}")


def disarm_kill_switch() -> None:
    existing = {}
    if KILL_SWITCH_CONFIG.exists():
        with KILL_SWITCH_CONFIG.open() as f:
            existing = yaml.safe_load(f) or {}

    payload = {key: False for key in existing}
    payload.setdefault("triggered_at", False)
    payload.setdefault("triggered_reason", False)

    KILL_SWITCH_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with KILL_SWITCH_CONFIG.open("w") as f:
        yaml.safe_dump(payload, f, sort_keys=False)
    logger.warning("KILL SWITCH DISARMED — bot will resume on next loop")


def enforce(state_engine=None) -> bool:
    triggered, key = kill_switch_triggered()
    if triggered:
        logger.critical(f"KILL SWITCH ACTIVE [{key}] — blocking all execution")
        if state_engine is not None:
            close_all_positions = getattr(state_engine, "close_all_positions", None)
            if callable(close_all_positions):
                close_all_positions()
            else:
                logger.warning("state_engine has no close_all_positions method")
        return True

    return False


def check_auto_arm(daily_pnl_pct: float, consecutive_losses: int, api_error_count: int) -> bool:
    if daily_pnl_pct < -0.03:
        arm_kill_switch("auto_daily_loss_limit")
        return True

    if consecutive_losses >= 4:
        arm_kill_switch("auto_consecutive_losses")
        return True

    if api_error_count >= 10:
        arm_kill_switch("auto_api_error_storm")
        return True

    return False
