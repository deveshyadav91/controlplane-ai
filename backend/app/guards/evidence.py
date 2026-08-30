
import re
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.guards.evidence_judge import judge_claim


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parents[3]

KNOWLEDGE_DIR = (
    BASE_DIR / "knowledge"
)


# ============================================================
# EVIDENCE STORE
# ============================================================

class EvidenceStore:

    def __init__(self):

        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"
        )
        self.model.max_seq_length = 256

        self.documents = []

        self.index = None

        self._load_documents()


    # ========================================================
    # LOAD KNOWLEDGE BASE
    # ========================================================

    def _load_documents(self):

        if not KNOWLEDGE_DIR.exists():

            raise RuntimeError(
                f"Knowledge directory not found: "
                f"{KNOWLEDGE_DIR}"
            )

        for file_path in KNOWLEDGE_DIR.glob(
            "*.txt"
        ):

            try:

                text = file_path.read_text(
                    encoding="utf-8"
                )

            except Exception as exc:

                print(
                    f"Warning: failed to read "
                    f"{file_path}: {exc}"
                )

                continue


            # Split documents into paragraphs.
            chunks = [
                chunk.strip()
                for chunk in text.split(
                    "\n\n"
                )
                if chunk.strip()
            ]


            for chunk in chunks:

                self.documents.append(
                    {
                        "text": chunk,
                        "source": file_path.name
                    }
                )


        if not self.documents:

            raise RuntimeError(
                "No documents found in knowledge/"
            )


        # ----------------------------------------------------
        # Create embeddings ONCE at startup.
        # ----------------------------------------------------

        texts = [
            document["text"]
            for document
            in self.documents
        ]


        embeddings = self.model.encode(
            texts,

            normalize_embeddings=True,

            convert_to_numpy=True,

            show_progress_bar=False,

            batch_size=32
        )


        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )


        dimension = embeddings.shape[1]


        # Inner Product + normalized vectors
        # = cosine similarity.

        self.index = faiss.IndexFlatIP(
            dimension
        )


        self.index.add(
            embeddings
        )


        print(
            f"EvidenceStore loaded "
            f"{len(self.documents)} chunks."
        )


    # ========================================================
    # SINGLE SEARCH
    # ========================================================

    def search(
        self,
        query: str,
        top_k: int = 3
    ):

        results = self.batch_search(
            [query],
            top_k=top_k
        )

        if not results:

            return []

        return results[0]


    # ========================================================
    # BATCH SEARCH
    # ========================================================

    def batch_search(
        self,
        queries: list[str],
        top_k: int = 3
    ):

        if not queries:

            return []


        if self.index is None:

            return [
                []
                for _ in queries
            ]


        # Never request more results than
        # available documents.

        k = min(
            top_k,
            len(self.documents)
        )


        # ----------------------------------------------------
        # ONE encoder call for ALL claims.
        # ----------------------------------------------------

        embeddings = self.model.encode(
            queries,

            normalize_embeddings=True,

            convert_to_numpy=True,

            show_progress_bar=False,

            batch_size=32
        )


        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )


        # ----------------------------------------------------
        # ONE FAISS search for ALL claims.
        # ----------------------------------------------------

        scores, indices = (
            self.index.search(
                embeddings,
                k
            )
        )


        all_results = []


        for query_scores, query_indices in zip(
            scores,
            indices
        ):

            results = []


            for score, index in zip(
                query_scores,
                query_indices
            ):

                if index < 0:
                    continue


                document = self.documents[
                    int(index)
                ]


                results.append(
                    {
                        "text": document["text"],

                        "source": document[
                            "source"
                        ],

                        "score": round(
                            float(score),
                            4
                        )
                    }
                )


            all_results.append(
                results
            )


        return all_results


# ============================================================
# CLAIM EXTRACTION
# ============================================================

def extract_claims(
    answer: str
) -> list[str]:
    """
    Extract potentially factual claims from
    the generated response.

    This is intentionally lightweight and local.
    """

    if not answer:

        return []


    # Remove markdown formatting.

    text = re.sub(
        r"[*_`#]",
        "",
        answer
    )


    # Split into sentences.

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )


    claims = []


    for sentence in sentences:

        sentence = sentence.strip()


        if not sentence:
            continue


        # Ignore very short fragments.

        if len(
            sentence.split()
        ) < 5:

            continue


        # Ignore headings.

        if sentence.endswith(":"):

            continue


        # Remove common list prefixes.

        sentence = re.sub(
            r"^[\-\*\d\.\)\s]+",
            "",
            sentence
        ).strip()


        if not sentence:
            continue


        claims.append(
            sentence
        )


    # Limit claims so a long answer doesn't
    # create excessive CPU work.

    return claims[:8]


