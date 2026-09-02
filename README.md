<p align="center">
  <img src="assets/branding/decodex_logo_full_horizontal.png" alt="DecodeX Security Technologies" width="520" />
</p>

<h1 align="center">Data Leakage Detection & Cyber Attribution Platform (DLD-SOC)</h1>

<p align="center">
  <strong>Enterprise Data Loss Prevention (DLP) & Third-Party Vendor Breach Attribution Engine</strong><br>
  <em>A proprietary work product of <strong>DecodeX Security Technologies Private Limited</strong></em>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://reactjs.org/"><img src="https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black" alt="React" /></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white" alt="Docker" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" /></a>
</p>

---

An **enterprise-grade Data Loss Prevention (DLP) & Cyber Attribution Platform** developed by **DecodeX Security Technologies Private Limited** that solves the data distributor problem: when sensitive enterprise datasets (Fintech PII, HIPAA medical records, employee directories) are shared with third-party vendors and subsequently leaked on the dark web, **mathematically pinpoint the responsible agent with cryptographic certainty**.

Built upon the **Papadimitriou & Garcia-Molina Probabilistic Guilt Model** combined with **Context-Aware Synthetic Canary Honeytokens**, and architected for plug-and-play integration with the **DecodeX Threat Hunting Platform** (`github.com/Decoder420/DecodeX-Threat-Hunting-Platform`).

---

## 📸 System Architecture

```
+-----------------------------------------------------------------------------------+
|                           CYBERSECURITY SOC DASHBOARD                             |
|    Telemetry | Datasets | Vendors | Allocation Matrix | Inspector | SOC Feed Feed |
+-----------------------------------------+-----------------------------------------+
                                          | (REST APIs / JSON)
+-----------------------------------------v-----------------------------------------+
|                               FASTAPI ENGINE CORE                                 |
|  +---------------------------+  +------------------------+  +-------------------+  |
|  |  Smart Allocation Engine  |  | Synthetic Canary Gen   |  | Guilt Model Math  |  |
|  |  (Overlap Minimization)   |  | (HMAC Honeytokens)     |  | (Vectorized 100k+)|  |
|  +---------------------------+  +------------------------+  +-------------------+  |
|  +-------------------------------------------------------+  +-------------------+  |
|  |  Swappable Alert Adapter (Retry Backoff & Dispatch)   |  | Service Auth API  |  |
|  |  (Pushes to DecodeX Threat Hunting SOC REST Endpoint) |  | (X-API-Key / JWT) |  |
|  +-------------------------------------------------------+  +-------------------+  |
+-----------------------------------------------------------------------------------+
                                          | (Outbound Alerts / Webhooks)
+-----------------------------------------v-----------------------------------------+
|                DECODEX THREAT HUNTING PLATFORM (EXTERNAL SOC)                     |
|          github.com/Decoder420/DecodeX-Threat-Hunting-Platform                    |
+-----------------------------------------------------------------------------------+
```

---

## 🧮 Mathematical Model & Theoretical Foundation

When an unauthorized leaked dataset $S$ is discovered on the dark web, the platform determines the guilt probability $P(G_i \mid S)$ that vendor $U_i$ is the leaker:

$$P(G_i \mid S) = 1 - \prod_{t \in S \cap R_i} \left(1 - \frac{1 - p}{|V_t|(1 - p) + p}\right)$$

Where:
* $R_i$: Dataset slice distributed to Agent $U_i$.
* $S$: Intercepted dark web leak dump.
* $V_t$: Set of all agents who were given record $t$ (i.e. $\{j \mid t \in R_j\}$).
* $p$: Independent leakage probability (background empirical noise).
* **Canary Honeytoken Override**: If an injected synthetic record $t_{\text{canary}}$ unique to Agent $i$ is found in $S$, $|V_{t}| = 1$ and $p = 0$, guaranteeing **$P(G_i \mid S) = 1.0$ (100% cryptographic certainty)**.

---

## 🔗 DecodeX Threat Hunting SOC Integration

The platform provides a **swappable, isolated adapter module** (`backend/app/services/alert_adapter.py`) designed to push real-time alerts into the **DecodeX Threat Hunting Platform** with automatic retry and exponential backoff.

### Internal Standard Security Event Schema (Stored in `security_events` table):
```json
{
  "event_id": "evt_4f380a2c1c8742a7",
  "event_type": "guilt_detection",
  "severity": "critical",
  "confidence_score": 0.992,
  "source_dataset": "Global Banking Master PII",
  "implicated_agent": "Beta Cloud Solutions (AGT-BETA)",
  "evidence": {
    "analysis_id": "LEAK-ANL-6E222383",
    "canary_hits": 2,
    "matched_records": 48
  },
  "timestamp": "2026-09-02T11:45:00.000Z"
}
```

