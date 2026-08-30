# 🛡️ ControlPlane.ai

### Real-Time AI Governance Infrastructure

> **ControlPlane.ai is a model-agnostic runtime governance layer that sits between AI applications and Large Language Models (LLMs) to continuously evaluate, score, and control AI outputs before they reach users.**

AI systems can generate responses that are useful but still introduce risks such as **hallucinations, privacy leaks, unsafe content, bias, and policy violations**.

ControlPlane.ai addresses this by placing a governance layer between the application and the model.

---

## 🚀 Why ControlPlane.ai?

Traditional AI applications generally follow this pipeline:

```text
User
  │
  ▼
Application
  │
  ▼
LLM
  │
  ▼
User
```

The problem is that the application often trusts the model output directly.

ControlPlane.ai introduces a runtime governance layer:

```text
                         ControlPlane.ai
                              │
User Request ──► Pre-Flight ──┤
                              │
                              ▼
                             LLM
                              │
                              ▼
                     Parallel Guard Layer
                              │
               ┌──────────────┼──────────────┐
               │              │              │
            Privacy         Safety        Evidence
               │              │              │
               └──────────────┼──────────────┘
                              │
                            Bias
                              │
                              ▼
                        Risk Engine
                              │
                              ▼
                       Policy Engine
                              │
             ┌────────────────┼────────────────┐
             │                │                │
           ALLOW             EDIT         HUMAN_REVIEW
                                              │
                                            BLOCK
```

Instead of simply generating an answer, ControlPlane.ai asks:

> **"Should this AI-generated answer actually reach the user?"**

---

# ✨ Key Features

## 🔐 Privacy Guard

Detects sensitive information and personally identifiable information (PII) in AI-generated responses.

Examples include:

* Email addresses
* Phone numbers
* Credit card numbers
* Sensitive identifiers
* Other configurable PII patterns

The guard can redact detected sensitive information before the response reaches the user.

---

## 🛡️ Safety Guard

A lightweight local safety guard checks generated responses for potentially unsafe content.

The guard operates locally using rule-based detection, making it:

* Fast
* Deterministic
* Low latency
* Independent of additional LLM calls

This avoids adding unnecessary model inference latency to every governance request.

---

## ⚖️ Bias Guard

The Bias Guard evaluates responses for potentially problematic:

* Stereotyping
* Discriminatory language
* Group-based generalizations
* Unfair or exclusionary statements

The current implementation is designed as a fast runtime guard rather than another expensive LLM inference step.

---

## 🔎 Claim-Level Evidence Guard

One of the core components of ControlPlane.ai.

Instead of treating an entire AI response as one claim, the Evidence Guard breaks the response into individual claims and evaluates them against trusted organizational knowledge.

For example:

```text
AI Response:

"Customers can request a refund within 30 days."

             │
             ▼
        Claim Extraction
             │
             ▼
"Customers can request a refund
within 30 days."
             │
             ▼
       Knowledge Retrieval
             │
             ▼
refund_policy.txt
             │
             ▼
        Evidence Judge
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
   SUPPORTED  UNCERTAIN  CONTRADICTED
```

This allows ControlPlane.ai to identify exactly **which claims are supported or contradicted** by trusted sources.

---

## 🧠 Trusted Knowledge Retrieval

The Evidence Store uses:

* Sentence Transformers
* `all-MiniLM-L6-v2`
* FAISS
* Cosine-style similarity using normalized embeddings

Trusted documents are stored in:

```text
knowledge/
├── product_policy.txt
└── refund_policy.txt
```

Documents are loaded at startup and embedded into a FAISS index.

During governance:

```text
AI Response
     │
     ▼
Claim Extraction
     │
     ▼
Embedding
     │
     ▼
FAISS Retrieval
     │
     ▼
Relevant Trusted Evidence
```

This makes evidence verification grounded in the organization's own knowledge base rather than arbitrary external information.

---

# 📊 Risk Engine

ControlPlane.ai combines multiple governance dimensions into an overall risk score.

Current dimensions:

```text
Privacy
Safety
Hallucination
Bias
```

Conceptually:

