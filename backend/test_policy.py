from app.risk.engine import calculate_risk
from app.policy.engine import make_decision


risk = calculate_risk(
    privacy=0.10,
    safety=0.05,
    hallucination=0.85,
    bias=0.05,
)


print("\nRisk:")
print(risk)


for application in [
    "customer_support",
    "internal_assistant",
    "decision_support",
]:

    decision = make_decision(
        application=application,
        overall_risk=risk.overall_risk,
        breakdown=risk.breakdown,
    )

    print(
        f"\n{application}:"
    )

    print(decision)