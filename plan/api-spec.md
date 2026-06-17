# FastAPI Endpoint Specification — PS-05 Personal Finance Agent

## Base URL
`https://api.ps05-finance.app/v1`

## Authentication
All endpoints marked with **(Auth: Y)** require a Bearer JWT token in the `Authorization` header:
```
Authorization: Bearer <supabase_access_token>
```
Tokens are obtained via Supabase Auth (`/auth` endpoints). Tokens expire after 3600 seconds. Refresh via `/auth/refresh`.

---

## Endpoints

### 1. Auth — Sign Up

**POST /auth/signup**

- **Auth:** N
- **Description:** Register a new user account. Triggers email verification.
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123!",
    "phone": "+919876543210",
    "full_name": "Priya Sharma"
  }
  ```
- **Response 201:**
  ```json
  {
    "user_id": "uuid",
    "email": "user@example.com",
    "access_token": "jwt...",
    "refresh_token": "jwt...",
    "expires_in": 3600
  }
  ```
- **Response 409:** `{"detail": "Email already registered"}`
- **Response 422:** Validation error

---

### 2. Auth — Login

**POST /auth/login**

- **Auth:** N
- **Description:** Authenticate user and return JWT tokens.
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123!"
  }
  ```
- **Response 200:**
  ```json
  {
    "user_id": "uuid",
    "email": "user@example.com",
    "access_token": "jwt...",
    "refresh_token": "jwt...",
    "expires_in": 3600
  }
  ```
- **Response 401:** `{"detail": "Invalid credentials"}`

---

### 3. Auth — Refresh Token

**POST /auth/refresh**

- **Auth:** N
- **Description:** Refresh an expired access token using a valid refresh token.
- **Request Body:**
  ```json
  {
    "refresh_token": "jwt..."
  }
  ```
- **Response 200:**
  ```json
  {
    "access_token": "jwt...",
    "refresh_token": "jwt...",
    "expires_in": 3600
  }
  ```
- **Response 401:** `{"detail": "Invalid refresh token"}`

---

### 4. Auth — Get Profile

**GET /auth/me**

- **Auth:** Y
- **Description:** Get the current authenticated user's profile.
- **Response 200:**
  ```json
  {
    "user_id": "uuid",
    "email": "user@example.com",
    "phone": "+919876543210",
    "full_name": "Priya Sharma",
    "avatar_url": "https://...",
    "onb_complete": true,
    "monthly_income": 85000.00,
    "currency": "INR",
    "locale": "en-IN",
    "created_at": "2025-01-15T10:30:00Z",
    "last_login_at": "2025-06-17T08:15:00Z"
  }
  ```
- **Response 401:** Unauthorized

---

### 5. Auth — Update Profile

**PUT /auth/me**

- **Auth:** Y
- **Description:** Update the current user's profile fields.
- **Request Body:**
  ```json
  {
    "full_name": "Priya Sharma",
    "phone": "+919876543211",
    "monthly_income": 90000.00,
    "currency": "INR",
    "locale": "en-IN"
  }
  ```
- **Response 200:**
  ```json
  {
    "user_id": "uuid",
    "full_name": "Priya Sharma",
    "phone": "+919876543211",
    "monthly_income": 90000.00,
    "updated_at": "2025-06-17T09:00:00Z"
  }
  ```

---

### 6. Upload Statement

**POST /upload/statement**

- **Auth:** Y
- **Description:** Upload a bank/credit card statement file (PDF, CSV, XLSX, or image). Accepts multipart form data. Triggers async ingestion pipeline.
- **Request Body (multipart/form-data):**
  ```
  file: <binary>
  source: "hdfc"
  password: "optional_pdf_password"
  ```
- **Response 202:**
  ```json
  {
    "statement_id": "uuid",
    "file_name": "HDFC_Statement_Mar2025.pdf",
    "file_type": "pdf",
    "source": "hdfc",
    "status": "pending",
    "message": "Statement uploaded. Processing started.",
    "estimated_completion_seconds": 45
  }
  ```
- **Response 400:** `{"detail": "Unsupported file type. Accepted: pdf, csv, xlsx, image"}`
- **Response 413:** `{"detail": "File too large. Max 20MB"}`
- **Response 502:** `{"detail": "Ingestion pipeline unavailable"}`

---

### 7. Upload Status

**GET /upload/status/{statement_id}**

