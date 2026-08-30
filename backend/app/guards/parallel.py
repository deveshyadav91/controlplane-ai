from concurrent.futures import ThreadPoolExecutor


def run_parallel_guards(
    response: str,
    evidence_store
) -> dict:

    with ThreadPoolExecutor(max_workers=4) as executor:

        privacy_future = executor.submit(
            _privacy,
            response
        )

        safety_future = executor.submit(
            _safety,
            response
        )

        evidence_future = executor.submit(
            _evidence,
            response,
            evidence_store
        )

        bias_future = executor.submit(
            _bias,
            response
        )

        return {
            "privacy": privacy_future.result(),
            "safety": safety_future.result(),
            "evidence": evidence_future.result(),
            "bias": bias_future.result(),
        }


def _privacy(response):
    from app.guards.privacy import evaluate_privacy

    return evaluate_privacy(response)


def _safety(response):
    from app.guards.safety import evaluate_safety

    return evaluate_safety(response)


def _evidence(response, evidence_store):
    from app.guards.evidence import evaluate_evidence

    return evaluate_evidence(
        response,
        evidence_store
    )


def _bias(response):
    from app.guards.bias import evaluate_bias

    return evaluate_bias(response)