```text
                ┌──────────┐
                │ Privacy  │
                └────┬─────┘
                     │
                ┌────▼─────┐
                │  Safety  │
                └────┬─────┘
                     │
                ┌────▼─────┐
                │Evidence  │
                └────┬─────┘
                     │
                ┌────▼─────┐
                │   Bias   │
                └────┬─────┘
                     │
                     ▼
               Risk Engine
                     │
                     ▼
              Overall Risk
```

The resulting score is classified into risk levels such as:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

---

# 🚦 Policy Engine

Risk does not directly determine the final response.

The Policy Engine converts the risk assessment into an actionable governance decision.

Possible decisions include:

| Decision       | Meaning                              |
| -------------- | ------------------------------------ |
| `ALLOW`        | Response is safe to return           |
| `EDIT`         | Response should be modified/redacted |
| `HUMAN_REVIEW` | Response requires human inspection   |
| `BLOCK`        | Response must not reach the user     |

Example:

```json
{
  "decision": "BLOCK",
  "policy": "Customer Support",
  "reason": "High privacy risk"
}
```

This separates **risk detection** from **business policy**, making the governance layer easier to extend.

---

# ⚡ Parallel Guard Architecture

The guards are executed concurrently to minimize runtime overhead.

```text
                    AI Response
                         │
                         ▼
                ThreadPoolExecutor
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
     Privacy          Safety          Evidence
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                        Bias
                         │
                         ▼
                    Risk Engine
```

The architecture prevents independent guards from unnecessarily running one after another.

This is particularly important for runtime AI governance where every additional millisecond affects the user experience.

---

# 📈 Observability

ControlPlane.ai measures the runtime cost of every governance request.

The dashboard reports:

```text
PRE-FLIGHT
LLM
GUARDS
TOTAL
```

Example:

```text
PRE-FLIGHT     1.87 ms
LLM        16,714.00 ms
GUARDS         96.00 ms
TOTAL      16,811.00 ms
```

The optimization goal is to ensure that governance adds minimal overhead compared with the actual LLM generation time.

---

# 🧾 Audit Logging

Every governance request can produce an audit event containing information such as:

* Request ID
* Application
* Governance stage
* Overall risk
* Risk breakdown
* Guard results
* Final decision
* Latency
* Evidence
* Intervention result

Example:

```json
{
  "request_id": "example-request-id",
  "stage": "POST_FLIGHT",
  "risk": {
    "overall": 0.30,
    "level": "MEDIUM"
  },
  "decision": {
    "decision": "ALLOW"
  },
  "observability": {
    "total_latency_ms": 16811
  }
}
```

Audit events are stored locally in JSONL format during development.

Runtime logs should not be committed to the repository.

---

# 🏗️ Architecture

## High-Level Architecture

```text
                         ┌───────────────────┐
                         │    User / App     │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   FastAPI Gateway │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   Pre-Flight      │
                         │      Guard        │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    Gemini LLM     │
                         └─────────┬─────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │     Parallel Guard Layer   │
                    ├────────────────────────────┤
                    │                            │
                    │  Privacy   Safety         │
                    │                            │
                    │  Evidence  Bias           │
                    │                            │
                    └──────────────┬─────────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    Risk Engine    │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   Policy Engine   │
                         └─────────┬─────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
                 ALLOW           EDIT       HUMAN REVIEW
                                                   │
                                                   ▼
                                                 BLOCK
```

---

# 🔄 Governance Pipeline

A complete request follows this lifecycle:

### 1. Request

The application sends:

```http
POST /chat
```

with:

```json
{
  "prompt": "Can customers get a refund?",
  "application": "customer_support"
}
```

### 2. Pre-Flight

The request is checked for immediate risks before reaching the LLM.

### 3. LLM Generation

The request is sent to the configured Gemini model.

### 4. Parallel Evaluation

The generated response is evaluated by:

```text
Privacy Guard
Safety Guard
Evidence Guard
Bias Guard
```

### 5. Risk Calculation

The individual guard scores are combined.

### 6. Policy Decision

The Policy Engine determines:

```text
ALLOW
EDIT
HUMAN_REVIEW
BLOCK
```

### 7. Intervention

If required, ControlPlane.ai modifies, blocks, or routes the response for review.

### 8. Audit

The complete governance event is recorded for observability and auditing.

---

# 🖥️ Dashboard

The frontend provides a real-time governance dashboard showing:

