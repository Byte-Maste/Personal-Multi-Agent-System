# Database Schema Documentation — PS-05 Personal Finance Agent

## Overview
Complete PostgreSQL schema for the PS-05 Personal Finance Agent platform. Designed for Supabase (PostgreSQL 15+) with Row-Level Security (RLS), real-time subscriptions, and full-text search support.

---

## Table: `users`

Stores user accounts and authentication metadata.

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE NOT NULL,
    phone           TEXT UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    avatar_url      TEXT,
    onb_complete    BOOLEAN DEFAULT FALSE,
    monthly_income  NUMERIC(12,2),
    currency        TEXT DEFAULT 'INR',
    locale          TEXT DEFAULT 'en-IN',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    last_login_at   TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
COMMENT ON TABLE users IS 'User accounts and profile data';
```

**RLS:** `id = auth.uid()` for all operations.

---

## Table: `family_members`

Links family members to a primary user account for family finance aggregation.

```sql
CREATE TABLE family_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    member_user_id  UUID REFERENCES users(id) ON DELETE SET NULL,
    member_name     TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('self','spouse','parent','child','sibling','other')),
    relationship    TEXT,
    sharing_level   TEXT NOT NULL DEFAULT 'summary'
                        CHECK (sharing_level IN ('full','summary','goals_only','none')),
    is_dependent    BOOLEAN DEFAULT FALSE,
    monthly_income  NUMERIC(12,2),
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_family_primary ON family_members(primary_user_id);
CREATE INDEX idx_family_member ON family_members(member_user_id);
COMMENT ON TABLE family_members IS 'Links family members to a primary user for aggregation';
```

**RLS:** `primary_user_id = auth.uid()` for read/write.

---

## Table: `statements`

Tracks uploaded bank/credit card statements with processing status.

```sql
CREATE TABLE statements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_name       TEXT NOT NULL,
    file_type       TEXT NOT NULL CHECK (file_type IN ('pdf','csv','xlsx','image')),
    file_size_bytes INTEGER,
    source          TEXT NOT NULL CHECK (source IN (
                        'hdfc','icici','sbi','axis','idfc','yes_bank',
                        'kotak','amex','citi','other_bank','manual_csv'
                    )),
    statement_month DATE NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','processing','completed','failed','partial')),
    error_message   TEXT,
    tx_count        INTEGER DEFAULT 0,
    total_amount    NUMERIC(12,2),
    processed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_statements_user ON statements(user_id);
CREATE INDEX idx_statements_status ON statements(status);
CREATE INDEX idx_statements_month ON statements(statement_month);
COMMENT ON TABLE statements IS 'Uploaded financial statements and processing status';
```

**RLS:** `user_id = auth.uid()` for all operations.

---

## Table: `categories`

Predefined and user-defined transaction categories.

```sql
CREATE TABLE categories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    icon            TEXT,
    color           TEXT,
    parent_id       UUID REFERENCES categories(id) ON DELETE SET NULL,
    is_system       BOOLEAN DEFAULT FALSE,
    budget_type     TEXT CHECK (budget_type IN ('need','want','saving','income')),
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX idx_categories_user_name ON categories(user_id, name) WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX idx_categories_system_name ON categories(name) WHERE user_id IS NULL;
COMMENT ON TABLE categories IS 'Transaction categories (system + user-defined)';
```

**RLS:** `user_id IS NULL OR user_id = auth.uid()` — system categories visible to all.

---

## Table: `transactions`

Core transaction records parsed from statements, enriched with categories and flags.

```sql
CREATE TABLE transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    statement_id    UUID REFERENCES statements(id) ON DELETE SET NULL,
    category_id     UUID REFERENCES categories(id) ON DELETE SET NULL,
    tx_date         DATE NOT NULL,
    description     TEXT NOT NULL,
    merchant        TEXT,
    amount          NUMERIC(12,2) NOT NULL,
    tx_type         TEXT NOT NULL CHECK (tx_type IN ('debit','credit','transfer')),
    currency        TEXT DEFAULT 'INR',
    tx_mode         TEXT CHECK (tx_mode IN (
                        'upi','neft','rtgs','imps','card','cheque','cash','auto_debit','wallet','other'
                    )),
    is_recurring    BOOLEAN DEFAULT FALSE,
    is_flagged      BOOLEAN DEFAULT FALSE,
    flag_reason     TEXT,
    notes           TEXT,
    tags            TEXT[] DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tx_user_date ON transactions(user_id, tx_date DESC);
