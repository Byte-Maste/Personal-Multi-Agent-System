# Agent 13: Financial Twin Agent

## Purpose
Creates a digital replica of the user's financial state that can be used to test "what-if" scenarios in isolation. Supports testing salary increase, job loss, new loan, expense shock, and investment changes against the twin, predicting outcomes over 12 months. Maintains a baseline snapshot and one or more what-if branches for comparison.

## Domain: FinTech
A financial twin is a powerful decision-support concept. Rather than running calculations on live data, the twin is a frozen snapshot that can be mutated and projected forward without risk. This enables side-by-side comparison of multiple scenarios (e.g., "What if I take a 20L home loan vs. 15L?" or "What if I lose my job for 6 months?"). The twin must model income growth (3-5% annual), expense inflation (4-6%), EMI schedules, investment returns (conservative 8-10%), and tax liabilities. Indian-specific considerations include: TDS, advance tax, provident fund contributions, and medical insurance premium escalation.

## LangGraph ReAct Pattern
**Reasoning:** The agent evaluates the request to determine if a new twin should be created, an existing twin should be cloned, or an event should be applied to an existing twin. It then decides the projection path based on the scenario parameters.

**Action:** It creates a deep copy of the user's financial state, applies one or more events to the copy, runs the 12-month Monte Carlo projection, and returns comparison data between baseline and branched twin.

## Input (from SharedState)
- `user_id`: for fetching user's current financial data
- `income`: full income profile (sources, amounts, frequency)
- `expenses`: full expense breakdown by category
- `debts`: list of `{type, principal, rate, emi, remaining_tenure}`
- `assets`: list of `{type, value, liquidity}`
- `investments`: portfolio snapshot (holdings, values, returns)
- `insurance`: policy details (premium, coverage, tenure)
- `goals`: active goals for continuation in twin
- `transactions`: historical transaction data for pattern calibration

## Output (writes to SharedState)
- `twin_id`: unique identifier for the created twin
- `baseline_snapshot`: frozen copy of user's financial state at creation time
- `what_if_branches`: list of `{branch_id, label, events_applied, projection, comparison}`
- `predictions_12mo`: monthly projections for each branch (income, expenses, balance, net_worth)
- `comparison_metrics`: side-by-side comparison of baseline vs. each branch

## Internal Tools Used

| Tool | Description |
|---|---|
| `create_twin(user_id)` | Deep-clones the user's current financial state into a new twin record |
| `apply_event(twin_id, event_params)` | Mutates the twin by applying a financial event (salary change, new loan, expense shock, etc.) |
| `predict_12mo(twin_id)` | Runs a 12-month forward projection on the twin: month-by-month income, expenses, balance, net worth |
| `compare_twins(baseline_id, branch_id)` | Produces side-by-side metric comparison between two twins |

## Agent Logic Flow

```
1. Receive request: create twin / apply event / predict / compare
2. If request is "create twin":
   a. Call create_twin(user_id) → deep-clone all financial data
   b. Store baseline_snapshot with timestamp
   c. Return twin_id
3. If request is "apply event":
   a. Load existing twin by twin_id (or create baseline first if none)
   b. Parse event_params: {event_type, parameters}
   c. Supported event types:
      - salary_increase: {new_amount, effective_month}
      - job_loss: {severance_months, gap_months, effective_month}
      - new_loan: {type, principal, rate, tenure, effective_month}
      - expense_shock: {category, delta, duration_months}
      - investment_change: {new_monthly_investment, expected_return}
      - lumpsum_credit: {amount, source, month}
      - insurance_add: {premium, coverage, type}
   d. Deep-clone the twin → create what_if_branch with label
   e. Call apply_event(branch_id, event_params)
   f. Store the mutated branch
4. If request is "predict 12mo":
   a. For the specified twin/branch, call predict_12mo(twin_id):
      - Month 0: start with current balance
      - For each month 1-12:
        i.   Add income (with growth factor if employed)
        ii.  Subtract expenses (with inflation factor)
        iii. Apply EMI deductions for active loans
        iv.  Apply investment returns (annualized return / 12)
        v.   Track net worth monthly
        vi.  If job_loss event active: skip income after gap_months
        vii. If expense_shock active: add delta to expenses
      - Return monthly array of {month, income, expenses, balance, net_worth, emi_total}
5. If request is "compare":
   a. Call compare_twins(baseline_id, branch_id)
   b. Compute deltas for each metric at each month
   c. Return comparison_metrics with before/after/delta
6. Update SharedState with twin data, branches, predictions, and comparisons
7. Return control to Orchestrator
```

