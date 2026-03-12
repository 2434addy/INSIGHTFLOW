# InsightFlow — Backend API Architecture

## Framework & Stack

| Layer | Tool | Version |
|-------|------|---------|
| Web Framework | FastAPI | 0.115+ |
| ORM | SQLAlchemy 2.0 (async) | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Database | PostgreSQL (RLS, partitioning) | 16 |
| Cache / Broker | Redis | 7+ |
| Task Queue | Celery | 5.4+ |
| Validation | Pydantic v2 | 2.9+ |
| Auth | JWT (PyJWT) + bcrypt | — |
| AI | Anthropic Claude API | — |
| HTTP Client | httpx (async) | 0.27+ |
| Logging | structlog (JSON) | — |
| Testing | pytest + pytest-asyncio | — |

---

## Project Structure

Legend: `[E]` = exists, `[P]` = planned

```
backend/
├── alembic/                                [P] Database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│       ├── 001_initial_schema.py          [P] All tables + RLS policies
│       └── 002_partitions.py              [P] Monthly metric partitions
│
├── app/
│   ├── __init__.py                        [E]
│   ├── main.py                            [E] FastAPI app factory + lifespan
│   │
│   ├── core/                              ─── Framework layer ───
│   │   ├── config.py                      [E] Pydantic Settings (env-based)
│   │   ├── database.py                    [E] Async engine, session factory, get_db()
│   │   ├── security.py                    [E] JWT create/decode, bcrypt hash/verify
│   │   ├── exceptions.py                  [E] Domain exceptions (NotFound, Forbidden, etc.)
│   │   ├── logging.py                     [E] structlog setup (JSON/console)
│   │   └── redis.py                       [P] Redis client factory, cache helpers
│   │
│   ├── middleware/                         ─── Request pipeline ───
│   │   ├── error_handler.py               [E] RFC 7807 error responses
│   │   ├── request_context.py             [E] X-Request-ID → structlog binding
│   │   ├── rate_limiter.py                [P] Token-bucket per endpoint class
│   │   └── workspace_context.py           [P] SET LOCAL app.current_workspace_id
│   │
│   ├── api/                               ─── HTTP layer ───
│   │   ├── deps.py                        [E] get_current_user, get_current_organization, require_role
│   │   └── v1/
│   │       ├── router.py                  [E] Aggregates all endpoint routers
│   │       └── endpoints/
│   │           ├── health.py              [E] GET /v1/health
│   │           ├── auth.py                [E] register, login, me (partial)
│   │           ├── workspaces.py          [P] CRUD + members
│   │           ├── clients.py             [P] CRUD + metrics + campaigns
│   │           ├── campaigns.py           [P] List, detail, tier classification
│   │           ├── metrics.py             [P] Summary, daily, by-platform
│   │           ├── integrations.py        [P] OAuth flows, connections, sync
│   │           ├── reports.py             [P] Generate, list, detail, PDF
│   │           ├── insights.py            [P] List with filters
│   │           ├── recommendations.py     [P] List with filters
│   │           └── dashboard.py           [P] Overview, trends, alerts
│   │
│   ├── schemas/                           ─── Request/Response contracts ───
│   │   ├── common.py                      [E] SuccessResponse[T], ErrorResponse, PaginatedResponse[T]
│   │   ├── auth.py                        [E] RegisterRequest, LoginRequest, TokenResponse
│   │   ├── workspace.py                   [P] WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
│   │   ├── client.py                      [P] ClientCreate, ClientResponse, ClientMetrics
│   │   ├── campaign.py                    [P] CampaignResponse, CampaignFilter
│   │   ├── metric.py                      [P] MetricSummary, MetricTimeseries, PlatformBreakdown
│   │   ├── integration.py                 [P] ConnectionResponse, SyncStatus, OAuthInit
│   │   ├── report.py                      [P] GenerateRequest, ReportResponse, ReportDetail
│   │   ├── insight.py                     [P] InsightResponse, InsightFilter
│   │   └── recommendation.py              [P] RecommendationResponse
│   │
│   ├── services/                          ─── Business logic ───
│   │   ├── auth_service.py                [E] register, login, get_user_organizations
│   │   ├── client_service.py              [P] CRUD, metrics aggregation, campaign listing
│   │   ├── campaign_service.py            [P] List with tiers, detail, filter/sort
│   │   ├── metric_service.py              [P] Summary, timeseries, platform breakdown, comparison
│   │   ├── integration_service.py         [P] OAuth initiation, callback, disconnect, sync trigger
│   │   ├── report_service.py              [P] Generate (queue), list, detail, PDF assembly
│   │   ├── insight_service.py             [P] List/filter persisted insights
│   │   ├── dashboard_service.py           [P] Cross-client aggregation, alerts
│   │   └── ingestion/                     ─── Platform data sync ───
│   │       ├── __init__.py                [E]
│   │       ├── base_connector.py          [E] Abstract connector + rate limiter + circuit breaker
│   │       ├── meta_ads.py                [E] Meta Marketing API connector
│   │       ├── google_ads.py              [E] Google Ads API connector
│   │       ├── google_analytics.py        [E] GA4 Data API connector
│   │       ├── shopify.py                 [E] Shopify Admin API connector
│   │       ├── normalizer.py              [E] Raw → unified MetricRecord transform
│   │       └── ingestion_service.py       [E] Sync orchestration (fetch → normalize → upsert)
│   │
│   ├── repositories/                      ─── Data access ───
│   │   ├── user_repository.py             [E] get_by_id, get_by_email, create
│   │   ├── organization_repository.py     [E] get_by_id, get_by_slug, get_membership
│   │   ├── client_repository.py           [P] CRUD, search, list with pagination
│   │   ├── campaign_repository.py         [P] List by client/workspace, filter by status/platform
│   │   ├── metric_repository.py           [P] Aggregated queries, timeseries, platform breakdown
│   │   ├── connection_repository.py       [P] CRUD, get by platform, update sync status
│   │   ├── report_repository.py           [P] CRUD, list with status filter, update status
│   │   ├── insight_repository.py          [P] Bulk create, list by report/workspace
│   │   └── recommendation_repository.py   [P] Bulk create, list by report/workspace
│   │
│   ├── models/                            ─── SQLAlchemy ORM ───
│   │   ├── __init__.py                    [E] Re-exports all models
│   │   ├── base.py                        [E] Base, TimestampMixin, SoftDeleteMixin, BaseModel
│   │   ├── user.py                        [E] User
│   │   ├── organization.py                [E] Organization, Membership
│   │   ├── data_source_connection.py      [E] DataSourceConnection
│   │   ├── campaign.py                    [E] Campaign
│   │   ├── ad_set.py                      [E] AdSet
│   │   ├── ad.py                          [E] Ad
│   │   ├── metrics.py                     [E] Metrics (partitioned by date)
│   │   ├── report.py                      [E] Report
│   │   ├── insight.py                     [E] Insight
│   │   ├── recommendation.py              [E] Recommendation
│   │   ├── client.py                      [P] Client
│   │   ├── client_connection.py           [P] ClientConnection (M2M junction)
│   │   ├── invitation.py                  [P] Invitation
│   │   ├── sync_job.py                    [P] SyncJob
│   │   └── audit_log.py                   [P] AuditLog (partitioned by created_at)
│   │
│   ├── tasks/                             ─── Celery background jobs ───
│   │   ├── __init__.py                    [P] Celery app factory
│   │   ├── celery_app.py                  [P] Celery instance + config
│   │   ├── report_tasks.py               [P] generate_report, retry_failed_reports
│   │   ├── sync_tasks.py                 [P] sync_connection, sync_all_active
│   │   └── maintenance_tasks.py          [P] create_partitions, cleanup_expired_tokens
│   │
│   ├── pipeline/                          ─── AI analytics pipeline ───
│   │   ├── __init__.py                    [E]
│   │   ├── schemas.py                     [E] 30+ Pydantic models for inter-stage contracts
│   │   └── orchestrator.py                [E] DAG execution: 8 stages, parallel 3+4
│   │
│   ├── agents/                            ─── Pipeline stage executors ───
│   │   ├── __init__.py                    [E]
│   │   ├── base.py                        [E] BaseAgent[InputT, OutputT] with retry + timing
│   │   ├── data_validation_agent.py       [E] Stage 1: validate raw metric records
│   │   ├── kpi_computation_agent.py       [E] Stage 2: derive KPIs + period comparison
│   │   ├── trend_detection_agent.py       [E] Stage 3: linear regression + pacing
│   │   ├── anomaly_detection_agent.py     [E] Stage 4: z-score + contextual anomalies
│   │   ├── campaign_evaluation_agent.py   [E] Stage 5: tier classification + budget assessment
│   │   ├── insight_generation_agent.py    [E] Stage 6: Claude API → insights + executive summary
│   │   ├── recommendation_agent.py        [E] Stage 7: Claude API → recommendations
│   │   └── report_generation_agent.py     [E] Stage 8: assemble PipelineResult
│   │
│   └── skills/                            ─── Reusable computation modules ───
│       ├── __init__.py                    [E]
│       ├── semantic_metric_layer.py       [E] Metric definitions, formatters, benchmarks
│       ├── kpi_computation.py             [E] KPIComputer, Aggregator, PeriodComparer, EfficiencyScorer
│       ├── trend_detection.py             [E] LinearRegression, MovingAverage, TrendClassifier, Pacing
│       ├── anomaly_detection.py           [E] ZScore, IQR, Contextual, CorrelationBreak, MissingData
│       ├── campaign_evaluation.py         [E] TierClassifier, BudgetAssessor, PlatformComparator
│       ├── data_quality_validation.py     [E] Raw, Normalized, Analysis, AI output validators
│       └── insight_summarization.py       [E] PromptBuilder, InsightParser, TemplateFallback
│
├── tests/
│   ├── conftest.py                        [P] Fixtures: async DB, test client, auth helpers
│   ├── test_pipeline.py                   [E] 23 tests (skills, agents, orchestrator)
│   ├── test_auth.py                       [P] Auth endpoints: register, login, refresh, me
│   ├── test_clients.py                    [P] Client CRUD + metrics
│   ├── test_campaigns.py                  [P] Campaign list, filter, sort
│   ├── test_reports.py                    [P] Generate, status, detail
│   ├── test_integrations.py              [P] OAuth flow, sync trigger
│   └── test_services/                     [P] Unit tests for service layer
│
├── database_schema.md                     [E] Full SQL DDL + RLS + indexes
├── api_design.md                          [E] REST conventions + endpoint specs
└── requirements.txt                       [E] Python dependencies
```

