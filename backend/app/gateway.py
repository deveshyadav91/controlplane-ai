from app.guards.privacy import evaluate_privacy
from app.guards.safety import evaluate_safety


def preflight_check(prompt: str) -> dict:

    privacy = evaluate_privacy(prompt)

    safety = evaluate_safety(prompt)

    # Critical safety violation
    if safety["risk"] >= 0.90:

        return {
            "allowed": False,
            "decision": "BLOCK",
            "reason": "Unsafe request detected",
            "privacy": privacy,
            "safety": safety,
        }

    # Critical PII in input
    if privacy["risk"] >= 0.90:

        return {
            "allowed": False,
            "decision": "BLOCK",
            "reason": "Sensitive information detected in request",
            "privacy": privacy,
            "safety": safety,
        }

    return {
        "allowed": True,
        "decision": "ALLOW",
        "reason": "Pre-flight checks passed",
        "privacy": privacy,
        "safety": safety,
    }