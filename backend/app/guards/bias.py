import re


# Terms/patterns that commonly indicate discriminatory or stereotyping
# language. This is intentionally conservative: the guard flags potential
# bias rather than claiming that every match is definitively biased.

BIAS_PATTERNS = {
    "gender": [
        r"\bwomen are\b",
        r"\bmen are\b",
        r"\bgirls are\b",
        r"\bboys are\b",
        r"\bfemales are\b",
        r"\bmales are\b",
        r"\bwomen can't\b",
        r"\bmen can't\b",
        r"\bwomen cannot\b",
        r"\bmen cannot\b",
    ],

    "race_ethnicity": [
        r"\b[a-z]+ people are (lazy|stupid|violent|criminals?)\b",
        r"\b[a-z]+ people (are|tend to be)\b",
    ],

    "age": [
        r"\bold people are\b",
        r"\byoung people are\b",
        r"\bthe elderly are\b",
        r"\bold people can't\b",
        r"\byoung people can't\b",
    ],

    "disability": [
        r"\bdisabled people are\b",
        r"\bdisabled people can't\b",
        r"\bpeople with disabilities are\b",
    ],

    "religion": [
        r"\bmuslims are\b",
        r"\bchristians are\b",
        r"\bhindus are\b",
        r"\bjews are\b",
        r"\bbuddhists are\b",
        r"\batheists are\b",
    ],

    "stereotyping": [
        r"\ball \w+ are\b",
        r"\bthose people are\b",
        r"\bpeople like that are\b",
        r"\bthey are all\b",
    ],
}


def evaluate_bias(text: str) -> dict:
    """
    Fast deterministic bias guard.

    No external API calls.
    No Gemini.
    """

    if not text or not text.strip():
        return {
            "risk": 0.0,
            "status": "PASS",
            "categories": [],
            "violations": [],
            "reason": "No text provided."
        }

    normalized = re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()

    violations = []
    categories = set()

    for category, patterns in BIAS_PATTERNS.items():

        for pattern in patterns:

            matches = re.findall(
                pattern,
                normalized,
                flags=re.IGNORECASE
            )

            if matches:

                categories.add(category)

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

    # Remove duplicate violations
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
            unique_violations.append(violation)

    violation_count = len(unique_violations)

    if violation_count == 0:

        risk = 0.0
        status = "PASS"

        reason = (
            "No obvious biased or stereotyping "
            "language detected by the local rule engine."
        )

    elif violation_count == 1:

        risk = 0.5
        status = "REVIEW"

        reason = (
            "Potential biased or stereotyping "
            "language detected."
        )

    else:

        risk = min(
            1.0,
            0.5 + (violation_count - 1) * 0.15
        )

        status = "HIGH_RISK"

        reason = (
            "Multiple potential biased or "
            "stereotyping expressions detected."
        )

    return {
        "risk": round(risk, 4),
        "status": status,
        "categories": sorted(categories),
        "violations": unique_violations,
        "reason": reason
    }