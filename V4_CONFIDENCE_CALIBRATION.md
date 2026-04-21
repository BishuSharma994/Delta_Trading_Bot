Version: V5.1 | Status: IMPLEMENTED CONFIDENCE MODEL | Last Updated: 2026-04-22

# V4 Confidence Calibration

The V4 confidence layer is active in V5.1 through `core/alignment_evaluator.py`.

## Why V5.1 Changed It

| Item | Old behavior | V5.1 behavior |
| --- | --- | --- |
| Threshold | `0.30` | `0.65` |
| Confidence source | Hardcoded | Computed from live evidence |
| Funding window | 3600 seconds | 900 seconds |
| Vote comparison | Raw string comparison | Direction-normalized comparison |

The old `0.30` threshold was too permissive and wrong for live gating. V5.1 raises the standard and requires confidence to be earned from observable market evidence.

## Formula

```text
computed_confidence = (vol_confidence + funding_confidence) / 2
```

## Inputs

| Input | Source | Definition |
| --- | --- | --- |
| `vol_confidence` | `strategy_votes.jsonl` | Float from the volatility strategy in `[0.0, 1.0]` |
| `funding_confidence` | `funding_snapshot.jsonl` | `min(funding_rate_abs * 25, 0.60)` |

## Calibration Principles

| Principle | Meaning |
| --- | --- |
| Confidence must be earned | No hardcoded execution confidence |
| Confidence should be rare | High-confidence states should not be common |
| Confidence must be penalized when wrong | Overconfidence is a model defect |

## Gate Behavior

| Condition | Result |
| --- | --- |
| `computed_confidence < 0.50` | `ABSTAIN` with `confidence_below_threshold` |
| `0.50 <= computed_confidence < 0.65` | `ABSTAIN` because entry minimum is not met |
| `computed_confidence >= 0.65` and all other gates pass | Eligible for `ALIGNED` |

## Operational Consequence

Confidence is no longer a constant. It is recomputed from live strategy output and live funding intensity on every evaluation cycle.