---

## 1. Database Models

### Entity Relationship Diagram

```
users ─────── memberships ──────── workspaces (organizations)
                                       │
              ┌──────────────┬─────────┼──────────┬──────────────┐
              │              │         │          │              │
           clients      connections  invitations  sync_jobs  audit_logs
              │              │
       client_connections ───┘
              │
     ┌────────┼────────┐
     │        │        │
  reports  campaigns  metrics (partitioned by date)
     │        │
     │     ┌──┴──┐
     │   ad_sets  │
     │     │      │
insights  ads     │
     │            │
recommendations ──┘
```

### Model Inventory

| Model | Table | Tenant-scoped | Soft Delete | Partitioned | Status |
|-------|-------|:---:|:---:|:---:|--------|
| `User` | `users` | — | Yes | — | **Exists** |
| `Organization` | `workspaces` | — | Yes | — | **Exists** |
| `Membership` | `memberships` | — | — | — | **Exists** |
| `Client` | `clients` | Yes | Yes | — | **Planned** |
| `DataSourceConnection` | `connections` | Yes | — | — | **Exists** |
| `ClientConnection` | `client_connections` | — | — | — | **Planned** |
| `Campaign` | `campaigns` | Yes | — | — | **Exists** |
| `AdSet` | `ad_sets` | Yes | — | — | **Exists** |
| `Ad` | `ads` | Yes | — | — | **Exists** |
| `Metrics` | `metrics` | Yes | — | Monthly | **Exists** |
| `Report` | `reports` | Yes | Yes | — | **Exists** |
| `Insight` | `report_sections` / `insights` | Yes | — | — | **Exists** |
| `Recommendation` | `recommendations` | Yes | — | — | **Exists** |
| `Invitation` | `invitations` | Yes | — | — | **Planned** |
| `SyncJob` | `sync_jobs` | Yes | — | — | **Planned** |
| `AuditLog` | `audit_logs` | Yes | — | Monthly | **Planned** |

