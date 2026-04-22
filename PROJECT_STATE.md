Version: PHASE5-DASHBOARD-ACTIVE | Status: AUTHORITATIVE PROJECT STATE | Last Updated: 2026-04-23

# Project State

## System Summary

Delta Trading Bot is a Python paper-trading bot for Delta Exchange India perpetual futures. It runs on a DigitalOcean VPS and currently trades no live capital. The active validation mode is a 72-hour paper-trading window before any live deployment decision.

xStock perpetuals are treated as 24/7 instruments on Delta Exchange in the current paper-trading path.

Covered symbols:

- `BTCUSD`
- `ETHUSD`
- `SOLUSD`
- `BNBUSD`

## Current Operating Mode

| Field | Value |
| --- | --- |
| Mode | PHASE5-DASHBOARD-ACTIVE |
| Exchange | Delta Exchange India |
| Market | Perpetual Futures |
| Execution | PAPER TRADE ONLY - NO LIVE EXCHANGE CALLS |
| Capital Exposure | ZERO (paper only) |
| Sizing | DYNAMIC (confidence + volatility scaled, paper notional only) |
| Hosting | DigitalOcean VPS |
| Runtime mode | Paper trading |
| Validation window | 72 hours |
| Live deployment status | Blocked pending target metrics |

## Version History

| Version | Layer | Summary |
| --- | --- | --- |
| V2 | Observer | Live observation loop and raw market collection |
| V3 | Associate Analyst | Regime classification and descriptive context |
| V4 | Senior Research | Hypotheses, scenarios, stress framework, confidence research |
| V5.0 | Dry-run execution | Paper-trade execution path with governance and exits |
| V5.1 | Live-ready paper validation | Risk and alignment fixes applied to production paper loop |

## Completed Phases Locked

## Phase 4 — Runtime Risk Layer (COMPLETE, DRY-RUN ACTIVE)

- Dynamic position sizing: confidence scale x volatility scale -> notional USD
- Portfolio-level daily drawdown kill-switch (all symbols halted when breached)
- Funding-rate ceiling guard (skips overheated entries above configurable threshold)
- Configurable trailing-stop behavior (reads from `risk.py`, not hardcoded)
- Per-symbol concurrent-position limits enforced in state engine
- Trade log includes sizing metadata: `position_notional_usd`, `position_size_units`, `confidence_scale`, `volatility_scale`

## Phase 5 - Performance Dashboard (COMPLETE)

### Output files
| File | Description |
| --- | --- |
| reports/equity_curve.jsonl | Append-only equity curve, one point per closed trade |
| reports/report_YYYY-MM-DD.txt | Daily full report saved with --save flag |
| reports/weekly_YYYY-MM-DD.txt | Weekly summary saved with --weekly flag |

### How to view
Run from project root:
    python trade_stats.py                        # print full report to stdout
    python trade_stats.py --equity --save        # update equity log + save daily report
    python trade_stats.py --weekly               # generate this week's summary
    python trade_stats.py --symbol BTCUSD        # filter to one symbol
    python trade_stats.py --since 7              # last 7 days only

### Scheduler
Register recurring tasks with: python scripts/schedule_setup.py
- Daily report: 08:00 every day
- Weekly summary: 07:00 every Monday
- Brain runner: 02:00 every Sunday

## What V5.1 Changed From V5.0

| File | V5.0 | V5.1 |
| --- | --- | --- |
| `core/alignment_evaluator.py` | `CONFIDENCE_THRESHOLD = 0.30` | `CONFIDENCE_THRESHOLD = 0.65` |
| `core/alignment_evaluator.py` | `MAX_FUNDING_WINDOW_SEC = 3600` | `MAX_FUNDING_WINDOW_SEC = 900` |
| `core/alignment_evaluator.py` | Confidence hardcoded | Confidence computed from live evidence |
| `core/alignment_evaluator.py` | Raw vote string comparison | Direction-normalized comparison |
| `config/risk.py` | `max_daily_trades_per_symbol = 3` | `2` |
| `config/risk.py` | `max_daily_loss_pct = 0.012` | `0.010` |
| `config/risk.py` | `vol_timeout_sec = 15 * 60` | `45 * 60` |
| `config/risk.py` | `max_bid_ask_spread_pct = 0.0020` | `0.0008` |
| `config/risk.py` | `funding_entry_window_sec = 120` | `900` |
| `config/risk.py` | `min_vol_confidence = 0.55` | `0.65` |
| `config/risk.py` | `funding_blackout_for_vol_sec = 180` | `1800` |
| `config/risk.py` | `vol_trailing_stop_pct = 0.0040` | `0.0025` |
| `core/state_engine.py` | No portfolio circuit breaker | 3% daily portfolio circuit breaker |
| `core/state_engine.py` | No post-loss symbol halt | 1-hour cooldown after 3 consecutive losses |
| `app/strategy/exit_manager.py` | Trailing stop activated too early | Activates only after +0.10% profit |
| `app/strategy/exit_manager.py` | Timeout exited profitable trades | Profitable timeout now switches to trailing mode |
| `v5/runtime/kill_switch.py` | Incomplete | Implemented, auto-arm capable, fail-safe on missing config |

