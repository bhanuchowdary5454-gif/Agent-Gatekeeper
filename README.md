# AirGuard AI – Intelligent Airline Agent Gatekeeper
### Case Study: Delta Air Lines (Academic Cybersecurity & Agentic AI Prototype)

---

## 📌 Executive Summary

With the explosive emergence of autonomous third-party AI agents (personal travel bots, enterprise concierge agents, and LLM plugins), consumers increasingly delegate airline tasks—such as flight searching, seat selection, extra baggage booking, itinerary modification, and automated payments—to external software agents. 

However, delegating financial and operational actions to autonomous AI entities introduces severe cybersecurity and operational vulnerabilities:
1. **Identity Spoofing & Credential Hijacking:** Malicious or unregistered bots impersonating legitimate passengers.
2. **Consent & Scope Creep:** AI agents exceeding customer permissions (e.g., executing debit payments when only authorized to search).
3. **Financial Limit Breaches:** Agents repeatedly making high-value reservations without customer awareness.
4. **Rogue / Hallucinating Agents:** AI agents executing erroneous bookings, rapid-fire booking loops, or abnormal luggage allotments.
5. **Lack of Instant Revocation:** Inability to immediately deactivate compromised agents and invalidate their pending transactions.

**AirGuard AI** serves as an intelligent **Policy Enforcement Point (PEP)** and **Policy Decision Point (PDP)** sitting between customer AI agents and airline transactional services. Drawing inspiration from Zero-Trust security principles and Delta Air Lines operational excellence, AirGuard AI verifies agent identity, enforces granular customer consent, computes multi-factor risk scores, and guards against unauthorized transactions.

> **Disclaimer:** This project is an academic research prototype. It connects only to simulated airline inventory and does not interact with live Delta Air Lines production APIs, real payment gateways, or actual customer accounts.

---

## 🏗️ System Architecture & Workflow

```
+-------------------------------------------------------------------------+
|                       Customer / Third-Party Agent                      |
|                  (e.g., SkyAssistant Pro, VoyageBot)                    |
+-------------------------------------------------------------------------+
                                     |
                          [NLU Intent / Tool Call]
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  AI Travel Agent Orchestrator (ai_agent.py)             |
|   1. Parses natural language travel queries (Routing, Budget, Seat)     |
|   2. Invokes Simulated Inventory Tool (FlightService.search_flights)     |
|   3. Selects optimal flight & calculates total fees                     |
|   4. Synthesizes structured booking request payload                     |
+-------------------------------------------------------------------------+
                                     |
                                     | [Cryptographic Bearer Token]
                                     | [Structured Booking Payload]
                                     v
+=========================================================================+
|                   AIRGUARD GATEKEEPER ENGINE (PEP / PDP)                |
|                                                                         |
|  Step 1: Receive Agent Booking Request Payload                          |
|  Step 2: Authenticate Agent ID & Cryptographic Bearer Token             |
|  Step 3: Verify Agent Operational Status (Active vs Revoked)            |
|  Step 4: Verify Customer Consent & Account Association                  |
|  Step 5: Enforce Granular Permission Matrix (8 Privileges)              |
|  Step 6: Enforce Customer Financial Spending & Transaction Limits       |
|  Step 7: Execute Risk Assessment Engine (Heuristics & Anomalies)        |
|  Step 8: Formulate Policy Decision:                                     |
|           • APPROVED               (Risk <= 35, all bounds clear)       |
|           • REJECTED               (Security, budget, or auth failure)  |
|           • PENDING HUMAN APPROVAL (High risk / budget escalation)      |
|  Step 9: Commit Tamper-Evident Record into Audit Trail & Transactions   |
+=========================================================================+
            |                                           |
            v                                           v
[APPROVED: Auto-Execute]                   [HIGH RISK / ESCALATED]
            |                                           |
            v                                           v
  Debit Simulated Wallet                     Human-in-the-Loop Queue
  Issue Boarding Reference                   Customer / Admin Review
```

---

## 🧰 Technology Stack

1. **Language:** Python 3.10+ / 3.14
2. **Web Framework / UI:** Streamlit (Custom Delta Air Lines Navy & Red Theme)
3. **Database:** SQLite with WAL mode (`database/airguard.db`)
4. **Data Analytics:** Pandas
5. **Interactive Data Visualization:** Plotly (Donut charts, distribution histograms, route volume bars, scatter plots)
6. **Security Logic:** Zero-Trust PEP/PDP policy verification, token-based authentication, tamper-evident audit logging
7. **Agentic AI:** Autonomous Travel Agent Orchestrator with structured tool execution, step-by-step reasoning trace, and local deterministic fallback parser (guaranteeing 100% offline operation).

---

## 📦 Core Modules

