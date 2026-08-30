from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import json
import time
import uuid
from pathlib import Path

from app.llm.gemini import generate_response

from app.observability.audit import write_audit_log

from app.gateway import preflight_check

from app.guards.parallel import run_parallel_guards

from app.guards.evidence import EvidenceStore

from app.risk.engine import calculate_risk

from app.policy.engine import make_decision


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="ControlPlane.ai",
    description="Real-Time AI Governance Layer",
    version="0.3.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# KNOWLEDGE BASE
# ============================================================

# Load the evidence store once when the server starts.
evidence_store = EvidenceStore()


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    prompt: str
    application: str = "customer_support"


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def health_check():

    return {
        "status": "online",
        "service": "ControlPlane.ai",
        "version": "0.3.0",
    }


# ============================================================
# CHAT / GOVERNANCE PIPELINE
# ============================================================

@app.post("/chat")
def chat(request: ChatRequest):

    # ========================================================
    # START TOTAL TIMER
    # ========================================================

    start_time = time.perf_counter()

    request_id = str(uuid.uuid4())


    # ========================================================
    # 1. PRE-FLIGHT
    # ========================================================

    preflight_start = time.perf_counter()

    preflight = preflight_check(
        request.prompt
    )

    preflight_latency_ms = round(
        (time.perf_counter() - preflight_start) * 1000,
        2
    )


    # ========================================================
    # 2. PRE-FLIGHT BLOCK
    # ========================================================

    if not preflight["allowed"]:

        latency_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        decision = {
            "decision": "BLOCK",
            "policy": request.application,
            "reason": preflight["reason"],
        }

        risk = {
            "overall": 1.0,
            "level": "CRITICAL",
            "breakdown": {
                "privacy": preflight["privacy"]["risk"],
                "safety": preflight["safety"]["risk"],
                "hallucination": 0.0,
                "bias": 0.0,
            },
            "reasons": [
                preflight["reason"]
            ],
        }

        # ----------------------------------------------------
        # AUDIT EVENT
        # ----------------------------------------------------

        audit_event = {

            "request_id": request_id,

            "application": request.application,

            "stage": "PRE_FLIGHT",

            "risk": risk,

            "decision": decision,

            "latency_ms": latency_ms,

            "guards": {
                "privacy": preflight["privacy"],
                "safety": preflight["safety"],
            },

            "observability": {
                "preflight_latency_ms": preflight_latency_ms,
                "llm_latency_ms": 0.0,
                "guard_latency_ms": 0.0,
                "total_latency_ms": latency_ms,
            },
        }

        write_audit_log(
            audit_event
        )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {

            "request_id": request_id,

            "response": (
                "Request blocked by "
                "ControlPlane.ai before reaching "
                "the language model."
            ),

            "stage": "PRE_FLIGHT",

            "decision": decision,

            "risk": risk,

            "guards": {
                "privacy": preflight["privacy"],
                "safety": preflight["safety"],
            },

            "observability": {
                "preflight_latency_ms": preflight_latency_ms,
                "llm_latency_ms": 0.0,
                "guard_latency_ms": 0.0,
                "total_latency_ms": latency_ms,
            },
        }


    # ========================================================
    # 3. LLM GENERATION
    # ========================================================

    llm_start = time.perf_counter()

    response = generate_response(
        request.prompt
    )

    llm_latency_ms = round(
        (time.perf_counter() - llm_start) * 1000,
        2
    )


    # ========================================================
    # 4. POST-FLIGHT GUARDS
    # ========================================================

    guard_start = time.perf_counter()

    guard_results = run_parallel_guards(
        response,
        evidence_store
    )

    guard_latency_ms = round(
        (time.perf_counter() - guard_start) * 1000,
        2
    )


    # ========================================================
    # 5. EXTRACT GUARD RESULTS
    # ========================================================

    privacy_result = guard_results["privacy"]

    safety_result = guard_results["safety"]

    evidence_result = guard_results["evidence"]

    bias_result = guard_results["bias"]


    # ========================================================
    # 6. RISK ENGINE
    # ========================================================

    risk_result = calculate_risk(

        privacy=privacy_result["risk"],

        safety=safety_result["risk"],

        hallucination=evidence_result["risk"],

        bias=bias_result["risk"],

    )


    # ========================================================
    # 7. POLICY ENGINE
    # ========================================================


    decision = make_decision(
        application=request.application,
        overall_risk=risk_result.overall_risk,
        breakdown=risk_result.breakdown,
        evidence_status=evidence_result.get(
            "status",
            "UNKNOWN"
        ),
        evidence_contradiction=evidence_result.get(
            "contradiction",
            0.0
        ),
    )




    # ========================================================
    # 8. INTERVENTION
    # ========================================================

    final_response = response


    # --------------------------------------------------------
    # EDIT
    # --------------------------------------------------------

    if decision["decision"] == "EDIT":

        final_response = (
            privacy_result["redacted_text"]
        )


    # --------------------------------------------------------
    # HUMAN REVIEW
    # --------------------------------------------------------

    elif decision["decision"] == "HUMAN_REVIEW":

        final_response = (
            "This response requires human review "
            "before it can be delivered."
        )


    # --------------------------------------------------------
    # BLOCK
    # --------------------------------------------------------

    elif decision["decision"] == "BLOCK":

        final_response = (
            "Response blocked by "
            "ControlPlane.ai due to "
            "policy violation."
        )


    # ========================================================
    # 9. TOTAL LATENCY
    # ========================================================

    latency_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2
    )


    # ========================================================
    # 10. AUDIT EVENT
    # ========================================================

    audit_event = {

        "request_id": request_id,

        "application": request.application,

        "stage": "POST_FLIGHT",

        "risk": {

            "overall": risk_result.overall_risk,

            "level": risk_result.risk_level,

            "breakdown": risk_result.breakdown,

            "reasons": risk_result.reasons,

        },

        "decision": decision,

        "latency_ms": latency_ms,

        "guards": {

            "privacy": privacy_result,

            "safety": safety_result,

            "evidence": evidence_result,

            "bias": bias_result,

        },

        "observability": {

            "preflight_latency_ms": preflight_latency_ms,

            "llm_latency_ms": llm_latency_ms,

            "guard_latency_ms": guard_latency_ms,

            "total_latency_ms": latency_ms,

        },
    }


    write_audit_log(
        audit_event
    )


    # ========================================================
    # 11. FINAL RESPONSE
    # ========================================================

    return {

        "request_id": request_id,

        "response": final_response,

        "stage": "POST_FLIGHT",

        "decision": decision,

        "risk": {

            "overall": risk_result.overall_risk,

            "level": risk_result.risk_level,

            "breakdown": risk_result.breakdown,

            "reasons": risk_result.reasons,

        },

        "guards": {

            "privacy": privacy_result,

            "safety": safety_result,

            "evidence": evidence_result,

            "bias": bias_result,

        },

        "observability": {

            "preflight_latency_ms": preflight_latency_ms,

            "llm_latency_ms": llm_latency_ms,

            "guard_latency_ms": guard_latency_ms,

            "total_latency_ms": latency_ms,

        },
    }