# ============================================================
# CLAIM RISK
# ============================================================

def calculate_claim_risk(
    judgement: dict
) -> float:

    contradiction = float(
        judgement.get(
            "contradiction",
            0.0
        )
    )

    uncertainty = float(
        judgement.get(
            "uncertainty",
            1.0
        )
    )


    return round(
        max(
            contradiction,
            uncertainty
        ),
        4
    )


# ============================================================
# EVIDENCE EVALUATION
# ============================================================

def evaluate_evidence(
    answer: str,
    store: EvidenceStore
) -> dict:
    """
    Evaluate the generated answer claim-by-claim.

    Compatible with the existing:

        run_parallel_guards()

    and frontend:

        guards.evidence.claims[]
    """

    claims = extract_claims(
        answer
    )


    # --------------------------------------------------------
    # No claims
    # --------------------------------------------------------

    if not claims:

        return {
            "risk": 0.0,

            "support": 1.0,

            "contradiction": 0.0,

            "uncertainty": 0.0,

            "status": "NO_CLAIMS",

            "reason": "No factual claims detected.",

            "claims": [],

            "evidence": []
        }


    # --------------------------------------------------------
    # Batch retrieval.
    #
    # IMPORTANT:
    # Do NOT call store.search() inside the loop.
    # --------------------------------------------------------

    evidence_sets = store.batch_search(
        claims,
        top_k=3
    )


    claim_results = []


    # --------------------------------------------------------
    # Judge each claim locally.
    # --------------------------------------------------------

    for claim, evidence in zip(
        claims,
        evidence_sets
    ):

        judgement = judge_claim(
            claim,
            evidence
        )


        claim_result = {

            "claim": claim,

            "status": judgement.get(
                "status",
                "UNVERIFIED"
            ),

            "risk": calculate_claim_risk(
                judgement
            ),

            "support": round(
                float(
                    judgement.get(
                        "support",
                        0.0
                    )
                ),
                4
            ),

            "contradiction": round(
                float(
                    judgement.get(
                        "contradiction",
                        0.0
                    )
                ),
                4
            ),

            "uncertainty": round(
                float(
                    judgement.get(
                        "uncertainty",
                        1.0
                    )
                ),
                4
            ),

            "reason": judgement.get(
                "reason",
                ""
            ),

            "evidence": evidence
        }


        claim_results.append(
            claim_result
        )


    # ========================================================
    # AGGREGATION
    # ========================================================

    risks = [
        claim["risk"]
        for claim
        in claim_results
    ]


    supports = [
        claim["support"]
        for claim
        in claim_results
    ]


    contradictions = [
        claim["contradiction"]
        for claim
        in claim_results
    ]


    uncertainties = [
        claim["uncertainty"]
        for claim
        in claim_results
    ]


    overall_risk = (
        sum(risks)
        / len(risks)
    )


    overall_support = (
        sum(supports)
        / len(supports)
    )


    overall_contradiction = (
        max(contradictions)
        if contradictions
        else 0.0
    )


    overall_uncertainty = (
        sum(uncertainties)
        / len(uncertainties)
    )


    # ========================================================
    # OVERALL STATUS
    # ========================================================

    if overall_contradiction >= 0.70:

        status = "CONTRADICTED"

        reason = (
            "One or more claims strongly "
            "contradict trusted evidence."
        )

    elif overall_support >= 0.70:

        status = "SUPPORTED"

        reason = (
            "The generated claims are "
            "strongly supported by trusted "
            "evidence."
        )

    elif overall_support >= 0.40:

        status = "UNCERTAIN"

        reason = (
            "Some retrieved evidence is "
            "related to the generated claims, "
            "but the evidence does not fully "
            "establish them."
        )

    else:

        status = "UNVERIFIED"

        reason = (
            "The generated claims could not "
            "be sufficiently verified against "
            "trusted evidence."
        )


    # ========================================================
    # BACKWARD-COMPATIBLE RESPONSE
    # ========================================================

    first_evidence = []

    if claim_results:

        first_evidence = (
            claim_results[0].get(
                "evidence",
                []
            )
        )


    return {

        "risk": round(
            overall_risk,
            4
        ),

        "support": round(
            overall_support,
            4
        ),

        "contradiction": round(
            overall_contradiction,
            4
        ),

        "uncertainty": round(
            overall_uncertainty,
            4
        ),

        "status": status,

        "reason": reason,

        # Frontend uses this.
        "claims": claim_results,

        # Kept for compatibility with
        # existing backend code.
        "evidence": first_evidence
    }