- **Auth:** Y
- **Description:** Poll the processing status of an uploaded statement.
- **Response 200:**
  ```json
  {
    "statement_id": "uuid",
    "status": "processing",
    "progress_pct": 65,
    "tx_count": null,
    "total_amount": null,
    "error_message": null,
    "created_at": "2025-06-17T09:05:00Z",
    "estimated_remaining_seconds": 15
  }
  ```
- **Response 200 (completed):**
  ```json
  {
    "statement_id": "uuid",
    "status": "completed",
    "progress_pct": 100,
    "tx_count": 85,
    "total_amount": 245000.00,
    "error_message": null,
    "processed_at": "2025-06-17T09:06:30Z"
  }
  ```
- **Response 404:** `{"detail": "Statement not found"}`

---

### 8. Get Transactions

**GET /transactions**

- **Auth:** Y
- **Description:** Retrieve the user's transactions with pagination, filtering, and sorting.
- **Query Parameters:**
  | Param | Type | Default | Description |
  |---|---|---|---|
  | `page` | int | 1 | Page number (1-indexed) |
  | `per_page` | int | 50 | Items per page (max 200) |
  | `start_date` | date | — | Filter: start date (inclusive) |
  | `end_date` | date | — | Filter: end date (inclusive) |
  | `category_id` | uuid | — | Filter by category |
  | `tx_type` | string | — | Filter: debit / credit / transfer |
  | `merchant` | string | — | Search by merchant name (partial match) |
  | `min_amount` | numeric | — | Filter: minimum amount |
  | `max_amount` | numeric | — | Filter: maximum amount |
  | `is_flagged` | bool | — | Filter flagged transactions only |
  | `sort_by` | string | `tx_date` | Sort field: tx_date, amount, created_at |
  | `sort_order` | string | `desc` | asc / desc |
- **Response 200:**
  ```json
  {
    "data": [
      {
        "id": "uuid",
        "tx_date": "2025-03-15",
        "description": "Amazon.in",
        "merchant": "Amazon Pay",
        "amount": 2499.00,
        "tx_type": "debit",
        "currency": "INR",
        "tx_mode": "upi",
        "category": {
          "id": "uuid",
          "name": "Shopping",
          "icon": "🛍️",
          "color": "#06b6d4"
        },
        "is_recurring": false,
        "is_flagged": false,
        "tags": ["online", "shopping"]
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total_items": 342,
      "total_pages": 7,
      "has_next": true,
      "has_prev": false
    },
    "summary": {
      "total_debits": 72000.00,
      "total_credits": 85000.00,
      "net_flow": 13000.00,
      "tx_count": 342
    }
  }
  ```
- **Response 401:** Unauthorized

---

### 9. Categorize Transaction

**POST /transactions/{transaction_id}/category**

- **Auth:** Y
- **Description:** Manually assign or change a transaction's category. Triggers recategorization in the agent pipeline.
- **Request Body:**
  ```json
  {
    "category_id": "uuid"
  }
  ```
- **Response 200:**
  ```json
  {
    "transaction_id": "uuid",
    "previous_category": "Uncategorized",
    "new_category": "Shopping",
    "recategorized_at": "2025-06-17T09:10:00Z"
  }
  ```
- **Response 404:** `{"detail": "Transaction or category not found"}`
- **Response 422:** `{"detail": "Category does not belong to user's budget types"}`

---

### 10. Get Dashboard

**GET /dashboard**

- **Auth:** Y
- **Description:** Get the main dashboard summary for the current user. Aggregates latest month's data.
- **Response 200:**
  ```json
  {
    "user_id": "uuid",
    "period": {
      "month": "2025-03",
      "label": "March 2025"
    },
    "income": {
      "total": 85000.00,
      "sources": [
        {"name": "Salary", "amount": 80000.00},
        {"name": "Freelance", "amount": 5000.00}
      ]
    },
    "expenses": {
      "total": 72000.00,
      "by_category": [
        {"category": "Rent", "amount": 25000.00, "pct": 34.7},
        {"category": "EMIs", "amount": 18000.00, "pct": 25.0},
        {"category": "Groceries", "amount": 8500.00, "pct": 11.8}
      ]
    },
    "savings": {
      "amount": 13000.00,
      "rate": 15.3
    },
    "budget_summary": {
      "on_track": 3,
      "at_risk": 1,
      "exceeded": 1
    },
    "health_score": {
      "score": 52,
      "trend": "improved",
      "updated_at": "2025-06-17T08:00:00Z"
    },
    "alerts_count": {
      "unread": 3,
      "critical": 1
    },
    "recent_transactions": [
      {
        "id": "uuid",
        "tx_date": "2025-03-30",
        "description": "BigBasket",
        "amount": 1245.00,
        "category": "Groceries"
      }
    ]
  }
  ```