### Module 1: Admin Operations Dashboard
- Real-time KPI metric cards (Total Agents, Active Agents, Revoked Agents, Total Requests, Approved Requests, Rejected Requests, Pending Approvals, Security Alerts).
- Interactive Plotly visualizations:
  - Gatekeeper Authorization Outcomes (Donut Chart)
  - Risk Severity Distribution (Bar Chart)
  - Route Activity & Booking Volume (City Hub Analysis)
  - Risk Score vs. Transaction Value (Scatter Plot with threshold lines)
- Live stream of security and authorization alerts.

### Module 2: AI Agent Registration & Management
- Provision new third-party AI agents with auto-generated unique IDs (`AGT-XXXX`).
- Issue secure simulated API bearer tokens (`agtok_...`).
- Associate agents with customer SkyMiles accounts.
- Toggle operational status (`ACTIVE` ↔ `INACTIVE`).
- Baseline risk profile assignment (`LOW`, `MEDIUM`, `HIGH`).

### Module 3: Agent Authentication & Revocation Detection
- Agent ID validation.
- Cryptographic token matching.
- Customer association validation (preventing cross-account identity fraud).
- **Zero-Tolerance Revocation Gate:** Permanently rejected if status is `REVOKED`.

### Module 4: Granular Permission Management
Enforces the **Principle of Least Privilege** with 8 fine-grained permissions:
1. `SEARCH_FLIGHTS`: Query flight schedules and availability.
2. `VIEW_FLIGHT_DETAILS`: View aircraft specifications and seat layouts.
3. `BOOK_FLIGHTS`: Initiate reservation requests.
4. `SELECT_SEATS`: Select preferred, extra legroom, or premium seats.
5. `PURCHASE_BAGGAGE`: Purchase additional baggage allowance.
6. `CANCEL_BOOKINGS`: Cancel existing confirmed reservations.
7. `MODIFY_BOOKINGS`: Alter travel dates, times, or routes.
8. `MAKE_PAYMENTS`: Authorize automatic payment debits.

### Module 5: Airline Flight Simulator
- Realistic simulated inventory connecting 8 major Indian aviation hubs:
  **Delhi (DEL), Mumbai (BOM), Bengaluru (BLR), Hyderabad (HYD), Chennai (MAA), Kolkata (CCU), Pune (PNQ), and Goa (GOI)**.
- Flight numbers (e.g. DL-101, DL-204, DL-515), aircraft types (Airbus A350, A321neo, Boeing 737-900ER), cabin classes, available seats, and dynamic pricing calculations.

### Module 6: Gatekeeper Policy Engine (PEP / PDP)
- Enforces the 9-step gatekeeper evaluation pipeline.
- Emits explainable decision rationales for every transaction.
- Decrements inventory upon approval and triggers simulated transactions.

### Module 7: Risk Assessment Engine
Calculates a composite risk score (0 - 100):
- **Agent Status & Baseline:** Revoked (100 pts), Inactive (50 pts), Baseline risk.
- **Permission Sensitivity:** Sensitive mutations (+10 to +15 pts), Missing permissions (+35 pts).
- **Financial Heuristics:** Exceeding transaction budget (+40 pts), Nearing budget (+15 pts), High absolute value (+10 pts).
- **Behavioral Anomalies:** Excess baggage > 2 bags (+15 pts), Premium cabin upgrade (+10 pts), Velocity anomalies (+20 pts).
- **Risk Tiers:**
  - `LOW RISK` (0 - 35) → Auto-Approved
  - `MEDIUM RISK` (36 - 70) → Conditionally Approved or Flagged
  - `HIGH RISK` (71 - 100) → Escalated to Human Approval or Rejected

### Module 8: Human-in-the-Loop Approval Queue
- Central portal where customers or security administrators review escalated transactions.
- Inspect complete transaction details, flight numbers, requested permissions, and risk factor diagnostics.
- Approve or Reject with custom reviewer justification notes.

### Module 9: Emergency Agent Revocation (Kill-Switch)
- One-click cryptographic de-authorization.
- Instantly sets status to `REVOKED`.
- Permanently disables all 8 permissions.
- Automatically generates immutable revocation ledger entries and logs critical audit alerts.

### Module 10: Central Audit Logging & Forensic Trail
- Tamper-evident logging of all events (`AGENT_REGISTRATION`, `AUTH_SUCCESS`, `AUTH_FAILURE`, `PERMISSION_CHANGED`, `BOOKING_REQUEST`, `GATEKEEPER_DECISION`, `HUMAN_APPROVAL`, `AGENT_REVOCATION`, `RISK_ALERT`).
- Filter by Event Type, Severity (`INFO`, `WARNING`, `CRITICAL`, `ALERT`), and Agent ID.
- Keyword search and one-click **CSV Export**.

---

## 🗄️ Database Schema (`airguard.db`)

