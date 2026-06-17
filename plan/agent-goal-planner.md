# Agent 11: Goal-Based Planning Agent

## Purpose
User sets financial goals (e.g., "Buy car in 2 years", "Build 6-month emergency fund"). Agent calculates required monthly savings (`target / months_remaining`), tracks progress against actual savings, and alerts if off-track. Supports multiple concurrent goals with priority ranking. Handles goal types: emergency fund, debt payoff, large purchase, investment.

## Domain: FinTech
Goal-based planning is a proven method to increase user engagement and savings discipline. Indian users commonly set goals for wedding expenses (₹10-25L), children's education (₹20-50L), home down payment (₹20-60L), vehicle purchase (₹5-15L), and emergency corpus (6 months of expenses). The agent must account for inflation on long-term goals, variable contribution capabilities, and goal interaction (e.g., saving for two goals simultaneously with a single income). Priority ranking helps users decide which goal to fund first when resources are limited.

## LangGraph ReAct Pattern
**Reasoning:** The agent evaluates all active goals against the user's current savings rate, available surplus after expenses, and goal deadlines. It determines whether each goal is on track, ahead, or behind schedule, and computes the adjustment needed.

**Action:** It creates goal records with monthly targets, updates progress percent, generates off-track alerts with catch-up recommendations, and re-prioritizes goals when the user's financial situation changes.

## Input (from SharedState)
- `user_id`: for user-specific goals and progress history
- `income`: monthly after-tax income
- `transactions`: recent transaction list (for actual savings calculation)
- `category_summaries`: spending by category (to determine available surplus)
- `health_score`: financial health score for context
- `budgets` and `utilization_report`: to understand spending constraints

## Output (writes to SharedState)
- `goals`: list of `{id, type, name, target_amount, target_date, monthly_target, current_savings, progress_pct, status, priority}`
- `goal_alerts`: list of off-track goals with catch-up recommendations
- `goal_priority_ranking`: ordered list of goals by priority with rationale
- `surplus_after_goals`: remaining monthly surplus after all goal contributions

## Internal Tools Used

| Tool | Description |
|---|---|
| `create_goal(user_id, name, type, target, deadline)` | Persists a new goal record and returns goal ID |
| `calculate_monthly_target(target_amount, months_remaining, inflation_rate)` | Computes required monthly deposit; optionally inflates target |
| `track_progress(goal_id, actual_savings)` | Calculates progress percentage and status (ahead / on_track / behind / critical) |
| `assess_affordability(user_income, existing_goals, proposed_monthly)` | Checks if the user can afford a new goal given existing commitments |
| `reprioritize_goals(goals, user_financial_state)` | Re-ranks goals by urgency, importance, and user's current capacity |
| `recommend_catchup(goal, months_remaining, shortfall)` | Suggests increased monthly contribution or extended deadline to get back on track |

## Agent Logic Flow

```
1. Load user's active goals from DB via create_goal() or fetch existing
2. Load current financial state: income, expenses, surplus from SharedState
3. For each new goal request:
   a. Determine goal type for inflation assumptions:
      - emergency_fund → no inflation, target = 6× monthly expenses
      - debt_payoff → no inflation, target = outstanding balance
      - large_purchase → apply 5-8% annual inflation to target
      - investment → no inflation, target as specified
   b. Compute months_remaining = target_date - today
   c. Call calculate_monthly_target(target, months_remaining, inflation)
   d. Call assess_affordability(income, existing_goals, monthly_target)
   e. If affordable → save goal; if not → flag and suggest adjustment
4. For each existing goal, call track_progress():
   a. Compare actual_savings to expected_savings (monthly_target × months_elapsed)
   b. If actual >= expected → status = "ahead" or "on_track"
   c. If actual < 75% of expected → status = "behind"
   d. If actual < 50% of expected → status = "critical", create goal_alert
5. Call reprioritize_goals() to rank all active goals:
   a. Emergency fund and debt payoff → highest priority
   b. Large purchases with approaching deadlines → medium-high
   c. Investment goals → lower priority (adjustable)
6. For each "behind" or "critical" goal:
   a. Call recommend_catchup() to propose corrective action
   b. Add to goal_alerts
7. Compute surplus_after_goals = monthly_surplus - sum(monthly_targets)
8. Update SharedState with goals, alerts, ranking, and surplus
9. Return control to Orchestrator
```

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| Goal deadline already passed | Flag as "overdue"; recalculate with extended timeline or revised target |
| Multiple goals exceed total surplus | Reprioritize; suggest partial funding for lower-priority goals |
| User stops contributing to a goal | Detect via zero savings for 2+ months; flag as "paused"; alert user |
| Early goal achievement (ahead of schedule) | Reduce monthly target or let surplus roll to next goal |
| Goal target changes mid-course | Recalculate monthly target with remaining months; flag impact |
| Negative surplus after adding goal | Block goal creation; show affordability gap |
| Inflation adjustment on long goals (5+ years) | Apply 6% CAGR to target; recalculate monthly deposit |
| Partial goal funding (one-time lumpsum) | Credit lumpsum as progress; recalculate remaining monthly target |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
New goal for user u_123: {type: "large_purchase", name: "Buy Car", target: ₹12,00,000, deadline: "2027-06"}
Current income: ₹85,000/mo, expenses: ₹72,000/mo, surplus: ₹13,000/mo
Existing goals: Emergency fund (₹2,40,000 target, ₹1,20,000 saved)
```

**Agent Reasoning:**
```
Goal type: large_purchase → apply 6% inflation → inflated target ₹13,48,320
Months remaining: June 2025 → June 2027 = 24 months
Monthly target: ₹13,48,320 / 24 = ₹56,180
Surplus after emergency fund (₹10,000/mo): ₹13,000 - ₹10,000 = ₹3,000
₹56,180 >> ₹3,000 → user CANNOT afford this goal.
Need to suggest either: longer timeline, lower target, or increase income.
```

**Action Taken:**
```
create_goal(u_123, "Buy Car", "large_purchase", 1200000, "2027-06-01")
→ Goal created with inflated target ₹13,48,320
calculate_monthly_target(1348320, 24, 0.06) → ₹56,180/mo
assess_affordability(85000, [emergency_fund], 56180) → FAIL
→ Alert: "Car goal is not affordable with current surplus of ₹13,000/mo
   Options: extend deadline to 5 years (₹22,472/mo), reduce target, or increase savings"
reprioritize_goals([emergency_fund, car], {surplus: 13000})
→ Emergency fund stays priority 1 (urgent, essential)
→ Car goal set to priority 2 (cannot fund until surplus increases)
```

## Verification
- Every goal has a valid `monthly_target` > 0
- Sum of all `monthly_targets` ≤ user's monthly surplus (validated at creation)
- `progress_pct` = `current_savings / target_amount` × 100 for every goal
- Every "behind" or "critical" goal has a corresponding entry in `goal_alerts`
- `surplus_after_goals` is non-negative; if negative, goals flag is set
- Goal priority ranking places emergency fund and debt payoff above investment goals
