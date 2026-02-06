# REGIME_DEFINITION.md
Delta Trading Bot — Market Regime Taxonomy (V3.0)

Status: DESIGN-ONLY  
Authority: ASSOCIATE ANALYST  
Bound By: PROJECT_GOVERNANCE.md, V3_ASSOCIATE_ANALYST_SPEC.md  
Last Defined: 2026-02-06

---

## 1. PURPOSE

This document defines the **only valid market regimes** recognized by the
Associate Analyst (V3.0).

Regimes provide **context**, not signals.
They do not trigger actions, change votes, or influence execution.

---

## 2. CORE PRINCIPLES

- Regimes are descriptive, not predictive
- Regimes are mutually exclusive at a timestamp
- Uncertainty is an explicit state
- No regime implies tradability
- Regimes do not change system behavior

---

## 3. CANONICAL REGIME SET (V3.0)

### 3.1 TREND_UP
Market exhibits sustained directional movement upward.

Characteristics:
- Higher highs and higher lows
- Directional bias consistency
- Expanding or stable volatility

---

### 3.2 TREND_DOWN
Market exhibits sustained directional movement downward.

Characteristics:
- Lower highs and lower lows
- Directional bias consistency
- Expanding or stable volatility

---

### 3.3 RANGE
Market oscillates within bounded price levels.

Characteristics:
- Mean reversion behavior
- Low directional persistence
- Contracting volatility

---

### 3.4 VOLATILITY_EXPANSION
Market volatility increasing rapidly.

Characteristics:
- Range expansion
- Large candles or wicks
- Increased disagreement across strategies

---

### 3.5 VOLATILITY_COMPRESSION
Market volatility decreasing.

Characteristics:
- Tight ranges
- Low realized volatility
- Signal scarcity

---

### 3.6 TRANSITION
Market state is changing or ambiguous.

Characteristics:
- Regime disagreement
- Feature instability
- Low classification confidence

This regime is **explicitly valid** and preferred over forced classification.

---

## 4. REGIME CONFIDENCE

Each regime label must include a confidence score in `[0,1]`.

Low confidence implies:
- High uncertainty
- Reduced interpretability
- No behavioral implication

---

## 5. FORBIDDEN USES

Regimes must NEVER:
- Trigger trades
- Override strategies
- Modify execution gate behavior
- Adjust confidence scores
- Be optimized for performance

---

## 6. EXTENSIBILITY RULE

New regimes may only be added by:
- Documentation update
- Explicit versioning
- Offline validation

No silent expansion is allowed.

---

END OF REGIME_DEFINITION
