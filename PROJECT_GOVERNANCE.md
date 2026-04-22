Version: V5.1 | Status: ACTIVE GOVERNANCE POLICY | Last Updated: 2026-04-22

# Project Governance

## Core Principles

| Principle | Meaning |
| --- | --- |
| Capital first | Capital preservation overrides all profit objectives |
| Abstention preferred | No trade is better than a low-quality trade |
| Evidence before action | Execution requires live evidence, not assumption |

## Hard Risk Rules

| Rule | V5.1 Value | Enforcement |
| --- | --- | --- |
| Risk per trade | 1% of capital | ATR-based stop sizing |
| Portfolio circuit breaker | -3% daily realized return | Halts all symbols |
| Per-symbol cooldown | 1 hour after 3 consecutive losses | Blocks new entries |
| Minimum confidence | 0.65 | Alignment gate |
| Max trades per symbol per day | 2 | State engine |
| Funding entry window | 900 seconds | Funding-only entry gate |
| Max bid/ask spread | 0.0008 | Entry filter |
| Trailing stop activation | Profit >= 0.10% | Exit manager |
| Vol timeout | 45 minutes | Exit manager |
| Minimum R:R | 1.5:1 | Strategy design requirement |

## Signal Rules

Execution permission requires all of the following:

| Rule | Requirement |
| --- | --- |
| Directional agreement | Funding vote and volatility vote must match |
| Confidence | Computed confidence must be at least `0.65` |
| Funding timing | Funding entry must be inside `<= 15 minutes` |
| Regime filter | `VOLATILITY_EXPANSION` and `TRANSITION` block execution |

## Execution Rules

| Rule | Requirement |
| --- | --- |
| Trade lifecycle | `FLAT -> ENTER -> EXIT -> FLAT` only |
| Position count | Single lifecycle per symbol at a time |
| Daily symbol cap | Maximum 2 trades per symbol |
| Spread gate | Must be `<= 0.08%` |
| Paper mode | Required during current validation phase |

## Kill Switch Rules

Kill-switch configuration lives at `config/v5/kill_switch.yaml`.

| Trigger type | Threshold |
| --- | --- |
| Manual halt | `manual_halt: true` |
| Auto daily loss | Daily PnL below `-3%` |
| Auto consecutive losses | `>= 4` |
| Auto API storm | `>= 10` API errors |
| Missing config file | Treated as armed |

`enforce()` runs at the first line of every observer loop tick. If armed, execution is blocked for that iteration and open positions should be closed if supported by the state engine.

## Permanently Forbidden

| Forbidden behavior | Reason |
| --- | --- |
| Machine learning, neural networks, LLMs | Out of scope and not part of governed logic |
| Averaging down | Increases exposure after adverse movement |
| Martingale | Unbounded risk escalation |
| Cross-symbol correlation trades | Not part of V5.1 design |
| Auto-compounding | Not part of risk model |
| Size positions for live capital (paper sizing for audit and research is permitted) | Live-capital sizing remains out of scope in dry-run governance |
| Self-disarming kill switch | Emergency halt must remain explicit and auditable |
| Hypothesis auto-promotion | Research evidence does not self-authorize execution |

## Phase 4 Risk Controls (Active, Dry-Run Scope)

- All position sizing is paper-notional only - no real capital is deployed
- Portfolio drawdown kill-switch is enforced at the state engine level
- Funding ceiling and trailing-stop thresholds are config-driven (`risk.py`)
- Sizing metadata is logged to `paper_trades.jsonl` for post-hoc analysis only
- Live execution remains impossible and requires a separate repository

See `PROJECT_STATE.md` for full performance data.