The SQLite database comprises 8 relational tables:
1. `customers`: Passenger profiles, SkyMiles tiers, transaction limits, daily spending bounds.
2. `agents`: Registered AI agents, owner links, developer orgs, bearer tokens, operational status.
3. `permissions`: Granular capability flags (0 or 1), timestamps for grants and revocations.
4. `flights`: Simulated flight routes, aircraft specs, cabin classes, seat counts, and base fares.
5. `booking_requests`: Central record of every agent booking submission, risk scores, decisions, and reviewer comments.
6. `transactions`: Executed financial debits (`SUCCESS`, `BLOCKED`, `REFUNDED`).
7. `revocation_records`: Permanent audit record of revoked agents, actors, and reasons.
8. `audit_logs`: Time-stamped forensic trail of all security actions with severity levels.

---

## 🚀 Installation & Execution Guide

### 1. Workspace Configuration
If you cloned or placed the project inside your Antigravity scratch directory:
```powershell
cd "C:\Users\bhanu\.gemini\antigravity\scratch\AirGuard_AI"
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```
*(Dependencies: `streamlit`, `pandas`, `plotly`)*

### 3. Run the Streamlit Application
```powershell
streamlit run app.py
```
The application will launch in your browser at `http://localhost:8501`.

The database automatically initializes and seeds sample data on the first launch!

---

## 🧪 Automated Testing & Verification

Run the comprehensive test suite verifying all 8 academic scenarios:
```powershell
python test_airguard.py
```

### Verified Scenarios:
1. `test_01_authorized_agent_booking`: Authorized agent with valid permissions and budget books a flight (Expected: `APPROVED`, `LOW RISK`).
2. `test_02_unauthorized_agent_attempt`: Non-existent agent ID or invalid token attempts booking (Expected: `REJECTED`, `AUTH_FAILURE`).
3. `test_03_revoked_agent_attempt`: Revoked agent attempts transaction (Expected: `REJECTED`, Score 100, `ALERT` logged).
4. `test_04_agent_exceeding_customer_budget`: Agent booking exceeds customer spending ceiling (Expected: `PENDING_HUMAN_APPROVAL` / `REJECTED`).
5. `test_05_agent_requesting_restricted_permissions`: Agent requesting permission not granted by customer (Expected: `REJECTED`).
6. `test_06_high_risk_transaction`: High baggage count + premium cabin + ungranted sensitive mutations (Expected: `HIGH RISK`).
7. `test_07_human_approval_workflow`: Escalated request reviewed and manually authorized with audit note (Expected: `APPROVED`, status updated).
8. `test_08_successful_agent_revocation`: Active agent revoked; credentials deactivated, permissions stripped, future transactions blocked (Expected: `REVOKED`).

---

## 📂 Project Directory Structure

```
AirGuard_AI/
│
├── app.py                     # Main Streamlit router & executive entry point
├── database.py                # SQLite schema, connection pool & seed generator
├── gatekeeper.py              # Core Gatekeeper Engine (PEP & PDP policy evaluation)
├── agent_manager.py           # Registration, Token Auth & Revocation Logic
├── risk_engine.py             # Multi-factor Risk Scoring & Anomaly Detection
├── audit_logger.py            # Centralized Audit & Forensics Logger
├── flight_service.py          # Simulated Airline Flight Inventory & Pricing
├── ai_agent.py                # Agentic AI Travel Orchestrator & Deterministic NLU
├── test_airguard.py           # Top-level automated test suite runner
├── requirements.txt           # Python dependency requirements
├── README.md                  # Comprehensive architectural documentation
│
├── database/
│   └── airguard.db            # Persistent SQLite database (auto-initialized)
│
├── pages/
│   ├── dashboard.py           # Page 1: Admin Security Operations Dashboard
│   ├── agents.py              # Page 2: AI Agent Management & Provisioning
│   ├── permissions.py         # Page 3: Granular Permission Matrix (8 privileges)
│   ├── flights.py             # Page 4: Flight Search & Schedule Explorer
│   ├── bookings.py            # Page 5: Agentic AI Booking Simulator & Console
│   ├── decisions.py           # Page 6: Gatekeeper Policy Enforcement Ledger
│   ├── approvals.py           # Page 7: Human-in-the-Loop Approval Queue
│   ├── risk_monitoring.py     # Page 8: Risk Assessment Lab & Simulator
│   ├── revoke.py              # Page 9: Emergency Agent Revocation Kill-Switch
│   └── audit_logs.py          # Page 10: Audit Logs & Forensic Trail
│
├── tests/
│   └── test_scenarios.py      # Detailed test cases covering all 8 scenarios
│
└── utils/
    └── helpers.py             # Delta Air Lines CSS styles, badges & formatters
```

---

## 🎓 Academic Contribution

This project models how enterprise airlines can adapt their cybersecurity architectures for the impending wave of consumer Agentic AI. By placing a specialized Gatekeeper between external LLM agents and core flight inventory, airlines protect customer financial bounds, maintain regulatory compliance, and enforce the Principle of Least Privilege without degrading user autonomy.
