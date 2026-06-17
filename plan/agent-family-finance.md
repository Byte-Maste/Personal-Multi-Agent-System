# Agent 15: Family Finance Agent

## Purpose
Aggregates financial data across family members (parents, spouse, children) to provide a consolidated view of household finances. Combines income, expenses, budgets, and goals across members. Generates a combined financial health score for the family unit. Tracks per-member contributions to shared goals and identifies gaps or imbalances in the household financial picture.

## Domain: FinTech
Indian household finances are typically interdependent — multiple earning members, shared expenses (rent, groceries, utilities, school fees, insurance), and joint goals (children's education, family vacation, home purchase). A family finance view helps identify:
- Combined household DTI (often understated when viewed per-member)
- Which member is carrying the household's debt burden
- Shared vs. individual expense categorization
- Per-member savings rate disparity
- Joint goal progress transparency

The agent respects privacy — members can opt to share only aggregated data rather than full transaction details. The Indian joint family structure (parents living with married children) is explicitly supported with configurable member roles.

## LangGraph ReAct Pattern
**Reasoning:** The agent evaluates which family members have linked accounts, determines the sharing permissions for each member's data, and then computes the combined aggregation while respecting privacy boundaries.

**Action:** It fetches per-member financial summaries (within sharing permissions), merges income/expenses/goals, computes household-level metrics, and tracks goal contributions per member.

## Input (from SharedState)
- `user_id`: primary user (head of family group)
- `family_members`: list of `{member_id, role, relationship, sharing_level}`
- `income`: primary user's income
- `transactions`: primary user's transactions
- `goals`: primary user's goals
- Shared data from linked family member accounts (per sharing permissions)

## Output (writes to SharedState)
- `combined_summary`: dict of `{total_income, total_expenses, total_savings, savings_rate, dti}`
- `family_health_score`: composite health score for the entire family unit
- `per_member_contributions`: list of `{member_id, name, role, income_share, expense_share, goal_contribution}`
- `shared_goals`: list of goals with per-member progress tracking
- `household_imbalances`: list of flags (e.g., "One member bears 80% of household debt")

## Internal Tools Used

| Tool | Description |
|---|---|
| `get_family_members(user_id)` | Returns list of linked family members and their sharing permissions |
| `fetch_member_summary(member_id, sharing_level)` | Retrieves aggregated financial data for a member within permission boundaries |
| `aggregate_finances(member_summaries)` | Merges income, expenses, debts, and assets across all members |
| `compute_family_score(aggregated_data)` | Runs health score algorithm on combined household data |
| `track_goal_contributions(goal_id, member_contributions)` | Maps per-member contributions to shared goals and computes share % |
| `detect_imbalances(per_member_data)` | Identifies disproportionate burdens or disparities exceeding configurable thresholds |

## Sharing Permission Levels

| Level | Description | Data Visible |
|---|---|---|
| `full` | Complete financial transparency | All transactions, accounts, investments, debts |
| `summary` | Aggregated monthly totals | Total income, total expenses, savings rate, DTI |
| `goals_only` | Only shared goal progress | Goal name, target, progress %, contribution made |
| `none` | Not linked (default) | No data shared |

## Agent Logic Flow

```
1. Load primary user's financial data and family_members list from SharedState
2. Call get_family_members(user_id) to get all linked members and permissions
3. For each family member (including primary user):
   a. Call fetch_member_summary(member_id, sharing_level)
   b. If sharing_level = "full" → detailed data
   c. If sharing_level = "summary" → aggregated totals only
   d. If sharing_level = "goals_only" → just shared goal data
   e. Store in member_summaries array
4. Call aggregate_finances(member_summaries):
   a. Sum all incomes → total_household_income
   b. Sum all expenses → total_household_expenses
   c. Sum all debts → total_household_debt
   d. Sum all savings → total_household_savings
   e. Combined DTI = total_debt_emis / total_income
   f. Combined savings_rate = total_savings / total_income
   g. Normalize shared expenses to avoid double-counting
5. Call compute_family_score(aggregated_data):
   a. Run same health score algorithm as Health Score agent
   b. But using household-level metrics instead of individual
   c. Returns family_health_score with breakdown
6. For each shared goal:
   a. Sum contributions from all members
   b. Compute per_member share_percentage
   c. Add to shared_goals with member breakdown
7. Call detect_imbalances(per_member_data):
   a. Check if any member contributes > 70% of income
   b. Check if any member carries > 60% of debt
   c. Check if savings rate disparity > 2× between members
   d. Add flags for each imbalance detected
8. Compute per_member_contributions:
   a. Income share % = member_income / total_income
   b. Expense share % = member_expenses / total_expenses
   c. Goal contribution = member_contribution / total_goal_target
9. Update SharedState with combined_summary, family_health_score,
   per_member_contributions, shared_goals, and household_imbalances
10. Return control to Orchestrator
```

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| Only one member in family (no linked accounts) | Treat as individual; return single-member aggregation |
| Member unlinks account mid-cycle | Exclude from aggregation; flag "member data unavailable" |
| Double-counting shared expenses (rent paid by one) | Normalize: only count shared expenses once, attribute to paying member |
| Children with minor accounts (no income) | Include expenses only; flag as "dependent" |
| Family member in different currency zone | Convert all to INR at average monthly rate; flag conversion applied |
| Partial family data (some members not shared) | Aggregate only available data; note "X of Y members included" |
| Member has negative savings (spending > income) | Include in aggregation; family savings rate may be lower |
| Divorced/separated members with split expenses | Support "partial contribution" field for shared expenses |
| New member added mid-month | Pro-rate contributions from join date |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Family finance aggregation for user u_123 (primary)
Family members: spouse (summary), parent (goals_only)
Primary: ₹85,000/mo income, ₹72,000/mo expenses, DTI 21%
Spouse: ₹45,000/mo income, ₹38,000/mo expenses, DTI 0%
Parent: No income, ₹15,000/mo pension, ₹12,000/mo expenses
Shared goal: "Children education fund" ₹20L target, ₹4.2L saved
```

**Agent Reasoning:**
```
Three members: primary (self), spouse (summary), parent (goals_only)
Total income: ₹85,000 + ₹45,000 + ₹15,000 = ₹1,45,000
Total expenses: ₹72,000 + ₹38,000 + ₹12,000 = ₹1,22,000
Combined savings: ₹23,000/mo, savings rate = 15.9%
Combined DTI: primary EMIs ₹18,000 → DTI = 18,000 / 1,45,000 = 12.4%
Family health score: savings rate drags it down vs individual
Shared goal: ₹20L education fund, ₹4.2L saved (21%)
Contributions: primary ₹3.0L, spouse ₹1.2L → primary 71%, spouse 29%
Imbalance: primary contributes 58.6% of income but 71% of goal → flagged
```

**Action Taken:**
```
get_family_members(u_123) → [{spouse, summary}, {parent, goals_only}]
fetch_member_summary(spouse, "summary") → income: 45000, expenses: 38000, debts: none
fetch_member_summary(parent, "goals_only") → no income data, goal: education fund
aggregate_finances([primary, spouse, parent])
→ {income: 145000, expenses: 122000, savings: 23000, savings_rate: 15.9%, dti: 12.4%}
compute_family_score({income: 145000, expenses: 122000, savings_rate: 15.9, dti: 12.4})
→ Family health score: 68/100
track_goal_contributions("edu_fund", {primary: 300000, spouse: 120000})
→ primary: 71%, spouse: 29%
detect_imbalances({primary, spouse, parent})
→ "Primary contributes 59% of income but 71% of goal — moderate imbalance"
→ "Parent has no income but expenses are covered — dependent flag"
```

## Verification
- `total_income` equals sum of all member incomes (within sharing permissions)
- `total_expenses` does not double-count shared expenses
- `family_health_score` is 0-100 with breakdown
- `per_member_contributions` income_shares sum to 100%
- No member data is accessed beyond their `sharing_level` permission
- `household_imbalances` flags are based on configurable thresholds (default: 70% income, 60% debt, 2× savings disparity)
- Missing members are listed in output with "data not available" note
