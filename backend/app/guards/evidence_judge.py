
import re


def _normalize(text: str) -> str:
    """Normalize text for lightweight lexical comparison."""

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


def _tokenize(text: str) -> set[str]:
    """Extract simple alphanumeric tokens."""

    return set(
        re.findall(
            r"\b[a-zA-Z0-9]+\b",
            _normalize(text)
        )
    )


def _keyword_overlap(
    claim: str,
    evidence: str
) -> float:
    """
    Calculate how much of the claim vocabulary
    appears in the evidence.
    """

    claim_words = _tokenize(claim)
    evidence_words = _tokenize(evidence)

    if not claim_words:
        return 0.0

    return (
        len(claim_words & evidence_words)
        / len(claim_words)
    )


def _contains_negation(text: str) -> bool:
    """Detect simple negation patterns."""

    text = _normalize(text)

    negations = {
        "not",
        "no",
        "never",
        "cannot",
        "can't",
        "isn't",
        "aren't",
        "doesn't",
        "don't",
        "won't",
        "shouldn't",
        "without",
        "false",
        "unable",
    }

    words = set(
        re.findall(
            r"\b[a-zA-Z']+\b",
            text
        )
    )

    return bool(words & negations)


def _semantic_score(
    evidence: dict
) -> float:
    """
    FAISS similarity score.

    IndexFlatIP + normalized embeddings produces
    cosine similarity in the range [-1, 1].
    """

    score = float(
        evidence.get(
            "score",
            0.0
        )
    )

    # Clamp to a safe range.
    return max(
        0.0,
        min(1.0, score)
    )


def judge_claim(
    claim: str,
    evidence: list[dict]
) -> dict:
    """
    Local evidence judge.

    IMPORTANT:
    This function intentionally does NOT call Gemini.

    It combines:
        - FAISS semantic similarity
        - lexical overlap
        - simple contradiction signals

    This keeps the evidence guard extremely fast
    and avoids consuming Gemini API quota.
    """

    if not evidence:

        return {
            "support": 0.0,
            "contradiction": 0.0,
            "uncertainty": 1.0,
            "status": "UNVERIFIED",
            "reason": (
                "No trusted evidence was retrieved."
            ),
            "evidence": []
        }

    # Best semantic match.
    best_evidence = max(
        evidence,
        key=lambda item: float(
            item.get("score", 0.0)
        )
    )

    similarity = _semantic_score(
        best_evidence
    )

    # Calculate lexical overlap against
    # all retrieved evidence and keep the best.
    best_overlap = max(
        (
            _keyword_overlap(
                claim,
                item.get("text", "")
            )
            for item in evidence
        ),
        default=0.0
    )

    # ------------------------------------------
    # Support score
    # ------------------------------------------

    support = (
        0.70 * similarity
        +
        0.30 * best_overlap
    )

    support = max(
        0.0,
        min(1.0, support)
    )

    # ------------------------------------------
    # Simple contradiction signal
    # ------------------------------------------
    #
    # We only use contradiction when the evidence
    # is strongly related to the claim.
    #
    # This prevents unrelated documents from
    # being incorrectly classified as contradictory.
    # ------------------------------------------

    contradiction = 0.0

    if similarity >= 0.55:

        claim_negated = _contains_negation(
            claim
        )

        evidence_negated = _contains_negation(
            best_evidence.get(
                "text",
                ""
            )
        )

        # Different negation state + strong
        # semantic similarity can indicate conflict.
        if (
            claim_negated
            != evidence_negated
            and similarity >= 0.65
        ):
            contradiction = min(
                1.0,
                similarity
            )

    # ------------------------------------------
    # Classification
    # ------------------------------------------

    if contradiction >= 0.70:

        status = "CONTRADICTED"

        uncertainty = 0.0

        reason = (
            "The claim appears to conflict "
            "with strongly matching trusted evidence."
        )

    elif support >= 0.70:

        status = "SUPPORTED"

        contradiction = 0.0

        uncertainty = 1.0 - support

        reason = (
            "The claim is strongly supported "
            "by retrieved trusted evidence."
        )

    elif support >= 0.40:

        status = "UNCERTAIN"

        contradiction = 0.0

        uncertainty = 1.0 - support

        reason = (
            "Retrieved evidence is related to "
            "the claim but does not strongly "
            "establish it."
        )

    else:

        status = "UNVERIFIED"

        contradiction = 0.0

        uncertainty = 1.0 - support

        reason = (
            "No sufficiently strong trusted "
            "evidence supports the claim."
        )

    return {
        "support": round(
            support,
            4
        ),

        "contradiction": round(
            contradiction,
            4
        ),

        "uncertainty": round(
            uncertainty,
            4
        ),

        "status": status,

        "reason": reason,

        "evidence": evidence
    }

