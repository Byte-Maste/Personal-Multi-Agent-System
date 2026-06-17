# Agent 14: Investment Readiness Agent

## Purpose
Assesses whether the user is ready to increase investment risk based on three gate checks: emergency fund ≥ 6 months of expenses, no high-interest debt (interest rate > 12%), and savings rate ≥ 20%. Returns a readiness score (0-100) plus specific blockers that must be resolved first. Does NOT recommend specific investments, sectors, or financial products — stays strictly within regulatory guidelines.

## Domain: FinTech
Increasing investment risk (moving from debt to equity, or from conservative to aggressive allocation) is only appropriate when the user's financial foundation is secure. Regulatory bodies (SEBI, RBI) and financial advisors uniformly recommend: emergency fund first, high-interest debt clearance second, then risk-based investing. In India, common high-interest debt includes credit card rollover (36-48% APR), personal loans (11-24%), and some consumer durables financing (15-30%). The agent must avoid any specific product recommendations to comply with investment advisory regulations. The readiness framework educates rather than advises, empowering users to make informed decisions.

## LangGraph ReAct Pattern
**Reasoning:** The agent evaluates the user's financial situation against three hard gate checks, then computes a readiness score based on how well each gate is satisfied. It identifies the most impactful blocker and provides educational guidance.

**Action:** It calls assessment tools for each gate, compiles results into a readiness score, generates a blocker list with educational explanations, and returns the assessment without any product recommendations.

## Input (from SharedState)
- `user_id`: for user-specific financial data
- `income`: monthly after-tax income
- `expenses`: monthly expense breakdown
- `transactions`: full transaction history (for debt and savings analysis)
- `emergency_fund`: current emergency fund balance or savings balance
- `debts`: list of `{type, principal, interest_rate, monthly_payment}`
- `savings_rate`: current savings rate (could be from Health Score agent)
- `investments`: current investment portfolio (for context only)
- `health_score`: financial health score breakdown

## Output (writes to SharedState)
- `readiness_score`: integer 0-100
- `gate_results`: dict of `{gate_name: {passed, value, threshold, explanation}}`
- `blockers`: list of `{blocker, severity, resolution_guidance}`
- `readiness_level`: one of "not_ready", "nearly_ready", "ready"
- `disclaimer`: regulatory disclaimer text

## Internal Tools Used

| Tool | Description |
|---|---|
| `check_emergency_fund(balance, monthly_expenses)` | Returns months of coverage and pass/fail vs 6-month threshold |
| `check_high_interest_debt(debts, threshold_rate)` | Scans all debts; flags any with rate above threshold (default 12%) |
| `check_savings_rate(savings_rate)` | Evaluates savings rate vs 20% threshold |
| `compute_readiness(emergency, debt, savings)` | Weighted computation: 40% emergency, 35% debt, 25% savings |
| `get_educational_guidance(blocker_type)` | Returns non-advisory educational content about the blocker |

## Readiness Scoring Rubric

| Component | Weight | Threshold | Scoring |
|---|---|---|---|
| Emergency Fund | 40% | ≥ 6 months expenses | ≥ 6mo = 100, 4-5.9 = 60, 2-3.9 = 30, < 2 = 0 |
| High-Interest Debt | 35% | No debt > 12% APR | None = 100, < 25% of income = 60, 25-50% = 30, > 50% = 0 |
| Savings Rate | 25% | ≥ 20% of income | ≥ 20% = 100, 15-19.9 = 70, 10-14.9 = 40, 5-9.9 = 20, < 5 = 0 |

Readiness Level: ≥ 80 = "ready", 50-79 = "nearly_ready", < 50 = "not_ready"

## Agent Logic Flow

```
1. Load user financial data from SharedState / DB
2. Gate 1 — Emergency Fund Check:
   a. Call check_emergency_fund(ef_balance, monthly_expenses)
   b. Compute months_coverage = ef_balance / monthly_expenses
   c. If >= 6 → passed; score contribution = weight × 100
   d. If < 6 → failed; score = weight × partial_score
   e. Store gate_result
3. Gate 2 — High-Interest Debt Check:
   a. Call check_high_interest_debt(debts, 0.12)
   b. Scan all debts for interest_rate > 12%
   c. If none → passed; score contribution = 35
   d. If any → failed; compute severity by debt-to-income of high-interest debt
   e. Store gate_result with list of problematic debts
4. Gate 3 — Savings Rate Check:
   a. Call check_savings_rate(actual_savings_rate)
   b. If >= 20% → passed; score contribution = 25
   c. If < 20% → failed; score = weight × partial_score
   d. Store gate_result
5. Compute total readiness_score = sum of weighted component scores
6. Call compute_readiness() to determine readiness_level
7. For each failed gate, call get_educational_guidance():
   a. Emergency fund blocker → "An emergency fund of 6 months expenses is recommended before
      taking investment risk. Consider building this corpus in a savings account or liquid fund."
   b. High-interest debt blocker → "Paying off debt with interest above 12% provides a guaranteed
      return equal to the interest rate. Consider clearing this debt before increasing investment risk."
   c. Savings rate blocker → "A savings rate of at least 20% helps ensure you have sufficient
      funds to invest after meeting expenses. Consider reducing discretionary spending."
   d. NOTE: All guidance is educational, not advisory. No specific products named.
8. Add regulatory disclaimer to output
9. Update SharedState with readiness score, gate results, blockers, and disclaimer
10. Return control to Orchestrator
```

