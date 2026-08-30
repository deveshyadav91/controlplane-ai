from app.guards.evidence import (
    EvidenceStore,
    evaluate_evidence
)


store = EvidenceStore()


tests = [

    "Customers can request a refund within 30 days.",

    "Customers can request a refund within 90 days.",

    "Digital products are refundable.",

]


for answer in tests:

    print("\n" + "=" * 60)

    print("ANSWER:")
    print(answer)

    result = evaluate_evidence(
        answer,
        store
    )

    print("\nRESULT:")
    print(result)