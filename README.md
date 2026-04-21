Version: V5.1 | Status: ACTIVE PAPER TRADING | Last Updated: 2026-04-22

# Delta Trading Bot

Delta Trading Bot is a Python paper-trading system for Delta Exchange India perpetual futures. It runs on a DigitalOcean VPS, observes `BTCUSD`, `ETHUSD`, `SOLUSD`, and `BNBUSD` every 60 seconds, and simulates full trade lifecycle management under hard risk controls.

Current operating mode is `PAPER TRADING` with a mandatory 72-hour validation window before any go-live decision.

## What The Bot Does

- Observes live mark price, funding rate, and bid/ask every 60 seconds
- Builds a per-symbol feature vector
- Generates directional votes from `FundingBias` and `VolatilityRegime`
- Requires both strategies to agree in direction and computed confidence to be at least `0.65`
- Executes paper trades through a single lifecycle: `FLAT -> ENTER -> EXIT -> FLAT`
- Applies kill-switch and portfolio risk enforcement on every observer loop tick

## What The Bot Does Not Do

- No machine learning
- No neural network
- No LLM
- No martingale
- No averaging down
- No cross-symbol correlation trades
- No auto-compounding

## Architecture

```text
observer.py
  -> v5/runtime/kill_switch.py::enforce()
  -> core/feature_pipeline.py
  -> strategies/funding_bias.py
  -> strategies/volatility_regime.py
  -> core/alignment_evaluator.py
  -> core/evaluator.py
  -> core/state_engine.py
  -> app/strategy/exit_manager.py
```

Execution order:

1. `observer.py` runs the 60-second loop and fetches Delta market data.
2. `kill_switch.enforce()` runs first and can halt the tick before any processing.
3. `core/feature_pipeline.py` builds symbol features.
4. `strategies/funding_bias.py` votes from funding direction.
5. `strategies/volatility_regime.py` votes from order-block retest breakout logic.
6. `core/alignment_evaluator.py` checks directional agreement and computes live confidence.
7. `core/evaluator.py` returns `ALIGNED` or `ABSTAIN`.
8. `core/state_engine.py` manages entries, exits, daily limits, and the portfolio circuit breaker.
9. `app/strategy/exit_manager.py` manages trailing stop, timeout, and hard-stop behavior.

## Setup

### Requirements

- Python
- Delta Exchange India API credentials
- DigitalOcean VPS or equivalent always-on Linux host

### Environment Variables

Create a `.env` file in the project root with:

```env
DELTA_API_KEY=your_delta_api_key
DELTA_API_SECRET=your_delta_api_secret
```

### Run Paper Mode

```powershell
python observer.py
```

The bot remains in paper mode during the full 72-hour validation period.

### Check Trade Statistics

```powershell
python trade_stats.py
```

## Kill Switch Operations

Kill switch state is stored at `config/v5/kill_switch.yaml`.

### Manual Arm From PowerShell

```powershell
@"
manual_halt: true
triggered_at: $(Get-Date -AsUTC -Format o)
triggered_reason: manual_halt
"@ | Set-Content -LiteralPath "config/v5/kill_switch.yaml"
```

### Manual Disarm From PowerShell

```powershell
@"
manual_halt: false
triggered_at: false
triggered_reason: false
"@ | Set-Content -LiteralPath "config/v5/kill_switch.yaml"
```

The kill switch is fail-safe. If the YAML file is missing, the system treats the bot as armed and blocks execution.

## Risk Parameters

| Parameter | V5.1 Value | Notes |
| --- | --- | --- |
| Risk per trade | 1% of capital | ATR-based stop sizing |
| Global daily circuit breaker | 3% portfolio loss | Halts all symbols |
| Per-symbol cooldown | 1 hour after 3 consecutive losses | Enforced in `state_engine.py` |
| Min confidence to enter | 0.65 | Computed from live evidence |
| Max trades per symbol per day | 2 | Hard cap |
| Funding entry window | 900 seconds | 15 minutes before settlement |
| Max bid/ask spread | 0.0008 | 0.08% |
| Trailing stop activation | Profit >= 0.10% | Prevents premature stop-out |
| Vol timeout | 45 minutes | Suppressed if trade is profitable |
| Minimum R:R | 1.5:1 | TP distance must exceed SL distance |

## Paper Trading Results

See `PROJECT_STATE.md` for full performance data.

Summary for Apr 17-21 2026:

| Metric | Result |
| --- | --- |
| Closed trades | 44 |
| Win rate | 47.7% |
| Total PnL | +2.16% |
| Average win | +0.2596% |
| Average loss | -0.1430% |
| Reward/Risk | 1.82:1 |
| Main issue in V5.0 | Timeout exits |
| V5.1 correction | Timeout suppression for profitable trades |

## Go-Live Checklist

All conditions below must pass after 72 hours of paper trading:

| Requirement | Target |
| --- | --- |
| Win rate | Greater than 50% |
| Take-profit count | More than 5 per 44 trades |
| Timeout exits | Fewer than 12 per 44 trades |
| Average win size | Greater than 0.40% |
| Total PnL | Greater than 4% over 72 hours |
| Circuit breaker triggers | Zero |

Live deployment is blocked until every target passes.
