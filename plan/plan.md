# PS-05: Personal Finance Agent — Master Build Plan

## 1. Project Identity

- **Project Name:** Personal Finance Agent
- **Domain:** FinTech
- **Build Location:** `C:\Users\krish\Downloads\Testing-Kim2.7\`
- **Architecture:** LangGraph ReAct multi-agent system with shared state
- **Frontend:** React + Vite + shadcn/ui + Tailwind CSS
- **Backend:** FastAPI + async SQLAlchemy + Alembic
- **Database:** PostgreSQL (local now, schema ready for Supabase cloud)
- **LLM Provider:** Groq API
- **PDF Parsing:** `pypdf` / `pdfplumber` + OCR fallback (`pytesseract` / `easyocr`)

---

## 2. Mission Statement

Build an autonomous financial wellness agent that converts raw financial documents (bank statements, credit card statements, UPI history, CSV) into structured intelligence, then continuously monitors spending, detects anomalies, tracks budgets, forecasts cash flow, and proactively recommends actions to improve financial health.

The system is not a passive dashboard. It is a continuous financial advisor.

---

## 3. Core Design Decisions

1. **LangGraph with ReAct Pattern:** Every agent is a node in a graph. Each node can reason over the `SharedState`, decide which internal tool (database query, math operation, LLM call) to invoke, and produce structured output back into the state.
2. **Shared State:** A single `TypedDict` state object passes between all agents. It contains lightweight summaries and metadata. Raw transaction data never lives fully in the state; it is read from PostgreSQL via tools when needed.
3. **State-DB Split:** Full raw history is stored in Postgres. The graph state only carries aggregated summaries, batch previews, computed metrics, flags, and pending actions.
4. **Password-Protected PDFs:** Frontend provides a password field during upload. Backend attempts decryption. If decryption fails, a clear error is returned without storing the password.
5. **Advanced Features as First-Class:** Goal planning, life-event simulation, financial twin, investment readiness, family finance, and AI CFO dashboard are not add-ons — they are core agent modules.
6. **Cloud-Ready Schema:** UUID primary keys, JSONB metadata fields, timezone-aware timestamps, and documented Supabase migration steps.

---

## 4. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                         │
│  (shadcn/ui + Tailwind + Recharts + Zustand + React Query)     │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS / HTTP 1.1
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                        │
│  JWT Auth │ Upload │ Dashboard │ Insights │ Goals │ Scenarios  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              LangGraph Orchestrator (ReAct Graph)              │
│    SharedState passes through: raw_extract → categorize →      │
│    parallel analysis → advisor → advanced → notifications      │
└────────────────────────────┬────────────────────────────────────┘
                             │ Reads / Writes
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                       │
│  users │ statements │ transactions │ budgets │ goals │ alerts  │
│  subscriptions │ scenarios │ family_members │ health_reports  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. LangGraph Orchestration Flow

```
                 ┌──────────────────┐
                 │      START       │
                 └────────┬─────────┘
                          │ user_id, file_ids
                          ▼
              ┌───────────────────────┐
              │   Data Ingestion Agent│
              │  extract + normalize  │
              └───────────┬───────────┘
                          │ transactions[batch]
                          ▼
              ┌───────────────────────┐
              │ Categorization Agent  │
              │ classify transactions │
              └───────────┬───────────┘
                          │ categorized
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
   ┌────────────────┐ ┌────────┐ ┌────────────────┐
   │ Spending       │ │ Budget │ │ Anomaly        │
   │ Analysis Agent │ │ Agent  │ │ Detection Agent│
   └───────┬────────┘ └───┬────┘ └───────┬────────┘
           │              │              │
           ▼              ▼              ▼
   ┌────────────────┐ ┌────────┐ ┌────────────────┐
   │ Health Score   │ │ Subscr │ │ Cash Flow      │
   │ Agent          │ │ Agent  │ │ Forecast Agent │
   └───────┬────────┘ └────┬───┘ └───────┬────────┘
           │               │             │
           └───────────────┼─────────────┘
                           │ all summaries
                           ▼
                  ┌───────────────────┐
                  │ Financial Advisor │
                  │ Agent             │
                  └─────────┬─────────┘
                            │ insights
                            ▼
                  ┌───────────────────┐
                  │ Advanced Agent    │
                  │ Layer             │
                  │ goals/scenarios/  │
                  │ twin/investment/  │
                  │ family            │
                  └─────────┬─────────┘
                            │ alerts_to_send
                            ▼
                  ┌───────────────────┐
                  │ Notification      │
                  │ Agent             │
                  └─────────┬─────────┘
                            │ final response
                            ▼
                          END