### Row-Level Security

Every tenant-scoped table enforces isolation via PostgreSQL RLS:

```sql
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

CREATE POLICY workspace_isolation ON clients
    USING (workspace_id = current_setting('app.current_workspace_id')::UUID);
```

The `WorkspaceContextMiddleware` sets `app.current_workspace_id` on every request:

```python
# middleware/workspace_context.py
await session.execute(text(
    "SET LOCAL app.current_workspace_id = :ws_id"
), {"ws_id": str(workspace_id)})
```

---

## 2. API Endpoints

### Conventions

- **Base URL:** `/v1/` prefix on all routes
- **Auth:** `Authorization: Bearer <JWT>` header
- **Tenant:** `X-Organization-ID` header selects workspace
- **Responses:** `SuccessResponse[T]` envelope with `data` + `meta`
- **Errors:** RFC 7807 with `code`, `message`, `details[]`
- **Pagination:** Cursor-based (`?limit=20&cursor=abc`)
- **Sorting:** `?sort=field&order=asc|desc`
- **Rate limits:** Token-bucket per endpoint class, headers in response

### 2.1 Health

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/health` | — | DB + Redis connectivity check | **Exists** |

---

### 2.2 Authentication

| Method | Path | Auth | Request Body | Response | Status |
|--------|------|:----:|-------------|----------|--------|
| `POST` | `/v1/auth/register` | — | `RegisterRequest` | `201` `RegisterResponse` | **Exists** |
| `POST` | `/v1/auth/login` | — | `LoginRequest` | `200` `TokenResponse` + HttpOnly cookie | **Exists** |
| `POST` | `/v1/auth/refresh` | Cookie | — | `200` `TokenResponse` | **Planned** |
| `POST` | `/v1/auth/logout` | Yes | — | `204` | **Planned** |
| `GET` | `/v1/auth/me` | Yes | — | `200` `MeResponse` | **Exists** |
| `PUT` | `/v1/auth/me` | Yes | `UpdateProfileRequest` | `200` `MeResponse` | **Planned** |
| `POST` | `/v1/auth/forgot-password` | — | `ForgotPasswordRequest` | `202` | **Planned** |
| `POST` | `/v1/auth/reset-password` | — | `ResetPasswordRequest` | `200` | **Planned** |
| `GET` | `/v1/auth/oauth/:provider` | — | — | `302` redirect to provider | **Planned** |
| `GET` | `/v1/auth/oauth/:provider/callback` | — | — | `200` `TokenResponse` | **Planned** |

**Rate limit:** 5 req/min on `login`, `register`, `forgot-password`

---

### 2.3 Workspaces

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/workspaces` | Yes | List user's workspaces | **Planned** |
| `GET` | `/v1/workspaces/:id` | Yes | Workspace details | **Planned** |
| `PUT` | `/v1/workspaces/:id` | Admin | Update workspace name, settings | **Planned** |
| `DELETE` | `/v1/workspaces/:id` | Owner | Soft-delete workspace | **Planned** |

---

### 2.4 Team Members

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/workspaces/:id/members` | Yes | List members with roles | **Planned** |
| `POST` | `/v1/workspaces/:id/members/invite` | Admin | Send email invitation | **Planned** |
| `PUT` | `/v1/workspaces/:id/members/:uid` | Admin | Update member role | **Planned** |
| `DELETE` | `/v1/workspaces/:id/members/:uid` | Admin | Remove member | **Planned** |

---

### 2.5 Clients

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/clients` | Yes | List clients (paginated, searchable) | **Planned** |
| `POST` | `/v1/clients` | Yes | Create client | **Planned** |
| `GET` | `/v1/clients/:id` | Yes | Client detail with summary metrics | **Planned** |
| `PUT` | `/v1/clients/:id` | Yes | Update client | **Planned** |
| `DELETE` | `/v1/clients/:id` | Admin | Soft-delete client | **Planned** |
| `GET` | `/v1/clients/:id/metrics` | Yes | Client metrics with date range | **Planned** |
| `GET` | `/v1/clients/:id/campaigns` | Yes | Client's campaigns | **Planned** |

**Query params for `GET /v1/clients`:**

