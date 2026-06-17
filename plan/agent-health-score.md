# Agent 5: Financial Health Scoring Agent

## Purpose
Computes a composite financial health score (0-100) based on six key metrics: savings rate, debt-to-income ratio, spending consistency, emergency fund coverage months, budget discipline, and investment allocation. Returns a breakdown of which factors are pulling the score down and what the user can improve.

## Domain: FinTech
A single-number financial health score is a powerful user engagement tool. It gives users an instant, intuitive sense of their financial standing and motivates action. The score must be transparent — users should see exactly how it's calculated and what they need to do to improve it. In the Indian market, factors like high EMIs, low emergency fund adoption, and under-investing in equities are common drags on the score.

## LangGraph ReAct Pattern
**Reasoning:** The agent reviews all available financial data (income, expenses, debts, savings, investments, budget compliance) and determines the score for each sub-metric, then weights them into a composite score.

**Action:** It calls statistical computation tools to calculate ratios and rates, then assembles the final score with explainability data.

## Input (from SharedState)
- `category_summaries`: spending by category
- `income`: monthly income (from profile or income category)
- `transactions`: full transaction list for the period
- `budgets` and `utilization_report` from Budget Agent
- `user_id`: for fetching any stored score history

## Output (writes to SharedState)
- `health_score`: integer 0-100
- `score_breakdown`: dict of `{metric: {score, weight, impact, explanation}}`
- `score_trend`: comparison with previous scores (improved / declined / stable)
- `top_drags`: list of up to 3 factors most negatively impacting the score

## Internal Tools Used

| Tool | Description |
|---|---|
| `calculate_savings_rate(total_income, total_expenses)` | Returns (rate, grade) where rate = (income - expenses) / income |
| `compute_debt_ratio(total_debt_emi, total_income)` | Returns DTI ratio and grade based on standard thresholds |
| `assess_emergency_fund(balance_avg, monthly_expenses)` | Computes months of coverage from average balance / monthly expenses |
| `compute_score(metric_scores)` | Weighted aggregation of all sub-scores into 0-100 composite |

## Scoring Rubric

| Metric | Weight | Calculation | Scoring |
|---|---|---|---|
| Savings Rate | 25% | 1 - (expenses / income) | >30% = 100, 20-30% = 80, 10-20% = 60, 5-10% = 40, <5% = 20, negative = 0 |
| Debt-to-Income | 20% | Total monthly EMI / monthly income | <20% = 100, 20-30% = 80, 30-40% = 60, 40-50% = 40, >50% = 20 |
| Emergency Fund | 20% | Avg balance / monthly expenses | >6 mo = 100, 4-6 mo = 80, 3-4 mo = 60, 1-3 mo = 40, <1 mo = 20, zero = 0 |
| Budget Discipline | 15% | % of budget envelopes on track | 100% on track = 100, 80% = 80, 60% = 60, 40% = 40, <40% = 20 |
| Spending Consistency | 10% | Std dev of monthly spending / mean | <10% = 100, 10-20% = 80, 20-30% = 60, 30-50% = 40, >50% = 20 |
| Investment Allocation | 10% | % of savings deployed to investments | >70% = 100, 50-70% = 80, 30-50% = 60, 10-30% = 40, <10% = 20 |

## Agent Logic Flow

```
1. Load income, expenses, budgets, and transactions from SharedState
2. Compute each sub-metric:
   a. calculate_savings_rate(income, sum(expenses))
   b. compute_debt_ratio(total_emi, income)
   c. assess_emergency_fund(avg_monthly_balance, monthly_expenses)
   d. Budget discipline = % of budget envelopes with status "on_track"
   e. Spending consistency = coefficient of variation across last 6 months
   f. Investment allocation = investment spend / total savings
3. Grade each metric (0-100) using the scoring rubric
4. Call compute_score() with weighted aggregation
5. Identify top 3 drags (metrics with lowest score × weight)
6. Compare with previous score from DB; compute trend
7. Update SharedState with score, breakdown, drags, and trend
8. Return control to Orchestrator
```

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| Insufficient data (<1 month) | Return null score; prompt user to upload more data |
| Zero income reported | Score = 0 with explanation; flag as critical |
| No debt (DTI = 0%) | Score DTI as 100 (healthy) |
| Negative savings rate | Score 0; flag "spending exceeds income" as critical drag |
| First-time user with no history | No trend data; skip comparison |
| Emergency fund inaccuracies (large one-off deposits) | Use 3-month median balance, not raw average |
| Student / unemployed user | Adjust scoring: skip savings rate, weight emergency fund higher |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Compute health score for user u_123
Income: ₹85,000, Expenses: ₹72,000, EMIs: ₹18,000
Avg balance: ₹45,000, Budgets: 3 of 5 on track
Investments: ₹5,000/mo, Savings: ₹13,000/mo
```

**Agent Reasoning:**
```
Savings rate: 15.3% → score 60 (25% weight)
DTI: 21.2% → score 80 (20% weight)
Emergency fund: 0.63 months → score 20 (20% weight)
Budget discipline: 60% → score 60 (15% weight)
Spending consistency: need 6 months data → skipping
Investment allocation: 38.5% → score 60 (10% weight)
Emergency fund is the biggest drag at 20 × 0.20 = 4 pts lost
```

**Action Taken:**
```
calculate_savings_rate(85000, 72000) → 15.3%, grade 60
compute_debt_ratio(18000, 85000) → 21.2%, grade 80
assess_emergency_fund(45000, 72000) → 0.63mo, grade 20
compute_score({savings: 60, dti: 80, emergency: 20, budget: 60, investment: 60})
→ Composite: 52 / 100
top_drags = ["Emergency fund (only 0.63 months)", "Savings rate (15.3%)", "Investment allocation (38.5%)"]
```

## Verification
- Score is always 0-100 inclusive
- Weights in `score_breakdown` sum to 100%
- Missing metrics are excluded and remaining weights re-normalized
- `top_drags` accurately reflects the lowest weighted contributions
