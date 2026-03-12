# InsightFlow — Database Schema

## 1. Design Principles

- **Multi-tenant isolation:** Every table includes `workspace_id`; Row-Level Security (RLS) enforced
- **UUID primary keys:** Non-guessable, globally unique
- **Soft deletes:** `deleted_at` timestamp instead of physical deletion (critical data)
- **Audit fields:** `created_at`, `updated_at` on every table
- **Normalized schema:** 3NF with strategic denormalization for read performance

## 2. Entity Relationship Diagram

```
┌──────────┐     ┌───────────────┐     ┌──────────────┐
│  users   │────▶│  memberships  │◀────│  workspaces  │
└──────────┘     └───────────────┘     └──────┬───────┘
                                              │
                         ┌────────────────────┼────────────────────┐
                         │                    │                    │
                         ▼                    ▼                    ▼
                  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
                  │  clients     │    │  connections  │    │  invitations │
                  └──────┬───────┘    └──────┬───────┘    └──────────────┘
                         │                   │
                    ┌────┴────┐              │
                    │         │              │
                    ▼         ▼              ▼
             ┌──────────┐ ┌────────┐  ┌──────────────┐
             │ reports  │ │campaigns│  │  sync_jobs   │
             └────┬─────┘ └───┬────┘  └──────────────┘
                  │           │
                  ▼           ▼
          ┌──────────────┐ ┌──────────────┐
          │report_sections│ │  metrics     │
          └──────────────┘ └──────────────┘
```

## 3. Table Definitions

### 3.1 users
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255),          -- NULL for OAuth-only users
    full_name       VARCHAR(255) NOT NULL,
    avatar_url      VARCHAR(500),
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    auth_provider   VARCHAR(50) NOT NULL DEFAULT 'email',  -- 'email', 'google'
    provider_id     VARCHAR(255),          -- External provider user ID
    last_login_at   TIMESTAMPTZ,
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_provider ON users(auth_provider, provider_id) WHERE deleted_at IS NULL;
```

### 3.2 workspaces
```sql
CREATE TABLE workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) NOT NULL UNIQUE,
    owner_id        UUID NOT NULL REFERENCES users(id),
    plan            VARCHAR(50) NOT NULL DEFAULT 'starter',  -- 'starter', 'growth', 'agency', 'enterprise'
    settings        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_workspaces_slug ON workspaces(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_workspaces_owner ON workspaces(owner_id);
```

### 3.3 memberships
```sql
CREATE TABLE memberships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id),
    role            VARCHAR(50) NOT NULL DEFAULT 'member',  -- 'owner', 'admin', 'member', 'viewer'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, workspace_id)
);

CREATE INDEX idx_memberships_workspace ON memberships(workspace_id);
CREATE INDEX idx_memberships_user ON memberships(user_id);
```

### 3.4 invitations
```sql
CREATE TABLE invitations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id),
    email           VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'member',
    invited_by      UUID NOT NULL REFERENCES users(id),
    token           VARCHAR(255) NOT NULL UNIQUE,
    expires_at      TIMESTAMPTZ NOT NULL,
    accepted_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_invitations_token ON invitations(token) WHERE accepted_at IS NULL;
CREATE INDEX idx_invitations_workspace ON invitations(workspace_id);
```

### 3.5 clients
```sql
CREATE TABLE clients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id),
    name            VARCHAR(255) NOT NULL,
    industry        VARCHAR(100),
    website         VARCHAR(500),
    notes           TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'active',  -- 'active', 'paused', 'archived'
    settings        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_clients_workspace ON clients(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_clients_workspace_name ON clients(workspace_id, name) WHERE deleted_at IS NULL;
```

### 3.6 connections (Platform Integrations)
```sql
CREATE TABLE connections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id),
    platform        VARCHAR(50) NOT NULL,  -- 'meta_ads', 'google_ads', 'ga4', 'shopify'
    account_id      VARCHAR(255) NOT NULL,  -- Platform-specific account ID
    account_name    VARCHAR(255),
    encrypted_access_token  BYTEA NOT NULL,
    encrypted_refresh_token BYTEA,
    wrapped_dek     BYTEA NOT NULL,         -- Wrapped data encryption key
    token_expires_at TIMESTAMPTZ,
    scopes          TEXT[],
    status          VARCHAR(50) NOT NULL DEFAULT 'active',  -- 'active', 'expired', 'revoked', 'error'
    last_synced_at  TIMESTAMPTZ,
    sync_frequency  VARCHAR(50) NOT NULL DEFAULT 'daily',  -- 'hourly', 'daily', 'weekly'
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(workspace_id, platform, account_id)
);

CREATE INDEX idx_connections_workspace ON connections(workspace_id);
CREATE INDEX idx_connections_status ON connections(status) WHERE status = 'active';
```

### 3.7 client_connections (Many-to-Many: Clients ↔ Connections)
```sql
CREATE TABLE client_connections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID NOT NULL REFERENCES clients(id),
    connection_id   UUID NOT NULL REFERENCES connections(id),
    platform_entity_id VARCHAR(255),  -- e.g., Meta ad account ID mapped to this client
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(client_id, connection_id)
);

CREATE INDEX idx_client_connections_client ON client_connections(client_id);
CREATE INDEX idx_client_connections_connection ON client_connections(connection_id);
```

### 3.8 campaigns
```sql
CREATE TABLE campaigns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id),
    client_id       UUID NOT NULL REFERENCES clients(id),
    connection_id   UUID NOT NULL REFERENCES connections(id),
    platform        VARCHAR(50) NOT NULL,
    platform_campaign_id VARCHAR(255) NOT NULL,
    name            VARCHAR(500) NOT NULL,
    status          VARCHAR(50),   -- 'active', 'paused', 'completed', etc.
    campaign_type   VARCHAR(100),  -- 'search', 'display', 'video', 'shopping', etc.
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(connection_id, platform_campaign_id)
);