```
?limit=20&cursor=abc
&search=acme                    # name search
&status=active                  # active | paused | archived
&platform=meta_ads              # filter by connected platform
&sort=spend_30d&order=desc      # sort field + direction
```

**Response shape for `GET /v1/clients/:id/metrics`:**

```typescript
{
  data: {
    summary: KPISummary,            // spend, impressions, clicks, conversions, roas, cpa, ctr
    comparison: PeriodComparison,   // *_change_pct fields
    timeseries: DailyMetric[],      // date, spend, conversions, impressions, clicks
    by_platform: PlatformMetric[]   // platform, spend, conversions, roas
  }
}
```

---

### 2.6 Campaigns

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/campaigns` | Yes | List all campaigns (paginated, filtered) | **Planned** |
| `GET` | `/v1/campaigns/:id` | Yes | Campaign detail with metrics | **Planned** |

**Query params:**

```
?limit=20&cursor=abc
&client_id=uuid                 # filter by client
&platform=meta_ads              # filter by platform
&status=active                  # active | paused | completed
&tier=star                      # star | strong | average | underperformer | waster
&sort=efficiency_score&order=desc
```

**Response enrichments:**

The campaign list response includes computed fields not stored in the database:

```typescript
{
  // from campaigns table
  id, name, platform, status,
  // computed by CampaignService
  tier: CampaignTier,              // from TierClassifier
  efficiency_score: number,        // from EfficiencyScorer
  spend: number,                   // aggregated from metrics
  conversions: number,
  roas: number,
  cpa: number,
  ctr: number
}
```

---

### 2.7 Metrics

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/metrics/summary` | Yes | Aggregated KPIs for date range | **Planned** |
| `GET` | `/v1/metrics/daily` | Yes | Daily time series | **Planned** |
| `GET` | `/v1/metrics/by-platform` | Yes | Platform breakdown | **Planned** |

**Query params (shared):**

```
?start_date=2026-02-01
&end_date=2026-02-28
&client_id=uuid                 # optional — omit for workspace-wide
&platform=meta_ads              # optional — filter by platform
&compare=previous_period        # optional — include comparison
```

---

### 2.8 Integrations

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/integrations` | Yes | Available platforms + connection status | **Planned** |
| `GET` | `/v1/integrations/connections` | Yes | Active connections with sync info | **Planned** |
| `POST` | `/v1/integrations/connect/:platform` | Admin | Initiate OAuth → returns redirect URL | **Planned** |
| `GET` | `/v1/integrations/callback/:platform` | — | OAuth callback → store tokens | **Planned** |
| `DELETE` | `/v1/integrations/connections/:id` | Admin | Revoke + delete connection | **Planned** |
| `POST` | `/v1/integrations/connections/:id/sync` | Yes | Trigger manual data sync | **Planned** |
| `GET` | `/v1/integrations/connections/:id/status` | Yes | Sync job status | **Planned** |

**OAuth flow:**

```
1. Frontend calls POST /v1/integrations/connect/meta_ads
2. Backend returns { authorization_url: "https://facebook.com/dialog/oauth?..." }
3. User authorizes on platform
4. Platform redirects to GET /v1/integrations/callback/meta_ads?code=...
5. Backend exchanges code → tokens, encrypts, stores in connections table
6. Backend returns success, frontend redirects to /integrations
```

---

### 2.9 Reports

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/reports` | Yes | List reports (paginated, filterable) | **Planned** |
| `POST` | `/v1/reports/generate` | Yes | Queue report generation → returns `202` | **Planned** |
| `GET` | `/v1/reports/:id` | Yes | Report detail with sections, insights, recs | **Planned** |
| `GET` | `/v1/reports/:id/status` | Yes | Generation status + progress | **Planned** |
| `GET` | `/v1/reports/:id/pdf` | Yes | Download PDF | **Planned** |
| `PUT` | `/v1/reports/:id` | Yes | Edit AI-generated content | **Planned** |
| `DELETE` | `/v1/reports/:id` | Yes | Soft-delete report | **Planned** |

**Generate request:**

```json
{
  "client_id": "uuid",
  "date_range": { "start_date": "2026-02-01", "end_date": "2026-02-28" },
  "comparison_period": "previous_period",
  "platforms": ["meta_ads", "google_ads"],
  "tone": "executive",
  "sections": ["executive_summary", "metrics_overview", "insights", "recommendations"],
  "ai_model": "standard"
}
```

**Generate response (`202 Accepted`):**

```json
{
  "data": {
    "report_id": "uuid",
    "status": "generating",
    "estimated_seconds": 45
  }
}
```

**Status polling response:**

```json
{
  "data": {
    "status": "generating",
    "progress": {
      "percent": 62,
      "current_stage": "insight_generation",
      "stages": [
        { "name": "data_validation", "status": "done" },
        { "name": "kpi_computation", "status": "done" },
        { "name": "trend_detection", "status": "done" },
        { "name": "anomaly_detection", "status": "done" },
        { "name": "campaign_evaluation", "status": "done" },
        { "name": "insight_generation", "status": "running" },
        { "name": "recommendation", "status": "pending" },
        { "name": "report_assembly", "status": "pending" }
      ]
    }
  }
}
```

---

