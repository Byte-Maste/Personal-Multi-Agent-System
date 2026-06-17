# Agent 12: Life Event Simulator Agent

## Purpose
Simulates the financial impact of major life decisions before the user commits to them. Answers "what-if" questions like "What if I buy a ₹12L car?" or "What if I switch to a freelance career?" Computes EMI impact, cash flow impact, savings impact, and debt ratio change. Returns a structured scenario report with risk flags.

## Domain: FinTech
Major life decisions — vehicle purchase, home buying, job change, marriage, higher education, starting a business — have profound financial consequences. Indian users often underestimate the full cost of ownership (insurance, maintenance, fuel for a car; stamp duty, registration, furnishing for a home). The simulator must model real-world Indian costs: typical auto loan rates (9-11%), home loan rates (8.5-10%), processing fees (0.5-2%), GST on insurance, and inflation on recurring costs. The output must be clear and actionable, not just numbers.

## LangGraph ReAct Pattern
**Reasoning:** The agent parses the user's scenario description, maps it to a structured event with financial parameters, loads the user's current financial state, and computes the projected impact across all key metrics.

**Action:** It calls the simulation engine with event parameters, generates a before/after comparison report, calculates risk flags, and returns the structured result.

## Input (from SharedState)
- `user_id`: for user's current financial baseline
- `income`: monthly income and income sources
- `transactions`: recent transaction history
- `expenses`: monthly expense breakdown
- `debts`: existing loan/EMI obligations
- `emergency_fund`: current emergency fund status
- `savings_rate`: current savings rate
- `goals`: active goals for impact assessment

## Output (writes to SharedState)
- `scenario_result`: structured scenario report with before/after comparison
- `impact_metrics`: dict of `{metric, before, after, delta, direction}`
- `risk_flags`: list of `{severity, message, metric_affected}` (e.g., "HIGH: DTI exceeds 50%")
- `cashflow_projection`: 12-month projected cash flow under the scenario

## Internal Tools Used

| Tool | Description |
|---|---|
| `parse_scenario(user_input)` | Converts natural language scenario (e.g., "buy car for 12L") into structured event_params |
| `simulate_event(event_params, user_baseline)` | Computes full financial impact: EMI, cash flow, DTI, savings, expense delta |
| `calculate_emi(principal, rate, tenure)` | Standard EMI formula: `P × r × (1+r)^n / ((1+r)^n - 1)` |
| `compute_dti(existing_debts, new_emi, income)` | Debt-to-Income = (sum of EMIs + new EMI) / monthly income |
| `assess_risk(impact_metrics, user_profile)` | Flags metrics exceeding thresholds; returns risk_flags with severity |
| `generate_report(scenario_name, before, after, risks)` | Assembles structured markdown/JSON report |

## Agent Logic Flow

```
1. Receive scenario description from user via Orchestrator
2. Call parse_scenario() to extract structured event_params:
   a. Event type: vehicle_purchase, home_purchase, job_change, education, marriage, business, custom
   b. Parameters depend on type:
      - vehicle_purchase: {cost, down_payment, loan_rate (default 10%), tenure (default 5yr)}
      - home_purchase: {cost, down_payment, loan_rate (default 9%), tenure (default 20yr), stamp_duty_pct}
      - job_change: {new_salary, joining_bonus, notice_period_pay, gap_months}
      - education: {total_fees, course_duration, loan_required, loan_rate}
3. Load user's current financial baseline from SharedState / DB
4. Compute baseline metrics:
   a. Current EMI total
   b. Current DTI ratio
   c. Current monthly savings
   d. Current savings rate
   e. Emergency fund coverage (months)
5. Call simulate_event(event_params, baseline):
   a. If loan-based event: calculate_emi(principal, rate, tenure)
   b. Add new EMI to existing debt obligations
   c. Compute new monthly expense total (EMI + ongoing costs + one-time costs amortized)
   d. Compute new monthly savings = income - new expenses
   e. Compute new DTI = total_emi / income
   f. Compute new savings rate
   g. Compute emergency fund impact (if down payment reduces it)
6. Call assess_risk() on the impact_metrics:
   a. If DTI > 50% → HIGH risk flag
   b. If savings rate drops below 10% → MEDIUM risk flag
   c. If emergency fund drops below 3 months → HIGH risk flag
   d. If negative savings → CRITICAL risk flag
   e. If goal funding disrupted → MEDIUM risk flag
7. Call generate_report() to assemble the scenario report
8. Compute 12-month cashflow_projection under scenario
9. Update SharedState with scenario_result, impact_metrics, risk_flags, cashflow_projection
10. Return control to Orchestrator
```