## Regulatory Compliance Notes

| Requirement | Implementation |
|---|---|
| No specific investment recommendations | Educational guidance only; no fund names, stocks, or sector picks |
| No performance guarantees | Returns are historical references only; "past performance" disclaimer |
| Risk profiling without product push | Risk tolerance is assessed; no product linkage |
| SEBI investment advisor rules | Agent does not advise; it educates on readiness criteria |
| Clear distinction fact vs. opinion | All statements cite widely accepted financial principles |
| User data privacy | No readiness data shared with third parties |

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| User has no debt | Gate 2 passes automatically; full score contribution |
| User has only low-interest debt (home loan at 8.5%) | Passes gate 2; home loan with ≤ 12% rate is considered healthy |
| Emergency fund is in investments (not cash) | Count at 70% value (liquidity discount); flag as "partially liquid" |
| Negative savings rate | Gate 3 score = 0; blocker: "spending exceeds income" |
| Student with part-time income | Adjust thresholds: use 3-month expenses for emergency fund check |
| User already investing aggressively but failing gates | Flag: "Current investment risk may exceed readiness level" |
| Multiple high-interest debts | List all; priority order by highest rate first |
| Savings rate includes employer PF/NPS | Include mandatory contributions; flag as "includes forced savings" |
| Refusal to provide debt information | Treat as unknown; warn "Debt assessment skipped due to missing data" |

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Check investment readiness for user u_123
Income: ₹85,000/mo, Expenses: ₹72,000/mo, Savings rate: 15.3%
Emergency fund: ₹1,20,000 (1.67 months)
Debts: Credit card ₹45,000 @ 42% APR, Personal loan ₹1,20,000 @ 15% APR, Home loan ₹24,00,000 @ 8.5%
```

**Agent Reasoning:**
```
Gate 1 - Emergency fund: ₹1,20,000 / ₹72,000 = 1.67 months. Threshold = 6. FAILED.
Gate 2 - High-interest debt:
  - Credit card ₹45,000 @ 42% > 12% → HIGH interest, FAIL
  - Personal loan ₹1,20,000 @ 15% > 12% → HIGH interest, FAIL
  - Home loan ₹24,00,000 @ 8.5% < 12% → OK
Gate 3 - Savings rate: 15.3% < 20% → FAILED.
Score: Emergency 0% × 0.40 = 0, Debt 0% × 0.35 = 0, Savings 40% × 0.25 = 10
Total: 10 / 100 → "not_ready"
Blockers: 1) Emergency fund critically low, 2) High-interest credit card debt,
3) Personal loan above 12%, 4) Savings rate below 20%.
Most impactful: Clear the credit card debt first (42% APR = guaranteed 42% return).
```

**Action Taken:**
```
check_emergency_fund(120000, 72000) → 1.67mo, FAIL
check_high_interest_debt([cc@42%, pl@15%, hl@8.5%], 0.12)
→ [cc: FAIL (42%), pl: FAIL (15%)]
check_savings_rate(0.153) → 15.3%, FAIL
compute_readiness(0, 0, 40) → 10/100
get_educational_guidance("emergency_fund") → "An emergency fund of 6 months expenses..."
get_educational_guidance("high_interest_debt") → "Paying off debt with interest above 12%..."
get_educational_guidance("savings_rate") → "A savings rate of at least 20%..."
→ Readiness: "not_ready" | Score: 10/100
→ Top blocker: "Credit card debt at 42% APR — clearing this yields a guaranteed 42% return."
→ Disclaimer: "This assessment is for educational purposes only and does not constitute
   investment advice. No specific investment products are recommended."
```

## Verification
- `readiness_score` is always 0-100 inclusive
- Gate weights sum to 100% (40 + 35 + 25)
- Each failed gate has a corresponding entry in `blockers` with educational guidance
- `blockers` list is sorted by severity (most critical first)
- Output contains no specific investment product, fund, or stock recommendations
- Regulatory `disclaimer` is always present in output
- `readiness_level` is one of exactly three values: "not_ready", "nearly_ready", "ready"