### 2.10 Insights & Recommendations

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/insights` | Yes | List insights across reports | **Planned** |
| `GET` | `/v1/recommendations` | Yes | List recommendations across reports | **Planned** |

**Query params:**

```
?client_id=uuid
&report_id=uuid
&category=performance            # performance | efficiency | anomaly | opportunity | risk
&sentiment=attention_needed
&priority=high
&limit=20&cursor=abc
```

---

### 2.11 Dashboard

| Method | Path | Auth | Description | Status |
|--------|------|:----:|-------------|--------|
| `GET` | `/v1/dashboard/overview` | Yes | Cross-client KPIs + comparison | **Planned** |
| `GET` | `/v1/dashboard/trends` | Yes | Aggregated daily time series | **Planned** |
| `GET` | `/v1/dashboard/alerts` | Yes | System alerts (sync failures, expiring tokens) | **Planned** |

---

## 3. Service Layer

Services encapsulate all business logic. They are injected into endpoint handlers and operate on repositories + external systems. Services never access `Request` or `Response` objects directly.

### Architecture Pattern

```
Endpoint (api/v1/endpoints/)
    │
    │   Validates request, extracts params
    │   Calls service method
    │   Returns SuccessResponse[T]
    │
    ▼
Service (services/)
    │
    │   Business logic, orchestration
    │   Calls one or more repositories
    │   Calls external services (AI, platform APIs)
    │   Enforces authorization rules
    │
    ▼
Repository (repositories/)
    │
    │   Single-table data access
    │   SQLAlchemy queries scoped to workspace_id
    │   Returns model instances
    │
    ▼
Model (models/)
    │
    │   SQLAlchemy ORM mapping
    │   Column definitions, relationships
    │   Computed properties
    │
    ▼
PostgreSQL (RLS enforced)
```

### Service Inventory

#### AuthService `[Exists]`

```python
class AuthService:
    def __init__(self, db: AsyncSession)

    async def register(email, password, full_name, agency_name) -> tuple[User, Organization]
    async def login(email, password) -> str                 # returns access_token
    async def refresh_token(refresh_token: str) -> str      # [planned]
    async def logout(user_id: UUID) -> None                 # [planned]
    async def get_user_organizations(user_id) -> list[Organization]
    async def update_profile(user_id, data) -> User         # [planned]
    async def forgot_password(email) -> None                # [planned]
    async def reset_password(token, new_password) -> None   # [planned]
```

#### ClientService `[Planned]`

```python
class ClientService:
    def __init__(self, db: AsyncSession)

    async def list(workspace_id, filters, pagination) -> PaginatedResponse[ClientResponse]
    async def create(workspace_id, data: ClientCreate) -> Client
    async def get(workspace_id, client_id) -> Client
    async def update(workspace_id, client_id, data: ClientUpdate) -> Client
    async def delete(workspace_id, client_id) -> None
    async def get_metrics(workspace_id, client_id, date_range, compare) -> ClientMetrics
    async def get_campaigns(workspace_id, client_id, filters) -> list[CampaignResponse]
```

#### CampaignService `[Planned]`

```python
class CampaignService:
    def __init__(self, db: AsyncSession)

    async def list(workspace_id, filters, pagination) -> PaginatedResponse[CampaignResponse]
    async def get(workspace_id, campaign_id) -> CampaignDetail
    async def compute_tiers(workspace_id, client_id) -> dict[str, list[TieredCampaign]]
```

Internally uses `TierClassifier`, `EfficiencyScorer`, and `BudgetAssessor` from the skills layer to enrich campaign records with computed fields (tier, efficiency_score).

#### MetricService `[Planned]`

```python
class MetricService:
    def __init__(self, db: AsyncSession)

    async def get_summary(workspace_id, date_range, client_id?, platform?) -> KPISummary
    async def get_daily(workspace_id, date_range, client_id?, platform?) -> list[DailyMetric]
    async def get_by_platform(workspace_id, date_range, client_id?) -> dict[str, KPISummary]
    async def get_comparison(workspace_id, date_range, compare_mode) -> PeriodComparison
```

Uses `KPIComputer` and `PeriodComparer` from skills layer for derived metric computation.

#### IntegrationService `[Planned]`

```python
class IntegrationService:
    def __init__(self, db: AsyncSession)

    async def list_platforms(workspace_id) -> list[PlatformStatus]
    async def list_connections(workspace_id) -> list[ConnectionResponse]
    async def initiate_oauth(workspace_id, platform) -> str    # returns authorization_url
    async def handle_callback(workspace_id, platform, code) -> Connection
    async def disconnect(workspace_id, connection_id) -> None
    async def trigger_sync(workspace_id, connection_id) -> SyncJob
    async def get_sync_status(workspace_id, connection_id) -> SyncStatus
```

Delegates to `IngestionService` (existing) for actual data sync. Uses envelope encryption for token storage.

#### ReportService `[Planned]`

```python
class ReportService:
    def __init__(self, db: AsyncSession)

    async def list(workspace_id, filters, pagination) -> PaginatedResponse[ReportResponse]
    async def generate(workspace_id, user_id, config: GenerateRequest) -> Report
        # 1. Validate config
        # 2. Create Report row with status='generating'
        # 3. Queue Celery task: generate_report.delay(report_id)
        # 4. Return report with status='generating'
    async def get(workspace_id, report_id) -> ReportDetail
    async def get_status(workspace_id, report_id) -> ReportStatus
    async def update(workspace_id, report_id, data) -> Report
    async def delete(workspace_id, report_id) -> None
    async def get_pdf_url(workspace_id, report_id) -> str
```

#### InsightService `[Planned]`

```python
class InsightService:
    def __init__(self, db: AsyncSession)

    async def list(workspace_id, filters, pagination) -> PaginatedResponse[InsightResponse]
    async def bulk_create(report_id, insights: list[GeneratedInsight]) -> list[Insight]