- **Response 401:** Unauthorized

---

### 11. Get Insights

**GET /insights**

- **Auth:** Y
- **Description:** Get AI-generated financial insights and recommendations for the user. Triggered by the latest pipeline run.
- **Response 200:**
  ```json
  {
    "insights": [
      {
        "type": "spending_pattern",
        "title": "Dining out spending increased 40%",
        "description": "You spent ₹4,200 on dining this month vs ₹3,000 last month.",
        "severity": "warning",
        "actionable": true,
        "suggestion": "Consider setting a dining budget of ₹3,500/month."
      },
      {
        "type": "savings_opportunity",
        "title": "Unused subscription detected",
        "description": "Spotify Premium (₹119/mo) has had no usage in 4 months.",
        "severity": "info",
        "actionable": true,
        "suggestion": "Annual savings if cancelled: ₹1,428."
      }
    ],
    "anomalies": [
      {
        "type": "unusual_transaction",
        "tx_date": "2025-03-28",
        "amount": 45000.00,
        "merchant": "Unknown UPI ID",
        "reason": "Amount 3.5× larger than average UPI transaction",
        "flagged": true
      }
    ],
    "generated_at": "2025-06-17T08:05:00Z",
    "pipeline_session_id": "uuid"
  }
  ```
- **Response 401:** Unauthorized

---

### 12. Get Alerts

**GET /alerts**

- **Auth:** Y
- **Description:** Retrieve all alerts for the user, with filtering and pagination.
- **Query Parameters:**
  | Param | Type | Default | Description |
  |---|---|---|---|
  | `unread_only` | bool | false | Return only unread alerts |
  | `severity` | string | — | Filter: info / warning / critical |
  | `alert_type` | string | — | Filter by alert type |
  | `page` | int | 1 | Page number |
  | `per_page` | int | 20 | Items per page |
- **Response 200:**
  ```json
  {
    "data": [
      {
        "id": "uuid",
        "alert_type": "budget_risk",
        "severity": "warning",
        "title": "Food budget 90% utilized",
        "message": "You've spent ₹6,300 of your ₹7,000 food budget. 10 days remaining in the month.",
        "data": {
          "category": "Groceries",
          "limit": 7000,
          "spent": 6300,
          "percentage": 90
        },
        "is_read": false,
        "source_agent": "budget",
        "created_at": "2025-06-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total_items": 15,
      "total_pages": 1
    },
    "unread_count": 3
  }
  ```
- **Response 401:** Unauthorized

---

### 13. Mark Alert as Read

**PUT /alerts/{alert_id}/read**

- **Auth:** Y
- **Description:** Mark a specific alert as read.
- **Response 200:**
  ```json
  {
    "alert_id": "uuid",
    "is_read": true,
    "read_at": "2025-06-17T09:15:00Z"
  }
  ```
- **Response 404:** `{"detail": "Alert not found"}`
- **Alternative (batch):** `PUT /alerts/read-all` — marks all unread alerts as read.
  ```json
  {
    "updated_count": 3,
    "read_at": "2025-06-17T09:15:00Z"
  }
  ```

---

### 14. Get Goals

**GET /goals**

- **Auth:** Y
- **Description:** Retrieve all financial goals for the user.
- **Query Parameters:**
  | Param | Type | Default | Description |
  |---|---|---|---|
  | `status` | string | — | Filter: active / paused / completed / overdue / cancelled |
  | `goal_type` | string | — | Filter by goal type |
- **Response 200:**
  ```json
  {
    "data": [
      {
        "id": "uuid",
        "goal_type": "large_purchase",
        "name": "Buy Car",
        "target_amount": 1200000.00,
        "current_amount": 240000.00,
        "target_date": "2027-06-01",
        "monthly_target": 56180.00,
        "priority": 2,
        "status": "active",
        "progress_pct": 20.0,
        "months_remaining": 24,
        "is_on_track": false,
        "alert": "Monthly target of ₹56,180 exceeds current surplus of ₹13,000"
      }
    ],
    "summary": {
      "total_goals": 3,
      "active_goals": 2,
      "completed_goals": 1,
      "total_target": 3200000.00,
      "total_saved": 840000.00,
      "overall_progress_pct": 26.3
    }
  }
  ```

