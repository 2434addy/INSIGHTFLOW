# InsightFlow Backend Architecture

> **Version:** 1.1 — Post architecture review
> **Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Celery, Redis, PostgreSQL 16

---

## 1. Folder Structure

```
backend/
├── alembic/                          # Database migrations
│   ├── env.py                       # Async migration environment
│   ├── script.py.mako               # Migration template
│   └── versions/                    # Migration files
├── app/
│   ├── main.py                      # FastAPI app factory + lifecycle
│   ├── __init__.py
│   │
│   ├── api/                          # ── API Layer ──────────────────
│   │   ├── deps.py                  # Shared dependencies (auth, pagination)
│   │   └── v1/
│   │       ├── router.py            # V1 router aggregator
│   │       └── endpoints/
│   │           ├── auth.py          # Registration, login, me
│   │           └── health.py        # Health check
│   │
│   ├── core/                         # ── Core Infrastructure ────────
│   │   ├── config.py                # Pydantic Settings (env vars)
│   │   ├── database.py              # Async engine + session factory
│   │   ├── exceptions.py            # Exception hierarchy
│   │   ├── logging.py               # Structured logging (structlog)
│   │   └── security.py              # JWT + password hashing
│   │
│   ├── middleware/                    # ── Middleware ──────────────────
│   │   ├── error_handler.py         # RFC 7807 error responses
│   │   ├── rate_limiter.py          # Sliding-window rate limiting
│   │   ├── request_context.py       # Request ID + structlog binding
│   │   └── security_headers.py      # OWASP security headers
│   │
│   ├── models/                       # ── Domain Models (ORM) ────────
│   │   ├── base.py                  # UUID PK, timestamps, soft-delete
│   │   ├── user.py                  # User (email + OAuth)
│   │   ├── organization.py          # Organization + Membership
│   │   ├── campaign.py              # Campaign
│   │   ├── ad_set.py                # Ad Set
│   │   ├── ad.py                    # Ad
│   │   ├── data_source_connection.py # OAuth connections (encrypted)
│   │   ├── metrics.py               # Time-series marketing data
│   │   ├── report.py                # AI-generated reports
│   │   ├── insight.py               # AI-generated insights
│   │   └── recommendation.py        # AI-generated recommendations
│   │
│   ├── schemas/                      # ── API Schemas (Pydantic) ─────
│   │   ├── common.py                # Envelope, pagination, errors
│   │   └── auth.py                  # Auth request/response schemas
│   │
│   ├── repositories/                 # ── Data Access Layer ──────────
│   │   ├── base.py                  # Generic CRUD repository
│   │   ├── user_repository.py       # User queries
│   │   └── organization_repository.py # Org + membership queries
│   │
│   ├── services/                     # ── Business Logic Layer ───────
│   │   ├── auth_service.py          # Registration, login, tokens
│   │   └── ingestion/               # Data sync from platforms
│   │       ├── base_connector.py    # Abstract connector with retry
│   │       ├── meta_ads.py          # Meta Ads connector
│   │       ├── google_ads.py        # Google Ads connector
│   │       ├── google_analytics.py  # GA4 connector
│   │       ├── shopify.py           # Shopify connector
│   │       ├── normalizer.py        # Cross-platform normalization
│   │       └── ingestion_service.py # Sync orchestration
│   │
│   ├── pipeline/                     # ── Analytics Pipeline ─────────
│   │   ├── orchestrator.py          # DAG-based pipeline runner
│   │   ├── pipeline_context.py      # Shared execution context
│   │   ├── pipeline_state.py        # Stage tracking + resumability
│   │   ├── schemas.py               # Inter-stage data contracts
│   │   └── stages/                  # Individual stage executors
│   │       ├── stage_validation.py  # Stage 1: Data validation
│   │       ├── stage_kpi.py         # Stage 2: KPI computation
│   │       ├── stage_trend.py       # Stage 3: Trend detection
│   │       ├── stage_anomaly.py     # Stage 4: Anomaly detection
│   │       ├── stage_evaluation.py  # Stage 5: Campaign evaluation
│   │       ├── stage_insight.py     # Stage 6: Insight generation
│   │       ├── stage_recommendation.py # Stage 7: Recommendations
│   │       └── stage_report.py      # Stage 8: Report assembly
│   │
│   ├── agents/                       # ── AI Agents ──────────────────
│   │   ├── base.py                  # BaseAgent<InputT, OutputT>
│   │   ├── data_validation_agent.py # Validates raw records
│   │   ├── kpi_computation_agent.py # Computes derived metrics
│   │   ├── trend_detection_agent.py # Time-series trend analysis
│   │   ├── anomaly_detection_agent.py # Outlier detection
│   │   ├── campaign_evaluation_agent.py # Tier classification
│   │   ├── insight_generation_agent.py  # Claude API insights
│   │   ├── recommendation_agent.py  # Claude API recommendations
│   │   └── report_generation_agent.py   # Final report assembly
│   │
│   ├── skills/                       # ── Reusable Skills ────────────
│   │   ├── semantic_metric_layer.py # Metric definitions + benchmarks
│   │   ├── kpi_computation.py       # KPI formulas + aggregation
│   │   ├── trend_detection.py       # Regression + moving averages
│   │   ├── anomaly_detection.py     # Z-score + contextual detectors
│   │   ├── campaign_evaluation.py   # Tier + budget assessment
│   │   ├── data_quality_validation.py # Multi-stage validation
│   │   └── insight_summarization.py # Prompt building + parsing
│   │
│   ├── workers/                      # ── Background Workers ─────────
│   │   ├── celery_app.py            # Celery factory + beat schedule
│   │   └── tasks/
│   │       ├── report.py            # Report generation tasks
│   │       ├── ingestion.py         # Data sync tasks
│   │       └── maintenance.py       # Cleanup + health tasks
│   │
│   ├── events/                       # ── Internal Events ────────────
│   │   └── event_bus.py             # Domain event bus + event types
│   │
│   └── utils/                        # ── Utilities ──────────────────
│       ├── encryption.py            # AES-256-GCM token encryption
│       ├── sanitize.py              # Safe logging + secret redaction
│       └── pagination.py            # Cursor encode/decode
│
├── tests/                            # ── Test Suite ──────────────────
│   ├── conftest.py                  # Shared fixtures
│   ├── api/                         # API endpoint tests
│   ├── services/                    # Service layer tests
│   ├── repositories/                # Repository tests
│   ├── pipeline/                    # Pipeline state/context tests
│   ├── middleware/                   # Rate limiter tests
│   ├── events/                      # Event bus tests
│   └── utils/                       # Utility tests
│
├── alembic.ini                       # Alembic configuration
├── pyproject.toml                    # Python project config
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Container build
└── .env.example                      # Environment template
```