```

#### DashboardService `[Planned]`

```python
class DashboardService:
    def __init__(self, db: AsyncSession)

    async def get_overview(workspace_id, date_range) -> DashboardOverview
        # Aggregates across all clients in workspace
    async def get_trends(workspace_id, date_range) -> list[DailyMetric]
    async def get_alerts(workspace_id) -> list[Alert]
        # Expiring tokens, failed syncs, stale data, budget warnings
```

---

## 4. Analytics Pipeline

### Pipeline Architecture

The analytics pipeline transforms raw metric data into AI-generated insights and reports. It is implemented as a DAG-based orchestrator with 8 sequential stages (stages 3+4 run in parallel).

```
                    ┌─────────────────┐
                    │  ReportRequest   │
                    │  + MetricRecord[]│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
              ┌─────│ 1. Data         │
              │     │    Validation   │──── RawDataValidator (skill)
              │     └────────┬────────┘
              │              │
              │     ┌────────▼────────┐
              │     │ 2. KPI          │──── KPIComputer, Aggregator,
              │     │    Computation  │     PeriodComparer, EfficiencyScorer
              │     └────────┬────────┘
              │              │
              │         ┌────┴────┐
              │         │         │
              │  ┌──────▼──────┐ ┌▼──────────────┐
  Sequential  │  │ 3. Trend    │ │ 4. Anomaly    │  ← Parallel (asyncio.gather)
  execution   │  │    Detection│ │    Detection  │
              │  └──────┬──────┘ └┬──────────────┘
              │         │         │
              │         └────┬────┘
              │              │
              │     ┌────────▼────────┐
              │     │ 5. Campaign     │──── TierClassifier, BudgetAssessor,
              │     │    Evaluation   │     PlatformComparator
              │     └────────┬────────┘
              │              │
              │     ┌────────▼────────┐
              │     │ 6. Insight      │──── Claude API (or TemplateFallback)
              │     │    Generation   │     InsightPromptBuilder, InsightParser
              │     └────────┬────────┘
              │              │
              │     ┌────────▼────────┐
              │     │ 7. Recommend-   │──── Claude API (or template recs)
              │     │    ations       │
              │     └────────┬────────┘
              │              │
              │     ┌────────▼────────┐
              └─────│ 8. Report       │──── Assemble PipelineResult, cost estimate
                    │    Assembly     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  PipelineResult  │
                    └─────────────────┘
```

### Pipeline Entry Points

There are two ways to invoke the pipeline:

#### 1. Celery Task (Production)

```python
# tasks/report_tasks.py

@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_report(self, report_id: str) -> None:
    """
    Celery task that runs the full analytics pipeline.

    Flow:
    1. Load Report row from DB
    2. Fetch MetricRecord[] from metrics table for the date range
    3. Build ReportRequest from Report config
    4. Run PipelineOrchestrator.execute()
    5. Persist insights, recommendations, executive summary to DB
    6. Update Report status to 'completed'
    7. Generate PDF, upload to S3, store URL
    8. On failure: update Report status to 'failed' with error message
    """
    # Uses sync wrapper around async orchestrator
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(_run_pipeline(report_id))
    loop.close()
```

**Triggered by:** `POST /v1/reports/generate` → `ReportService.generate()` → `generate_report.delay(report_id)`

**Progress tracking:** The Celery task calls `PipelineOrchestrator.execute()` with a `progress_callback` that updates a Redis key:

```python
# Redis key: report_progress:{report_id}
{
    "percent": 62,
    "current_stage": "insight_generation",
    "stages": { "data_validation": "done", ... }
}
```

**Polled by:** `GET /v1/reports/:id/status` reads from Redis.

#### 2. Direct Invocation (Testing / CLI)

```python
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.schemas import ReportRequest, MetricRecord

orchestrator = PipelineOrchestrator(anthropic_client=client)
result = await orchestrator.execute(
    request=ReportRequest(
        workspace_id="...",
        date_range_start=date(2026, 2, 1),
        date_range_end=date(2026, 2, 28),
        platforms=["meta_ads", "google_ads"],
        tone="executive",
        ai_model="claude-sonnet-4-6",
    ),
    records=metric_records,
    progress_callback=lambda stage, pct: print(f"{stage}: {pct}%"),
)
```

### Pipeline Data Contracts

Each stage communicates via typed Pydantic models defined in `pipeline/schemas.py`:

| Stage | Input | Output |
|-------|-------|--------|
| 1. Data Validation | `list[MetricRecord]` | `ValidationResult` |
| 2. KPI Computation | `list[MetricRecord]` + date range | `KPIResult` |
| 3. Trend Detection | `list[MetricRecord]` + budget | `TrendAnalysis` |
| 4. Anomaly Detection | `list[MetricRecord]` | `AnomalyAnalysis` |
| 5. Campaign Evaluation | `KPIResult` | `CampaignEvaluationResult` |
| 6. Insight Generation | KPIs + Trends + Anomalies + Evaluation + tone | `InsightGenerationResult` |
| 7. Recommendations | KPIs + Trends + Anomalies + Evaluation + Insights + tone | `RecommendationResult` |
| 8. Report Assembly | All above | `PipelineResult` |

### Agent → Skill Mapping

| Agent | Skills Used |
|-------|-------------|
| DataValidationAgent | `RawDataValidator` |
| KPIComputationAgent | `KPIComputer`, `Aggregator`, `PeriodComparer`, `EfficiencyScorer` |
| TrendDetectionAgent | `TrendClassifier`, `MovingAverageAnalyzer`, `PacingAnalyzer` |
| AnomalyDetectionAgent | `ZScoreDetector`, `ContextualDetector`, `CorrelationBreakDetector`, `MissingDataDetector` |
| CampaignEvaluationAgent | `TierClassifier`, `BudgetAssessor`, `PlatformComparator` |
| InsightGenerationAgent | `InsightPromptBuilder`, `InsightParser`, `TemplateFallback` + **Claude API** |
| RecommendationAgent | `InsightPromptBuilder`, `InsightParser` + **Claude API** |
| ReportGenerationAgent | — (assembles final result, estimates cost) |

### AI Fallback Strategy

If Claude API calls fail (stages 6-7), the pipeline does not fail:

1. `InsightGenerationAgent.fallback()` → uses `TemplateFallback.generate_fallback_insights()` — rule-based insights from KPIs and campaign evaluations
2. `RecommendationAgent.fallback()` → uses `_generate_template_recs()` — rule-based recommendations from tier classifications and anomalies
3. Executive summary falls back to a structured template with key numbers

---

## 5. Celery Tasks

### Task Registry

```python
# tasks/celery_app.py
from celery import Celery
from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "insightflow",
    broker=settings.CELERY_BROKER_URL,        # redis://localhost:6379/0
    backend=settings.CELERY_RESULT_BACKEND,   # redis://localhost:6379/1
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
```

### Report Tasks `[Planned]`

```python
# tasks/report_tasks.py

