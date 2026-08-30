POLICIES = {

    "customer_support": {
        "name": "Customer Support",
        "max_risk": 0.70,
        "block_risk": 0.85,
        "require_human_review": False,
        "require_evidence": False,
    },

    "internal_assistant": {
        "name": "Internal Knowledge Assistant",
        "max_risk": 0.50,
        "block_risk": 0.80,
        "require_human_review": True,
        "require_evidence": False,
    },

    "decision_support": {
        "name": "Decision Support",
        "max_risk": 0.25,
        "block_risk": 0.60,
        "require_human_review": True,
        "require_evidence": True,
    },
}


def get_policy(application: str):

    return POLICIES.get(
        application,
        POLICIES["customer_support"]
    )


def make_decision(
    risk_score: float,
    application: str,
    evidence_risk: float = 0.0
):

    policy = get_policy(application)

    # Critical risk → BLOCK
    if risk_score >= policy["block_risk"]:

        return {
            "decision": "BLOCK",
            "reason": "Risk exceeds blocking threshold.",
            "policy": policy["name"],
        }


    # Evidence required but insufficient
    if (
        policy["require_evidence"]
        and evidence_risk >= 0.50
    ):

        return {
            "decision": "HUMAN_REVIEW",
            "reason": "Evidence verification required.",
            "policy": policy["name"],
        }


    # Human review threshold
    if (
        policy["require_human_review"]
        and risk_score >= policy["max_risk"]
    ):

        return {
            "decision": "HUMAN_REVIEW",
            "reason": "Risk exceeds automatic approval threshold.",
            "policy": policy["name"],
        }


    # Moderate risk → EDIT
    if risk_score >= policy["max_risk"]:

        return {
            "decision": "EDIT",
            "reason": "Response requires policy-based modification.",
            "policy": policy["name"],
        }


    # Safe
    return {
        "decision": "ALLOW",
        "reason": "Response satisfies policy requirements.",
        "policy": policy["name"],
    }