* Governance request interface
* Application selection
* AI response
* Final governance decision
* Overall risk
* Individual guard scores
* Claim-level evidence verification
* Trusted evidence
* Runtime latency
* Governance observability

Example dashboard flow:

```text
┌─────────────────────────────────────────────┐
│              ControlPlane.ai                │
│         REAL-TIME AI GOVERNANCE             │
├─────────────────────────────────────────────┤
│                                             │
│  Governance Request                         │
│                                             │
│  Application: Customer Support              │
│                                             │
│  User Prompt:                               │
│  ┌───────────────────────────────────────┐  │
│  │ Ask something that should be governed │  │
│  └───────────────────────────────────────┘  │
│                                             │
│       [ RUN GOVERNANCE CHECK ]              │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  DECISION: ALLOW                            │
│                                             │
│  Risk Assessment                            │
│                                             │
│  Privacy   Safety   Hallucination   Bias    │
│   0.00      0.00       0.12         0.00   │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  Evidence Verification                     │
│                                             │
│  ✓ Supported                               │
│  ⚠ Uncertain                               │
│  ✕ Contradicted                            │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  Observability                              │
│                                             │
│  PRE-FLIGHT   LLM   GUARDS   TOTAL         │
│                                             │
└─────────────────────────────────────────────┘
```

---

# 📁 Project Structure

```text
controlplane-ai/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── gateway.py
│   │   ├── policy.py
│   │   │
│   │   ├── llm/
│   │   │   └── gemini.py
│   │   │
│   │   ├── guards/
│   │   │   ├── parallel.py
│   │   │   ├── privacy.py
│   │   │   ├── safety.py
│   │   │   ├── bias.py
│   │   │   ├── evidence.py
│   │   │   └── evidence_judge.py
│   │   │
│   │   ├── risk/
│   │   │   └── engine.py
│   │   │
│   │   ├── policy/
│   │   │   └── engine.py
│   │   │
│   │   └── observability/
│   │       └── audit.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   └── index.css
│   │
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── knowledge/
│   ├── product_policy.txt
│   └── refund_policy.txt
│
├── .env.example
├── .gitignore
└── README.md
```

---

# 🛠️ Technology Stack

## Backend

* Python
* FastAPI
* Pydantic
* Google Gemini API
* FAISS
* Sentence Transformers
* NumPy

## Frontend

* React
* Vite
* JavaScript
* Lucide React
* CSS

## AI / Governance

* Large Language Model inference
* Semantic retrieval
* Claim-level verification
* Risk scoring
* Policy enforcement
* Runtime observability
* Audit logging

---

# ⚙️ Installation

## Prerequisites

Make sure you have installed:

* Python 3.10+
* Node.js 18+
* npm
* Git

---

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/controlplane-ai.git