---

### 15. Create Goal

**POST /goals**

- **Auth:** Y
- **Description:** Create a new financial goal. Agent calculates monthly target and checks affordability.
- **Request Body:**
  ```json
  {
    "name": "Buy Car",
    "goal_type": "large_purchase",
    "target_amount": 1200000.00,
    "target_date": "2027-06-01",
    "priority": 2,
    "family_member_id": null,
    "notes": "Down payment 20%, rest through loan"
  }
  ```
- **Response 201:**
  ```json
  {
    "goal_id": "uuid",
    "name": "Buy Car",
    "monthly_target": 56180.00,
    "is_affordable": false,
    "affordability_gap": 43180.00,
    "suggestions": [
      "Extend deadline to 5 years → ₹22,472/mo",
      "Reduce target to ₹5,00,000 → ₹20,833/mo"
    ],
    "status": "active"
  }
  ```
- **Response 400:** `{"detail": "Goal type 'retirement' requires retirement_age in user profile"}`

---

### 16. Simulate Scenario

**POST /scenarios/simulate**

- **Auth:** Y
- **Description:** Run a life event or what-if scenario simulation. Returns structured impact report.
- **Request Body:**
  ```json
  {
    "scenario_type": "life_event",
    "label": "Buy ₹12L Car",
    "event_params": {
      "event_type": "vehicle_purchase",
      "cost": 1200000,
      "down_payment": 240000,
      "loan_rate": 0.10,
      "tenure_years": 5
    }
  }
  ```
- **Response 200:**
  ```json
  {
    "scenario_id": "uuid",
    "label": "Buy ₹12L Car",
    "impact_metrics": {
      "monthly_emi": 20392.00,
      "dti_before": 21.2,
      "dti_after": 45.2,
      "savings_before": 13000.00,
      "savings_after": -15392.00,
      "savings_rate_before": 15.3,
      "savings_rate_after": -18.1,
      "ef_months_before": 6.25,
      "ef_months_after": 2.92
    },
    "risk_flags": [
      {
        "severity": "critical",
        "message": "Negative savings — expenses exceed income by ₹15,392/mo",
        "metric": "savings_after"
      },
      {
        "severity": "high",
        "message": "Emergency fund drops to 2.92 months (below 3-month threshold)",
        "metric": "ef_months_after"
      },
      {
        "severity": "medium",
        "message": "DTI at 45.2% — above 40%警戒线",
        "metric": "dti_after"
      }
    ],
    "cashflow_12mo": [
      {"month": 1, "balance": 410000, "income": 85000, "expenses": 100392},
      {"month": 2, "balance": 394608, "income": 85000, "expenses": 100392}
    ],
    "created_at": "2025-06-17T09:20:00Z"
  }
  ```
- **Response 422:** `{"detail": "Invalid event_params for event_type 'vehicle_purchase': missing 'cost'"}`

---

### 17. Get Scenarios

**GET /scenarios**

- **Auth:** Y
- **Description:** Retrieve previously simulated scenarios for the user.
- **Query Parameters:**
  | Param | Type | Default | Description |
  |---|---|---|---|
  | `scenario_type` | string | — | Filter: life_event / financial_twin / what_if |
  | `page` | int | 1 | Page number |
  | `per_page` | int | 10 | Items per page |
- **Response 200:**
  ```json
  {
    "data": [
      {
        "id": "uuid",
        "scenario_type": "life_event",
        "label": "Buy ₹12L Car",
        "risk_flags": [
          {"severity": "critical", "message": "Negative savings"}
        ],
        "created_at": "2025-06-17T09:20:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total_items": 5,
      "total_pages": 1
    }
  }
  ```

---

### 18. Get Family Aggregation

**GET /family/aggregation**

