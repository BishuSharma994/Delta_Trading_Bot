# tools/replay.py
# Offline replay of evaluator to verify parity with live decisions

from core.feature_pipeline import build_feature_vector
from core.evaluator import evaluate

SYMBOL = "BTCUSD"
ITERATIONS = 300  # simulate ~300 decision cycles


def main():
    state_counts = {}

    for _ in range(ITERATIONS):
        features = build_feature_vector(SYMBOL)
        decision = evaluate(features)

        state = decision.get("state")
        state_counts[state] = state_counts.get(state, 0) + 1

    print("Replay state distribution:")
    for k, v in state_counts.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
