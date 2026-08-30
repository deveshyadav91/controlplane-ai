
"""
Adaptive policy engine for ControlPlane.ai.

Decides what to do with an AI response based on:
- Overall risk
- Individual guard risks
- Application type

Possible decisions:
    ALLOW
    EDIT
    HUMAN_REVIEW
    BLOCK
"""

from typing import Dict, Any


def make_decision(
    application: str,
    overall_risk: float,
    breakdown: Dict[str, float],
) -> Dict[str, Any]:
    """
    Determine the appropriate governance intervention.

    Priority:
        1. Critical privacy/safety -> BLOCK
        2. Severe hallucination/bias -> HUMAN_REVIEW
        3. Moderate risks -> EDIT
        4. Low risk -> ALLOW
    """

    privacy = float(breakdown.get("privacy", 0.0))
    safety = float(breakdown.get("safety", 0.0))
    hallucination = float(
        breakdown.get("hallucination", 0.0)
    )
    bias = float(breakdown.get("bias", 0.0))

    overall_risk = float(overall_risk)

    # --------------------------------------------------
    # 1. CRITICAL SECURITY / SAFETY
    # --------------------------------------------------

    if privacy >= 0.90:
        return {
            "decision": "BLOCK",
            "policy": application,
            "reason": (
                f"Critical privacy risk detected "
                f"({privacy:.2f})"
            ),
        }

    if safety >= 0.90:
        return {
            "decision": "BLOCK",
            "policy": application,
            "reason": (
                f"Critical safety risk detected "
                f"({safety:.2f})"
            ),
        }

    # --------------------------------------------------
    # 2. HIGH HALLUCINATION / BIAS
    # --------------------------------------------------

    if hallucination >= 0.80:
        return {
            "decision": "HUMAN_REVIEW",
            "policy": application,
            "reason": (
                f"High hallucination risk "
                f"({hallucination:.2f}) requires review"
            ),
        }

    if bias >= 0.80:
        return {
            "decision": "HUMAN_REVIEW",
            "policy": application,
            "reason": (
                f"High bias risk "
                f"({bias:.2f}) requires review"
            ),
        }

    # --------------------------------------------------
    # 3. MODERATE PRIVACY / SAFETY
    # --------------------------------------------------

    if privacy >= 0.40:
        return {
            "decision": "EDIT",
            "policy": application,
            "reason": (
                f"Privacy risk detected "
                f"({privacy:.2f}); response redaction required"
            ),
        }

    if safety >= 0.40:
        return {
            "decision": "EDIT",
            "policy": application,
            "reason": (
                f"Safety risk detected "
                f"({safety:.2f}); response requires filtering"
            ),
        }

    # --------------------------------------------------
    # 4. APPLICATION-SPECIFIC GOVERNANCE
    # --------------------------------------------------

    if application == "decision_support":

        if hallucination >= 0.50 or bias >= 0.50:
            return {
                "decision": "HUMAN_REVIEW",
                "policy": application,
                "reason": (
                    "Decision-support output requires "
                    "human verification"
                ),
            }

    if application == "internal_assistant":

        if overall_risk >= 0.60:
            return {
                "decision": "HUMAN_REVIEW",
                "policy": application,
                "reason": (
                    f"Elevated internal-assistant risk "
                    f"({overall_risk:.2f})"
                ),
            }

    # --------------------------------------------------
    # 5. OVERALL RISK
    # --------------------------------------------------

    if overall_risk >= 0.75:
        return {
            "decision": "HUMAN_REVIEW",
            "policy": application,
            "reason": (
                f"Overall risk is high "
                f"({overall_risk:.2f})"
            ),
        }

    if overall_risk >= 0.40:
        return {
            "decision": "EDIT",
            "policy": application,
            "reason": (
                f"Moderate overall risk "
                f"({overall_risk:.2f}); response edited"
            ),
        }

    # --------------------------------------------------
    # 6. SAFE
    # --------------------------------------------------

    return {
        "decision": "ALLOW",
        "policy": application,
        "reason": (
            f"Overall risk = {overall_risk:.2f}"
        ),
    }