CREATE INDEX idx_tx_category ON transactions(category_id);
CREATE INDEX idx_tx_merchant ON transactions(merchant);
CREATE INDEX idx_tx_recurring ON transactions(user_id, is_recurring) WHERE is_recurring = TRUE;
CREATE INDEX idx_tx_flagged ON transactions(user_id, is_flagged) WHERE is_flagged = TRUE;
CREATE INDEX idx_tx_tags ON transactions USING GIN(tags);
COMMENT ON TABLE transactions IS 'Categorized and enriched transaction records';
```

**RLS:** `user_id = auth.uid()` for all operations.

---

## Table: `budgets`

Monthly budget envelopes per user.

```sql
CREATE TABLE budgets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id     UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    month           DATE NOT NULL,
    limit_amount    NUMERIC(12,2) NOT NULL CHECK (limit_amount > 0),
    spent_amount    NUMERIC(12,2) DEFAULT 0,
    rollover_from   NUMERIC(12,2) DEFAULT 0,
    is_auto_generated BOOLEAN DEFAULT TRUE,
    is_user_override BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_user_category_month UNIQUE (user_id, category_id, month)
);

CREATE INDEX idx_budgets_user_month ON budgets(user_id, month DESC);
COMMENT ON TABLE budgets IS 'Monthly budget envelopes per category';
```

**RLS:** `user_id = auth.uid()` for all operations.

---

## Table: `goals`

User-defined financial goals with tracking.

```sql
CREATE TABLE goals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_id       UUID REFERENCES family_members(id) ON DELETE SET NULL,
    goal_type       TEXT NOT NULL CHECK (goal_type IN (
                        'emergency_fund','debt_payoff','large_purchase','investment','education','retirement','other'
                    )),
    name            TEXT NOT NULL,
    target_amount   NUMERIC(12,2) NOT NULL CHECK (target_amount > 0),
    current_amount  NUMERIC(12,2) DEFAULT 0,
    target_date     DATE NOT NULL,
    monthly_target  NUMERIC(12,2),
    priority        INTEGER DEFAULT 1 CHECK (priority >= 1),
    status          TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','paused','completed','overdue','cancelled')),
    inflation_rate  NUMERIC(5,4) DEFAULT 0,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_goals_user ON goals(user_id);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_family ON goals(family_id);
COMMENT ON TABLE goals IS 'Financial goals with progress tracking';
```

**RLS:** `user_id = auth.uid()` for all operations.

---

## Table: `subscriptions`

Detected and user-tracked recurring subscriptions.

```sql
CREATE TABLE subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    merchant        TEXT NOT NULL,
    amount          NUMERIC(12,2) NOT NULL,
    frequency       TEXT NOT NULL CHECK (frequency IN ('monthly','quarterly','half_yearly','yearly')),
    category        TEXT NOT NULL,
    is_essential    BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    is_unused       BOOLEAN DEFAULT FALSE,
    last_paid_date  DATE,
    next_billing_date DATE,
    detected_by     TEXT DEFAULT 'auto' CHECK (detected_by IN ('auto','manual')),
    annual_savings  NUMERIC(12,2) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_subs_user ON subscriptions(user_id);