- **Auth:** Y
- **Description:** Get the combined family financial summary. Aggregates all linked members' data per their sharing permissions.
- **Response 200:**
  ```json
  {
    "family_id": "uuid",
    "primary_user_id": "uuid",
    "members_included": 3,
    "members_total": 3,
    "combined_summary": {
      "total_income": 145000.00,
      "total_expenses": 122000.00,
      "total_savings": 23000.00,
      "savings_rate": 15.9,
      "dti": 12.4
    },
    "family_health_score": {
      "score": 68,
      "breakdown": {}
    },
    "per_member": [
      {
        "member_id": "uuid",
        "name": "You",
        "role": "self",
        "income_share_pct": 58.6,
        "expense_share_pct": 59.0,
        "goal_contribution_pct": 71.0,
        "sharing_level": "full"
      },
      {
        "member_id": "uuid",
        "name": "Spouse",
        "role": "spouse",
        "income_share_pct": 31.0,
        "expense_share_pct": 31.1,
        "goal_contribution_pct": 29.0,
        "sharing_level": "summary"
      }
    ],
    "shared_goals": [
      {
        "goal_id": "uuid",
        "name": "Children Education Fund",
        "target": 2000000.00,
        "saved": 420000.00,
        "progress_pct": 21.0,
        "members": [
          {"member_id": "uuid", "contribution": 300000.00, "share_pct": 71.4},
          {"member_id": "uuid", "contribution": 120000.00, "share_pct": 28.6}
        ]
      }
    ],
    "imbalances": [
      "Primary contributes 59% of income but 71% of goal — moderate imbalance"
    ],
    "last_updated": "2025-06-17T09:00:00Z"
  }
  ```
- **Response 200 (no family members):** `{"members_included": 1, "note": "No additional family members linked"}`
- **Response 401:** Unauthorized

---

### 19. Get Family Members

**GET /family/members**

- **Auth:** Y
- **Description:** List all linked family members with their sharing levels.
- **Response 200:**
  ```json
  {
    "data": [
      {
        "member_id": "uuid",
        "name": "Rajesh Sharma",
        "role": "spouse",
        "relationship": "Spouse",
        "sharing_level": "summary",
        "is_dependent": false,
        "monthly_income": 45000.00,
        "linked_since": "2025-03-01T10:00:00Z"
      }
    ]
  }
  ```

---

### 20. Add Family Member

**POST /family/members**

- **Auth:** Y
- **Description:** Link a family member to the user's family group. Can link by email (if existing user) or create a placeholder.
- **Request Body:**
  ```json
  {
    "member_email": "spouse@example.com",
    "member_name": "Rajesh Sharma",
    "role": "spouse",
    "relationship": "Spouse",
    "sharing_level": "summary",
    "is_dependent": false,
    "monthly_income": 45000.00
  }
  ```
- **Response 201:**
  ```json
  {
    "member_id": "uuid",
    "name": "Rajesh Sharma",
    "role": "spouse",
    "sharing_level": "summary",
    "status": "invited",
    "invite_sent": true,
    "message": "Invitation sent to spouse@example.com"
  }
  ```
- **Response 409:** `{"detail": "Family member already linked"}`

---

### 21. Update Family Member

**PUT /family/members/{member_id}**

- **Auth:** Y
- **Description:** Update a family member's sharing level, role, or income.
- **Request Body:**
  ```json
  {
    "sharing_level": "full",
    "monthly_income": 50000.00
  }
  ```
- **Response 200:**
  ```json
  {
    "member_id": "uuid",
    "sharing_level": "full",
    "updated_at": "2025-06-17T09:25:00Z"
  }
  ```

---

### 22. Remove Family Member

**DELETE /family/members/{member_id}**

- **Auth:** Y
- **Description:** Unlink a family member from the group.
- **Response 200:**
  ```json
  {
    "member_id": "uuid",
    "status": "removed",
    "message": "Family member unlinked"
  }
  ```
- **Response 404:** `{"detail": "Family member not found"}`

---

### 23. Get Health Score

**GET /health-score**

- **Auth:** Y
- **Description:** Get the user's current financial health score with full breakdown and history.
- **Query Parameters:**
  | Param | Type | Default | Description |
  |---|---|---|---|
  | `include_history` | bool | true | Include monthly score history |
  | `months` | int | 6 | Number of past months to include (if include_history) |
