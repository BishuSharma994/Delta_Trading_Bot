Version: V5.1 | Status: IMPLEMENTED ALIGNMENT LAYER | Last Updated: 2026-04-22

# V4 Senior Analyst Spec

The Senior Analyst role in V5.1 is the live alignment layer implemented by `core/alignment_evaluator.py`.

## Role

The Senior Analyst does not generate a strategy vote. It validates whether the two existing strategy votes are aligned strongly enough to permit execution review.

## Inputs

| Input | Source |
| --- | --- |
| Volatility vote | `strategies/volatility_regime.py` |
| Funding vote | `strategies/funding_bias.py` |
| `time_to_funding_sec` | Feature pipeline and funding snapshot |
| `funding_rate_abs` | Feature pipeline and funding snapshot |

## Enforcement Rules

| Rule | Requirement |
| --- | --- |
| Directional agreement | Both votes must resolve to the same direction |
| Confidence | Computed confidence must be at least `0.65` |
| Funding window | `time_to_funding_sec <= 900` |
| Output states | `ALIGNED` or `ABSTAIN` |

## Confidence Computation

```text
vol_confidence = strategy vote confidence
funding_confidence = min(funding_rate_abs * 25, 0.60)
computed_confidence = (vol_confidence + funding_confidence) / 2
```

## Output Contract

| Field | Meaning |
| --- | --- |
| `alignment_state` | `ALIGNED` or `ABSTAIN` |
| `direction` | Normalized `LONG` or `SHORT` when aligned |
| `confidence` | Live computed confidence |
| `reason` | Explicit abstain or aligned reason |

## V5.1 Fixes Applied

| Area | V5.1 fix |
| --- | --- |
| Confidence threshold | Raised from `0.30` to `0.65` |
| Confidence source | Removed hardcoded constant and replaced with computed value |
| Direction comparison | Fixed mismatched raw-string comparison |
| Funding window | Tightened from `3600` to `900` seconds |

## Data Flow

```text
FundingBias vote ----\
                      -> alignment_evaluator.py -> ALIGNED or ABSTAIN
Volatility vote -----/
Funding snapshot ----/
Feature data --------/
```

The Senior Analyst is a gate, not a signal source.
