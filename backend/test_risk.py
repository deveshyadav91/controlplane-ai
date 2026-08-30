from app.risk.engine import calculate_risk


result = calculate_risk(
    privacy=0.95,
    safety=0.10,
    hallucination=0.82,
    bias=0.15,
)


print("Overall Risk:", result.overall_risk)
print("Risk Level:", result.risk_level)
print("Breakdown:", result.breakdown)
print("Reasons:", result.reasons)