## Event Type Parameters

| Event Type | Required Params | Optional Params | Default Assumptions |
|---|---|---|---|
| `vehicle_purchase` | cost, down_payment | loan_rate, tenure, insurance_year, maintenance_pct | 10% rate, 5yr tenure, 3% insurance, 5% maintenance |
| `home_purchase` | cost, down_payment | loan_rate, tenure, stamp_duty_pct, furnishing_cost | 9% rate, 20yr tenure, 7% stamp duty, 5% furnishing |
| `job_change` | new_salary | gap_months, joining_bonus, relocation_cost | 1 month gap, 0 bonus, 0 relocation |
| `education` | total_fees, duration | loan_amt, loan_rate, living_expenses | 12% education loan rate, ₹15k/mo living |
| `marriage` | estimated_cost | own_share_pct, loan_required | 50% own share, no loan |
| `business` | initial_investment | monthly_burn, breakeven_month, projected_revenue | 6mo burn, 18mo breakeven |
| `custom` | expense_delta, income_delta, one_time_cost | — | User specifies all params |

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| User has no existing debt (DTI = 0) | Treat as clean slate; show full headroom |
| Scenario requires down payment larger than savings | Flag "insufficient funds for down payment"; suggest lower cost or higher loan |
| Multiple scenarios simulated in one session | Maintain baseline; each scenario branches independently |
| Income decrease scenario (job change with pay cut) | Flag savings rate impact; check if essential expenses covered |
| Loan tenure longer than user's working years | Flag tenure risk for users >50 years old |
| Scenario involves foreign currency | Convert at current exchange rate; flag currency risk |
| User already has DTI > 40% | Pre-flag that new debt may push over 50% threshold |
| One-time costs hidden (registration, GST, moving) | Auto-add standard ancillary costs per event type |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Simulate scenario: "What if I buy a ₹12L car?"
User u_123: Income ₹85,000/mo, Expenses ₹72,000/mo, Savings ₹13,000/mo
Existing EMIs: ₹18,000/mo, Emergency fund: ₹4,50,000
Down payment: ₹2,40,000 (20%), Loan: ₹9,60,000
```

**Agent Reasoning:**
```
Event type: vehicle_purchase, cost ₹12,00,000
Down payment ₹2,40,000 from emergency fund → new EF = ₹2,10,000
Loan ₹9,60,000 @ 10% for 5 years → EMI ≈ ₹20,392
Total EMIs: ₹18,000 + ₹20,392 = ₹38,392
New DTI: 38,392 / 85,000 = 45.2% → MEDIUM risk (over 40%)
Monthly expenses increase by: EMI ₹20,392 + insurance ₹3,000 + maintenance ₹5,000 = ₹28,392
New monthly surplus: ₹85,000 - ₹72,000 - ₹28,392 = -₹15,392 → NEGATIVE savings
Savings rate drops from 15.3% to -18.1% → CRITICAL
Emergency fund drops from 6.25mo to 2.92mo → HIGH risk (below 3mo)
```

**Action Taken:**
```
parse_scenario("buy 12L car") → {type: vehicle_purchase, cost: 1200000, down_payment: 240000, rate: 0.10, tenure: 5}
simulate_event({...}, baseline) → EMI ₹20,392, new_expenses ₹1,00,392, new_savings -₹15,392
compute_dti(18000, 20392, 85000) → 45.2%
assess_risk({dti: 45.2, savings_rate: -18.1, ef_months: 2.92})
→ CRITICAL: "Negative savings — expenses exceed income by ₹15,392/mo"
→ HIGH: "Emergency fund drops to 2.92 months (below 3-month threshold)"
→ MEDIUM: "DTI at 45.2% — above 40%警戒线"
generate_report("Buy ₹12L Car", before, after, risks)
→ Returns structured report with all metrics and 3 risk flags
```

## Verification
- `impact_metrics` contains all key metrics with before, after, delta values
- Every `risk_flag` has a severity (LOW / MEDIUM / HIGH / CRITICAL)
- EMI calculation matches standard formula within 0.1% tolerance
- Scenario result does not modify user's actual financial data (read-only simulation)
- `cashflow_projection` covers 12 consecutive months from simulation date
- Ancillary costs (insurance, stamp duty, maintenance) are included in expense delta
