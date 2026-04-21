"""
brain/__init__.py
Adaptive Intelligence Layer — Delta Trading Bot V5.1

Architecture:
    data_collector.py  → fetches 1.5yr OHLCV from Delta Exchange API
    pattern_detector.py → pure statistical pattern detection (no ML)
    log_book.py        → stores all detected patterns with metadata
    drift_monitor.py   → detects when pattern performance changes
    config_writer.py   → writes approved changes to config/risk.py
    runner.py          → runs full pipeline in one command

Rules:
    - Brain NEVER trades
    - Brain NEVER connects to live market
    - Brain NEVER auto-applies changes
    - Human reviews all recommendations before approval
    - Run weekly: python -m brain.runner
    - Apply changes: python -m brain.config_writer --approve

Status: OFFLINE — do not push to git until 72h paper validation passes
"""
