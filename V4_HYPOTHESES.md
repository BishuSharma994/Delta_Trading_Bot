Version: V5.1 | Status: ACTIVE RESEARCH HYPOTHESES | Last Updated: 2026-04-22

# V4 Hypotheses

Hypotheses remain research statements. They do not automatically authorize execution and they can fail.

## HYP-001

| Field | Value |
| --- | --- |
| ID | `HYP-001` |
| Statement | When funding rate is extreme and volatility compresses, breakouts become more probable |
| Preconditions | Extreme funding, volatility compression, valid directional agreement, trade occurs inside the V5.1 execution gates |
| Null hypothesis | Breakouts under this setup are random and do not produce positive expectancy |
| Failure conditions | Negative expectancy, unstable reward/risk, regime dependence that disappears out of sample, or results collapsing under stress |
| Evidence required | Paper-trade expectancy, exit-quality distribution, repeatability across tracked symbols, stress survival |
| Expected rarity | Rare |

## Status

| Status | Interpretation |
| --- | --- |
| Partially confirmed | Positive expectancy observed, but evidence base is still limited |

## What The Data Shows

Apr 17-21 2026 paper-trade data:

| Metric | Value |
| --- | --- |
| Win rate | 47.7% |
| Reward/Risk | 1.82:1 |
| Total PnL | +2.16% |
| Expectancy | Positive |

Interpretation:

- Win rate alone is below 50%.
- Reward/risk is strong enough to keep the system net profitable.
- The setup is promising, not proven.

## Null Hypothesis Status

The null hypothesis is weakened but not rejected. More data is required before promoting HYP-001 from partial confirmation to stronger support.

## Governance Rules

| Rule | Meaning |
| --- | --- |
| Hypotheses can fail | Failure is valid and must be recorded |
| No automatic promotion | Positive results do not self-authorize live deployment |
| Research is descriptive | Hypothesis status informs review, not execution |

See `PROJECT_STATE.md` for full performance data.
