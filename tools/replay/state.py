"""
Virtual Replay State
V2.4 — Offline Only

Tracks non-executing state used to enforce gate rules.
No real positions are ever opened.
"""

from typing import TypedDict


class VirtualState(TypedDict):
    open_position: bool
    last_allow_ts: str | None
    cooldown_remaining_sec: int