- **Response 200:**
  ```json
  {
    "current": {
      "score": 52,
      "breakdown": {
        "savings_rate": {"score": 60, "weight": 0.25, "impact": 15.0, "explanation": "15.3% rate → score 60"},
        "debt_to_income": {"score": 80, "weight": 0.20, "impact": 16.0, "explanation": "21.2% DTI → score 80"},
        "emergency_fund": {"score": 20, "weight": 0.20, "impact": 4.0, "explanation": "0.63 months → score 20"},
        "budget_discipline": {"score": 60, "weight": 0.15, "impact": 9.0, "explanation": "60% on track → score 60"},
        "investment_allocation": {"score": 60, "weight": 0.10, "impact": 6.0, "explanation": "38.5% → score 60"}
      },
      "top_drags": [
        "Emergency fund (only 0.63 months)",
        "Savings rate (15.3%)",
        "Investment allocation (38.5%)"
      ],
      "trend": "improved"
    },
    "history": [
      {"month": "2025-01", "score": 42},
      {"month": "2025-02", "score": 45},
      {"month": "2025-03", "score": 52}
    ],
    "last_updated": "2025-06-17T08:00:00Z"
  }
  ```
- **Response 200 (insufficient data):**
  ```json
  {
    "current": null,
    "message": "Insufficient data. Upload at least 1 month of transactions to generate a health score.",
    "history": [],
    "last_updated": null
  }
  ```

---

### 24. Get Investment Readiness

**GET /investment-readiness**

- **Auth:** Y
- **Description:** Assess whether the user is ready to increase investment risk. Returns readiness score, gate results, and blockers.
- **Response 200:**
  ```json
  {
    "readiness_score": 25,
    "readiness_level": "not_ready",
    "gate_results": {
      "emergency_fund": {
        "passed": false,
        "value": 1.67,
        "threshold": 6.0,
        "unit": "months",
        "explanation": "Emergency fund covers only 1.67 months of expenses"
      },
      "high_interest_debt": {
        "passed": false,
        "value": 2,
        "threshold": 0,
        "unit": "debts > 12% APR",
        "explanation": "2 debts exceed 12% APR: Credit card (42%), Personal loan (15%)"
      },
      "savings_rate": {
        "passed": false,
        "value": 15.3,
        "threshold": 20.0,
        "unit": "%",
        "explanation": "Savings rate is 15.3%, below the 20% threshold"
      }
    },
    "blockers": [
      {
        "blocker": "Credit card debt at 42% APR",
        "severity": "critical",
        "resolution_guidance": "Paying off credit card debt at 42% APR provides a guaranteed 42% return. Prioritize clearing this balance before taking investment risk."
      },
      {
        "blocker": "Emergency fund insufficient",
        "severity": "high",
        "resolution_guidance": "An emergency fund covering 6 months of expenses (₹4,32,000) is recommended. Currently at ₹1,20,000."
      },
      {
        "blocker": "Savings rate below 20%",
        "severity": "medium",
        "resolution_guidance": "A savings rate of at least 20% helps ensure you have sufficient funds to invest. Consider reducing discretionary spending."
      }
    ],
    "disclaimer": "This assessment is for educational purposes only and does not constitute investment advice. No specific investment products are recommended.",
    "assessed_at": "2025-06-17T09:30:00Z"
  }
  ```

---

### 25. Create Financial Twin

**POST /twin/create**

- **Auth:** Y
- **Description:** Create a baseline financial twin snapshot of the user's current financial state.
- **Response 201:**
  ```json
  {
    "twin_id": "uuid",
    "baseline_snapshot": {
      "income": 85000.00,
      "expenses": 72000.00,
      "debts": [
        {"type": "home_loan", "principal": 2400000, "rate": 8.5, "emi": 22000, "tenure_remaining_months": 180}
      ],
      "emergency_fund": 450000.00,
      "investments": 350000.00,
      "snapshot_date": "2025-06-17"
    },
    "created_at": "2025-06-17T09:35:00Z"
  }
  ```
- **Response 400:** `{"detail": "Insufficient data to create twin. Missing: income, expenses"}`

---

### 26. Apply Event to Twin

**POST /twin/{twin_id}/apply**

- **Auth:** Y
- **Description:** Apply a financial event to a twin (creates a what-if branch). Supported events: salary_increase, job_loss, new_loan, expense_shock, investment_change, lumpsum_credit, insurance_add.
- **Request Body:**
  ```json
  {
    "branch_label": "Job Loss 6 Months",
    "event": {
      "event_type": "job_loss",
      "severance_months": 0,
      "gap_months": 6,
      "effective_month": "2025-07"
    }
  }
  ```
- **Response 200:**
  ```json
  {
    "branch_id": "uuid",
    "twin_id": "uuid",
    "label": "Job Loss 6 Months",
    "event_applied": {
      "event_type": "job_loss",
      "gap_months": 6,
      "description": "No income for 6 months starting July 2025"
    },
    "created_at": "2025-06-17T09:40:00Z"
  }
  ```