cd controlplane-ai
```

---

# 🔧 Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔑 Configure Environment Variables

Create a `.env` file inside `backend/`:

```env
GEMINI_API_KEY=your_gemini_api_key
MODEL_NAME=gemini-3.6-flash
```

**Never commit your `.env` file or API key to GitHub.**

Use `.env.example` as the template.

---

# ▶️ Run the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Health check:

```text
GET /
```

Expected response:

```json
{
  "status": "online",
  "service": "ControlPlane.ai",
  "version": "0.2.0"
}
```

---

# 🎨 Frontend Setup

Open another terminal.

From the project root:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will typically be available at:

```text
http://localhost:5173
```

---

# 🔌 API

## `GET /`

Health check.

---

## `POST /chat`

Runs an AI request through the complete governance pipeline.

### Request

```json
{
  "prompt": "Can customers request a refund?",
  "application": "customer_support"
}
```

### Response

```json
{
  "request_id": "uuid",
  "response": "AI generated response",
  "stage": "POST_FLIGHT",
  "decision": {
    "decision": "ALLOW",
    "policy": "Customer Support"
  },
  "risk": {
    "overall": 0.15,
    "level": "LOW",
    "breakdown": {
      "privacy": 0.0,
      "safety": 0.0,
      "hallucination": 0.15,
      "bias": 0.0
    }
  }
}
```

---

## `GET /audit`

Returns recent governance audit events.

---

## `GET /metrics`

Returns aggregated runtime metrics such as:

* Total requests
* Average latency
* Average risk
* Decision distribution

---

# 🧪 Example Governance Scenario

Suppose the trusted knowledge base contains:

```text
Customers can request a refund within 30 days of purchase.
```

The AI generates:

```text
Customers can request refunds within 7 days of purchase.
```

ControlPlane.ai retrieves the trusted policy and identifies the conflict.

The Evidence Guard can produce:

```json
{
  "claim": "Customers can request refunds within 7 days.",
  "status": "CONTRADICTED",
  "support": 0.0,
  "contradiction": 1.0,
  "uncertainty": 0.0
}
```

The Risk Engine increases the hallucination risk and the Policy Engine determines the appropriate intervention.

This demonstrates the core idea:

> **The LLM generates. ControlPlane.ai governs.**

---

# ⚡ Performance

A major design goal of ControlPlane.ai is to minimize governance overhead.

The system originally relied on multiple model-based evaluation steps, which introduced significant latency.

The architecture was optimized by moving lightweight guards such as:

```text
Safety
Bias
Privacy
```

toward fast local evaluation and running independent guards concurrently.

The resulting architecture keeps governance evaluation substantially faster than sequential multi-model evaluation.

Example runtime:

```text
PRE-FLIGHT       ~1–2 ms
LLM              ~16–17 s
GUARDS           ~100 ms
TOTAL            ~16–18 s
```

Actual latency depends primarily on the configured LLM, network conditions, and machine.

---

# 🔐 Security

ControlPlane.ai is designed with security considerations including:

* Environment-based API key configuration
* PII detection
* Response redaction
* Pre-flight request filtering
* Policy-based blocking
* Audit logging

### Never commit:

```text
.env
venv/
node_modules/
__pycache__/
logs/*.jsonl
```

---

# 🎯 Design Principles

ControlPlane.ai follows several architectural principles.

### 1. Model Agnostic

The governance layer should not depend on a specific LLM provider.

The current implementation uses Gemini, but the architecture allows the model layer to be replaced.

---

### 2. Defense in Depth

No single guard is responsible for governance.

Instead:

```text
Pre-Flight
    ↓
LLM
    ↓
Privacy
    ↓
Safety
    ↓
Evidence
    ↓
Bias
    ↓
Risk
    ↓
Policy
```

Multiple independent controls reduce the chance of a single failure reaching users.

---

### 3. Local-First Evaluation

Where possible, deterministic checks are performed locally.

This provides:

* Lower latency
* Lower cost
* Better predictability
* Reduced dependency on additional LLM calls

---

### 4. Evidence-Based Governance

AI responses should be evaluated against trusted organizational information instead of relying solely on model confidence.

---

### 5. Separation of Detection and Decision

Guards detect risks.

The Risk Engine aggregates those risks.

The Policy Engine determines what should happen.

This separation makes the architecture easier to maintain and extend.

---

# 🔮 Future Improvements

Potential future extensions include:

* Multi-model routing
* Streaming governance
* Human review dashboard
* Configurable governance policies
* Enterprise policy management
* More advanced PII detection
* Automated policy ingestion
* Vector database integrations
* Governance analytics
* Role-based access control
* Distributed deployment
* Prometheus/Grafana observability
* Model-specific risk profiles
* Continuous evaluation pipelines

---

# 📌 Roadmap

```text
[x] FastAPI governance gateway
[x] Gemini integration
[x] Pre-flight guard
[x] Privacy guard
[x] Safety guard
[x] Bias guard
[x] Evidence retrieval
[x] Claim-level evidence verification
[x] Risk engine
[x] Policy engine
[x] Parallel guard execution
[x] Audit logging
[x] Runtime observability
[x] React governance dashboard

[ ] Human review workflow
[ ] Multi-model routing
[ ] Production authentication
[ ] Distributed deployment
[ ] Advanced analytics
```

---

# 🧠 Core Insight

Most AI applications focus on improving the model.

ControlPlane.ai focuses on **controlling the model's behavior at runtime**.

```text
Traditional AI

Application → LLM → User


Governed AI

Application
     ↓
Control Plane
     ↓
LLM
     ↓
Evaluation
     ↓
Risk Assessment
     ↓
Policy
     ↓
User
```

The model is no longer the final authority.

**The governance layer is.**