---

## 2. Layered Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                     │
│  Endpoints → Schemas → Dependencies                       │
├──────────────────────────────────────────────────────────┤
│                    Middleware Stack                        │
│  RequestContext → RateLimit → SecurityHeaders → CORS      │
├──────────────────────────────────────────────────────────┤
│                   Service Layer                           │
│  AuthService · IngestionService · (future services)       │
├──────────────────────────────────────────────────────────┤
│                 Repository Layer                          │
│  BaseRepository<T> → UserRepo · OrgRepo · (others)       │
├──────────────────────────────────────────────────────────┤
│                    Domain Models                          │
│  User · Organization · Campaign · Metrics · Report · ...  │
├──────────────────────────────────────────────────────────┤
│                  Analytics Pipeline                       │
│  Orchestrator → Stages → Agents → Skills                  │
├──────────────────────────────────────────────────────────┤
│                 Background Workers                        │
│  Celery tasks (report gen, data sync, maintenance)        │
├──────────────────────────────────────────────────────────┤
│                    Infrastructure                         │
│  PostgreSQL · Redis · S3 · Claude API                     │
└──────────────────────────────────────────────────────────┘
```

**Dependency rule:** Each layer only depends on the layer directly below it. No upward imports.

---

## 3. Request Lifecycle

```
Client Request
    │
    ├─→ RequestContextMiddleware    # Bind request_id to logs
    ├─→ RateLimiterMiddleware       # Check rate limits by IP + category
    ├─→ SecurityHeadersMiddleware   # Add OWASP security headers
    ├─→ CORSMiddleware              # Cross-origin access control
    │
    ├─→ FastAPI Router              # Route to endpoint handler
    │   ├─→ get_current_user()      # JWT validation (dependency)
    │   ├─→ get_current_organization() # Tenant resolution
    │   └─→ require_role()          # RBAC permission check
    │
    ├─→ Service Layer               # Business logic
    │   └─→ Repository Layer        # Database operations
    │
    └─→ Response (JSON envelope)
```

---

## 4. Data Flow

### 4.1 Synchronous API Request
```
HTTP Request → Middleware → Endpoint → Service → Repository → DB → Response
```

### 4.2 Report Generation (Async)
```
POST /v1/reports/generate
    │
    ├─→ Validate request
    ├─→ Create Report record (status=processing)
    ├─→ Enqueue Celery task → Redis broker
    └─→ Return 202 Accepted + report_id

Celery Worker picks up task:
    ├─→ Fetch metrics from DB
    ├─→ PipelineOrchestrator.execute()
    │   ├─→ Stage 1: Validate data
    │   ├─→ Stage 2: Compute KPIs
    │   ├─→ Stage 3+4 (parallel): Trends + Anomalies
    │   ├─→ Stage 5: Evaluate campaigns
    │   ├─→ Stage 6: Generate insights (Claude API)
    │   ├─→ Stage 7: Generate recommendations (Claude API)
    │   └─→ Stage 8: Assemble report
    ├─→ Save results to DB
    ├─→ Publish ReportCompleted event
    └─→ Update Report status=completed

