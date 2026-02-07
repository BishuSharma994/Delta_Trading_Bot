# V4 — Hypotheses Specification
Senior Analyst Layer (Design Only)

Status: DESIGN — NO IMPLEMENTATION

---

## PURPOSE

This document defines how hypotheses are formed, tested, and invalidated.
A hypothesis is a **research statement**, not a trading rule.

Hypotheses exist to answer:
- Under what conditions does market behavior change?
- When do signals become *less unreliable* (not profitable)?
- What evidence must align before attention is warranted?

---

## HYPOTHESIS STRUCTURE (MANDATORY)

Each hypothesis MUST define:

1. Hypothesis ID
2. Statement
3. Preconditions
4. Observation Window
5. Null Hypothesis
6. Failure Conditions
7. Required Evidence
8. Expected Rarity

---

## EXAMPLE (NON-OPERATIONAL)

**ID:** HYP-001  
**Statement:**  
When funding rate is extreme AND volatility compresses over multiple windows, breakouts become more probable.

**Preconditions:**
- funding_rate_abs = hot
- pre_volatility_5m = hot but declining
- persistence >= N windows

**Null Hypothesis:**  
Breakouts occur at random frequency regardless of funding/volatility interaction.

**Failure Conditions:**
- Breakouts do not exceed baseline frequency
- Results disappear under time randomization

**Expected Rarity:**  
Very high (exceptional market state)

---

## GOVERNANCE RULES

- Hypotheses are allowed to FAIL
- No hypothesis is ever promoted automatically
- Hypotheses do NOT map to execution
- All results must be reproducible offline

---

END OF DOCUMENT
