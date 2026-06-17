# Agent 2: Transaction Categorization Agent

## Purpose
Automatically classify every transaction into meaningful spending categories. This transforms raw text like "Swiggy" into "Food & Dining" and "Uber" into "Transportation". The agent continuously improves through user feedback.

## Domain: FinTech
Categorization is the foundation of financial intelligence. Without accurate categories, budgets are meaningless, spending patterns are invisible, and financial advice is generic. Indian banks have diverse merchant names (e.g., "Zomato Online", "PVR Cinemas", "BigBasket", "HDFC Credit Card Payment") that require both pattern-matching and semantic understanding.

## LangGraph ReAct Pattern
**Reasoning:** The agent reviews each uncategorized transaction and determines the most appropriate category based on merchant name, transaction description, amount patterns, and historical categorization.

**Action:** It calls LLM for semantic classification on ambiguous entries and applies regex-based keyword matching for known patterns. It stores the result and learns from user corrections.

## Input (from SharedState)
- `transactions`: list of parsed transactions (merchant, description, amount)
- `user_id`: for user-specific categories
- `category_id_map`: existing category mappings for this user

## Output (writes to SharedState)
- `transactions`: each now has `category_id` populated
- `category_summaries`: dict of `{category_name: total_amount}` for the batch
- `category_id_map`: updated with any new learned mappings

## Internal Tools Used
| Tool | Description |
|---|---|
| `match_keyword(merchant, description)` | Regex + keyword lookup against known patterns |
| `classify_llm(merchant, description, amount)` | Sends to Groq for semantic classification of ambiguous entries |
| `get_user_categories(user_id)` | Fetches user's existing category list from DB |
| `update_transaction_category(tx_id, category_id)` | Writes category to transaction in DB |
| `learn_from_correction(tx_id, corrected_category)` | Updates keyword map when user manually corrects |

## Category Taxonomy

```
Food & Dining
├── Restaurant / Dining Out
├── Food Delivery (Swiggy, Zomato, Zepto)
└── Groceries (BigBasket, Blinkit, DMart)

Transportation
├── Fuel (Indian Oil, BPCL, HPCL)
├── Metro / Bus
├── Cab / Auto (Uber, Ola, Rapido)
├── Flight
└── Train

Shopping
├── Online (Amazon, Flipkart, Myntra)
├── Clothing
├── Electronics
└── Other Retail

Bills & Utilities
├── Electricity
├── Water
├── Internet
├── Phone / Mobile Recharge
└── Credit Card Payment

Entertainment
├── Movies (PVR, INOX)
├── OTT (Netflix, Prime Video, Hotstar)
├── Gaming
└── Events

Healthcare
├── Doctor / Clinic
├── Pharmacy / Medicine
├── Hospital
├── Insurance Premium
└── Lab Tests

Education
├── Tuition / Coaching
├── Online Courses
├── Books / Study Material
└── Exam Fees

Subscriptions
├── SaaS (ChatGPT, Google Drive, GitHub)
├── Music (Spotify, Apple Music)
├── Streaming (Netflix, Prime, Hotstar, JioCinema)
└── Gym / Club

Investments
├── Mutual Funds SIP
├── Stocks
├── Fixed Deposit / RD
├── PPF / NPS
└── Crypto

Bills & EMI
├── Personal Loan EMI
├── Home Loan EMI
├── Auto Loan EMI
└── Credit Card EMI

Income
├── Salary
├── Freelance
├── Interest
├── Refund / Cashback
└── Gift / Transfer

Other / Uncategorized
└── Catch-all for unrecognized entries
```

## Agent Logic Flow

```
1. Load all transactions without category_id from SharedState
2. For each transaction:
   a. Run match_keyword() against known patterns
   b. If match found → assign category, skip LLM
   c. If no match → call classify_llm()
   d. Write to DB via update_transaction_category()
3. Aggregate category summaries
4. Update SharedState with categories and summaries
5. Return to Orchestrator
```

## Edge Cases Handled

| Edge Case | Response |
|---|---|
| Empty merchant name | Use description field; if both empty → "Uncategorized" |
| Transfer between own accounts | "Transfer / Internal" — exclude from spending analysis |
| EMI debit vs actual purchase | Mark as "EMI Payment" and link to original category |
| Cash withdrawal | "Cash Withdrawal" — separate category |
| Refund / Reversal | Negative amount → "Refund" category, excluded from spending |
| Unknown merchant (unlikely) | LLM classifies based on amount + description context |

## Learning Loop
```
User corrects a category in frontend
→ API call: POST /transactions/{id}/category
→ learn_from_correction() updates keyword map
→ Future same-merchant transactions auto-categorize correctly
→ State is updated
```

## ReAct Example Interaction

**User Input (from Orchestrator):**
```
Categorize 85 new transactions for user u_123
```

**Agent Reasoning:**
```
I have 85 transactions. Let me batch-process them.
First, fast pattern-match known merchants (Swiggy, Uber, Netflix, Amazon, etc.).
Remaining 23 ambiguous ones need LLM classification.
```

**Action Taken:**
```
match_keyword() → 62 of 85 matched in <1s
classify_llm() on remaining 23 → all classified
Write 85 category assignments to DB
category_summaries = {
  "Food & Dining": 12500.00,
  "Transportation": 3200.00,
  "Entertainment": 1500.00,
  ...
}
```

## Verification
- Every transaction has a non-null `category_id`
- `category_summaries` total equals sum of transaction amounts
- No transaction in "Other / Uncategorized" if a valid category exists
- User feedback correctly overrides stale classifications