@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_report(self, report_id: str) -> dict:
    """Full pipeline execution → persist results → generate PDF."""

@celery_app.task
def retry_failed_reports() -> int:
    """Re-queue reports stuck in 'generating' for >10 minutes. Returns count."""
```

### Sync Tasks `[Planned]`

```python
# tasks/sync_tasks.py

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_connection(self, connection_id: str, sync_type: str = "incremental") -> dict:
    """Fetch data from platform API → normalize → upsert metrics."""

@celery_app.task
def sync_all_active() -> int:
    """Trigger incremental sync for all active connections. Returns count."""
```

### Maintenance Tasks `[Planned]`

```python
# tasks/maintenance_tasks.py

@celery_app.task
def create_metric_partitions() -> list[str]:
    """Create next month's metric partition if it doesn't exist."""

@celery_app.task
def cleanup_expired_tokens() -> int:
    """Mark connections with expired tokens as 'expired'. Returns count."""

@celery_app.task
def cleanup_old_audit_logs(days: int = 365) -> int:
    """Delete audit logs older than N days. Returns count."""
```

### Celery Beat Schedule

```python
celery_app.conf.beat_schedule = {
    "sync-all-daily": {
        "task": "app.tasks.sync_tasks.sync_all_active",
        "schedule": crontab(hour=6, minute=0),          # 6:00 AM UTC daily
    },
    "retry-stuck-reports": {
        "task": "app.tasks.report_tasks.retry_failed_reports",
        "schedule": crontab(minute="*/10"),              # Every 10 minutes
    },
    "create-partitions": {
        "task": "app.tasks.maintenance_tasks.create_metric_partitions",
        "schedule": crontab(day_of_month=25, hour=0),   # 25th of each month
    },
    "cleanup-tokens": {
        "task": "app.tasks.maintenance_tasks.cleanup_expired_tokens",
        "schedule": crontab(hour=1, minute=0),           # 1:00 AM UTC daily
    },
}
```

---

## 6. Request Lifecycle

### Authenticated Request Flow

```
Client Request
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  CORSMiddleware                                      │
│  → Validates origin, sets CORS headers               │
├─────────────────────────────────────────────────────┤
│  RequestContextMiddleware                            │
│  → Generates/extracts X-Request-ID                   │
│  → Binds request_id to structlog                     │
├─────────────────────────────────────────────────────┤
│  RateLimiterMiddleware                [planned]      │
│  → Token-bucket check per endpoint class             │
│  → Returns 429 if exceeded                           │
├─────────────────────────────────────────────────────┤
│  Endpoint Handler                                    │
│  │                                                   │
│  ├─ get_current_user(Authorization header)           │
│  │  → Decode JWT, load User from DB                  │
│  │  → Raise 401 if invalid/expired                   │
│  │                                                   │
│  ├─ get_current_organization(X-Organization-ID)      │
│  │  → Verify membership                              │
│  │  → Raise 403 if not a member                      │
│  │                                                   │
│  ├─ WorkspaceContextMiddleware        [planned]      │
│  │  → SET LOCAL app.current_workspace_id             │
│  │  → Enables PostgreSQL RLS                         │
│  │                                                   │
│  ├─ Service.method()                                 │
│  │  → Business logic                                 │
│  │  → Repository queries (RLS-scoped)                │
│  │                                                   │
│  └─ Return SuccessResponse[T]                        │
│                                                      │
├─────────────────────────────────────────────────────┤
│  Exception Handlers (if error thrown)                │
│  → InsightFlowError   → RFC 7807 JSON               │
│  → ValidationError    → 422 with field details       │
│  → Exception          → 500 with request_id          │
└─────────────────────────────────────────────────────┘
    │
    ▼
Client Response
```

### Report Generation Flow (Async)

```
POST /v1/reports/generate
    │
    ▼
ReportService.generate()
    │
    ├─ Validate config (client exists, platforms connected, date range valid)
    ├─ Create Report row → status='generating'
    ├─ generate_report.delay(report_id)  ←── Celery task queued
    └─ Return 202 { report_id, status: 'generating' }

                    ╔═══════════════════════════╗
                    ║  Celery Worker (async)     ║
                    ╠═══════════════════════════╣
                    ║                           ║
                    ║  1. Load Report from DB   ║
                    ║  2. Fetch metrics          ║
                    ║  3. Build ReportRequest    ║
                    ║  4. PipelineOrchestrator   ║
                    ║     .execute()             ║
                    ║     ├─ Stage 1-8          ║
                    ║     └─ progress → Redis   ║
                    ║  5. Persist insights       ║
                    ║  6. Persist recs           ║
                    ║  7. Generate PDF → S3     ║
                    ║  8. Update Report          ║
                    ║     status='completed'     ║
                    ║                           ║
                    ╚═══════════════════════════╝