CREATE INDEX idx_subs_active ON subscriptions(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_subs_unused ON subscriptions(user_id, is_unused) WHERE is_unused = TRUE;
COMMENT ON TABLE subscriptions IS 'Recurring subscriptions and usage tracking';
```

**RLS:** `user_id = auth.uid()` for all operations.

---

## Table: `alerts`

System-generated alerts and user notifications.

```sql
CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_type      TEXT NOT NULL CHECK (alert_type IN (
                        'budget_risk','budget_exceeded','anomaly','unused_subscription',
                        'low_balance','goal_off_track','goal_critical','dti_warning',
                        'readiness_blocker','family_imbalance','scenario_risk','health_drop'
                    )),
    severity        TEXT NOT NULL CHECK (severity IN ('info','warning','critical')),
    title           TEXT NOT NULL,
    message         TEXT NOT NULL,
    data            JSONB DEFAULT '{}'::jsonb,
    is_read         BOOLEAN DEFAULT FALSE,
    is_dismissed    BOOLEAN DEFAULT FALSE,
    source_agent    TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_alerts_user ON alerts(user_id, created_at DESC);
CREATE INDEX idx_alerts_unread ON alerts(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_alerts_severity ON alerts(severity);
COMMENT ON TABLE alerts IS 'System-generated alerts and user notifications';
```

**RLS:** `user_id = auth.uid()` for all operations.

---

## Table: `scenarios`

Persisted scenario simulation results from Life Event Simulator and Financial Twin agents.

```sql
CREATE TABLE scenarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    twin_id         UUID REFERENCES scenarios(id) ON DELETE SET NULL,
    scenario_type   TEXT NOT NULL CHECK (scenario_type IN (
                        'life_event','financial_twin','what_if'
                    )),
    label           TEXT NOT NULL,
    event_params    JSONB NOT NULL,
    before_snapshot JSONB NOT NULL,
    after_snapshot  JSONB NOT NULL,
    impact_metrics  JSONB NOT NULL,
    risk_flags      JSONB DEFAULT '[]'::jsonb,
    cashflow_12mo   JSONB DEFAULT '[]'::jsonb,
    is_baseline     BOOLEAN DEFAULT FALSE,
    parent_branch   UUID REFERENCES scenarios(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_scenarios_user ON scenarios(user_id);
CREATE INDEX idx_scenarios_type ON scenarios(scenario_type);
CREATE INDEX idx_scenarios_twin ON scenarios(twin_id);
COMMENT ON TABLE scenarios IS 'Persisted scenario simulations and what-if branches';
```

**RLS:** `user_id = auth.uid()` for all operations.

---

## Table: `financial_health_reports`

Historical snapshots of financial health scores.

```sql
CREATE TABLE financial_health_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score           INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    breakdown       JSONB NOT NULL,
    top_drags       JSONB DEFAULT '[]'::jsonb,
    trend           TEXT CHECK (trend IN ('improved','declined','stable','first_report')),
    report_month    DATE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_user_month UNIQUE (user_id, report_month)
);

CREATE INDEX idx_health_user ON financial_health_reports(user_id, report_month DESC);
COMMENT ON TABLE financial_health_reports IS 'Monthly financial health score snapshots';
```

**RLS:** `user_id = auth.uid()` for all operations.

---

## Table: `agent_runs`

Audit log of agent execution runs with inputs, outputs, and timing.

```sql
CREATE TABLE agent_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id      TEXT NOT NULL,
    agent_name      TEXT NOT NULL,
    pipeline_stage  TEXT,
    input_snapshot  JSONB,
    output_snapshot JSONB,
    status          TEXT NOT NULL DEFAULT 'running'
                        CHECK (status IN ('running','success','error','timeout','partial')),
    error_message   TEXT,
    retry_count     INTEGER DEFAULT 0,
    started_at      TIMESTAMPTZ DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    duration_ms     INTEGER
);

CREATE INDEX idx_agent_user ON agent_runs(user_id);
CREATE INDEX idx_agent_session ON agent_runs(session_id);
CREATE INDEX idx_agent_name ON agent_runs(agent_name);
CREATE INDEX idx_agent_status ON agent_runs(status);
COMMENT ON TABLE agent_runs IS 'Audit log of agent execution runs';
```

**RLS:** `user_id = auth.uid()` for all operations.

---

## Relationship Diagram

```
users (1) ───────< statements (N)
users (1) ───────< transactions (N)
users (1) ───────< categories (N)       [user-defined categories]
users (1) ───────< budgets (N)
users (1) ───────< goals (N)
users (1) ───────< subscriptions (N)
users (1) ───────< alerts (N)
users (1) ───────< scenarios (N)
users (1) ───────< financial_health_reports (N)
users (1) ───────< agent_runs (N)

users (1) ───────< family_members (N)   [as primary_user_id]
users (1) ───────< family_members (N)   [as member_user_id, nullable]

statements (1) ──< transactions (N)
categories (1) ──< transactions (N)
categories (1) ──< budgets (N)
categories (1) ──< categories (N)       [self-referential: parent_id]

goals (1) ───────< family_members (N)   [via family_id, optional]

scenarios (1) ───< scenarios (N)        [self-referential: twin_id, parent_branch]
```

**Key Relationships:**
- `transactions.statement_id` → `statements.id` (SET NULL on statement delete)
- `transactions.category_id` → `categories.id` (SET NULL on category delete)
- `budgets.category_id` → `categories.id` (CASCADE on category delete)
- `budgets.user_id + category_id + month` → unique constraint prevents duplicate envelopes
- `family_members.primary_user_id` → `users.id` (CASCADE)
- `family_members.member_user_id` → `users.id` (SET NULL — member can delete their account)
- `goals.family_id` → `family_members.id` (SET NULL — optional link for shared goals)
- `scenarios.twin_id` → `scenarios.id` (self-referential for what-if branching)
- `scenarios.parent_branch` → `scenarios.id` (self-referential for branch lineage)

---

## Migration Notes (Supabase Cloud)

1. **UUID Generation:** All primary keys use `gen_random_uuid()`. Supabase's `auth.users` uses UUID; match this convention.

2. **Timestamps:** All tables use `TIMESTAMPTZ` (timestamptz) with `DEFAULT now()`. Supabase automatically manages `updated_at` via triggers if enabled. Add trigger:
   ```sql
   CREATE OR REPLACE FUNCTION update_updated_at()
   RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;
   ```
   Apply to all tables with `updated_at` column.

3. **Row-Level Security:** Enable RLS on all tables after creation:
   ```sql
   ALTER TABLE users ENABLE ROW LEVEL SECURITY;
   ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
   -- ... repeat for all tables
   ```
   RLS policies follow the pattern: `USING (user_id = auth.uid())` for user-owned tables. The `users` table uses `USING (id = auth.uid())`. System categories (where `user_id IS NULL`) allow select to all authenticated users.

4. **Real-Time Subscriptions:** Enable Supabase Realtime on `alerts` and `transactions` tables for live updates:
   ```sql
   ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
   ALTER PUBLICATION supabase_realtime ADD TABLE transactions;
   ```

5. **Full-Text Search:** For transaction description search, add a generated tsvector column:
   ```sql
   ALTER TABLE transactions ADD COLUMN search_vector TSVECTOR
       GENERATED ALWAYS AS (to_tsvector('english', description || ' ' || COALESCE(merchant, ''))) STORED;
   CREATE INDEX idx_tx_search ON transactions USING GIN(search_vector);
   ```

6. **Indexing Strategy:**
   - All foreign key columns are indexed
   - All columns used in WHERE/ORDER BY are indexed (user_id, date ranges, status)
   - GIN indexes for JSONB (metadata) and array (tags) columns
   - Partial indexes for filtered queries (is_active, is_read, is_flagged)
   - Unique composite indexes prevent duplicates (user + category + month for budgets; user + month for health reports)

7. **Data Retention:**
   - `agent_runs`: retain 90 days (can be purged)
   - `scenarios`: retain 180 days
   - `financial_health_reports`: retain indefinitely (history)
   - `transactions`: retain indefinitely (financial record)
   - `alerts`: auto-delete read + dismissed after 90 days via cron job

8. **Supabase CLI Migration:**
   ```bash
   supabase migration new create_tables
   # Paste SQL into <timestamp>_create_tables.sql
   supabase db push
   ```

9. **Storage:** Statement PDF/CSV files stored in Supabase Storage bucket `statements` with RLS policy: `bucket_id = 'statements' AND auth.uid() = owner`. File path pattern: `{user_id}/{statement_id}/{file_name}`.

10. **Seed Data:** Insert system categories on migration apply:
    ```sql
    INSERT INTO categories (name, icon, color, is_system, budget_type, sort_order) VALUES
    ('Salary', '💰', '#22c55e', TRUE, 'income', 1),
    ('Rent', '🏠', '#ef4444', TRUE, 'need', 10),
    ('Groceries', '🛒', '#f97316', TRUE, 'need', 20),
    ('EMIs', '🏦', '#dc2626', TRUE, 'need', 30),
    ('Utilities', '⚡', '#eab308', TRUE, 'need', 40),
    ('Dining Out', '🍽️', '#ec4899', TRUE, 'want', 50),
    ('Entertainment', '🎬', '#a855f7', TRUE, 'want', 60),
    ('Shopping', '🛍️', '#06b6d4', TRUE, 'want', 70),
    ('Transport', '🚗', '#84cc16', TRUE, 'need', 80),
    ('Healthcare', '🏥', '#14b8a6', TRUE, 'need', 90),
    ('Education', '📚', '#8b5cf6', TRUE, 'need', 100),
    ('Savings', '🏦', '#22c55e', TRUE, 'saving', 110),
    ('Investments', '📈', '#3b82f6', TRUE, 'saving', 120),
    ('Insurance', '🛡️', '#6366f1', TRUE, 'need', 130),
    ('Subscriptions', '📺', '#d946ef', TRUE, 'want', 140),
    ('Income Tax', '📋', '#f43f5e', TRUE, 'need', 150),
    ('Transfer', '🔄', '#64748b', TRUE, 'saving', 160),
    ('Uncategorized', '❓', '#94a3b8', TRUE, 'need', 999);
    ```
