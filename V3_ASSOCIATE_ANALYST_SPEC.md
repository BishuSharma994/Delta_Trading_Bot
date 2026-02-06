# V3_ASSOCIATE_ANALYST_SPEC.md
Delta Trading Bot — Associate Analyst Layer (V3.0)

Status: DESIGN-ONLY (NO CODE)  
Authority Level: ANALYST (NO EXECUTION)  
Depends On: PROJECT_GOVERNANCE.md  
Last Defined: 2026-02-06

---

## 1. PURPOSE OF V3.0 (NON-NEGOTIABLE)

V3.0 introduces contextual market understanding on top of the existing
Junior Analyst system.

The purpose of V3.0 is to answer:
- What kind of market is this right now?
- How unusual is the current signal context?
- How should existing signals be interpreted given that context?

V3.0 does not attempt to improve performance or enable execution.

---

## 2. WHAT V3.0 ADDS (RELATIVE TO V2.x)

V3.0 adds context, not authority.

It introduces:
1. Market regime classification
2. Conditional statistics (descriptive only)
3. Pattern rarity measurement
4. Context annotations attached to existing artifacts

All additions are read-only and non-intrusive.

---

## 3. WHAT V3.0 EXPLICITLY DOES NOT DO

V3.0 must NEVER:
- Place trades
- Recommend buy/sell actions
- Size positions
- Allocate capital
- Adjust execution gate parameters
- Override strategy votes
- Optimize strategies
- Introduce machine learning
- Introduce feedback loops

---

## 4. NEW ANALYTICAL SUBSYSTEMS (DESIGN ONLY)

### 4.1 Regime Classification Engine

Purpose:
Label the market environment at each timestamp.

Initial regime set:
- Trend (up / down)
- Range
- Volatility expansion
- Volatility compression
- Transition / unclear

Properties:
- Deterministic
- Feature-based
- No learning

Example output:
{
  "timestamp_utc": "...",
  "symbol": "...",
  "regime": "range",
  "confidence": 0.73
}

---

### 4.2 Conditional Statistics Engine

Purpose:
Provide descriptive statistics conditioned on context.

Examples:
- Strategy confidence by regime
- Abstention rate by regime
- Confluence frequency by regime

Rules:
- Descriptive only
- No thresholds
- No decision impact

---

### 4.3 Pattern Rarity Index

Purpose:
Measure how uncommon the current signal configuration is historically.

Example:
{
  "pattern_signature": "...",
  "historical_frequency": 0.8,
  "rarity_score": 0.92
}

---

### 4.4 Context Annotation Layer

Purpose:
Attach V3 context to existing V2 artifacts without modifying them.

Example:
{
  "vote_id": "...",
  "regime": "range",
  "regime_confidence": 0.73,
  "rarity_score": 0.92
}

---

## 5. INTEGRATION RULES (STRICT)

- V3 consumes V2 outputs
- V2 is never modified by V3
- Execution Gate remains final authority
- All outputs are logged and auditable
- No live behavior change

---

## 6. DATA FLOW

[ Live Data ]
      ↓
[ Feature Extraction ]
      ↓
[ Strategies → Votes ]        (V2.x)
      ↓
[ Regime Classification ]    (V3.0)
      ↓
[ Context Annotation ]       (V3.0)
      ↓
[ Execution Gate ]           (UNCHANGED)
      ↓
[ Logging / Offline Analysis ]

---

## 7. EXIT CRITERIA FOR V3.0

V3.0 is complete when:
- Regime definitions are stable
- Context schemas are frozen
- Outputs are reproducible
- No authority creep exists
- Offline replay can include V3 context

---

## 8. GOVERNANCE BINDING

This specification is binding under PROJECT_GOVERNANCE.md.

Any deviation requires explicit revision and approval.

---

END OF V3_ASSOCIATE_ANALYST_SPEC
