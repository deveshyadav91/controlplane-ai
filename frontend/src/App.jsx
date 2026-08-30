
import { useState } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Activity,
  Lock,
  Scale,
  SearchCheck,
  FileText,
  Clock,
  Send,
} from "lucide-react";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

/* =========================================================
   SAFE HELPERS
   ========================================================= */

function safeNumber(value, fallback = 0) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : fallback;
}

function formatNumber(value, digits = 2) {
  return safeNumber(value).toFixed(digits);
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

/* =========================================================
   RISK CARD
   ========================================================= */

function RiskCard({ name, value, icon: Icon }) {
  const numericValue = safeNumber(value);

  const percentage = Math.min(
    100,
    Math.max(0, Math.round(numericValue * 100))
  );

  let status = "LOW";

  if (numericValue >= 0.7) {
    status = "HIGH";
  } else if (numericValue >= 0.4) {
    status = "MEDIUM";
  }

  return (
    <div className="risk-card">

      <div className="risk-card-header">

        <div className="risk-title">
          <Icon size={18} />
          <span>{name}</span>
        </div>

        <span
          className={`risk-status ${status.toLowerCase()}`}
        >
          {status}
        </span>

      </div>

      <div className="risk-value">
        {numericValue.toFixed(2)}
      </div>

      <div className="progress">

        <div
          className={`progress-fill ${status.toLowerCase()}`}
          style={{
            width: `${percentage}%`,
          }}
        />

      </div>

    </div>
  );
}

/* =========================================================
   DECISION BADGE
   ========================================================= */

function DecisionBadge({ decision }) {

  const config = {
    ALLOW: {
      icon: ShieldCheck,
      className: "allow",
    },

    EDIT: {
      icon: ShieldAlert,
      className: "edit",
    },

    HUMAN_REVIEW: {
      icon: Activity,
      className: "review",
    },

    BLOCK: {
      icon: ShieldX,
      className: "block",
    },
  };

  const normalizedDecision =
    decision || "UNKNOWN";

  const current =
    config[normalizedDecision] || {
      icon: Activity,
      className: "review",
    };

  const Icon = current.icon;

  return (
    <div
      className={`decision ${current.className}`}
    >

      <Icon size={26} />

      <div>

        <div className="decision-label">
          DECISION
        </div>

        <div className="decision-value">
          {normalizedDecision}
        </div>

      </div>

    </div>
  );
}

/* =========================================================
   CLAIM CARD
   ========================================================= */


function ClaimCard({ claim }) {
  const status = claim.status || "UNVERIFIED";
  const statusClass = status.toLowerCase();

  const risk = Number(claim.risk || 0);
  const support = Number(claim.support || 0);
  const contradiction = Number(
    claim.contradiction || 0
  );
  const uncertainty = Number(
    claim.uncertainty || 0
  );

  let StatusIcon = SearchCheck;

  if (status === "SUPPORTED") {
    StatusIcon = ShieldCheck;
  } else if (status === "CONTRADICTED") {
    StatusIcon = ShieldX;
  } else if (
    status === "UNCERTAIN" ||
    status === "UNVERIFIED"
  ) {
    StatusIcon = ShieldAlert;
  }

  return (
    <div
      className={`claim-card claim-${statusClass}`}
    >
      {/* HEADER */}

      <div className="claim-header">

        <div className="claim-status-wrapper">

          <StatusIcon size={17} />

          <span
            className={`claim-status ${statusClass}`}
          >
            {status}
          </span>

        </div>

        <span className="claim-risk">
          Risk {risk.toFixed(2)}
        </span>

      </div>


      {/* CLAIM */}

      <div className="claim-label">
        CLAIM
      </div>

      <div className="claim-text">
        {claim.claim}
      </div>


      {/* METRICS */}

      <div className="claim-metrics">

        <div className="claim-metric">
          <span>Support</span>
          <strong>
            {support.toFixed(2)}
          </strong>
        </div>

        <div className="claim-metric">
          <span>Contradiction</span>
          <strong>
            {contradiction.toFixed(2)}
          </strong>
        </div>

        <div className="claim-metric">
          <span>Uncertainty</span>
          <strong>
            {uncertainty.toFixed(2)}
          </strong>
        </div>

      </div>


      {/* REASON */}

      {claim.reason && (
        <div className="claim-reason">

          <SearchCheck size={15} />

          <span>
            {claim.reason}
          </span>

        </div>
      )}


      {/* EVIDENCE */}

      {claim.evidence?.length > 0 && (

        <div className="evidence-list">

          <div className="evidence-title">

            <FileText size={15} />

            <span>
              Trusted Evidence
            </span>

            <span className="evidence-count">
              {claim.evidence.length}
            </span>

          </div>


          {claim.evidence.map(
            (item, index) => (

              <div
                className="evidence-item"
                key={index}
              >

                <div className="source">

                  <span>
                    {item.source}
                  </span>

                  <span>
                    {(Number(item.score || 0) * 100).toFixed(1)}%
                  </span>

                </div>

                <div className="evidence-text">
                  {item.text}
                </div>

              </div>

            )
          )}

        </div>

      )}

    </div>
  );
}



function InterventionBanner({ decision, risk }) {
  const config = {
    ALLOW: {
      icon: ShieldCheck,
      title: "Response Approved",
      text: "The AI response passed the governance checks and can be delivered to the user.",
      className: "intervention-allow",
    },

    EDIT: {
      icon: ShieldAlert,
      title: "Response Modified",
      text: "The response contains a manageable risk. ControlPlane.ai applied an intervention before delivery.",
      className: "intervention-edit",
    },

    HUMAN_REVIEW: {
      icon: Activity,
      title: "Human Review Required",
      text: "The response contains elevated risk and should be verified by a human before being trusted.",
      className: "intervention-review",
    },

    BLOCK: {
      icon: ShieldX,
      title: "Response Blocked",
      text: "The response exceeded the configured governance threshold and was prevented from reaching the user.",
      className: "intervention-block",
    },
  };

  const current = config[decision] || config.HUMAN_REVIEW;
  const Icon = current.icon;

  return (
    <div className={`intervention-banner ${current.className}`}>
      <div className="intervention-icon">
        <Icon size={24} />
      </div>

      <div className="intervention-content">
        <strong>{current.title}</strong>

        <p>{current.text}</p>

        {risk?.reasons?.length > 0 && (
          <div className="intervention-reasons">
            {risk.reasons.map((reason, index) => (
              <span key={index}>
                • {reason}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="intervention-risk">
        <span>RISK</span>
        <strong>{risk?.overall?.toFixed(2) ?? "0.00"}</strong>
      </div>
    </div>
  );
}



/* =========================================================
   APP
   ========================================================= */

function App() {

  const [prompt, setPrompt] =
    useState("");

  const [application, setApplication] =
    useState("customer_support");

  const [result, setResult] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  /* =======================================================
     GOVERNANCE REQUEST
     ======================================================= */

  async function runGovernance() {

    if (!prompt.trim()) {
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {

      const response =
        await fetch(`${API_URL}/chat`, {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            prompt,
            application,
          }),
        });

      const responseText =
        await response.text();

      if (!response.ok) {

        throw new Error(
          responseText ||
          `Server returned ${response.status}`
        );
      }

      let data;

      try {

        data =
          JSON.parse(responseText);

      } catch {

        throw new Error(
          "Backend returned an invalid JSON response."
        );
      }

      console.log(
        "ControlPlane response:",
        data
      );

      setResult(data);

    } catch (err) {

      console.error(
        "Governance request failed:",
        err
      );

      setError(
        err?.message ||
        "Unable to connect to ControlPlane.ai"
      );

    } finally {

      setLoading(false);

    }
  }

  /* =======================================================
     SAFE RESULT DATA
     ======================================================= */

  const risk =
    result?.risk || {};

  const breakdown =
    risk?.breakdown || {};

  const guards =
    result?.guards || {};

  const evidence =
    guards?.evidence || {};

  const claims =
    safeArray(evidence?.claims);

  const observability =
    result?.observability || {};

  const decision =
    result?.decision?.decision ||
    "UNKNOWN";

  /* =======================================================
     CLAIM COUNTS
     ======================================================= */

  const supportedClaims =
    claims.filter(
      (claim) =>
        claim?.status === "SUPPORTED"
    ).length;

  const uncertainClaims =
    claims.filter(
      (claim) =>
        claim?.status === "UNCERTAIN" ||
        claim?.status === "UNVERIFIED"
    ).length;

  const contradictedClaims =
    claims.filter(
      (claim) =>
        claim?.status === "CONTRADICTED"
    ).length;

  return (
    <div className="app">

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-icon">
            <ShieldCheck size={25} />
          </div>

          <div>

            <div className="brand-name">
              ControlPlane<span>.ai</span>
            </div>

            <div className="brand-subtitle">
              REAL-TIME AI GOVERNANCE
            </div>

          </div>

        </div>

        <div className="system-status">

          <span className="status-dot" />

          SYSTEM ONLINE

        </div>

      </header>

      {/* =================================================
          MAIN
      ================================================= */}

      <main className="container">

        {/* =================================================
            HERO
        ================================================= */}

        <section className="hero">

          <div>

            <div className="eyebrow">
              AI GOVERNANCE GATEWAY
            </div>

            <h1>
              Control every AI decision
              <br />
              <span>
                before it reaches users.
              </span>
            </h1>

            <p>
              Detect hallucinations, privacy leaks,
              unsafe content and bias in real time.
            </p>

          </div>

        </section>

        {/* =================================================
            REQUEST PANEL
        ================================================= */}

        <section className="panel">

          <div className="panel-header">

            <div>

              <h2>
                Governance Request
              </h2>

              <p>
                Send an AI request through
                ControlPlane.ai
              </p>

            </div>

            <div className="live">

              <span />

              LIVE

            </div>

          </div>

          <div className="form-row">

            <div className="application">

              <label>
                APPLICATION
              </label>

              <select
                value={application}
                onChange={(e) =>
                  setApplication(
                    e.target.value
                  )
                }
              >

                <option value="customer_support">
                  Customer Support
                </option>

                <option value="internal_assistant">
                  Internal Assistant
                </option>

                <option value="decision_support">
                  Decision Support
                </option>

              </select>

            </div>

          </div>

          <div className="prompt-container">

            <label>
              USER PROMPT
            </label>

            <textarea
              value={prompt}
              onChange={(e) =>
                setPrompt(e.target.value)
              }
              placeholder="Ask something that should be governed..."
              rows={5}
            />

          </div>

          <button
            className="run-button"
            onClick={runGovernance}
            disabled={
              loading ||
              !prompt.trim()
            }
          >

            {loading ? (

              <>
                <span className="spinner" />
                ANALYZING...
              </>

            ) : (

              <>
                <Send size={18} />
                RUN GOVERNANCE CHECK
              </>

            )}

          </button>

        </section>

        {/* =================================================
            ERROR
        ================================================= */}

        {error && (

          <div className="error">

            <ShieldX size={20} />

            <div>

              <strong>
                Governance request failed
              </strong>

              <p>
                {error}
              </p>

            </div>

          </div>

        )}

        {/* =================================================
            RESULTS
        ================================================= */}

        {result && (
          <section className="results">

            <InterventionBanner
              decision={
                result.decision?.decision ||
                "UNKNOWN"
              }
              risk={risk}
            />

            {/* =================================================
                DECISION
            ================================================= */}

            <div className="result-top">

              <DecisionBadge
                decision={decision}
              />

              <div className="request-meta">

                <div>

                  <span>
                    REQUEST ID
                  </span>

                  <code>
                    {result?.request_id ||
                      "N/A"}
                  </code>

                </div>

                <div>

                  <span>
                    STAGE
                  </span>

                  <strong>
                    {result?.stage ||
                      "UNKNOWN"}
                  </strong>

                </div>

              </div>

            </div>

            {/* =================================================
                RISK
            ================================================= */}

            <div className="risk-section">

              <div className="section-heading">

                <div>

                  <h2>
                    Risk Assessment
                  </h2>

                  <p>
                    Multi-dimensional AI
                    output evaluation
                  </p>

                </div>

                <div className="overall-risk">

                  <span>
                    OVERALL RISK
                  </span>

                  <strong>
                    {formatNumber(
                      risk?.overall
                    )}
                  </strong>

                  <small>
                    {risk?.level ||
                      "UNKNOWN"}
                  </small>

                </div>

              </div>

              <div className="risk-grid">

                <RiskCard
                  name="Privacy"
                  value={breakdown?.privacy}
                  icon={Lock}
                />

                <RiskCard
                  name="Safety"
                  value={breakdown?.safety}
                  icon={ShieldAlert}
                />

                <RiskCard
                  name="Hallucination"
                  value={breakdown?.hallucination}
                  icon={SearchCheck}
                />

                <RiskCard
                  name="Bias"
                  value={breakdown?.bias}
                  icon={Scale}
                />

              </div>

            </div>

            {/* =================================================
                AI RESPONSE
            ================================================= */}

            <div className="response-section">

              <div className="section-heading">

                <div>

                  <h2>
                    AI Response
                  </h2>

                  <p>
                    Output after governance
                    intervention
                  </p>

                </div>

                <div className="latency">

                  <Clock size={16} />

                  {formatNumber(
                    observability?.total_latency_ms,
                    0
                  )}{" "}
                  ms

                </div>

              </div>

              <div className="response-box">

                {result?.response ||
                  "No response returned."}

              </div>

            </div>

            {/* =================================================
                EVIDENCE VERIFICATION
            ================================================= */}

            <div className="evidence-section">

              <div className="section-heading">

                <div>

                  <h2>
                    Evidence Verification
                  </h2>

                  <p>
                    Claim-level verification
                    against trusted sources
                  </p>

                </div>

                {claims.length > 0 && (
                  
                  <div className="evidence-summary">

                    <span className="summary-supported">
                      ✓{" "}
                      {
                        evidence.claims.filter(
                          c => c.status === "SUPPORTED"
                        ).length
                      } supported
                    </span>

                    <span className="summary-uncertain">
                      ⚠{" "}
                      {
                        evidence.claims.filter(
                          c =>
                            c.status === "UNCERTAIN" ||
                            c.status === "UNVERIFIED"
                        ).length
                      } uncertain
                    </span>

                    <span className="summary-contradicted">
                      ✕{" "}
                      {
                        evidence.claims.filter(
                          c =>
                            c.status === "CONTRADICTED"
                        ).length
                      } contradicted
                    </span>

                  </div>



                )}

              </div>

              {claims.length > 0 ? (

                <div className="claims">

                  {claims.map(
                    (claim, index) => (

                      <ClaimCard
                        claim={claim}
                        key={
                          claim?.id ||
                          index
                        }
                      />

                    )
                  )}

                </div>

              ) : (

                <div className="no-evidence">

                  <FileText size={20} />

                  <div>

                    <strong>
                      No claims available
                    </strong>

                    <p>
                      The evidence guard did not
                      return claim-level results
                      for this response.
                    </p>

                  </div>

                </div>

              )}

            </div>

            {/* =================================================
                OBSERVABILITY
            ================================================= */}

            <div className="observability">

              <div className="section-heading">

                <div>

                  <h2>
                    Observability
                  </h2>

                  <p>
                    Runtime governance
                    performance
                  </p>

                </div>

                <Activity size={22} />

              </div>

              <div className="metrics">

                <div>

                  <span>
                    PRE-FLIGHT
                  </span>

                  <strong>
                    {formatNumber(
                      observability?.preflight_latency_ms,
                      2
                    )}{" "}
                    ms
                  </strong>

                </div>

                <div>

                  <span>
                    LLM
                  </span>

                  <strong>
                    {formatNumber(
                      observability?.llm_latency_ms,
                      0
                    )}{" "}
                    ms
                  </strong>

                </div>

                <div>

                  <span>
                    GUARDS
                  </span>

                  <strong>
                    {formatNumber(
                      observability?.guard_latency_ms,
                      0
                    )}{" "}
                    ms
                  </strong>

                </div>

                <div>

                  <span>
                    TOTAL
                  </span>

                  <strong>
                    {formatNumber(
                      observability?.total_latency_ms,
                      0
                    )}{" "}
                    ms
                  </strong>

                </div>

              </div>

            </div>

          </section>

        )}

      </main>

      {/* =================================================
          FOOTER
      ================================================= */}

      <footer>

        <ShieldCheck size={16} />

        ControlPlane.ai · Responsible AI
        Governance Infrastructure

      </footer>

    </div>
  );
}

export default App;

