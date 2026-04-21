Version: V5.1 | Status: PAPER STRESS VALIDATION ACTIVE | Last Updated: 2026-04-22

# V4 Stress Results

The primary stress evidence for V5.1 is now real paper-trading performance rather than synthetic design-only testing.

## Validation Dataset

| Window | Scope |
| --- | --- |
| Apr 17-21 2026 | 44 closed paper trades across BTCUSD, ETHUSD, SOLUSD, BNBUSD |

## Exit Reason Stress Table

| Exit reason | Count | Win rate | Notes |
| --- | --- | --- | --- |
| `funding_stop` | 1 | 0% | Clean stop-loss failure |
| `funding_time` | 19 | 47% | Main funding lifecycle exit |
| `hard_stop` | 1 | 0% | Hard-loss containment |
| `take_profit` | 1 | 100% | Too rare in V5.0 |
| `timeout` | 22 | 50% | Primary failure mode |

## Primary Stress Finding

Timeout exits were the main V5.0 weakness.

| Metric | Value |
| --- | --- |
| Timeout trades | 22 |
| Timeout win rate | 50% |
| Avg timeout PnL | +0.014% |
| Interpretation | Near-zero expectancy due to premature exit of winners |

Half of the timeout trades were winners, but many winners were cut before they could reach the `+0.65%` take-profit objective.

## Fix Applied In V5.1

`app/strategy/exit_manager.py` now:

- Activates trailing stop only after `+0.10%` profit
- Suppresses timeout when the trade is still profitable
- Switches profitable timeout cases into trailing-stop mode instead of forcing immediate exit

## Next Stress Validation

The next required stress step is a fresh 72-hour paper-trading run after the V5.1 fixes. Success is measured through lower timeout frequency, higher take-profit frequency, and zero circuit-breaker triggers.

See `PROJECT_STATE.md` for full performance data.
