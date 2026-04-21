"""
brain/drift_monitor.py
Compares recent 30-day pattern win rate vs 90-day baseline.
If drift > 15% → writes parameter recommendation to staging config.
Bot reads staging config as suggestion — never auto-applied.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)
LOG_DIR = Path(__file__).parent / "data" / "log_book"
STAGING_DIR = Path(__file__).parent / "data" / "staging"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

DRIFT_THRESHOLD = 0.15
RECENT_DAYS = 30
BASELINE_DAYS = 90

# V5.1 default parameter values
DEFAULTS = {
    "min_vol_confidence": 0.65,
    "vol_timeout_sec": 2700,
    "vol_trailing_stop_pct": 0.0025,
    "max_bid_ask_spread_pct": 0.0008,
    "funding_entry_window_sec": 900,
}

# What to adjust when each pattern drifts
DRIFT_ACTIONS = {
    "VOLATILITY_COMPRESSION_BREAKOUT": {
        "param": "min_vol_confidence",
        "degrading": +0.05,
        "improving": -0.03,
        "min": 0.55,
        "max": 0.85,
    },
    "MEAN_REVERSION_AFTER_EXTENSION": {
        "param": "vol_timeout_sec",
        "degrading": -300,
        "improving": +300,
        "min": 900,
        "max": 5400,
    },
    "TREND_CONTINUATION_PULLBACK": {
        "param": "vol_trailing_stop_pct",
        "degrading": -0.0005,
        "improving": +0.0005,
        "min": 0.0010,
        "max": 0.0060,
    },
    "RANGE_BOUNDARY_REJECTION": {
        "param": "max_bid_ask_spread_pct",
        "degrading": -0.0001,
        "improving": +0.0001,
        "min": 0.0003,
        "max": 0.0015,
    },
}


def _recent(patterns: list, days: int) -> list:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
    return [
        pattern
        for pattern in patterns
        if pattern.get("timestamp") and float(pattern["timestamp"]) >= cutoff
    ]


def _wr(patterns: list) -> float:
    return (
        sum(1 for pattern in patterns if pattern["success"]) / len(patterns)
        if patterns else 0.0
    )


def compute_drift(all_patterns: list) -> list:
    grouped = defaultdict(list)
    for pattern in all_patterns:
        grouped[pattern["pattern"]].append(pattern)

    reports = []
    for name, items in grouped.items():
        recent = _recent(items, RECENT_DAYS)
        baseline = _recent(items, BASELINE_DAYS)
        if len(recent) < 5 or len(baseline) < 10:
            continue
        recent_wr = _wr(recent)
        baseline_wr = _wr(baseline)
        drift = recent_wr - baseline_wr
        status = (
            "DEGRADING" if drift < -DRIFT_THRESHOLD
            else "IMPROVING" if drift > DRIFT_THRESHOLD
            else "STABLE"
        )
        reports.append(
            {
                "pattern": name,
                "recent_wr": round(recent_wr, 4),
                "baseline_wr": round(baseline_wr, 4),
                "drift": round(drift, 4),
                "status": status,
                "recent_count": len(recent),
                "baseline_count": len(baseline),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info(
            f"DRIFT {name}: {baseline_wr:.1%} → {recent_wr:.1%} "
            f"({drift:+.1%}) {status}"
        )
    return reports


def generate_staging_config(drift_reports: list, current: dict = None) -> dict:
    config = dict(current or DEFAULTS)
    changes = []
    for report in drift_reports:
        if report["status"] == "STABLE":
            continue
        action = DRIFT_ACTIONS.get(report["pattern"])
        if not action:
            continue
        param = action["param"]
        old_val = config.get(param, DEFAULTS.get(param, 0))
        delta = (
            action["degrading"]
            if report["status"] == "DEGRADING"
            else action["improving"]
        )
        new_val = round(
            max(action["min"], min(action["max"], old_val + delta)),
            6,
        )
        if new_val != old_val:
            config[param] = new_val
            changes.append(
                {
                    "param": param,
                    "old_val": old_val,
                    "new_val": new_val,
                    "reason": (
                        f"{report['pattern']} {report['status']} "
                        f"drift={report['drift']:+.1%}"
                    ),
                }
            )
            logger.info(f"STAGING: {param} {old_val} → {new_val}")
    config["_generated_at"] = datetime.now(timezone.utc).isoformat()
    config["_changes"] = changes
    config["_drift_reports"] = drift_reports
    return config


def save_staging(config: dict) -> Path:
    path = STAGING_DIR / "risk_staging.json"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
    logger.info(f"Staging saved → {path}")
    return path


def run_drift_check(all_patterns: list, current: dict = None) -> dict:
    if not all_patterns:
        logger.warning("No patterns for drift check.")
        return {}
    reports = compute_drift(all_patterns)
    config = generate_staging_config(reports, current)
    save_staging(config)
    return config