CREATE INDEX idx_campaigns_client ON campaigns(client_id);
CREATE INDEX idx_campaigns_workspace ON campaigns(workspace_id);
```

### 3.9 metrics (Partitioned)
```sql
CREATE TABLE metrics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id),
    client_id       UUID NOT NULL REFERENCES clients(id),
    campaign_id     UUID REFERENCES campaigns(id),
    connection_id   UUID NOT NULL REFERENCES connections(id),
    platform        VARCHAR(50) NOT NULL,
    date            DATE NOT NULL,
    granularity     VARCHAR(20) NOT NULL DEFAULT 'daily',  -- 'hourly', 'daily'

    -- Core metrics (unified across platforms)
    impressions     BIGINT NOT NULL DEFAULT 0,
    clicks          BIGINT NOT NULL DEFAULT 0,
    spend           DECIMAL(12,2) NOT NULL DEFAULT 0,
    conversions     INTEGER NOT NULL DEFAULT 0,
    conversion_value DECIMAL(12,2) NOT NULL DEFAULT 0,

    -- Derived metrics (computed on insert)
    ctr             DECIMAL(8,4),   -- clicks / impressions
    cpc             DECIMAL(8,2),   -- spend / clicks
    cpa             DECIMAL(8,2),   -- spend / conversions
    roas            DECIMAL(8,2),   -- conversion_value / spend

    -- Platform-specific extended metrics
    platform_data   JSONB NOT NULL DEFAULT '{}',

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(campaign_id, date, granularity)
) PARTITION BY RANGE (date);

-- Create monthly partitions
CREATE TABLE metrics_2026_01 PARTITION OF metrics FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE metrics_2026_02 PARTITION OF metrics FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE metrics_2026_03 PARTITION OF metrics FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
-- ... auto-create future partitions via pg_partman or migration

CREATE INDEX idx_metrics_client_date ON metrics(client_id, date);
CREATE INDEX idx_metrics_workspace_date ON metrics(workspace_id, date);
CREATE INDEX idx_metrics_campaign_date ON metrics(campaign_id, date);
```

### 3.10 reports
```sql
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id),
    client_id       UUID NOT NULL REFERENCES clients(id),
    generated_by    UUID NOT NULL REFERENCES users(id),
    template        VARCHAR(100) NOT NULL DEFAULT 'monthly_performance',
    title           VARCHAR(500) NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'generating',  -- 'generating', 'completed', 'failed'
    date_range_start DATE NOT NULL,
    date_range_end  DATE NOT NULL,
    comparison_period VARCHAR(50),  -- 'previous_period', 'previous_year'
    platforms       TEXT[] NOT NULL,
    tone            VARCHAR(50) NOT NULL DEFAULT 'executive',
    pdf_url         VARCHAR(500),
    error_message   TEXT,
    ai_model        VARCHAR(100),
    ai_tokens_used  INTEGER,
    generation_time_ms INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_reports_workspace ON reports(workspace_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_reports_client ON reports(client_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_reports_status ON reports(status) WHERE status = 'generating';
```

### 3.11 report_sections
```sql
CREATE TABLE report_sections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    section_type    VARCHAR(100) NOT NULL,  -- 'executive_summary', 'metrics_overview', 'insights', 'recommendations'
    title           VARCHAR(255) NOT NULL,
    content         TEXT,           -- AI-generated narrative content
    data            JSONB,          -- Structured data for charts/tables
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_report_sections_report ON report_sections(report_id);
```

### 3.12 sync_jobs
```sql
CREATE TABLE sync_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id),
    connection_id   UUID NOT NULL REFERENCES connections(id),
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    sync_type       VARCHAR(50) NOT NULL DEFAULT 'incremental',  -- 'full', 'incremental', 'backfill'
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    records_synced  INTEGER DEFAULT 0,
    error_message   TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sync_jobs_connection ON sync_jobs(connection_id);
CREATE INDEX idx_sync_jobs_status ON sync_jobs(status) WHERE status IN ('pending', 'running');
```

### 3.13 audit_logs
```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    user_id         UUID,
    action          VARCHAR(100) NOT NULL,  -- 'user.login', 'report.generate', 'connection.create'
    resource_type   VARCHAR(100),
    resource_id     UUID,
    ip_address      INET,
    user_agent      TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE INDEX idx_audit_logs_workspace ON audit_logs(workspace_id, created_at);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at);
```

## 4. Row-Level Security (RLS)

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Example policy: users can only see data from their workspace
CREATE POLICY workspace_isolation ON clients
    USING (workspace_id = current_setting('app.current_workspace_id')::UUID);

CREATE POLICY workspace_isolation ON connections
    USING (workspace_id = current_setting('app.current_workspace_id')::UUID);

-- Application sets this at the start of each request:
-- SET LOCAL app.current_workspace_id = 'ws_abc123';
```

## 5. Indexes Summary

Key query patterns and their supporting indexes:
| Query Pattern | Index |
|--------------|-------|
| Client list for workspace | `idx_clients_workspace` |
| Metrics by client + date range | `idx_metrics_client_date` |
| Reports for a client | `idx_reports_client` |
| Active connections | `idx_connections_status` |
| Pending sync jobs | `idx_sync_jobs_status` |
| Audit trail for user | `idx_audit_logs_user` |
