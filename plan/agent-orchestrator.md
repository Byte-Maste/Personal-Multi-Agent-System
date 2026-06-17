# Agent 11: Master Orchestrator Agent

## Purpose
Implements the LangGraph state graph that connects all agents into a coherent pipeline. Routes the `SharedState` object between nodes, manages parallel fan-out for independent analysis agents, implements barrier synchronization before the advisor node, handles error states with retries and partial failures, and defines the complete routing logic for the system.

## Domain: FinTech
A personal finance agent system requires a carefully orchestrated pipeline: data must be ingested before it can be categorized, budgets depend on categorized data, health scores depend on budgets and spending, anomaly detection runs parallel to categorization, and the advisor synthesizes everything. The orchestrator defines this dependency graph, manages state transitions, and ensures resilience when individual agents fail.

## LangGraph ReAct Pattern
**Reasoning:** The orchestrator examines the current state of the pipeline (which agents have completed, what data is available, what errors have occurred) and determines the next node(s) to execute.

**Action:** It routes the `SharedState` to the appropriate agent node(s), manages fan-out for parallel agents, waits at barrier nodes, and handles error recovery or graceful degradation.

## Graph Topology

```
                    ┌──────────────────┐
                    │  START (Upload)  │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Data Ingestion  │  ← Agent 1
                    │  (single node)   │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Categorization  │  ← Agent 2
                    │  (single node)   │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────┐ ┌──────▼──────┐ ┌─────▼────────┐
      │   Budget    │ │  Anomaly    │ │  Subscription │  ← Agents 4, 6, 7
     │  Management │ │  Detection  │ │  Intelligence │
     └────────┬────┘ └──────┬──────┘ └──────┬────────┘
              │             │               │
              └─────────────┼───────────────┘
                            │
                    ┌───────▼────────┐
                    │    Barrier     │  ← Wait for all 3
                    │  Synchronize   │
                    └───────┬────────┘
                            │
              ┌─────────────┼──────────────┐
              │             │              │
     ┌────────▼────┐ ┌─────▼──────┐       │
     │  Health     │ │  Cash Flow │       │
      │  Score      │ │  Forecast  │       │  ← Agents 5, 8
     └────────┬────┘ └─────┬──────┘       │
              │            │              │
              └────────────┼──────────────┘
                           │
                    ┌──────▼───────┐
                     │   Advisor    │  ← Agent 9
                    │  (single)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                     │ Notification │  ← Agent 10
                    │  (single)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │     END      │
                    └──────────────┘
```

## SharedState Definition

```python
@dataclass
class SharedState:
    user_id: str
    session_id: str

    # Pipeline status
    pipeline_stage: str  # "ingestion" | "categorization" | "analysis" | "advisory" | "complete" | "error"
    error_state: Optional[dict]  # {agent, error_type, message, retry_count}

    # Agent outputs (populated sequentially)
    statement_ids: List[str] = field(default_factory=list)
    raw_text_preview: str = ""
    extracted_transactions: List[dict] = field(default_factory=list)
    transactions: List[dict] = field(default_factory=list)
    category_summaries: dict = field(default_factory=dict)
    category_id_map: dict = field(default_factory=dict)

    # Analysis agent outputs (populated in parallel)
    budgets: dict = field(default_factory=dict)
    utilization_report: dict = field(default_factory=dict)
    budget_alerts: List[dict] = field(default_factory=list)
    rebalance_recommendations: List[dict] = field(default_factory=list)
    anomaly_flags: List[dict] = field(default_factory=list)
    anomaly_summary: str = ""
    subscriptions: List[dict] = field(default_factory=list)
    unused_subscriptions: List[dict] = field(default_factory=list)
    cancellation_recommendations: List[dict] = field(default_factory=list)

    # Advisory agent outputs
    health_score: Optional[int] = None
    score_breakdown: dict = field(default_factory=dict)
    score_trend: str = ""
    top_drags: List[str] = field(default_factory=list)
    balance_forecast: List[dict] = field(default_factory=list)
    low_balance_alerts: List[dict] = field(default_factory=list)
    forecast_summary: str = ""
    stress_test_results: dict = field(default_factory=dict)
    advice_items: List[dict] = field(default_factory=list)
    advice_summary: str = ""

    # Notification outputs
    alerts: List[dict] = field(default_factory=list)
    batched_alerts: List[dict] = field(default_factory=list)
```

## Agent Logic Flow

