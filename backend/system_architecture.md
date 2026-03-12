# InsightFlow — System Architecture

## 1. Architecture Overview

InsightFlow follows a **modular monolith** architecture for MVP, designed for easy extraction into microservices as scale demands.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENTS                                    │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ Web App   │  │ Client Portal│  │ Mobile (v2)  │                 │
│  │ (Next.js) │  │ (Next.js)    │  │              │                 │
│  └─────┬─────┘  └──────┬──────┘  └──────┬───────┘                 │
│        │               │                │                           │
└────────┼───────────────┼────────────────┼───────────────────────────┘
         │               │                │
    ┌────┴────────────────┴────────────────┴────┐
    │              API Gateway                   │
    │         (Rate Limiting, Auth, CORS)        │
    └────────────────────┬──────────────────────┘
                         │
    ┌────────────────────┴──────────────────────┐
    │           APPLICATION LAYER                │
    │                                            │
    │  ┌────────────┐  ┌────────────────────┐   │
    │  │ Auth       │  │ Workspace          │   │
    │  │ Module     │  │ Module             │   │
    │  └────────────┘  └────────────────────┘   │
    │  ┌────────────┐  ┌────────────────────┐   │
    │  │ Integration│  │ Report             │   │
    │  │ Module     │  │ Module             │   │
    │  └────────────┘  └────────────────────┘   │
    │  ┌────────────┐  ┌────────────────────┐   │
    │  │ Data Sync  │  │ AI / Insights      │   │
    │  │ Module     │  │ Module             │   │
    │  └────────────┘  └────────────────────┘   │
    │                                            │
    └───────┬──────────────┬────────────────────┘
            │              │
    ┌───────┴──────┐  ┌────┴───────────┐
    │  Data Layer   │  │  External APIs  │
    │  PostgreSQL   │  │  Meta, Google   │
    │  Redis        │  │  Claude API     │
    │  S3           │  │  Shopify        │
    └──────────────┘  └────────────────┘
```

## 2. Technology Stack

### Backend
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Runtime | Python 3.12+ | AI/ML ecosystem, FastAPI performance |
| Framework | FastAPI | Async-first, automatic OpenAPI docs, Pydantic validation |
| ORM | SQLAlchemy 2.0 (async) | Mature, type-safe, async support |
| Migrations | Alembic | Industry standard for SQLAlchemy |
| Task Queue | Celery + Redis | Reliable async job processing |
| Cache | Redis | Sessions, rate limiting, hot data caching |
| Testing | pytest + pytest-asyncio | Comprehensive async test support |

### Frontend
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Framework | Next.js 14 (App Router) | SSR, RSC, excellent DX |
| Language | TypeScript | Type safety, better DX |
| UI Library | shadcn/ui + Tailwind CSS | Accessible, customizable, performant |
| State | Zustand + TanStack Query | Lightweight global state + server state |
| Charts | Recharts | SSR-compatible, composable |
| Forms | React Hook Form + Zod | Performance, validation |
| Testing | Vitest + Playwright | Unit + E2E testing |

### Infrastructure
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Cloud | AWS | Mature, comprehensive services |
| Compute | ECS Fargate | Serverless containers, auto-scaling |
| Database | RDS PostgreSQL 16 | Managed, reliable, RLS support |
| Cache | ElastiCache Redis | Managed Redis |
| Storage | S3 | PDF storage, static assets |
| CDN | CloudFront + CloudFlare | Performance, WAF, DDoS protection |
| CI/CD | GitHub Actions | Integrated with source control |
| IaC | Terraform | Declarative infrastructure |
| Monitoring | Datadog or AWS CloudWatch | APM, logs, metrics |

## 3. Module Architecture

### 3.1 Auth Module
```
auth/
├── router.py          # API endpoints (/auth/*)
├── service.py         # Business logic
├── models.py          # SQLAlchemy models (User, Session)
├── schemas.py         # Pydantic request/response schemas
├── dependencies.py    # Auth middleware, current_user dependency
├── security.py        # Password hashing, JWT, token management
└── oauth/
    ├── google.py      # Google OAuth provider
    └── base.py        # OAuth provider interface
```

### 3.2 Integration Module
```
integrations/
├── router.py          # API endpoints (/integrations/*)
├── service.py         # Connection management logic
├── models.py          # Connection, OAuthToken models
├── schemas.py         # Pydantic schemas
├── encryption.py      # Token encryption/decryption
└── providers/
    ├── base.py        # Abstract provider interface
    ├── meta_ads.py    # Meta Ads API client
    ├── google_ads.py  # Google Ads API client
    ├── ga4.py         # GA4 API client (Phase 2)
    └── shopify.py     # Shopify API client (Phase 2)
