# Evaluator applies hypotheses to feature values
# No execution. No capital logic. Reject-first.

from intelligence.registry import FEATURES
from intelligence.hypotheses import HYPOTHESES, HYPOTHESES_VERSION


def evaluate(features: dict):
    """
    features: dict of computed feature_name -> value

    returns:
        {
            "allow": bool,
            "reasons": list[str],
            "evaluated_features": dict,
            "hypotheses_version": str
        }
    """

    reasons = []

    # Validate feature completeness
    for f in FEATURES:
        if f not in features:
            reasons.append(f"missing_feature:{f}")

    if reasons:
        return {
            "allow": False,
            "reasons": reasons,
            "evaluated_features": features,
            "hypotheses_version": HYPOTHESES_VERSION,
        }

    # Apply hypotheses (reject-first)
    for hypothesis in HYPOTHESES:
        for reject_signal in hypothesis["reject_if"]:
            if reject_signal in features and features.get(reject_signal):
                reasons.append(
                    f"{hypothesis['name']}:{reject_signal}"
                )

    allow = len(reasons) == 0

    return {
        "allow": allow,
        "reasons": reasons,
        "evaluated_features": features,
        "hypotheses_version": HYPOTHESES_VERSION,
    }
