# V4 — Stress & Counterfactual Design
Senior Analyst Layer (Design Only)

Status: DESIGN — NO IMPLEMENTATION

---

## PURPOSE

Stress testing exists to **break hypotheses**.

If a hypothesis survives stress, it earns credibility.
If it fails, that is success.

---

## STRESS METHODS (DESIGN)

1. Feature Removal Test  
   Remove one feature → does hypothesis collapse?

2. Time Randomization  
   Shuffle timestamps → does effect disappear?

3. Regime Inversion  
   Flip regime labels → does outcome persist?

4. Symbol Isolation  
   Test hypothesis per symbol independently

---

## ACCEPTABLE OUTCOMES

- Hypothesis fails under stress → EXPECTED
- Hypothesis weakens → ACCEPTABLE
- Hypothesis survives → RARE, valuable

---

## FORBIDDEN OUTCOMES

- Hypothesis survives all stress easily
- Results improve under randomization
- Outcomes depend on one symbol only

---

END OF DOCUMENT
