import re


# High-risk safety categories.
# These are intentionally simple deterministic signals designed
# for fast runtime governance.

SAFETY_PATTERNS = {

    "violence": [
        r"\bhow to kill\b",
        r"\bhow to murder\b",
        r"\bhow to assassinate\b",
        r"\bhow to torture\b",
        r"\bmake a bomb\b",
        r"\bbuild a bomb\b",
        r"\bmake an explosive\b",
        r"\bbuild an explosive\b",
    ],

    "weapons": [
        r"\bhow to make a gun\b",
        r"\bhow to build a gun\b",
        r"\bhow to make a weapon\b",
        r"\bhow to build a weapon\b",
        r"\bhow to make a firearm\b",
        r"\bhow to build a firearm\b",
    ],

    "self_harm": [
        r"\bhow to kill myself\b",
        r"\bhow to commit suicide\b",
        r"\bways to commit suicide\b",
        r"\bhow to self[- ]harm\b",
        r"\bhow to hurt myself\b",
    ],

    "illegal_activity": [
        r"\bhow to hack\b",
        r"\bhow to steal\b",
        r"\bhow to rob\b",
        r"\bhow to break into\b",
        r"\bhow to evade police\b",
    ],

    "credential_theft": [
        r"\bsteal passwords\b",
        r"\bsteal credentials\b",
        r"\bget someone's password\b",
        r"\bget someone else's password\b",
        r"\bsteal login credentials\b",
    ],
}


def evaluate_safety(text: str) -> dict:
    """
    Fast deterministic safety guard.

    No Gemini/API calls.
    """

    if not text or not text.strip():

        return {
            "risk": 0.0,
            "status": "PASS",
            "violations": [],
            "reason": "No text provided."
        }

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()

    violations = []

    for category, patterns in SAFETY_PATTERNS.items():

        for pattern in patterns:

            matches = re.findall(
                pattern,
                normalized,
                flags=re.IGNORECASE
            )

            for match in matches:

                violations.append({
                    "category": category,
                    "pattern": pattern,
                    "match": (
                        match
                        if isinstance(match, str)
                        else str(match)
                    )
                })

    # Remove duplicates
    unique_violations = []

    seen = set()

    for violation in violations:

        key = (
            violation["category"],
            violation["pattern"],
            violation["match"]
        )

        if key not in seen:

            seen.add(key)

            unique_violations.append(
                violation
            )

    violation_count = len(
        unique_violations
    )

    categories = sorted(
        set(
            item["category"]
            for item in unique_violations
        )
    )

    if violation_count == 0:

        risk = 0.0
        status = "PASS"

        reason = (
            "No obvious unsafe content detected "
            "by the local safety rule engine."
        )

    elif violation_count == 1:

        risk = 0.8
        status = "HIGH_RISK"

        reason = (
            "Potentially unsafe content detected."
        )

    else:

        risk = 1.0
        status = "BLOCK"

        reason = (
            "Multiple high-risk safety patterns "
            "were detected."
        )

    return {
        "risk": round(risk, 4),
        "status": status,
        "violations": unique_violations,
        "categories": categories,
        "reason": reason
    }