```

### 3.3 Data Sync Module
```
data_sync/
├── tasks.py           # Celery tasks for scheduled syncs
├── service.py         # Sync orchestration logic
├── models.py          # SyncJob, SyncLog models
├── normalizer.py      # Cross-platform data normalization
├── validators.py      # Data quality validation
└── scheduler.py       # Sync schedule management
```

### 3.4 Report Module
```
reports/
├── router.py          # API endpoints (/reports/*)
├── service.py         # Report generation orchestration
├── models.py          # Report, ReportSection models
├── schemas.py         # Pydantic schemas
├── templates/         # Report template definitions
│   └── monthly_performance.py
├── pdf_generator.py   # PDF rendering
└── ai/
    ├── prompt_builder.py   # Construct AI prompts from data
    ├── insight_engine.py   # AI insight generation
    └── narrative_writer.py # AI narrative generation
```

### 3.5 Workspace Module
```
workspace/
├── router.py          # API endpoints (/workspaces/*)
├── service.py         # Workspace & client management
├── models.py          # Workspace, Client, Membership models
├── schemas.py         # Pydantic schemas
└── permissions.py     # RBAC permission checks
```

## 4. Data Flow Architecture

### 4.1 Data Sync Pipeline
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Scheduler    │────▶│  Celery Task │────▶│  Platform    │
│  (cron/manual)│     │  (sync_data) │     │  API Client  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │  Raw Data    │
                                          │  Validation  │
                                          └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │  Data        │
                                          │  Normalizer  │
                                          └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │  PostgreSQL  │
                                          │  (unified    │
                                          │   schema)    │
                                          └──────────────┘
```

### 4.2 Report Generation Pipeline
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User Request │────▶│  Data        │────▶│  Prompt      │
│  (client +    │     │  Aggregation │     │  Builder     │
│   date range) │     └──────────────┘     └──────┬───────┘
└──────────────┘                                   │
                                                   ▼
                                           ┌──────────────┐
                                           │  Claude API  │
                                           │  (narrative  │
                                           │   generation)│
                                           └──────┬───────┘
                                                   │
                                                   ▼
                                           ┌──────────────┐
                                           │  Report      │
                                           │  Assembly    │
                                           └──────┬───────┘
                                                   │
                                            ┌──────┴──────┐
                                            │             │
                                            ▼             ▼
                                     ┌──────────┐  ┌──────────┐
                                     │  Web View│  │  PDF     │
                                     │  (JSON)  │  │  Export  │
                                     └──────────┘  └──────────┘
```

## 5. Scalability Strategy

### 5.1 Horizontal Scaling Points
| Component | Scaling Trigger | Strategy |
|-----------|----------------|----------|
| API servers | CPU > 70% or latency > 200ms | Auto-scale ECS tasks |
| Celery workers | Queue depth > 100 | Auto-scale worker containers |
| PostgreSQL | Connections > 80% or CPU > 70% | Read replicas, connection pooling (PgBouncer) |
| Redis | Memory > 80% | Redis Cluster, eviction policies |

### 5.2 Caching Strategy
| Data | Cache | TTL | Invalidation |
|------|-------|-----|-------------|
| User session | Redis | 24 hours | On logout/password change |
| Dashboard KPIs | Redis | 5 minutes | On data sync completion |
| Platform API responses | Redis | 15 minutes | On manual refresh |
| Report content | PostgreSQL + S3 | Permanent | On regeneration |
| Rate limit counters | Redis | 1–60 minutes | Auto-expire |

### 5.3 Database Optimization
- **Connection pooling:** PgBouncer (transaction mode), max 100 connections per pool
- **Read replicas:** Route read-heavy queries (dashboards, reports) to replicas
- **Partitioning:** Partition `metrics` table by `workspace_id` and `date` (range partitioning)
- **Indexing strategy:** Compound indexes on (workspace_id, client_id, date) for common queries
- **Query optimization:** EXPLAIN ANALYZE on all new queries, no N+1 queries

## 6. Error Handling & Resilience

### Circuit Breaker Pattern (External APIs)
```python
# Conceptual implementation
class CircuitBreaker:
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery

    failure_threshold = 5
    recovery_timeout = 60   # seconds
```

### Retry Strategy
| Service | Max Retries | Backoff | Timeout |
|---------|------------|---------|---------|
| Meta Ads API | 3 | Exponential (1s, 2s, 4s) | 30s |
| Google Ads API | 3 | Exponential (1s, 2s, 4s) | 30s |
| Claude API | 2 | Exponential (2s, 4s) | 120s |
| Database | 3 | Fixed (500ms) | 5s |
| Redis | 2 | Fixed (100ms) | 1s |

## 7. Observability

### Structured Logging
```python
# Every log entry includes:
{
    "timestamp": "2026-03-12T10:30:00Z",
    "level": "INFO",
    "service": "api",
    "trace_id": "abc-123",
    "workspace_id": "ws_xxx",
    "user_id": "usr_xxx",
    "message": "Report generated",
    "duration_ms": 4523
}
```

### Key Metrics
| Metric | Type | Alert Threshold |
|--------|------|----------------|
| API latency (p95) | Histogram | > 500ms |
| Error rate (5xx) | Counter | > 1% |
| Report generation time | Histogram | > 120s |
| Data sync success rate | Gauge | < 95% |
| Active connections (DB) | Gauge | > 80% capacity |
| Queue depth (Celery) | Gauge | > 500 jobs |
| AI API cost per report | Gauge | > $0.50 |