### Swappable SOC Transformation Contract:
The adapter automatically maps the internal event to the payload shape expected by DecodeX SOC:
```json
{
  "alert_id": "evt_4f380a2c1c8742a7",
  "alert_type": "guilt_detection",
  "source": "DecodeX-Data-Leakage-Detection",
  "severity": "CRITICAL",
  "confidence": 0.992,
  "target_resource": "Global Banking Master PII",
  "attributed_entity": "Beta Cloud Solutions (AGT-BETA)",
  "metadata": { ... },
  "timestamp": "2026-09-02T11:45:00.000Z"
}
```

> **Note on Schema Assumption:** The default payload assumes DecodeX SOC ingests alerts via `POST /api/v1/alerts`. You can dynamically adjust field mappings at runtime in the UI under **DecodeX SOC Config** or in the `integration_settings` table.

---

## 📡 OpenAPI REST Endpoints (`/api/v1`)

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health, version & capabilities | Public |
| `GET` | `/api/v1/datasets` | List monitored datasets | Bearer / API Key |
| `POST` | `/api/v1/datasets/generate` | Generate realistic synthetic PII datasets | Bearer / API Key |
| `POST` | `/api/v1/datasets/upload` | Upload CSV / JSON master datasets | Bearer / API Key |
| `GET` | `/api/v1/agents` | List third-party vendors & trust scores | Bearer / API Key |
| `POST` | `/api/v1/distribute` | Smart data allocation with canary injection | Bearer / API Key |
| `GET` | `/api/v1/distribute/{id}/agent/{aid}/download` | Download agent slice package (CSV) | Bearer / API Key |
| `POST` | `/api/v1/analyze` | Vectorized leak analysis & guilt scoring | Bearer / API Key |
| `POST` | `/api/v1/analyze/file` | Upload and analyze dark-web leak dump | Bearer / API Key |
| `GET` | `/api/v1/events` | Pull recent security events (SIEM feed) | Bearer / API Key |
| `GET` | `/api/v1/integrations` | Inspect DecodeX SOC settings | Bearer / API Key |
| `PUT` | `/api/v1/integrations` | Update DecodeX SOC endpoint & API key | Bearer / API Key |
| `POST` | `/api/v1/integrations/test` | 1-Click connectivity probe to DecodeX SOC | Bearer / API Key |
| `GET` | `/api/v1/reports/{id}/pdf` | Download audit-ready PDF forensic report | Bearer / API Key |
| `GET` | `/api/v1/reports/{id}/html` | Printable forensic report (HTML) | Bearer / API Key |
| `GET` | `/api/v1/api-keys` | List service account API keys | Bearer / API Key |
| `POST` | `/api/v1/api-keys` | Generate new `dld_live_...` API key | Bearer / API Key |

---

## 💻 Command Line Interface (`dld`)

The platform includes a CLI tool for automation in security pipelines:

```bash
# 1. Distribute a dataset with 3% canaries to third-party vendors
python cli/dld.py distribute --input customers.csv --agents vendorA,vendorB,vendorC --canary-rate 0.03 --output ./dist/

# 2. Analyze a leaked breach dump against the allocation manifest
python cli/dld.py analyze --leaked breach_dump.csv --manifest ./dist/allocation_manifest.json --threshold 0.75

# 3. Test alert connectivity to DecodeX Threat Hunting SOC
python cli/dld.py test-soc --url http://localhost:8001/api/v1/alerts
```

---

## 🚀 Quick Start

### Run with Docker Compose
```bash
docker compose up --build
```
* **SOC Dashboard:** `http://localhost:3000` (or `http://localhost:8000`)
* **Interactive API Docs:** `http://localhost:8000/docs`

### Run Locally
```bash
# 1. Start Backend
cd backend
source venv/bin/activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 2. Start Frontend
cd ../frontend
npm run dev
```

---

## 🧪 Testing

Run the test suite (unit tests, vectorized 100k+ scaling benchmarks, edge cases, and API integration):
```bash
PYTHONPATH=. backend/venv/bin/pytest -v backend/tests/test_pure_engine_and_api.py
```

---

## 🏢 Branding & Intellectual Property

All architectural designs, mathematical models, code, and documentation are proprietary work products of **DecodeX Security Technologies Private Limited**.

**Copyright (c) 2026 DecodeX Security Technologies Private Limited. All rights reserved.**
