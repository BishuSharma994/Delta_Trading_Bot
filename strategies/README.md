# Strategy Layer (Design Contract)

- Strategies DO NOT execute trades
- Strategies DO NOT access APIs
- Strategies ONLY read features
- Strategies emit votes, not decisions

Evaluator (future):
- Collects strategy votes
- Applies risk gates
- Maintains capital discipline
- Owns final decision authority

No strategy can bypass evaluator.
