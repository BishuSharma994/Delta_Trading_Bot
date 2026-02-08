"""
V5 Manual Authorization Validation
NO EXECUTION
Human authorization only
"""

import json
from pathlib import Path
from datetime import datetime

AUTH_FILE = Path("config/v5/authorization.json")

def authorization_valid():
    if not AUTH_FILE.exists():
        return False, "authorization_file_missing"

    with AUTH_FILE.open() as f:
        auth = json.load(f)

    required = ["authorized_by", "date_utc", "scope", "revocation"]
    for field in required:
        if not auth.get(field):
            return False, f"missing_{field}"

    revocation = auth.get("revocation", {})
    if revocation.get("revoked") is True:
        return False, "authorization_revoked"

    try:
        datetime.fromisoformat(auth["date_utc"])
    except Exception:
        return False, "invalid_date"

    return True, "authorization_valid"