---

### 27. Predict Twin (12 Months)

**GET /twin/{twin_id}/predict**

- **Auth:** Y
- **Description:** Run a 12-month forward projection on a twin or branch.
- **Query Parameters:**
  | Param | Type | Default | Description |
  |---|---|---|---|
  | `branch_id` | uuid | — | Optional specific branch to predict |
- **Response 200:**
  ```json
  {
    "twin_id": "uuid",
    "branch_id": "uuid",
    "label": "Baseline (Job Loss 6 Months)",
    "projection": [
      {"month": 0, "balance": 450000, "income": 85000, "expenses": 72000, "net_worth": 800000},
      {"month": 1, "balance": 378000, "income": 0, "expenses": 72000, "net_worth": 728000},
      {"month": 2, "balance": 306000, "income": 0, "expenses": 72000, "net_worth": 656000},
      {"month": 3, "balance": 234000, "income": 0, "expenses": 72000, "net_worth": 584000},
      {"month": 4, "balance": 162000, "income": 0, "expenses": 72000, "net_worth": 512000},
      {"month": 5, "balance": 90000, "income": 0, "expenses": 72000, "net_worth": 440000},
      {"month": 6, "balance": 18000, "income": 0, "expenses": 72000, "net_worth": 368000},
      {"month": 7, "balance": 31000, "income": 85000, "expenses": 72000, "net_worth": 381000}
    ],
    "summary": {
      "start_balance": 450000,
      "min_balance": 18000,
      "end_balance": 31000,
      "start_net_worth": 800000,
      "end_net_worth": 381000,
      "depletion_risk": true,
      "depletion_month": 7,
      "risk_flags": [
        "Emergency fund exhausted by month 5",
        "1 month of negative cash flow before income resumes"
      ]
    }
  }
  ```

---

### 28. Compare Twins

**GET /twin/compare**

- **Auth:** Y
- **Description:** Compare two twins or branches side-by-side.
- **Query Parameters:**
  | Param | Type | Description |
  |---|---|---|
  | `baseline_id` | uuid | Baseline twin ID |
  | `branch_id` | uuid | Branch twin ID to compare against |
- **Response 200:**
  ```json
  {
    "baseline_label": "Baseline",
    "branch_label": "Job Loss 6 Months",
    "comparison": {
      "month_0": {
        "balance": {"baseline": 450000, "branch": 450000, "delta": 0},
        "net_worth": {"baseline": 800000, "branch": 800000, "delta": 0}
      },
      "month_6": {
        "balance": {"baseline": 483000, "branch": 18000, "delta": -465000},
        "net_worth": {"baseline": 833000, "branch": 368000, "delta": -465000}
      },
      "month_12": {
        "balance": {"baseline": 516000, "branch": 31000, "delta": -485000},
        "net_worth": {"baseline": 866000, "branch": 381000, "delta": -485000}
      }
    },
    "verdict": "Job loss scenario would deplete savings and reduce net worth by 56% over 12 months. Emergency fund is insufficient for a 6-month gap."
  }
  ```

---

### 29. Run Agent Pipeline

**POST /agent/run**

- **Auth:** Y
- **Description:** Manually trigger the full agent pipeline or a specific agent. Typically called automatically after statement upload, but exposed for re-runs and testing.
- **Request Body:**
  ```json
  {
    "pipeline": "full",
    "agents": null,
    "force_reprocess": false
  }
  ```
  Or for a specific agent:
  ```json
  {
    "pipeline": "single",
    "agents": ["budget", "anomaly"],
    "force_reprocess": true
  }
  ```
- **Response 202:**
  ```json
  {
    "session_id": "uuid",
    "pipeline": "full",
    "status": "running",
    "agents_triggered": ["data_ingestion", "categorization", "budget", "anomaly", "subscription", "health_score", "cashflow_forecast", "advisor", "notification"],
    "progress_url": "/ws/progress?session_id=uuid",
    "estimated_completion_seconds": 30
  }
  ```
- **Response 400:** `{"detail": "No data available to process. Upload a statement first."}`

---

### 30. WebSocket — Pipeline Progress

**WebSocket /ws/progress**

