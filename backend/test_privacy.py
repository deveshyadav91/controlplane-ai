from app.guards.privacy import detect_pii, redact_pii


text = """
Hello Rahul.

You can contact me at
9876543210 or rahul@example.com.

My card is 4111 1111 1111 1111.
"""


violations = detect_pii(text)


print("\nDetected PII:")

for violation in violations:
    print(
        violation.type,
        violation.confidence,
        violation.matched_text
    )


redacted = redact_pii(text, violations)

print("\nRedacted text:")
print(redacted)