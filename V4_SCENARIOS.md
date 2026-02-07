# V4 — Scenario Taxonomy
Senior Analyst Layer (Design Only)

Status: DESIGN — NO IMPLEMENTATION

---

## PURPOSE

Scenarios group **market contexts**, not actions.
They describe *where the market is*, not *what to do*.

---

## SCENARIO DEFINITION

Each scenario contains:

1. Scenario Name
2. Regime Label(s)
3. Feature State Profile
4. Historical Frequency
5. Known Failure Modes
6. Risk Flags

---

## EXAMPLE SCENARIOS

### Scenario: Crowded Long + Volatility Compression
- Funding: Elevated
- Volatility: Compressing
- Regime: Range → Expansion risk
- Frequency: Rare
- Risk: Violent liquidation cascades

---

### Scenario: Post-Trend Funding Normalization
- Funding: Normalizing
- Volatility: Elevated
- Regime: Trend exhaustion
- Risk: False continuation signals

---

## RULES

- Scenarios do NOT generate signals
- Scenarios do NOT suggest trades
- Scenarios may overlap
- Scenarios exist to guide *attention*, not action

---

END OF DOCUMENT
