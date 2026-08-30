from dataclasses import dataclass


@dataclass
class RiskResult:
    overall_risk: float
    risk_level: str
    breakdown: dict
    reasons: list[str]


def _clamp(value: float) -> float:
    """Keep risk values safely between 0 and 1."""
    return max(0.0, min(1.0, float(value)))


def _risk_level(risk: float) -> str:
    """
    Convert numerical risk into a human-readable level.
    """
    if risk < 0.30:
        return "LOW"

    if risk < 0.50:
        return "MEDIUM"

    if risk < 0.70:
        return "HIGH"

    return "CRITICAL"


def calculate_risk(
    privacy: float,
    safety: float,
    hallucination: float,
    bias: float,
) -> RiskResult:

    # --------------------------------------------------
    # 1. Normalize inputs
    # --------------------------------------------------

    privacy = _clamp(privacy)
    safety = _clamp(safety)
    hallucination = _clamp(hallucination)
    bias = _clamp(bias)

    breakdown = {
        "privacy": round(privacy, 4),
        "safety": round(safety, 4),
        "hallucination": round(hallucination, 4),
        "bias": round(bias, 4),
    }

    # --------------------------------------------------
    # 2. Weighted risk
    # --------------------------------------------------
    #
    # Safety and privacy are more important than bias.
    # Evidence/hallucination is also important because
    # this is an AI governance system.
    #

    weights = {
        "privacy": 0.30,
        "safety": 0.30,
        "hallucination": 0.25,
        "bias": 0.15,
    }

    weighted_risk = (
        privacy * weights["privacy"]
        + safety * weights["safety"]
        + hallucination * weights["hallucination"]
        + bias * weights["bias"]
    )

    # --------------------------------------------------
    # 3. Critical-risk override
    # --------------------------------------------------
    #
    # A weighted average alone is dangerous.
    #
    # Example:
    #
    # privacy = 1.0
    # safety = 0.0
    # hallucination = 0.0
    # bias = 0.0
    #
    # Weighted risk = 0.30
    #
    # That must NOT hide a severe privacy violation.
    #

    critical_risks = [
        privacy,
        safety,
    ]

    critical_max = max(critical_risks)

    overall_risk = max(
        weighted_risk,
        critical_max * 0.85
    )

    # --------------------------------------------------
    # 4. Evidence / hallucination escalation
    # --------------------------------------------------

    if hallucination >= 0.90:
        overall_risk = max(
            overall_risk,
            0.80
        )

    elif hallucination >= 0.70:
        overall_risk = max(
            overall_risk,
            0.65
        )

    # --------------------------------------------------
    # 5. Bias escalation
    # --------------------------------------------------

    if bias >= 0.90:
        overall_risk = max(
            overall_risk,
            0.75
        )

    # --------------------------------------------------
    # 6. Final clamp
    # --------------------------------------------------

    overall_risk = _clamp(overall_risk)

    # --------------------------------------------------
    # 7. Determine risk level
    # --------------------------------------------------

    level = _risk_level(
        overall_risk
    )

    # --------------------------------------------------
    # 8. Generate explanations
    # --------------------------------------------------

    reasons = []

    if privacy >= 0.70:
        reasons.append(
            f"High privacy risk ({privacy:.2f})"
        )

    elif privacy >= 0.40:
        reasons.append(
            f"Moderate privacy risk ({privacy:.2f})"
        )

    if safety >= 0.70:
        reasons.append(
            f"High safety risk ({safety:.2f})"
        )

    elif safety >= 0.40:
        reasons.append(
            f"Moderate safety risk ({safety:.2f})"
        )

    if hallucination >= 0.90:
        reasons.append(
            f"Critical hallucination/evidence risk "
            f"({hallucination:.2f})"
        )

    elif hallucination >= 0.70:
        reasons.append(
            f"High hallucination/evidence risk "
            f"({hallucination:.2f})"
        )

    elif hallucination >= 0.40:
        reasons.append(
            f"Moderate hallucination/evidence risk "
            f"({hallucination:.2f})"
        )

    if bias >= 0.70:
        reasons.append(
            f"High bias risk ({bias:.2f})"
        )

    elif bias >= 0.40:
        reasons.append(
            f"Moderate bias risk ({bias:.2f})"
        )

    # --------------------------------------------------
    # 9. Default explanation
    # --------------------------------------------------

    if not reasons:
        reasons.append(
            "No significant governance risks detected."
        )

    return RiskResult(
        overall_risk=round(
            overall_risk,
            4
        ),
        risk_level=level,
        breakdown=breakdown,
        reasons=reasons,
    )