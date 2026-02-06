# CONDITIONAL_STATS_SCHEMA.md
Delta Trading Bot — Conditional Statistics Schema (V3.0)

Status: DESIGN-ONLY  
Authority: ASSOCIATE ANALYST  
Bound By: PROJECT_GOVERNANCE.md, V3_ASSOCIATE_ANALYST_SPEC.md  
Last Defined: 2026-02-06

---

## 1. PURPOSE (LOCKED)

Defines the ONLY conditional statistics allowed in V3.0.

All statistics are:
- Descriptive
- Retrospective
- Non-actionable

No statistic may influence live behavior.

---

## 2. CONDITIONING AXES (EXHAUSTIVE)

Allowed conditioning ONLY on:
- Market regime
- Time window
- Strategy identity
- Vote bias (long / short / neutral)
- Confidence buckets

Anything else is forbidden.

---

## 3. ALLOWED METRICS

Frequency:
- Vote frequency by regime
- Abstention rate by regime
- Confluence rate

Distribution:
- Confidence distributions
- Persistence length distributions

Temporal:
- Time since last similar pattern
- Duration in regime
- Regime transition frequency

---

## 4. CANONICAL OUTPUT SCHEMA

{
  "metric_name": "abstention_rate",
  "regime": "range",
  "value": 0.82,
  "sample_size": 1243,
  "window": "30d",
  "computed_at": "YYYY-MM-DDTHH:MM:SSZ"
}

---

## 5. HARD CONSTRAINTS

Statistics must NEVER:
- Trigger actions
- Modify votes
- Adjust gate logic
- Rank opportunities
- Feed decision layers

---

## 6. STORAGE RULES

- Logged
- Reproducible
- No hidden state

---

## 7. EXIT CRITERIA

Schema is complete when stable and exhaustive.

---

END OF CONDITIONAL_STATS_SCHEMA