## Projection Assumptions

| Parameter | Default | Configurable? |
|---|---|---|
| Income growth rate | 5% annually | Yes |
| Expense inflation | 5% annually | Yes |
| Investment return (debt) | 7% annually | Yes |
| Investment return (equity) | 10% annually | Yes |
| Emergency fund depletion rate | 100% of expenses | Yes |
| Medical insurance premium escalation | 10% annually | Yes |
| Rent escalation | 8% annually | Yes |
| Tax rate (effective) | User-specific slab | No (from profile) |

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| Twin creation fails due to insufficient data | Return error with list of missing fields required for twin |
| Applying incompatible event (e.g., two salary changes) | Merge: apply highest salary or use latest effective_month |
| Predict detects negative balance for 3+ months | Flag "depletion risk" with month of zero balance |
| Multiple what-if branches (5+) | Warn user; recommend pruning old branches |
| Event effective_month in the past | Treat as already in effect; recalculate from that month forward |
| User deletes a financial account after twin creation | Twin is snapshot — unaffected; flag "stale" on comparison |
| Investment return variance | Use conservative estimate; note "returns not guaranteed" disclaimer |
| Job loss with insufficient emergency fund | Flag "emergency fund exhaustion" in projection at the month it runs out |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Create financial twin for u_123 and test: "What if I lose my job for 6 months?"
Current state: ₹85,000/mo income, ₹72,000/mo expenses, ₹4,50,000 emergency fund
EMIs: ₹18,000/mo (24 months remaining)
```

**Agent Reasoning:**
```
Creating baseline twin... done. twin_id = t_abc123.
Apply event: job_loss with 0 severance, 6 month gap, effective next month.
Clone to branch "job_loss_6mo".
Predict 12 months for both baseline and branch.
Baseline: balance grows from 4.5L to 7.8L over 12 months.
Branch: months 1-6 have expenses (72k) + EMIs (18k) = 90k/mo from EF.
After 5 months: EF = 4.5L - (90k × 5) = 0. EF exhausted at month 5.
Months 5-6: negative balance! Critical risk.
Comparison: net worth at month 12: baseline ₹7.8L vs branch -₹1.2L.
```

**Action Taken:**
```
create_twin(u_123) → twin_id "t_abc123", baseline snapshot stored
apply_event("t_abc123", {type: "job_loss", severance: 0, gap: 6, effective: "2025-07"})
→ branch "b_jobloss" created with job_loss event applied
predict_12mo("t_abc123") → baseline projection complete
predict_12mo("b_jobloss") → branch projection complete
compare_twins("t_abc123", "b_jobloss")
→ "Baseline net worth: ₹7.8L | Job loss branch: -₹1.2L"
→ "Emergency fund exhausted at month 5 → 1 month of negative cash flow before income resumes"
→ RISK: "Critical — 1 month of negative balance. Consider increasing EF to 9 months."
```

## Verification
- `baseline_snapshot` is a deep copy — mutations to the twin do not affect user's real data
- `predict_12mo` returns exactly 12 monthly entries per twin
- Income and expenses are positive in projection; balance and net worth may be negative
- `comparison_metrics` includes at minimum: balance, net_worth, savings_rate, DTI at months 0, 6, 12
- Each `what_if_branch` has a unique `branch_id` and references its `twin_id`
- "Depletion risk" flag is raised when monthly balance goes negative in projection