```
1. START: Receive user_id and optional file upload
   → Initialize SharedState with defaults
   → Set pipeline_stage = "ingestion"

2. Data Ingestion Node (single):
   → Route SharedState to Data Ingestion Agent
   → If success: advance to Categorization
   → If error: set error_state, retry up to 2 times, else partial_fail

3. Categorization Node (single):
   → Route SharedState to Categorization Agent
   → If success: advance to analysis (fan-out)
   → If error: retry 1 time, else set transactions to "Uncategorized"

4. Analysis Fan-Out Node (parallel):
   → Clone SharedState for 3 parallel branches:
      a. Budget Management Agent
      b. Anomaly Detection Agent
      c. Subscription Intelligence Agent
   → Execute all 3 in parallel
   → Collect results at Barrier Synchronization point
   → If any agent fails: log error, continue with partial data

5. Barrier Synchronization:
   → Wait for all 3 analysis agents to complete (or timeout after 30s)
   → Merge results back into SharedState
   → Block until all branches return before proceeding
   → Advance to advisory fan-out

6. Advisory Fan-Out Node (parallel):
   → Clone SharedState for 2 parallel branches:
      a. Health Score Agent (depends on budgets + categorization)
      b. Cash Flow Forecast Agent (depends on subscriptions + categorization)
   → Execute both in parallel
   → Collect results

7. Advisor Node (single, depends on all prior):
   → Route SharedState to Financial Advisor Agent
   → Requires: health_score, budgets, subscriptions, anomaly_flags, cashflow
   → If any dependency is missing: proceed with available data, flag gaps

8. Notification Node (single):
   → Route SharedState to Notification Agent
   → Creates alerts from all agent outputs
   → Returns batched_alerts for frontend

9. END:
   → Set pipeline_stage = "complete"
   → Return SharedState to caller (API / frontend)
```

## Parallel Fan-Out Implementation

```
function fan_out_analysis(state):
    branches = []
    spawn branch → budget_agent.run(state.user_id, state.category_summaries)
    spawn branch → anomaly_agent.run(state.user_id, state.transactions)
    spawn branch → subscription_agent.run(state.user_id, state.transactions)

    results = barrier_wait(branches, timeout=30s)

    if results.budget:
        state.budgets = results.budget.budgets
        state.utilization_report = results.budget.utilization_report
        state.budget_alerts = results.budget.budget_alerts
        state.rebalance_recommendations = results.budget.rebalance_recommendations

    if results.anomaly:
        state.anomaly_flags = results.anomaly.anomaly_flags
        state.anomaly_summary = results.anomaly.anomaly_summary

    if results.subscription:
        state.subscriptions = results.subscription.subscriptions
        state.unused_subscriptions = results.subscription.unused_subscriptions
        state.cancellation_recommendations = results.subscription.cancellation_recommendations

    return state
```

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| Agent timeout (>30s) | Mark agent as failed; continue pipeline with partial data |
| Multiple agents fail | Continue with whatever data is available; flag gaps in advisor |
| File upload fails at ingestion | Return error to user immediately; do not proceed |
| Retry exhausted (3 attempts) | Skip agent; mark as permanently failed; log for admin review |
| Empty transaction list after ingestion | Short-circuit to END with "No data" message |
| User session expires mid-pipeline | Persist state; resume from last checkpoint on re-auth |
| Non-deterministic agent outputs | Accept latest result; do not re-run unless explicitly requested |
| Circular dependency detected | Graph is acyclic by design — validate at startup with topological sort |

## Error States and Recovery

| Error | Recovery Strategy |
|---|---|
| `INGESTION_FAILED` | Retry up to 2 times; if still failing, return error to user |
| `CATEGORIZATION_FAILED` | Retry once; fall back to "Uncategorized" for all transactions |
| `BUDGET_FAILED` | Log error; continue; advisor notes "budget data unavailable" |
| `ANOMALY_FAILED` | Log error; continue; skip anomaly section in advisor |
| `SUBSCRIPTION_FAILED` | Log error; continue; skip subscription waste advice |
| `HEALTH_SCORE_FAILED` | Retry once; if still failing, set score to null; skip score-based advice |
| `CASHFLOW_FAILED` | Retry once; if still failing, skip forecast warnings |
| `ADVISOR_FAILED` | Retry once; if still failing, return generic advice from templates |
| `NOTIFICATION_FAILED` | Retry once; if still failing, drop alerts; frontend shows no notifications |
| `TIMEOUT` (any agent) | Treat as failed; continue with partial results |

## ReAct Example Interaction

**User Input (from API Gateway):**
```
POST /api/process
{
  user_id: "u_123",
  files: ["HDFC_Statement_Mar2025.pdf"],
  source: "HDFC Bank",
  password: null
}
```

**Orchestrator Reasoning:**
```
New session initiated. Starting pipeline at Ingestion node.
Uploaded 1 PDF from HDFC Bank. No password provided.
After ingestion → 85 transactions. Proceeding to Categorization.
After categorization → all 85 categorized. Fanning out to 3 parallel analysis agents.
Waiting at barrier for Budget, Anomaly, Subscription...
All 3 returned within 12s. Proceeding to advisory: Health Score + Cash Flow.
Health Score computed (52/100). Cash flow forecast done.
Advisor generated 5 recommendations. Notification batched 4 alerts.
Pipeline complete.
```

**State Transitions:**
```
START → INGESTION → CATEGORIZATION → ANALYSIS (fan-out)
→ BARRIER → ADVISORY (fan-out) → ADVISOR → NOTIFICATION → END
Total time: 18.4s
Agents succeeded: 10/10
Alerts created: 4
Score: 52/100
```

## Verification
- Pipeline executes all 10 agents (1–10) in correct dependency order
- Parallel fan-out nodes complete within configurable timeout (default 30s)
- Barrier synchronization correctly merges results from all branches
- Agent failure in analysis branches does not block non-dependent branches
- SharedState at END contains all non-null fields that were successfully produced
- Retry logic does not exceed configured max retries (default 2)
- Graph topology validation passes: no cycles, all dependencies satisfied