## Architecture In Execution Order

1. `observer.py`
2. `core/feature_pipeline.py`
3. `strategies/funding_bias.py`
4. `strategies/volatility_regime.py`
5. `core/alignment_evaluator.py`
6. `core/evaluator.py`
7. `core/state_engine.py`
8. `app/strategy/exit_manager.py`
9. `v5/runtime/kill_switch.py`

## Confidence Model

Confidence is now computed live and is never hardcoded.

| Component | Source | Formula |
| --- | --- | --- |
| `vol_confidence` | `strategy_votes.jsonl` | Strategy-provided float in `[0.0, 1.0]` |
| `funding_confidence` | `funding_snapshot.jsonl` | `min(funding_rate_abs * 25, 0.60)` |
| `computed_confidence` | Alignment evaluator | `(vol_confidence + funding_confidence) / 2` |

Entry gate:

- If `computed_confidence < 0.50`: `ABSTAIN`
- If `computed_confidence < 0.65`: `ABSTAIN`
- If votes disagree: `ABSTAIN`
- If funding window is above 900 seconds: `ABSTAIN`

## Risk State

| Rule | V5.1 Value |
| --- | --- |
| Risk per trade | 1% of capital |
| Portfolio breaker | -3% daily realized return |
| Per-symbol cooldown | 1 hour after 3 consecutive losses |
| Max trades per symbol per day | 2 |
| Funding entry window | 900 seconds |
| Max spread | 0.0008 |
| Vol trailing stop activation | +0.10% profit |
| Vol timeout | 45 minutes |
| Minimum R:R | 1.5:1 |

## Hypothesis Status

Primary tracked hypothesis:

| ID | Statement | Status |
| --- | --- | --- |
| HYP-001 | When funding rate is extreme and volatility compresses, breakouts become more probable | Partially confirmed |

Interpretation:

- Paper data shows positive expectancy.
- Win rate is below 50%.
- Reward/risk is strong enough to keep the system net profitable.
- The null hypothesis is weakened, not rejected.

## Paper Trade Performance

Validation window covered: Apr 17-21 2026

### Headline Results

| Metric | Value |
| --- | --- |
| Closed trades | 44 |
| Wins | 21 |
| Losses | 23 |
| Win rate | 47.7% |
| Total PnL | +2.16% |
| Average win | +0.2596% |
| Average loss | -0.1430% |
| Reward/Risk | 1.82:1 |

### Exit Breakdown

| Exit reason | Count | Notes |
| --- | --- | --- |
| `timeout` | 22 | Main failure mode in V5.0 |
| `funding_time` | 19 | Normal funding lifecycle exit |
| `take_profit` | 1 | Too rare; target must increase post-fix |
| `hard_stop` | 1 | Controlled hard loss |
| `funding_stop` | 1 | Funding stop loss |

### Exit Reason Win Rates

| Exit reason | Win rate |
| --- | --- |
| `funding_stop` | 0% |
| `funding_time` | 47% |
| `hard_stop` | 0% |
| `take_profit` | 100% |
| `timeout` | 50% |

### Trade Type Breakdown

| Trade type | Trades | Win rate | Average PnL |
| --- | --- | --- | --- |
| FUNDING | 20 | 45% | +0.10% |
| VOL | 24 | 50% | +0.007% |

### Timeout Failure Analysis

| Metric | Value |
| --- | --- |
| Timeout exits | 22 of 44 |
| Timeout winners | 11 |
| Avg PnL of profitable timeouts | +0.13% |
| V5.1 fix | Suppress timeout if profitable and switch to trailing stop mode |

## What Happens Next

The bot remains in paper mode until the next 72-hour validation window completes. Go-live is permitted only if all criteria below pass.

| Go-live criterion | Required value |
| --- | --- |
| Win rate | Greater than 50% |
| Take-profit frequency | More than 5 per 44 trades |
| Timeout exits | Fewer than 12 per 44 trades |
| Average win size | Greater than 0.40% |
| Total PnL | Greater than 4% |
| Circuit breaker triggers | Zero |

If any condition fails, the system remains in paper mode and another revision cycle is required.
