"""
brain/config_writer.py
Applies brain-recommended parameter changes to config/risk.py.

SAFETY RULE: Changes are NEVER auto-applied.
Every change requires --approve flag from human.

Usage:
    python -m brain.config_writer           # show pending changes
    python -m brain.config_writer --approve # apply after review
"""

import json
import logging
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)
STAGING_PATH = Path(__file__).parent / "data" / "staging" / "risk_staging.json"
RISK_PATH = Path(__file__).parent.parent / "config" / "risk.py"
BACKUP_DIR = Path(__file__).parent / "data" / "config_backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def load_staging() -> dict:
    if not STAGING_PATH.exists():
        print("No staging config found. Run: python -m brain.runner")
        return {}
    with open(STAGING_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def show_pending():
    staging = load_staging()
    changes = staging.get("_changes", [])
    if not changes:
        print("No pending changes.")
        return
    print(f"\n{'=' * 58}")
    print(f"BRAIN RECOMMENDATIONS  (generated {staging.get('_generated_at', '')})")
    print(f"{'=' * 58}")
    for change in changes:
        print(
            f"  {change['param']:<35} {change['old_val']} → {change['new_val']}"
        )
        print(f"    Reason: {change['reason']}")
    print("\n  To apply: python -m brain.config_writer --approve")
    print(f"{'=' * 58}\n")


def apply(approve: bool = False) -> bool:
    if not approve:
        show_pending()
        return False
    staging = load_staging()
    changes = staging.get("_changes", [])
    if not changes:
        print("Nothing to apply.")
        return False

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    shutil.copy2(RISK_PATH, BACKUP_DIR / f"risk_{ts}.py")

    content = RISK_PATH.read_text(encoding="utf-8")
    applied = []
    for change in changes:
        pattern = rf"^({change['param']}\s*=\s*)([^\n]+)"
        replacement = (
            rf"\g<1>{change['new_val']}"
            f"  # Brain {datetime.now(timezone.utc).date()}"
        )
        new_content, count = re.subn(
            pattern,
            replacement,
            content,
            flags=re.MULTILINE,
        )
        if count:
            content = new_content
            applied.append(change)
            logger.info(f"Applied: {change['param']} → {change['new_val']}")
        else:
            logger.warning(f"Not found in risk.py: {change['param']}")

    RISK_PATH.write_text(content, encoding="utf-8")
    record_path = BACKUP_DIR / f"applied_{ts}.json"
    with open(record_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "changes": applied,
            },
            handle,
            indent=2,
        )
    print(f"Applied {len(applied)} changes to config/risk.py")
    return True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    apply(approve="--approve" in sys.argv)
