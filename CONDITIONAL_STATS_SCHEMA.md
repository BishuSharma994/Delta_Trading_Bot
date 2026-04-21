Version: V5.1 | Status: IMPLEMENTED DESCRIPTIVE METRICS | Last Updated: 2026-04-22

# Conditional Stats Schema

Conditional statistics in V5.1 are descriptive only. They inform review, debugging, and governance decisions, but they do not directly trigger execution.

## Purpose

Allowed conditional statistics summarize how the paper-trading system behaves under different trade types, exits, and contexts.

## Conditioning Axes

| Axis | Allowed |
| --- | --- |
| Regime | Yes |
| Time window | Yes |
| Strategy identity | Yes |
| Vote direction | Yes |
| Confidence bucket | Yes |
| Trade type | Yes |
| Exit reason | Yes |

## Allowed Metrics

| Metric family | Examples |
| --- | --- |
| Frequency | Trade count, abstention count, exit count |
| Outcome | Win rate, loss rate, average PnL |
| Quality | Average win, average loss, reward/risk |
| Distribution | Exit-reason mix, trade-type mix |

## V5.1 Live Metrics

These are now measured from real paper-trading output, not design-only estimates.

### Win Rate By Trade Type

| Trade type | Trades | Win rate | Average PnL |
| --- | --- | --- | --- |
| FUNDING | 20 | 45% | +0.10% |
| VOL | 24 | 50% | +0.007% |

### Average PnL By Exit Reason

| Exit reason | Average PnL |
| --- | --- |
| `timeout` | +0.014% |
| `funding_time` | Not separately specified in current ground truth |
| `take_profit` | Positive by definition in current sample |
| `hard_stop` | Negative by definition in current sample |
| `funding_stop` | Negative by definition in current sample |

### Exit Reason Outcome View

| Exit reason | Count | Win rate |
| --- | --- | --- |
| `timeout` | 22 | 50% |
| `funding_time` | 19 | 47% |
| `take_profit` | 1 | 100% |
| `hard_stop` | 1 | 0% |
| `funding_stop` | 1 | 0% |

### Abstention Tracking

Abstention and exit are different event classes. An "abstention rate by exit reason" is not applicable because exit reasons exist only after a trade is entered and closed.

| Requested view | V5.1 status |
| --- | --- |
| Abstention rate by exit reason | Not applicable |
| Abstention rate by reason | Allowed, not yet populated in current state |
| Abstention rate by regime | Allowed, not yet populated in current state |
| Abstention rate by confidence gate | Allowed, not yet populated in current state |

## Governance Rule

Conditional statistics are descriptive only. They support diagnosis and review but must not directly trigger entries, exits, or kill-switch actions.