```

### Parallel Execution Strategy
- After categorization, analysis agents run in parallel fan-out.
- Each parallel branch writes to its own keys in `SharedState`.
- The `Advisor` node runs only after all parallel branches complete (barrier synchronization).
- The `Advanced Layer` and `Notification` nodes run sequentially after the advisor.

---

## 6. SharedState Definition

```python
from typing import TypedDict, Optional, Any
from datetime import date

class SharedState(TypedDict):
    # Identifiers
    user_id: str
    statement_ids: list[str]

    # Ingestion output
    raw_text_preview: str
    extracted_transactions: list[dict]

    # Categorization output
    transactions: list[dict]
    category_id_map: dict[str, str]
    category_summaries: dict[str, float]

    # Analysis outputs
    monthly_summaries: dict[str, dict[str, float]]
    trends: list[dict]
    utilization_report: dict[str, Any]
    budget_alerts: list[dict]
    rebalance_recommendations: list[dict]
    health_score: int
    health_breakdown: dict[str, float]
    anomalies: list[dict]
    subscriptions: list[dict]
    cashflow_forecast: dict[str, Any]

    # Advisory + Advanced
    insights: list[dict]
    goals_projection: list[dict]
    scenario_impact: dict[str, Any]
    financial_twin_snapshot: dict[str, Any]
    investment_readiness: dict[str, Any]
    family_aggregation: dict[str, Any]

    # Notification
    alerts_to_create: list[dict]
    response_to_user: str
    execution_log: list[str]
