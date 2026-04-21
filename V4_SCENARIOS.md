Version: V5.1 | Status: IMPLEMENTED SCENARIO TAXONOMY | Last Updated: 2026-04-22

# V4 Scenarios

Scenarios describe recurring execution contexts that the analyst layer can recognize. They do not bypass governance or risk gates.

## SCENARIO-001: Funding Extreme + Volatility Compression

| Field | Definition |
| --- | --- |
| Scenario ID | `SCENARIO-001` |
| Core idea | Funding is extreme and volatility is compressed before a directional move |
| Direction rule | Funding and volatility votes must agree on `LONG` or `SHORT` |
| Timing rule | Entry must occur within 15 minutes of funding settlement |
| Confidence rule | Computed confidence must be at least `0.65` |
| Regime context | Best aligned with `VOLATILITY_COMPRESSION`, can coexist with `TREND_UP`, `TREND_DOWN`, or `RANGE` |
| Blockers | `VOLATILITY_EXPANSION`, `TRANSITION`, confidence below threshold, spread above max, funding window violation |
| Expected frequency | Rare |
| Known failure modes | False breakouts, underpowered funding move, profitable timeouts that fail to reach full target |

## SCENARIO-002: OB Retest Breakout/Breakdown Confirmed

| Field | Definition |
| --- | --- |
| Scenario ID | `SCENARIO-002` |
| Core idea | Order-block retest confirms continuation after a breakout or breakdown |
| Signal rule | `breakout_confirmed` directional signal from the volatility layer |
| Confidence rule | Computed confidence must be at least `0.65` |
| Regime context | Allowed in `VOLATILITY_COMPRESSION`, `TREND_UP`, `TREND_DOWN`, or `RANGE` |
| Blockers | `VOLATILITY_EXPANSION`, `TRANSITION`, confidence below threshold, spread above max, daily caps, kill switch |
| Expected frequency | Low to moderate |
| Known failure modes | Retest failure, momentum collapse after confirmation, structure break, trailing stop before full target |

## Scenario Governance

| Rule | Meaning |
| --- | --- |
| Both scenarios require vote agreement | No split-direction entries |
| Both scenarios require computed confidence | No hardcoded confidence |
| Scenarios are contextual only | They do not override risk or kill-switch rules |

See `PROJECT_STATE.md` for full performance data.
