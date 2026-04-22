# Delta Trading Bot - Project Roadmap

> Single source of truth for all phases.
> Update this file as each phase completes.
> Last Updated: 2026-04-23

***

## Completed

### V1 - Observer
- Live market observation (read-only)
- Feature extraction
- Strategy voting
- Full event persistence

### V2 - Junior Analyst
- Abstention analysis
- Persistence analysis
- Rarity analysis
- Multi-symbol observation: BTC, ETH, BNB, SOL

### V3 - Associate Analyst
- Hypothesis Runner (offline)
- Scenario Tagger (offline)
- Confidence Calibration Engine (offline)
- Integrated Stress Harness (offline)

### V4 - Senior Research Layer
- Volatility regime analysis
- Funding bias analysis
- Hypothesis falsification
- Confidence inflation suppressed
- Abstention bias preserved

### V5 - Governed Execution (Dry-Run)
- Consumes locked V4 research artifacts
- Enforces evidence contracts
- Governance arming + kill-switch
- Emits dry-run order intents only
- Live execution: IMPOSSIBLE by design

### V5.1 - Live Execution Enabled CURRENT
- Live trading on Delta Exchange India
- 4 crypto perpetuals: BTCUSD, ETHUSD, SOLUSD, BNBUSD
- systemd service on VPS (auto-restart, auto-start on reboot)
- xStock symbols added to config (10 symbols, IDs confirmed)
- NYSE market hours gate (core/market_hours.py)
- Brain offline data collection architecture
- XSTOCK_ENABLED = True for xStock paper validation (live xStock still pending)
- Commit: 4f1e3ad

***

## Upcoming Phases

### Phase 2 - Brain Integration
**Goal:** Brain pattern recommendations auto-update risk config weekly.

- [ ] Brain completes first full data collection run (crypto 4 symbols)
- [ ] Brain completes xStock data collection (10 symbols)
- [x] brain/config_writer.py implemented with manual approval flow
- [ ] config/risk.py updated with brain recommendations
- [ ] Weekly brain run scheduled (Windows Task Scheduler - Sunday 2AM)
- [x] Brain drift monitor implemented to stage stale-param recommendations

### Phase 3 - xStock Paper Validation
**Goal:** 72h paper trade xStock symbols before enabling live trading.

- [x] Set XSTOCK_ENABLED = True in config/settings.py
- [ ] Run paper trades for 72 hours
- [ ] Review trade_stats.py output
- [x] Spread filter logic implemented for xStock during NYSE hours
- [x] xStock session-gating logic implemented outside NYSE hours
- [ ] If pass, enable live xStock trading on VPS

### Phase 4 - Risk Management Upgrade
**Goal:** Dynamic position sizing based on brain confidence scores.

- [x] Per-symbol volatility-adjusted position sizing
- [x] Max daily drawdown kill-switch (e.g. -3% stops all trading)
- [x] Per-symbol max concurrent positions cap
- [x] Trailing stop implementation for trending markets
- [x] Funding rate filter (skip entry if funding > threshold)

### Phase 5 - Performance Dashboard
**Goal:** Track bot performance locally without external tools.

- [x] trade_stats.py scheduled report (daily)
- [x] Win rate, avg bps, max drawdown per symbol
- [x] Equity curve log (append-only) -> reports/equity_curve.jsonl
- [x] Weekly summary report auto-generated -> reports/weekly_YYYY-MM-DD.txt
- [x] Compare crypto vs xStock performance

### Phase 6 - Multi-Account / Sub-Account
**Goal:** Separate crypto and xStock into isolated sub-accounts.

- [ ] Delta Exchange sub-account setup (max 2 allowed)
- [ ] Separate API keys per sub-account
- [ ] Separate risk budgets per sub-account
- [ ] Cross-account kill-switch

***

## Rules

1. Never push .env to git
2. Brain data (`brain/data/`) stays local only
3. Only `config/risk.py` changes get pushed after brain approval
4. Live xStock trading stays disabled until Phase 3 paper validation passes
5. systemd manages the live bot - never run `observer.py` manually

***

## Quick Reference

| What | Command |
|------|---------|
| Check bot status | `systemctl status trading-bot` |
| View live logs | `journalctl -u trading-bot -f` |
| Restart bot | `systemctl restart trading-bot` |
| Run brain locally | `python -m brain.runner --refresh` |
| Review brain changes | `python -m brain.config_writer` |
| Approve brain changes | `python -m brain.config_writer --approve` |
| View performance | `python trade_stats.py` |
| Save daily report | `python trade_stats.py --equity --save` |
| Weekly summary | `python trade_stats.py --weekly` |
| Filter by symbol | `python trade_stats.py --symbol BTCUSD` |
| Last 7 days only | `python trade_stats.py --since 7` |
| Setup scheduler | `python scripts/schedule_setup.py` |
| Deploy to VPS | `git push origin main` then `git pull` on VPS |
