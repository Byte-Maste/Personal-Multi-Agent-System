# Agent 10: Alert & Notification Agent

## Purpose
Creates and routes all user-facing alerts from across the system. Alert types include: budget risk, fraud/anomaly, subscription waste, savings rate drop, bill due reminders, and goal milestones. Stores alerts in the database, batches them for frontend display, and manages read/unread state.

## Domain: FinTech
Timely notifications are critical for user engagement and financial well-being. However, notification spam leads to app fatigue and opt-out. The agent must intelligently batch related alerts, suppress duplicates, respect quiet hours, and prioritize by severity. In the Indian market, SMS and in-app notifications are primary channels, with WhatsApp and email as secondary options.

## LangGraph ReAct Pattern
**Reasoning:** The agent examines all outputs from other agents for actionable events, determines the appropriate notification type and severity, checks for suppression rules (duplicates, quiet hours, frequency caps), and formats the message.

**Action:** It calls the alert creation tool, applies batching logic, persists to DB, and returns the formatted alert list for the frontend.

## Input (from SharedState)
- `budget_alerts` from Budget Agent
- `anomaly_flags` from Anomaly Detection Agent
- `cancellation_recommendations` from Subscription Agent
- `low_balance_alerts` from Cash Flow Agent
- `advice_summary` from Advisor Agent
- `health_score` from Health Score Agent
- `user_id`: for user notification preferences

## Output (writes to SharedState)
- `alerts`: list of `{id, type, severity, title, message, action_url, created_at}`
- `batched_alerts`: grouped alerts for UI rendering (by type or day)

## Internal Tools Used

| Tool | Description |
|---|---|
| `create_alert(user_id, type, severity, title, message, action_url)` | Persists an alert to the notification DB table |
| `batch_alerts(alerts, strategy)` | Groups alerts by type, severity, or time window for consolidated display |
| `mark_read(user_id, alert_ids)` | Updates alert read status in DB (called from frontend) |

## Alert Types and Severity

| Alert Type | Source Agent | Default Severity | Example Message |
|---|---|---|---|
| `budget_risk` | Budget | Medium | "Food budget at 90% — ₹1,200 remaining this month" |
| `budget_exceeded` | Budget | High | "Entertainment budget exceeded by ₹850" |
| `anomaly_critical` | Anomaly | Critical | "₹15,000 flagged as potential fraud at 2 AM" |
| `anomaly_medium` | Anomaly | Medium | "Duplicate charge detected: ₹480 at Swiggy" |
| `subscription_unused` | Subscription | Low | "Spotify unused for 4 months — save ₹119/mo by cancelling" |
| `savings_rate_drop` | Health Score | Medium | "Savings rate dropped from 22% to 12% this month" |
| `bill_due` | Cash Flow | Medium | "EMI ₹18,000 due in 3 days — current balance ₹34,500" |
| `low_balance` | Cash Flow | High | "Balance projected at ₹8,200 on Mar 20 — below threshold" |
| `goal_milestone` | Advisor | Low | "Wedding fund at 50% of target! ₹2.5L of ₹5L saved" |
| `advice_high` | Advisor | Medium | "Top recommendation: Build emergency fund — score impact +16 pts" |

## Agent Logic Flow

```
1. Poll all agent outputs from SharedState for new actionable items
2. For each actionable item, determine:
   a. Alert type (from mapping table above)
   b. Severity (from source or escalate if repeated)
   c. Title and message (template-based with dynamic values)
   d. Action URL (deep link to relevant screen in app)
3. Check suppression rules before creating:
   a. Is there already an unread alert of the same type in last 24h? → skip (duplicate)
   b. Is it within user's quiet hours? → defer or downgrade severity
   c. Has user hit daily notification cap? → queue for next day
4. Call create_alert() to persist each valid alert
5. Call batch_alerts() to group alerts by:
   a. Day (for daily digest)
   b. Type (budget alerts grouped together)
   c. Severity (critical alerts always standalone)
6. Update SharedState with alerts and batched_alerts
7. Return control to Orchestrator
```

## Suppression and Batching Rules

| Rule | Implementation |
|---|---|
| Duplicate suppression | Same type + same message within 24h → skip; update existing alert count instead |
| Quiet hours | Configurable window (default 11 PM – 7 AM); queue non-critical alerts |
| Severity escalation | If same alert type fires 3+ times → escalate severity one level |
| Daily cap | Max 10 notifications/day; excess batched into "3 more updates" summary |
| Critical bypass | Critical alerts always deliver, regardless of quiet hours or cap |
| Read expiry | Unread alerts auto-archive after 30 days |

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| User has not enabled notifications | Still create alerts in DB; skip channel delivery; frontend shows badge |
| Same alert fires multiple times (budget risk every day) | Coalesce into single "still at risk" alert; update count |
| Alert references deleted transaction | Soft-link with foreign key; display "no longer available" fallback |
| Massive batch (100+ alerts on first sync) | Create in bulk insert; batch into daily groups for UI |
| Real-time vs. batch mode | If running in real-time: deliver immediately. If batch: hold for next digest cycle |
| User marks all read | Single call to mark_read() with no IDs clears all unread |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Process alerts for user u_123
New items: 2 budget alerts, 1 anomaly critical, 1 subscription unused, 1 low balance
```

**Agent Reasoning:**
```
Critical anomaly must be delivered immediately — fraud alert.
Budget and low balance are same day — can batch into daily group.
Subscription unused is low severity — can wait or batch.
Check: Is this the 3rd food budget alert this week? Yes → escalate from medium to high.
User is in quiet hours (2 AM)? Critical anomaly bypasses, others queued.
```

**Action Taken:**
```
create_alert(u_123, "anomaly_critical", "critical",
  "Potential fraud detected", 
  "₹15,000 CryptoXchange at 2:14 AM — review immediately",
  "/transactions/42")
→ bypass quiet hours, deliver immediately

create_alert(u_123, "budget_exceeded", "high",
  "Food budget exceeded",
  "Food spend ₹47,200 vs limit ₹42,500 — ₹4,700 over",
  "/budget/needs/food")
→ escalated from medium to high (3rd occurrence)

batch_alerts([budget_exceeded, low_balance], "daily")
→ {date: "2025-03-15", alerts: [budget_exceeded, low_balance]}

batch_alerts([subscription_unused], "weekly")
→ queued for weekly digest
```

## Verification
- Every alert has a non-null `id`, `type`, `severity`, `title`, and `message`
- No duplicate unread alerts of the same type exist for the same user within 24h
- Critical severity alerts always bypass suppression rules
- `batched_alerts` grouping does not lose any alert entries
- Total alerts per user per day does not exceed configured cap (default 10)
