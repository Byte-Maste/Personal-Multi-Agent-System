# Agent 4: Budget Management Agent

## Purpose
Creates and manages budgets based on the 50/30/20 rule (needs/wants/savings), tracks budget utilization across categories, and recommends rebalancing when spending drifts off target. Detects when budgets are at risk (e.g., "Food budget 90% utilized") and proactively alerts the user.

## Domain: FinTech
Budgeting is the cornerstone of personal financial planning. The 50/30/20 framework is a widely accepted guideline: 50% of after-tax income for needs (rent, groceries, utilities, EMIs), 30% for wants (dining out, entertainment, shopping), and 20% for savings and investments. In the Indian context, needs often include higher EMIs and education costs, while wants may include OTT subscriptions and food delivery. The agent must handle irregular income patterns (freelancers, commission-based workers) and multi-currency budgets.

## LangGraph ReAct Pattern
**Reasoning:** The agent examines current spending across categories, compares against the 50/30/20 target allocation, identifies categories that are over or under budget, and determines whether rebalancing or an alert is needed.

**Action:** It creates or updates budget envelopes, computes utilization percentages, generates rebalancing recommendations, and issues budget risk alerts when thresholds are breached.

## Input (from SharedState)
- `category_summaries`: spending totals per category from Categorization Agent
- `user_id`: for user-specific budget settings
- `income`: user's monthly after-tax income (from profile or income transactions)
- `existing_budgets`: current budget allocations if any

## Output (writes to SharedState)
- `budgets`: list of budget envelopes with limits and current spend
- `utilization_report`: dict of `{category: {limit, spent, percentage, status}}`
- `budget_alerts`: any active alerts for budgets near/exceeding limits
- `rebalance_recommendations`: suggested adjustments to budget allocations

## Internal Tools Used

| Tool | Description |
|---|---|
| `fetch_budget(user_id, month)` | Retrieves current budget envelopes for the user from DB |
| `check_utilization(category, limit, spent)` | Computes spend vs. limit percentage and returns status (on_track / at_risk / exceeded) |
| `recommend_allocation(income, current_spend)` | Calculates ideal 50/30/20 split and suggests rebalancing moves |
| `alert_budget_risk(user_id, category, percentage)` | Creates a risk alert when utilization exceeds a configurable threshold (default 80%) |

## Agent Logic Flow

```
1. Load user's income and existing budgets from SharedState / DB
2. If no budgets exist for this month:
   a. Compute ideal 50/30/20 split from income
   b. Create budget envelopes: Needs = 50%, Wants = 30%, Savings = 20%
   c. Sub-allocate Needs across categories (rent, groceries, EMIs, etc.)
   d. Sub-allocate Wants across categories (dining, entertainment, etc.)
3. If budgets exist, load current spending from category_summaries
4. For each budget envelope, call check_utilization():
   a. If spent > 100% of limit → status = "exceeded", create alert
   b. If spent > 80% of limit → status = "at_risk", create alert
   c. Otherwise → status = "on_track"
5. Aggregate utilization_report from all envelopes
6. If total allocation deviates from 50/30/20 by >5%:
   a. Call recommend_allocation() to generate rebalancing suggestions
7. Update SharedState with budgets, utilization_report, alerts, and recommendations
8. Return control to Orchestrator
```

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| Irregular / variable income | Use 3-month average income; flag as "estimated" |
| No spending in a category yet | Utilization = 0%; mark as "unused" not "on_track" |
| Multiple income sources (salary + freelance) | Sum all income; separate tax allocation |
| User manually set non-standard allocation | Respect user override; annotate deviation from 50/30/20 |
| Partial month data | Pro-rate budget limits to days elapsed; flag as "partial" |
| Negative budget (refunds exceed spend) | Treat as 0% utilization; carry forward negative as credit |
| Currency mismatch (foreign transactions) | Convert at average monthly rate before comparison |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Budget check for user u_123, month March 2025
Income: ₹85,000/month
category_summaries loaded from SharedState
```

**Agent Reasoning:**
```
Income is ₹85,000. Ideal 50/30/20 = ₹42,500 needs / ₹25,500 wants / ₹17,000 savings.
Current spend: Needs ₹48,200 (113%), Wants ₹22,100 (87%), Savings ₹14,700 (86%).
Needs are over budget by ₹5,700. Food and EMIs are the drivers.
I should alert on Needs and recommend rebalancing from Wants to Needs or increasing total budget.
```

**Action Taken:**
```
fetch_budget(u_123, "2025-03") → existing budgets found
check_utilization("Needs", 42500, 48200) → 113%, exceeded → alert
check_utilization("Wants", 25500, 22100) → 87%, at_risk → alert
check_utilization("Savings", 17000, 14700) → 86%, at_risk → alert
recommend_allocation(85000, {needs: 48200, wants: 22100, savings: 14700})
→ "Needs exceeded by ₹5,700. Consider reducing wants by ₹2,000 or increasing income allocation."
```

## Verification
- Total of all budget limits equals income (for auto-created budgets)
- `utilization_report` percentages are all between 0 and 100+ (can exceed)
- Every "at_risk" or "exceeded" envelope has a corresponding alert in `budget_alerts`
- Rebalance recommendations do not suggest negative adjustments