Client polls: GET /v1/reports/{id}/progress
    └─→ Read from Redis → return stage + percentage
```

### 4.3 Data Ingestion (Background)
```
Celery Beat (hourly) → sync_all_connections
    ├─→ Query active DataSourceConnections
    └─→ Fan out sync_data_source tasks
         ├─→ Decrypt OAuth token
         ├─→ Platform connector fetches data
         ├─→ Normalizer standardizes metrics
         ├─→ Upsert campaigns + metrics
         └─→ Publish DataSyncCompleted event
```

---

## 5. Key Design Patterns

### 5.1 Generic Base Agent
```python
class BaseAgent(ABC, Generic[InputT, OutputT]):
    async def run(input_data: InputT) -> OutputT:
        # Retry loop with timing + logging
        # Falls back to fallback() on exhaustion
```

### 5.2 Generic Base Repository
```python
class BaseRepository(Generic[ModelT]):
    async def get_by_id(id) -> ModelT | None
    async def list(*filters, limit, cursor) -> (list[ModelT], next_cursor)
    async def create(entity) -> ModelT
    async def count(*filters) -> int
```

### 5.3 Pipeline State Machine
```python
PipelineState tracks per-stage: PENDING → RUNNING → COMPLETED | FAILED
    - Enables resumability (skip completed stages on retry)
    - Provides timing report for performance monitoring
    - Summary dict for API/logging
```

### 5.4 Domain Event Bus
```python
event_bus.subscribe(ReportCompleted, send_notification)
event_bus.subscribe(ReportCompleted, invalidate_cache)
await event_bus.publish(ReportCompleted(...))
# Handlers run concurrently; failures don't propagate
```

---

## 6. Configuration Management

All settings are centralized in `app/core/config.py` using Pydantic Settings:

| Category | Key Settings |
|----------|-------------|
| **Application** | ENVIRONMENT, DEBUG, APP_VERSION |
| **Security** | SECRET_KEY, JWT_ALGORITHM, BCRYPT_ROUNDS |
| **Database** | DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW |
| **Redis** | REDIS_URL, REDIS_CACHE_TTL |
| **Celery** | CELERY_BROKER_URL, CELERY_RESULT_BACKEND |
| **Rate Limiting** | RATE_LIMIT_AUTH, RATE_LIMIT_API, RATE_LIMIT_REPORT_GENERATION |
| **AI** | ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ANTHROPIC_MAX_TOKENS |
| **Storage** | S3_BUCKET, S3_REGION, S3_REPORTS_PREFIX |
| **Pipeline** | PIPELINE_TIMEOUT, PIPELINE_MAX_RECORDS |
| **Logging** | LOG_LEVEL, LOG_FORMAT |

Settings are loaded from environment variables with `.env` file support for local development. Production values come from AWS Secrets Manager via container env injection.

---

## 7. Multi-Tenant Architecture

- Every model has `organization_id` foreign key
- PostgreSQL Row-Level Security (RLS) enforces isolation at DB level
- API layer resolves tenant via `X-Organization-ID` header
- `get_current_organization()` dependency verifies membership
- Repositories filter by organization_id on all queries

---

## 8. Agent → Skill Dependency Map

| Agent | Skills Used |
|-------|------------|
| DataValidationAgent | DataQualityValidation |
| KPIComputationAgent | KPIComputation, SemanticMetricLayer |
| TrendDetectionAgent | TrendDetection |
| AnomalyDetectionAgent | AnomalyDetection |
| CampaignEvaluationAgent | CampaignEvaluation, SemanticMetricLayer |
| InsightGenerationAgent | InsightSummarization |
| RecommendationAgent | InsightSummarization |
| ReportGenerationAgent | (assembler — no skills) |

**Design principle:** Agents orchestrate; skills compute. Skills are stateless pure functions with no database access. Data is always passed as parameters.

---

## 9. Testing Strategy

```
tests/
├── api/          # HTTP endpoint tests (httpx AsyncClient)
├── services/     # Business logic unit tests
├── repositories/ # Data access tests
├── pipeline/     # Pipeline state + context tests
├── middleware/    # Rate limiter + security header tests
├── events/       # Event bus tests
└── utils/        # Encryption, sanitization, pagination tests
```

- **Test DB:** SQLite for fast unit tests, PostgreSQL for integration
- **Fixtures:** conftest.py provides test users, orgs, auth headers
- **Async:** All tests run async via `pytest-asyncio` with `asyncio_mode = "auto"`