# ============================================================
# AUDIT LOGS
# ============================================================

@app.get("/audit")
def get_audit_logs():

    log_file = (
        Path(__file__).resolve().parents[2]
        / "logs"
        / "audit.jsonl"
    )


    if not log_file.exists():

        return {
            "count": 0,
            "events": [],
        }


    events = []


    with open(
        log_file,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            if line.strip():

                try:

                    events.append(
                        json.loads(line)
                    )

                except json.JSONDecodeError:

                    # Ignore malformed log entries
                    continue


    return {

        "count": len(events),

        "events": events[-100:],

    }


# ============================================================
# METRICS
# ============================================================

@app.get("/metrics")
def get_metrics():

    log_file = (
        Path(__file__).resolve().parents[2]
        / "logs"
        / "audit.jsonl"
    )


    if not log_file.exists():

        return {
            "total_requests": 0,
            "average_latency_ms": 0,
            "average_risk": 0,
            "decisions": {},
        }


    events = []


    with open(
        log_file,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            if line.strip():

                try:

                    events.append(
                        json.loads(line)
                    )

                except json.JSONDecodeError:

                    continue


    total = len(events)


    if total == 0:

        return {

            "total_requests": 0,

            "average_latency_ms": 0,

            "average_risk": 0,

            "decisions": {},

        }


    # ========================================================
    # DECISION COUNTS
    # ========================================================

    decisions = {}


    for event in events:

        decision_data = event.get(
            "decision",
            {}
        )

        decision = decision_data.get(
            "decision",
            "UNKNOWN"
        )

        decisions[decision] = (
            decisions.get(
                decision,
                0
            ) + 1
        )


    # ========================================================
    # LATENCY
    # ========================================================

    latency_values = [

        event.get(
            "latency_ms",
            0
        )

        for event in events

    ]


    average_latency = (
        sum(latency_values) / total
    )


    # ========================================================
    # RISK
    # ========================================================

    risk_values = [

        event.get(
            "risk",
            {}
        ).get(
            "overall",
            0
        )

        for event in events

    ]


    average_risk = (
        sum(risk_values) / total
    )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "total_requests": total,

        "average_latency_ms": round(
            average_latency,
            2
        ),

        "average_risk": round(
            average_risk,
            4
        ),

        "decisions": decisions,

    }