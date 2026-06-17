# Agent 9: Financial Advisor Agent

## Purpose
Generates personalized, actionable financial advice tailored to the user's specific situation. Goes beyond generic observations like "you spent ₹10,000 on food" to deliver concrete, quantified recommendations like "reducing restaurant visits by 2/week could save ₹18,000/year." Considers health score gaps, spending trends, financial goals, and what-if scenarios.

## Domain: FinTech
The advisor is the "intelligence layer" that synthesizes output from all other agents into a coherent, prioritized action plan. In the Indian context, advice must be culturally relevant: PPF vs. mutual funds, tax-saving under Section 80C, wedding savings, parents' medical insurance, and real estate vs. equity questions. The agent must be conservative — it should never recommend specific stocks, only broad asset allocation advice.

## LangGraph ReAct Pattern
**Reasoning:** The agent reviews the user's complete financial picture — health score gaps, budget utilization, anomaly flags, subscription waste, cash flow risk — and identifies the highest-impact improvements.

**Action:** It calls the advice generation tool, prioritizes recommendations by financial impact, calculates quantified savings potential for each, and formats the output for the user.

## Input (from SharedState)
- `health_score` and `score_breakdown` from Health Score Agent
- `utilization_report` and `rebalance_recommendations` from Budget Agent
- `anomaly_flags` from Anomaly Detection Agent
- `cancellation_recommendations` from Subscription Agent
- `low_balance_alerts` and `forecast_summary` from Cash Flow Agent
- `user_id`: for fetching user's financial goals from profile

## Output (writes to SharedState)
- `advice_items`: list of `{id, type, priority, title, description, savings_potential, action_url}`
- `advice_summary`: top 3 things the user should do this month

## Internal Tools Used

| Tool | Description |
|---|---|
| `generate_advice(health_score, budgets, anomalies, subscriptions, cashflow, goals)` | Synthesizes all agent outputs into actionable advice items |
| `prioritize_recommendations(advice_items, user_goals)` | Sorts by impact, urgency, and alignment with user's stated goals |
| `calculate_savings_potential(category, frequency, reduction)` | Computes annual savings for a behavioral change (e.g., reduce X by Y) |

## Advice Categories

| Category | Description | Example |
|---|---|---|
| Savings Opportunity | Reduce discretionary spend | "Cut 2 Swiggy orders/week → save ₹18,000/yr" |
| Subscription Waste | Cancel unused subscriptions | "Cancel unused Spotify → save ₹1,428/yr" |
| Budget Rebalance | Shift allocation between categories | "Move ₹3,000 from Dining to Savings to hit 20% target" |
| Debt Management | Reduce high-interest debt burden | "EMI at 38% of income; target <30% to improve score by 12 pts" |
| Emergency Fund | Build rainy-day reserves | "Only 0.6 months covered; target 6 months → save ₹3,600/mo" |
| Investment Gap | Increase long-term investing | "Only 38% of savings invested; target >70%" |
| Cash Flow Risk | Prevent future shortfall | "Balance may dip below threshold Mar 20; delay discretionary spends" |
| Anomaly Alert | Review potentially fraudulent tx | "₹15,000 CryptoXchange at 2 AM flagged; verify or dispute" |
| Goal Progress | Track toward user-defined goals | "Wedding fund at 40% of ₹5L target; on track for Dec 2026" |

## Agent Logic Flow

```
1. Load all agent outputs from SharedState
2. Load user's financial goals from DB (if any)
3. For each area of opportunity, call generate_advice():
   a. Health score gaps → identify sub-score < 60 → generate improvement advice
   b. Budget at_risk/exceeded → generate rebalancing advice with quantified savings
   c. Unused subscriptions → include cancel recommendations
   d. Low balance alerts → generate cash flow risk advice
   e. Anomaly flags → include review recommendations
   f. Goals → measure progress and suggest acceleration
4. For behavioral advice (e.g., reduce dining out):
   a. Call calculate_savings_potential() to quantify
   b. Attach specific, achievable reduction targets
5. Call prioritize_recommendations() to sort by:
   a. Urgency (cash flow risk, fraud → high)
   b. Financial impact (savings potential → high)
   c. Goal alignment (matches user's stated priorities)
6. Select top 3 for advice_summary
7. Update SharedState with full advice list and summary
8. Return control to Orchestrator
```

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| User has no goals set | Default to general financial health improvement; prompt to set goals |
| Conflicting recommendations (e.g., save more vs. spend less on wants) | Balance advice across categories; prioritize highest impact |
| User already scores 90+ | Generate "maintenance" advice: tax optimization, portfolio rebalancing |
| Very low income user | Avoid "invest more" advice; focus on expense optimization and emergency fund |
| User has no subscriptions | Skip subscription advice category entirely |
| Already cancelled a recommended subscription | Check against recent cancellations before recommending |
| Advice exceeds user's risk tolerance | Tag as "aggressive" / "moderate" / "conservative" based on user profile |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Generate advice for user u_123
Health: 52/100 (drag: emergency fund, savings rate, investment)
Budget: Needs exceeded 113%, Wants at 87%, Savings at 86%
Subscriptions: Spotify unused, ₹1,428/yr savings
Cash flow: Low balance alert Mar 20
Goals: Wedding fund ₹5L by Dec 2026 (40% achieved)
```

**Agent Reasoning:**
```
Top priority: Cash flow risk (urgent — March 20) → delay non-essential spend
Second: Emergency fund (only 0.6mo, biggest score drag) → build to 3mo target
Third: Spotify cancellation (quick win, ₹1,428/yr)
Then: Budget rebalance from Needs, increase savings for wedding goal
```

**Action Taken:**
```
generate_advice(52, budgets, anomalies, subscriptions, cashflow, wedding_goal)
prioritize_recommendations(advice_items, ["wedding_fund"])
→ 1. "Cash flow alert: Postpone ₹8,000 in discretionary spends until after Mar 25 to avoid ₹8,200 low point"
→ 2. "Emergency fund: Build from 0.6mo to 3mo coverage → 82% score improvement potential on emergency metric"
→ 3. "Cancel Spotify: No usage in 4 months → save ₹1,428/yr"
→ 4. "Wedding goal: Increase monthly savings from ₹13,000 to ₹16,000 → hit ₹5L by Oct 2026 instead of Dec"
```

## Verification
- Every `advice_item` has a non-empty `title`, `description`, and `priority` (high / medium / low)
- `savings_potential` is a quantified number (₹ amount) where applicable, null otherwise
- Advice does not contain specific stock/fund recommendations
- Top 3 in `advice_summary` match the highest priority items
