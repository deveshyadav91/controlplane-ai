import re
from dataclasses import dataclass


@dataclass
class PIIViolation:
    type: str
    confidence: float
    matched_text: str


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"
)

CARD_PATTERN = re.compile(
    r"\b(?:\d[ -]*?){13,19}\b"
)

API_KEY_PATTERN = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{20,}|"
    r"AIza[A-Za-z0-9_-]{20,})\b"
)


def detect_pii(text: str) -> list[PIIViolation]:

    violations = []

    # Email
    for match in EMAIL_PATTERN.finditer(text):
        violations.append(
            PIIViolation(
                type="EMAIL",
                confidence=0.99,
                matched_text=match.group()
            )
        )

    # Indian phone number
    for match in PHONE_PATTERN.finditer(text):
        violations.append(
            PIIViolation(
                type="PHONE",
                confidence=0.98,
                matched_text=match.group()
            )
        )

    # Credit/debit card
    for match in CARD_PATTERN.finditer(text):

        digits = re.sub(r"\D", "", match.group())

        if 13 <= len(digits) <= 19:

            violations.append(
                PIIViolation(
                    type="CREDIT_CARD",
                    confidence=0.95,
                    matched_text=match.group()
                )
            )

    # API keys
    for match in API_KEY_PATTERN.finditer(text):
        violations.append(
            PIIViolation(
                type="API_KEY",
                confidence=0.99,
                matched_text=match.group()
            )
        )

    return violations
def redact_pii(text: str, violations: list[PIIViolation]) -> str:

    redacted_text = text

    # Replace longest matches first
    violations = sorted(
        violations,
        key=lambda x: len(x.matched_text),
        reverse=True
    )

    for violation in violations:

        placeholder = f"[{violation.type}_REDACTED]"

        redacted_text = redacted_text.replace(
            violation.matched_text,
            placeholder
        )

    return redacted_text
def evaluate_privacy(text: str) -> dict:

    violations = detect_pii(text)

    if not violations:

        return {
            "risk": 0.0,
            "status": "PASS",
            "violations": [],
            "redacted_text": text
        }

    max_confidence = max(
        violation.confidence
        for violation in violations
    )

    redacted_text = redact_pii(
        text,
        violations
    )

    return {
        "risk": max_confidence,
        "status": "PII_DETECTED",
        "violations": [
            {
                "type": violation.type,
                "confidence": violation.confidence
            }
            for violation in violations
        ],
        "redacted_text": redacted_text
    }