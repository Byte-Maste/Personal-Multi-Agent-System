# Agent 8: Cash Flow Forecasting Agent

## Purpose
Predicts future bank balance based on the user's income schedule, recurring bills, EMIs, and known upcoming expenses. Uses a simple time-series projection to forecast daily balances for the next 30–90 days. Alerts if the projected balance is going to fall below a configurable threshold (default: 1 month of expenses).

## Domain: FinTech
Cash flow forecasting helps users avoid overdrafts, insufficient funds, and late payment penalties. It answers the critical question: "Will I have enough money to cover my upcoming expenses?" For Indian users with irregular income (freelancers, gig workers) and multiple EMI obligations, a forward-looking view is essential. The agent must handle staggered salary payments, variable expense timing, and one-off large outflows.

## LangGraph ReAct Pattern
**Reasoning:** The agent analyzes historical cash flow patterns, identifies scheduled income and expense events, and projects forward using a simple linear model with event-based adjustments.

**Action:** It calls projection tools for income and expenses, runs the forecast model, stress-tests scenarios, and generates alerts for low-balance events.

## Input (from SharedState)
- `transactions`: historical transactions (minimum 3 months)
- `category_summaries`: monthly spend averages
- `user_id`: for fetching user profile (income schedule, threshold settings)
- `subscriptions`: from Subscription Agent for known recurring outflows

## Output (writes to SharedState)
- `balance_forecast`: array of `{date, projected_balance, min, max}` for next 90 days
- `low_balance_alerts`: list of dates where balance drops below threshold
- `forecast_summary`: narrative summary (e.g., "You may run low on funds around March 20")
- `stress_test_results`: impact of ±20% income/expense scenarios

## Internal Tools Used

| Tool | Description |
|---|---|
| `forecast_balance(start_balance, income_events, expense_events, days)` | Runs daily projection with event-driven adjustments; returns series |
| `project_income(transactions, user_profile)` | Extracts income schedule (salary dates, freelance cadence) from history |
| `project_expenses(transactions, subscriptions, upcoming)` | Builds expense calendar from recurring bills, EMIs, and known upcoming charges |
| `stress_test_scenario(forecast, income_shock_pct, expense_shock_pct)` | Re-runs forecast with modified parameters; returns worst-case projections |

## Agent Logic Flow

```
1. Load historical transactions, subscriptions, and user profile from SharedState / DB
2. Call project_income():
   a. Identify salary credit patterns (date range, amount)
   b. Identify freelance / irregular income patterns
   c. Build income event schedule for next 90 days
3. Call project_expenses():
   a. Gather recurring expenses from subscriptions
   b. Gather EMI schedules from transaction history
   c. Add average variable spend per category (food, transport, etc.)
   d. Build expense event schedule for next 90 days
4. Get current balance from latest statement or DB
5. Call forecast_balance() with start balance, income events, expense events
6. Scan projected balances for any day where balance < threshold
   → Create low_balance_alerts with dates and projected shortfall
7. Call stress_test_scenario() for:
   a. Income -20% (job loss / pay cut scenario)
   b. Expense +20% (emergency expense scenario)
   c. Combined worst case
8. Generate forecast_summary in natural language
9. Update SharedState with all forecast data
10. Return control to Orchestrator
```

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| No regular income pattern (freelancer) | Use 3-month average; widen confidence interval; flag as "estimated" |
| Upcoming large known expense (tax payment, vacation) | Include if user has marked it; otherwise flag as "unexpected" risk |
| Multiple bank accounts | If linked, aggregate all balances and cross-account transfers |
| Delayed salary credit | Model salary with ±3 day buffer window |
| Minimum balance requirement | Adjust effective threshold to account for bank's minimum balance rule |
| Holiday / weekend pushing expense dates | Shift to next business day if detected |
| Negative starting balance | Flag as "already overdrawn"; forecast from actual position |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Cash flow forecast for user u_123
Current balance: ₹34,500
Threshold: ₹15,000 (1 month expenses)
Next 90 days
```

**Agent Reasoning:**
```
Income: Salary ₹85,000 on 1st of each month, Freelance ~₹12,000 mid-month
Expenses: EMI ₹18,000 on 5th, Rent ₹15,000 on 7th, Subscriptions ₹4,400 spread across month
Variable spend: ~₹1,600/day avg (food, transport, shopping)
March 20-25: Balance dips to ₹8,200 — below ₹15,000 threshold
Worst case (income -20%): long negative from March 18
```

**Action Taken:**
```
project_income(transactions, u_123) → salary 1st, freelance ~15th
project_expenses(transactions, subscriptions, []) → EMI 5th, rent 7th, variable ~₹1,600/day
forecast_balance(34500, income_events, expense_events, 90)
→ March 20: projected ₹8,200 → ALERT below threshold
stress_test_scenario(forecast, income_shock=-0.2, expense_shock=0)
→ worst case: negative from March 18, min -₹6,300 on March 22
forecast_summary = "Your balance may drop to ₹8,200 around March 20, below your ₹15,000 threshold. In a 20% income loss scenario, you could be overdrawn by March 18."
```

## Verification
- `balance_forecast` array covers exactly 90 entries (one per day)
- `low_balance_alerts` only includes dates where projected balance < threshold
- Start of forecast matches the current balance from DB
- Stress test results are strictly worse (or equal) to the base forecast