GET /v1/reports/:id/status  ←── Frontend polls
    │
    ├─ Read progress from Redis
    └─ Return { percent, current_stage, stages[] }

GET /v1/reports/:id  ←── After completion
    │
    └─ Return full report with sections, insights, recommendations
```

---

## 7. Data Ingestion Flow

```
POST /v1/integrations/connections/:id/sync
    │
    ▼
IntegrationService.trigger_sync()
    │
    ├─ Create SyncJob row → status='pending'
    ├─ sync_connection.delay(connection_id)  ←── Celery task
    └─ Return 202 { sync_job_id }

                    ╔═══════════════════════════╗
                    ║  Celery Worker             ║
                    ╠═══════════════════════════╣
                    ║                           ║
                    ║  IngestionService          ║
                    ║  .sync_connection()        ║
                    ║    │                       ║
                    ║    ├─ Decrypt OAuth tokens ║
                    ║    ├─ Create connector     ║
                    ║    │  (Meta/Google/etc)    ║
                    ║    ├─ fetch_campaigns()    ║
                    ║    ├─ fetch_metrics()      ║
                    ║    ├─ MetricsNormalizer    ║
                    ║    │  .normalize_batch()   ║
                    ║    ├─ Upsert campaigns     ║
                    ║    ├─ Upsert metrics       ║
                    ║    └─ Update connection    ║
                    ║       last_synced_at       ║
                    ║                           ║
                    ╚═══════════════════════════╝
```

### Connector Architecture

```python
class BaseConnector(ABC):
    """Abstract base with rate limiting + circuit breaker."""

    rate_limiter: RateLimiter          # Token-bucket per platform
    circuit_breaker: CircuitBreaker    # Fail-fast after 5 consecutive errors

    async def _request(method, url, **kwargs) -> dict
        # 1. Check circuit breaker
        # 2. Acquire rate limiter token
        # 3. Make HTTP request (httpx)
        # 4. Retry on 429/5xx (exponential backoff)
        # 5. Record success/failure for circuit breaker

    @abstractmethod
    async def fetch_campaigns() -> list[dict]

    @abstractmethod
    async def fetch_metrics(date_start, date_end, campaign_ids) -> list[RawRecord]

    @abstractmethod
    async def validate_connection() -> bool
```

| Connector | Platform API | Rate Limit | Status |
|-----------|-------------|------------|--------|
| `MetaAdsConnector` | Meta Marketing API v21 | 200/hr | **Exists** |
| `GoogleAdsConnector` | Google Ads API v17 | 1000/day | **Exists** |
| `GoogleAnalyticsConnector` | GA4 Data API | 60/min | **Exists** |
| `ShopifyConnector` | Shopify Admin API 2024-01 | 40/sec | **Exists** |

---

## 8. Error Handling

### Exception Hierarchy

```
InsightFlowError (base)
├── NotFoundError          → 404
├── ConflictError          → 409
├── ValidationError        → 400
├── AuthenticationError    → 401
├── ForbiddenError         → 403
├── RateLimitError         → 429
└── ExternalServiceError   → 502
```

### Error Response Format (RFC 7807)

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Report rpt_abc123 not found",
    "details": []
  },
  "meta": {
    "request_id": "req_xyz789",
    "timestamp": "2026-03-12T10:30:00Z"
  }
}
```

### Validation Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "date_range.start_date", "message": "Must be before end_date" },
      { "field": "platforms", "message": "At least one platform required" }
    ]
  },
  "meta": { "request_id": "req_xyz789", "timestamp": "2026-03-12T10:30:00Z" }
}
```

---

## 9. Configuration

### Environment Variables

```bash
# ── Application ──
APP_NAME=InsightFlow
APP_VERSION=0.1.0
ENVIRONMENT=development              # development | staging | production
DEBUG=true
SECRET_KEY=<random-64-char>

# ── Database ──
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/insightflow
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# ── Redis ──
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=300

# ── Celery ──
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# ── Auth ──
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12

# ── AI ──
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6

# ── Rate Limiting ──
RATE_LIMIT_AUTH=5/minute
RATE_LIMIT_API=100/minute
RATE_LIMIT_REPORT_GENERATION=10/hour

# ── CORS ──
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 10. Security Checklist

| Concern | Implementation |
|---------|---------------|
| **Authentication** | JWT access tokens (15-min TTL) + HttpOnly refresh cookies (7-day) |
| **Multi-tenancy** | `workspace_id` on every query + PostgreSQL RLS policies |
| **Token encryption** | AES-256-GCM envelope encryption for OAuth tokens (DEK wrapped by KMS) |
| **Password storage** | bcrypt with 12 rounds |
| **Input validation** | Pydantic v2 on every request body and query param |
| **SQL injection** | SQLAlchemy ORM only — no raw SQL with user input |
| **Rate limiting** | Token-bucket per endpoint class (auth: 5/min, API: 100/min) |
| **CORS** | Explicit origin allowlist |
| **Request tracing** | X-Request-ID propagated through logs and error responses |
| **Audit logging** | All write operations logged to `audit_logs` table |
| **Soft deletes** | Critical data (users, workspaces, clients, reports) uses `deleted_at` |
| **Account lockout** | 5 failed logins → 15-min lock (`locked_until` field) |