```

---

## 7. File Directory Plan

```
Testing-Kim2.7/
├── plan/
│   ├── plan.md
│   ├── agent-data-ingestion.md
│   ├── agent-categorization.md
│   ├── agent-spending-analysis.md
│   ├── agent-budget.md
│   ├── agent-health-score.md
│   ├── agent-anomaly.md
│   ├── agent-subscription.md
│   ├── agent-cashflow-forecast.md
│   ├── agent-advisor.md
│   ├── agent-notification.md
│   ├── agent-orchestrator.md
│   ├── agent-goal-planner.md
│   ├── agent-life-event-simulator.md
│   ├── agent-financial-twin.md
│   ├── agent-investment-readiness.md
│   ├── agent-family-finance.md
│   ├── schema.md
│   └── api-spec.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── agents/
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   ├── nodes/
│   │   │   └── tools/
│   │   └── schemas/
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── lib/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── .env
├── docker-compose.yml
└── README.md
```

---

## 8. Implementation Phases

### Phase 0: Foundation (current phase)
- [x] Create directory structure
- [ ] Create Python virtual environment
- [ ] Create `requirements.txt`
- [ ] Create frontend `package.json`
- [ ] Create `.env.example`
- [ ] Write `README.md`

### Phase 1: Database & Auth
- [ ] Define SQLAlchemy models
- [ ] Create Alembic migrations
- [ ] Implement JWT auth routes
- [ ] Connect to local PostgreSQL

### Phase 2: Document Ingestion
- [ ] PDF upload endpoint with password support
- [ ] CSV upload endpoint
- [ ] Text extraction service (pdfplumber + OCR fallback)
- [ ] Transaction normalization service

### Phase 3: LangGraph Core
- [ ] Define SharedState
- [ ] Build Orchestrator graph
- [ ] Implement 10 core agents as nodes
- [ ] Connect DB tools

### Phase 4: Advanced Features
- [ ] Goal planner agent
- [ ] Life event simulator
- [ ] Financial twin
- [ ] Investment readiness
- [ ] Family finance aggregator

### Phase 5: Frontend
- [ ] Set up Vite + React + shadcn/ui
- [ ] Auth pages
- [ ] Upload page with password field
- [ ] AI CFO dashboard
- [ ] Transactions, insights, goals, scenarios, family pages

### Phase 6: Integration & Polish
- [ ] Wire frontend to backend
- [ ] WebSocket/SSE progress updates
- [ ] Write tests
- [ ] Add demo data
- [ ] Prepare Supabase migration SQL

---

## 9. Dependencies

### Backend (`requirements.txt`)
```txt
fastapi==0.111.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.13.1
langgraph==0.0.59
langchain-groq==0.1.4
langchain-core==0.2.0
pydantic==2.7.1
pydantic-settings==2.2.1
pypdf==4.2.0
pdfplumber==0.11.0
pytesseract==0.3.10
Pillow==10.3.0
easyocr==1.7.0
pandas==2.2.2
python-dateutil==2.9.0
python-dotenv==1.0.1
pytest==8.2.0
httpx==0.27.0
email-validator==2.1.1
```

### Frontend (`package.json`)
```json
{
  "name": "personal-finance-agent-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.1",
    "@tanstack/react-query": "^5.37.1",
    "axios": "^1.7.2",
    "zustand": "^4.5.2",
    "recharts": "^2.12.7",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.3.0",
    "lucide-react": "^0.378.0",
    "@radix-ui/react-*": "latest"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.4.5",
    "vite": "^5.2.11"
  }
}
```

---

## 10. Security Considerations

1. **Passwords:** Stored as bcrypt hashes. PDF passwords are used at runtime only and never persisted.
2. **JWT:** Access tokens expire in 60 minutes. Use refresh tokens in Phase 2 if needed.
3. **File Uploads:** Restrict to PDF, CSV, XLSX. Scan file size. Store temporarily or in DB blob.
4. **SQL Injection:** Use SQLAlchemy ORM binds; no raw interpolation.
5. **CORS:** Restrict to frontend origin in production.
6. **RLS:** When moving to Supabase, apply RLS policies tying rows to `user_id`.

---

## 11. Cloud Migration Path

1. Export schema using `pg_dump --schema-only`.
2. Apply to Supabase via SQL Editor.
3. Enable RLS on every table with `user_id`.
4. Change `DATABASE_URL` to Supabase connection string.
5. Keep backend unchanged because SQLAlchemy uses standard Postgres dialect.
6. Optionally migrate uploaded files to Supabase Storage instead of DB text columns.

---

## 12. How to Run Locally

```powershell
# Backend
cd C:\Users\krish\Downloads\Testing-Kim2.7\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# create .env from .env.example
uvicorn app.main:app --reload

# Frontend
cd C:\Users\krish\Downloads\Testing-Kim2.7\frontend
npm install
npm run dev
```

---

## 13. Success Criteria

- [ ] User can upload password-protected PDF bank statements.
- [ ] Transactions are extracted, normalized, categorized, and stored.
- [ ] Dashboard shows health score, budget utilization, anomalies, cash flow forecast.
- [ ] Alerts are generated proactively (budget risk, fraud, subscriptions, savings).
- [ ] Goal planning shows required monthly savings and progress.
- [ ] Life event simulator shows EMI/savings/cashflow impact.
- [ ] Financial twin can test salary change, job loss, new loan.
- [ ] Investment readiness blocks risky advice until emergency fund is complete.
- [ ] Family finance aggregates multiple members.
- [ ] Schema can be deployed to Supabase without structural changes.

---

*Plan generated for PS-05 Personal Finance Agent.*
