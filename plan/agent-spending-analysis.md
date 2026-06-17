# Agent 3: Spending Pattern Analysis Agent

## Purpose
Analyze categorized transactions over time to detect spending trends, patterns, and behavioral insights. This is where raw numbers become intelligence.

## Domain: FinTech
A monthly expense list is just data. The insight comes from comparing January vs March, noticing food spending increased 18% month-over-month, or spotting that fuel costs doubled. This agent identifies those signals.

## LangGraph ReAct Pattern
**Reasoning:** The agent examines monthly aggregations, computes period-over-period changes, and identifies statistically significant deviations.

**Action:** Fetches aggregated data from DB, runs trend computations, and writes structured findings to SharedState.

## Input (from SharedState)
- `user_id`
- `transactions` (categorized)
- Historical data from DB

## Output (writes to SharedState)
- `monthly_summaries`: `{ "2026-01": {"Food": 5000, "Travel": 3000}, "2026-02": {...} }`
- `trends`: `[{ category: "Food", direction: "up", pct_change: 18, message: "Food expenses increasing 18% monthly" }]`

## Internal Tools Used
| Tool | Description |
|---|---|
| `aggregate_monthly(user_id, months)` | Group by category and month |
| `compute_trend(monthly_data)` | Linear regression slope, percentage change |
| `detect_seasonality(data)` | Identifies cyclical patterns (holiday spikes, utility cycles) |
| `compare_to_income(monthly_spend, income)` | What percentage of income goes where |

## Agent Logic Flow

```
1. Fetch last 3-6 months of aggregated spending from DB
2. For each category:
   a. Compute month-over-month change
   b. Compute 3-month rolling average
   c. Flag if change > threshold (e.g., 15%)
3. Compare total spending vs income
4. Identify top-5 spending categories
5. Update SharedState with summaries and trends
6. Return to Orchestrator
```

## Trend Types Detected

| Trend Type | Example | Action |
|---|---|---|
| Consistent increase | Food: 5k→6.5k→8k over 3 months | Flag as rising cost center |
| Seasonal spike | Electricity: 5000 in summer vs 2000 in winter | Mark as expected seasonal |
| One-time outlier | Medical: 50000 in one month | Exclude from base trend |
| Decreasing trend | Eating out: 4000→3000→2000 | Positive signal, note in insights |
| New recurring | New subscription appeared last 3 months | Forward to subscription agent |

## Verification
- Trend calculations match manual arithmetic for test data
- Seasonal patterns correctly identified for utility bills
- Outliers excluded from trend baseline but flagged separately
