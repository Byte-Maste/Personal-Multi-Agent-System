# Agent 7: Subscription Intelligence Agent

## Purpose
Identifies recurring payments in the user's transaction history (Netflix, Spotify, Amazon Prime, ChatGPT, gym memberships, insurance premiums, SaaS tools). Detects subscriptions that are unused — no correlated usage indicators for 3+ months — and recommends cancellations with potential savings estimates.

## Domain: FinTech
Subscription creep is a major financial leak. The average Indian user has 4–6 active subscriptions (OTT, music, cloud storage, gym, insurance, credit card fees) totaling ₹2,000–₹5,000/month. Many go unused for months. The agent must distinguish between essential subscriptions (insurance, domain renewals) and discretionary ones (entertainment, SaaS), and estimate actual savings from cancellation net of any penalties.

## LangGraph ReAct Pattern
**Reasoning:** The agent scans transactions for recurring patterns (same merchant, same amount, periodic interval), classifies each as a subscription, and then correlates against usage indicators (login history, UPI autopay, merchant-specific transaction patterns).

**Action:** It calls detection tools for recurring payment identification, checks usage indicators, and generates cancellation recommendations with projected savings.

## Input (from SharedState)
- `transactions`: full categorized transaction list (minimum 3 months)
- `user_id`: for fetching any existing subscription tracking data
- `category_summaries`: for total spend context

## Output (writes to SharedState)
- `subscriptions`: list of `{merchant, amount, frequency, category, status}`
- `unused_subscriptions`: list of subscriptions with no usage for 3+ months
- `cancellation_recommendations`: list of `{subscription, savings_per_year, rationale, risk}`
- `total_subscription_spend`: monthly and annual totals

## Internal Tools Used

| Tool | Description |
|---|---|
| `detect_recurring_payments(transactions)` | Clusters transactions by merchant + amount with periodic intervals (monthly, quarterly, yearly) |
| `check_usage_indicators(merchant, user_transactions)` | Searches for engagement signals: login notifications, usage transactions, feature purchases, app store receipts |
| `recommend_cancellation(subscription, usage_data)` | Scores cancellation value: savings minus penalty, weighted by essential vs. discretionary classification |

## Agent Logic Flow

```
1. Load last 12 months of transactions from SharedState (or DB if more needed)
2. Call detect_recurring_payments() to find all recurring patterns:
   a. Group by merchant name
   b. Check for same amount recurring at fixed intervals
   c. Flag as subscription with frequency (monthly / quarterly / yearly)
3. For each detected subscription:
   a. Check if merchant is in "essential" list (insurance, domain, cloud backup, loan)
   b. If essential → mark as "required", skip usage check
   c. If discretionary → call check_usage_indicators()
   d. If no usage in 3+ months → mark as "unused"
4. For each unused subscription:
   a. Call recommend_cancellation() → compute annual savings
   b. Add to cancellation_recommendations
5. Compute total_subscription_spend
6. Update SharedState with subscriptions, unused list, and cancellation recommendations
7. Return control to Orchestrator
```

## Subscription Classification

| Category | Examples | Essential? | Typical Frequency |
|---|---|---|---|
| OTT / Streaming | Netflix, Prime Video, Hotstar, JioCinema, Sony LIV | No | Monthly |
| Music | Spotify, Apple Music, YouTube Music, Gaana | No | Monthly |
| Cloud / SaaS | Google Drive, iCloud, ChatGPT Plus, GitHub Pro | Depends | Monthly / Yearly |
| Fitness | Gym, Cult.fit, Yoga studio | No | Monthly / Quarterly |
| Insurance | Health, Life, Vehicle insurance | Yes | Monthly / Yearly |
| Domain / Hosting | GoDaddy, Hostinger, Namecheap | Yes | Yearly |
| Credit Card Fee | Annual fee on premium cards | Depends | Yearly |
| Education | Coursera, Udemy, Skillshare, Byju's | No | Monthly / Yearly |
| Utility | Internet, Mobile recharge, Electricity | Yes | Monthly |

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| Variable-amount subscriptions (usage-based) | Detect by merchant + frequency; flag amount as "variable" |
| Free trial converting to paid | Compare first charge date to trial start; flag "trial converted" |
| Family plan where one member pays | Detect if amount matches known family plan pricing; note shared |
| Annual vs. monthly subscription (same service) | If both detected, flag as double payment |
| Subscription paused / frozen | Check for gap in payment history >45 days |
| Refund after cancellation | Detect reversal transaction; mark as cancelled |
| Merchant name changes (e.g., "Netflix.com" vs "Netflix IN") | Fuzzy match merchants with same amount interval |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Find subscriptions for user u_123 — 12 months of transactions available
```

**Agent Reasoning:**
```
Scanning for recurring same-amount patterns...
Netflix: ₹649 × 12 months → active
Spotify: ₹119 × 12 months → active
Amazon Prime: ₹1,499 × 1 (yearly) → active
Cult.fit: ₹1,999 × 3 months then stopped → cancelled
ChatGPT Plus: ₹1,650 × 2 months → active but only 2 months, need usage check
Check usage indicators: No login or usage transactions for Spotify in 4 months → unused
```

**Action Taken:**
```
detect_recurring_payments(transactions) → 6 subscriptions found
check_usage_indicators("Spotify", transactions) → no usage indicators in 130 days
recommend_cancellation({merchant: "Spotify", amount: 119, freq: "monthly"})
→ savings: ₹1,428/yr, rationale: "No listening activity detected since Jan 2025"
→ add to cancellation_recommendations
total_subscription_spend = {monthly: ₹4,417, annual: ₹53,004}
```

## Verification
- Every entry in `subscriptions` has a detected frequency (monthly / quarterly / yearly)
- `unused_subscriptions` is a subset of `subscriptions`
- Each cancellation recommendation includes both savings_per_year and rationale
- `total_subscription_spend.monthly` equals sum of recurring monthly amounts (annualized / 12)