- **Auth:** Y (via token query param)
- **Description:** Real-time progress updates for a running agent pipeline. Connect via WebSocket.
- **Connection:**
  ```
  wss://api.ps05-finance.app/v1/ws/progress?session_id=<session_id>&token=<jwt_token>
  ```
- **Server Messages (JSON):**
  ```json
  {
    "type": "progress",
    "session_id": "uuid",
    "pipeline_stage": "categorization",
    "progress_pct": 45,
    "current_agent": "Categorization Agent",
    "message": "Categorizing transactions... (45/85 done)"
  }
  ```
  ```json
  {
    "type": "agent_complete",
    "session_id": "uuid",
    "agent": "budget",
    "status": "success",
    "duration_ms": 3200
  }
  ```
  ```json
  {
    "type": "pipeline_complete",
    "session_id": "uuid",
    "status": "success",
    "total_duration_ms": 28400,
    "agents_succeeded": 9,
    "agents_failed": 0
  }
  ```
  ```json
  {
    "type": "error",
    "session_id": "uuid",
    "agent": "ingestion",
    "error": "Failed to parse PDF: invalid format",
    "retry_count": 2
  }
  ```
- **Close Codes:**
  - 1000: Pipeline complete
  - 4001: Session not found
  - 4002: Token expired — reconnect with fresh token
  - 4003: Rate limited (max 5 concurrent connections per user)

---

## Summary of Endpoints

| # | Method | Path | Auth | Description |
|---|---|---|---|---|
| 1 | POST | `/auth/signup` | N | Register new user |
| 2 | POST | `/auth/login` | N | Login |
| 3 | POST | `/auth/refresh` | N | Refresh JWT token |
| 4 | GET | `/auth/me` | Y | Get profile |
| 5 | PUT | `/auth/me` | Y | Update profile |
| 6 | POST | `/upload/statement` | Y | Upload statement |
| 7 | GET | `/upload/status/{id}` | Y | Upload status |
| 8 | GET | `/transactions` | Y | List transactions |
| 9 | POST | `/transactions/{id}/category` | Y | Categorize transaction |
| 10 | GET | `/dashboard` | Y | Dashboard summary |
| 11 | GET | `/insights` | Y | AI insights |
| 12 | GET | `/alerts` | Y | List alerts |
| 13 | PUT | `/alerts/{id}/read` | Y | Mark alert read |
| 13b | PUT | `/alerts/read-all` | Y | Mark all read |
| 14 | GET | `/goals` | Y | List goals |
| 15 | POST | `/goals` | Y | Create goal |
| 16 | POST | `/scenarios/simulate` | Y | Simulate scenario |
| 17 | GET | `/scenarios` | Y | List scenarios |
| 18 | GET | `/family/aggregation` | Y | Family aggregation |
| 19 | GET | `/family/members` | Y | List family members |
| 20 | POST | `/family/members` | Y | Add family member |
| 21 | PUT | `/family/members/{id}` | Y | Update family member |
| 22 | DELETE | `/family/members/{id}` | Y | Remove family member |
| 23 | GET | `/health-score` | Y | Health score |
| 24 | GET | `/investment-readiness` | Y | Investment readiness |
| 25 | POST | `/twin/create` | Y | Create financial twin |
| 26 | POST | `/twin/{id}/apply` | Y | Apply event to twin |
| 27 | GET | `/twin/{id}/predict` | Y | Predict twin 12mo |
| 28 | GET | `/twin/compare` | Y | Compare twins |
| 29 | POST | `/agent/run` | Y | Run agent pipeline |
| 30 | WS | `/ws/progress` | Y | Pipeline progress |

---

## Common Error Responses

| Status | Body | When |
|---|---|---|
| 400 | `{"detail": "message"}` | Bad request / validation |
| 401 | `{"detail": "Unauthorized"}` | Missing/invalid token |
| 403 | `{"detail": "Forbidden"}` | Insufficient permissions |
| 404 | `{"detail": "Resource not found"}` | Invalid ID |
| 409 | `{"detail": "Conflict"}` | Duplicate resource |
| 422 | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` | Validation error |
| 429 | `{"detail": "Rate limit exceeded. Retry after X seconds"}` | Rate limited |
| 500 | `{"detail": "Internal server error"}` | Unhandled exception |
| 503 | `{"detail": "Service unavailable"}` | Pipeline/dependency down |

Rate limit: 100 requests/min per user (burst: 200). WebSocket: max 5 concurrent connections per user.
