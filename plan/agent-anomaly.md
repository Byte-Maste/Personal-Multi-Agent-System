# Agent 6: Anomaly Detection Agent

## Purpose
Flags unusual transactions that deviate from the user's historical patterns: sudden large spends, duplicate charges, out-of-pattern merchant visits, unusual timing (e.g., midnight transactions), and transactions at unfamiliar locations. Acts as the financial fraud and error detection layer of the system.

## Domain: FinTech
Anomaly detection is critical for both security (catching fraud early) and user awareness (catching mistakes like double charges or forgotten subscriptions). In the Indian payments landscape — UPI, credit card, wallet, NEFT — anomalies can appear as unexpected large UPI transactions, duplicate merchant charges, or transactions during odd hours. The agent must be sensitive enough to catch real issues but calibrated to avoid alert fatigue.

## LangGraph ReAct Pattern
**Reasoning:** The agent compares each new transaction against the user's historical transaction profile — typical amounts, merchants, timing, frequency, and merchant categories. It scores each transaction for anomalousness.

**Action:** It calls detection tools for specific anomaly types (duplicates, fraud patterns, timing outliers) and flags transactions that exceed the anomaly threshold.

## Input (from SharedState)
- `transactions`: list of newly categorized transactions (merchant, amount, date, category, description)
- `user_id`: for fetching historical patterns
- `historical_profile`: pre-computed user patterns from DB (typical spend ranges, common merchants, typical hours)

## Output (writes to SharedState)
- `anomaly_flags`: list of `{transaction_id, anomaly_type, severity, explanation}`
- `anomaly_summary`: high-level summary of flagged items for notification

## Internal Tools Used

| Tool | Description |
|---|---|
| `detect_fraud_flags(transaction, user_profile)` | Checks for known fraud indicators: amount > 3x typical, new merchant in high-risk category, location mismatch |
| `find_duplicates(transaction, recent_transactions)` | Searches for near-identical transactions (same merchant, same amount, within 48h) |
| `cross_check_patterns(transaction, user_profile)` | Validates merchant visit time, day-of-week, and frequency against historical norms |
| `flag_anomaly(user_id, transaction_id, type, severity, explanation)` | Writes anomaly flag to DB and returns the flag object |

## Agent Logic Flow

```
1. Load new transactions from SharedState and user's historical profile from DB
2. For each transaction:
   a. Call detect_fraud_flags() — check amount spike vs. user's 90th percentile
   b. Call find_duplicates() — match against last 48h of transactions
   c. Call cross_check_patterns() — compare time/day against typical pattern
   d. If any tool returns a match → compute severity (low / medium / high / critical)
   e. Call flag_anomaly() to persist
3. Aggregate anomaly_flags into anomaly_summary
4. Update SharedState with flags and summary
5. Return control to Orchestrator
```

## Anomaly Types and Thresholds

| Anomaly Type | Detection Logic | Severity |
|---|---|---|
| Amount Spike | Amount > 3× the user's 90th percentile transaction amount | High |
| Duplicate Charge | Same merchant + same amount within 48h | Medium |
| Off-Hours Transaction | Transaction between 12 AM and 5 AM and user has no history of such | Low |
| New Merchant High-Value | >₹10,000 at a merchant never seen before | High |
| Velocity Spike | >5 transactions at same merchant in 24h | Medium |
| Location Mismatch | Merchant category inconsistent with user's geo (if available) | Critical |
| Round-Trip Transfer | Same amount credited and debited within short window | Critical |

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| New user with no history | Skip pattern-based checks; use only global fraud rules |
| Planned large purchase (e.g., laptop) | User can pre-mark expected transactions as "planned" to suppress alerts |
| Diary / scheduled payments | Learn as recurring after 2 occurrences; suppress anomaly checks |
| Multiple small duplicates (e.g., UPI retries) | Flag first duplicate only; group subsequent as "related" |
| Festival / sale season spikes | Adjust thresholds 2× during known sale periods (Diwali, Amazon Great Indian Festival) |
| International transaction | Always flag as medium severity if user has no travel history |
| Cash withdrawal anomaly | Only flag if amount exceeds 2× user's typical ATM withdrawal pattern |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Check 85 new transactions for anomalies — user u_123
Historical profile: avg tx ₹1,200, 90th percentile ₹4,500
Typical hours: 8 AM – 11 PM
Common merchants: Swiggy, Uber, Amazon, BigBasket
```

**Agent Reasoning:**
```
Transaction #42: PayTM ₹15,000 at 2:14 AM to merchant "CryptoXchange"
- Amount 3.3× above 90th percentile → amount spike (high)
- Time 2:14 AM → off-hours (low)
- Merchant never seen before + crypto category → new merchant high-value (high)
- Combined severity → critical
Transaction #18: Swiggy ₹480 on March 5, another Swiggy ₹480 on March 6 → duplicate (medium)
```

**Action Taken:**
```
detect_fraud_flags(tx_42, profile) → amount_spike: high, new_merchant_high_value: high
cross_check_patterns(tx_42, profile) → off_hours: low
flag_anomaly(u_123, tx_42, "combined_fraud", "critical", 
  "₹15,000 CryptoXchange at 2 AM — amount 3.3× typical, new merchant, off-hours")
find_duplicates(tx_18, last_48h) → match found
flag_anomaly(u_123, tx_18, "duplicate", "medium", "Duplicate Swiggy charge ₹480 on Mar 6")
```

## Verification
- Every anomaly_flag has: transaction_id, anomaly_type, severity, and explanation
- No more than 1 "critical" flag per transaction (merged if multiple triggers)
- Duplicate detection does not false-positive on recurring subscriptions
- Severity level correctly reflects the highest triggering indicator
