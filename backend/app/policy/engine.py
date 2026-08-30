
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
    application,
    privacy_risk,
    safety_risk,
    hallucination_risk,
    bias_risk,
    evidence_status=None,
    evidence_risk=0.0,
):
    """
    Central policy decision engine.

    Returns:
        {
            "decision": "ALLOW" | "EDIT" | "BLOCK" | "HUMAN_REVIEW",
            "policy": str,
            "reason": str
        }
    """

    # ---------------------------------------------------------
    # Overall risk
    # ---------------------------------------------------------

    overall_risk = max(
        privacy_risk,
        safety_risk,
        
        bias_risk,
        evidence_risk,
    )

    # ---------------------------------------------------------
    # Policy
    # ---------------------------------------------------------

    policy_map = {
        "customer_support": "Customer Support",
        "internal_assistant": "Internal Assistant",
        "decision_support": "Decision Support",
    }

    policy = policy_map.get(
        application,
        "Default"
    )

    # ---------------------------------------------------------
    # HARD BLOCK CONDITIONS
    # ---------------------------------------------------------

    if privacy_risk >= 0.85:
        return {
            "decision": "BLOCK",
            "policy": policy,
            "reason": (
                f"Critical privacy risk "
                f"({privacy_risk:.2f})"
            ),
        }

    if safety_risk >= 0.85:
        return {
            "decision": "BLOCK",
            "policy": policy,
            "reason": (
                f"Critical safety risk "
                f"({safety_risk:.2f})"
            ),
        }

    # ---------------------------------------------------------
    # EVIDENCE CONTRADICTION
    # ---------------------------------------------------------

    if evidence_status == "CONTRADICTED":
        return {
            "decision": "BLOCK",
            "policy": policy,
            "reason": (
                "AI response contradicts trusted "
                "organizational evidence."
            ),
        }

    # ---------------------------------------------------------
    # HIGH HALLUCINATION
    # ---------------------------------------------------------

    if hallucination_risk >= 0.85:
        return {
            "decision": "HUMAN_REVIEW",
            "policy": policy,
            "reason": (
                f"High hallucination/evidence risk "
                f"({hallucination_risk:.2f})"
            ),
        }

    # ---------------------------------------------------------
    # HIGH BIAS
    # ---------------------------------------------------------

    if bias_risk >= 0.85:
        return {
            "decision": "HUMAN_REVIEW",
            "policy": policy,
            "reason": (
                f"High bias risk "
                f"({bias_risk:.2f})"
            ),
        }

    # ---------------------------------------------------------
    # MODERATE RISKS
    # ---------------------------------------------------------

    if (
        privacy_risk >= 0.50
        or safety_risk >= 0.50
        or bias_risk >= 0.50
    ):
        return {
            "decision": "EDIT",
            "policy": policy,
            "reason": (
                f"Moderate governance risk "
                f"({overall_risk:.2f})"
            ),
        }

    # ---------------------------------------------------------
    # UNCERTAIN EVIDENCE
    # ---------------------------------------------------------

    if evidence_status in (
        "UNCERTAIN",
        "UNVERIFIED",
        "NO_EVIDENCE",
    ):
        return {
            "decision": "EDIT",
            "policy": policy,
            "reason": (
                "Response contains claims that "
                "could not be sufficiently verified "
                "against trusted evidence."
            ),
        }

    # ---------------------------------------------------------
    # ALLOW
    # ---------------------------------------------------------

    return {
        "decision": "ALLOW",
        "policy": policy,
        "reason": (
            f"Overall risk = "
            f"{overall_risk:.2f}"
        ),
    }

