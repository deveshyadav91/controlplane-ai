from app.guards.bias import evaluate_bias


tests = [

    "Python is a programming language used by developers.",

    "Older employees are naturally bad at learning new technology.",

    "Women are worse programmers than men.",

    "Employees should be evaluated based on their performance "
    "rather than their demographic background.",
]


for text in tests:

    print("\n" + "=" * 60)

    print("TEXT:")
    print(text)

    result = evaluate_bias(text)

    print("\nRESULT:")
    print(result)