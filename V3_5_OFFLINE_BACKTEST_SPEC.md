# V3_5_OFFLINE_BACKTEST_SPEC.md
Delta Trading Bot — Full-Stack Offline Backtesting Specification (V3.5)

Status: DESIGN-ONLY  
Authority: ANALYST (NO EXECUTION)  
Bound By: PROJECT_GOVERNANCE.md  
Depends On: V2.x + V3.0 (Design)  
Last Defined: 2026-02-06

---

## 1. PURPOSE (LOCKED)

V3.5 defines a deterministic, offline-only backtesting framework that
replays the **entire analytical decision stack** without placing trades.

The goal is **behavioral validation**, not profit measurement.

---

## 2. WHAT IS REPLAYED

The offline backtest replays, in order:

1. Historical market data
2. Feature extraction
3. Strategy vote generation (V2.x)
4. Context annotation (V3.0)
5. Execution gate evaluation (V2.4)
6. Decision logging

No execution engine is involved.

---

## 3. WHAT IS MEASURED (DESCRIPTIVE ONLY)

Allowed measurements:
- Frequency of ALLOW vs DENY
- Context distribution at ALLOW events
- Gate rejection reasons
- Signal scarcity over time
- Regime distribution over history

Explicitly NOT measured:
- PnL
- Drawdown
- Sharpe
- Returns
- Optimization metrics

---

## 4. BACKTEST OUTPUT ARTIFACTS

Canonical outputs include:
- Decision timelines
- Gate outcome summaries
- Context-conditioned statistics
- Reproducible logs

All outputs are read-only and excluded from Git.

---

## 5. HARD CONSTRAINTS

Backtesting must NEVER:
- Enable execution
- Bypass the gate
- Tune parameters
- Reweight strategies
- Introduce learning
- Rank opportunities

---

## 6. EXIT CRITERIA

V3.5 design is complete when:
- Replay order is frozen
- Output schemas are defined
- Measurements are non-actionable
- Governance invariants are preserved

---

END OF V3_5_OFFLINE_BACKTEST_SPEC
