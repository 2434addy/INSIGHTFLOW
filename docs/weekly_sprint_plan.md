# InsightFlow — Weekly Engineering Sprint Plan

## Phase 8: MVP Build (10 Weeks)

**Start Date:** 2026-03-16
**Target Launch:** 2026-05-22
**Team:** 1 full-stack engineer

### Current State (as of 2026-03-12)

| Area | Status | Notes |
|------|--------|-------|
| DB Models | 100% | All SQLAlchemy models complete |
| Auth Service | 95% | JWT + refresh tokens, password hashing, middleware |
| AI Pipeline | 85% | 9 agents, 9 skills, orchestrator, 23 tests passing |
| Frontend Scaffold | 30% | 5 pages with demo data, component library, layout |
| API Routes | 20% | Auth endpoints only |
| Migrations | 0% | No Alembic setup |
| Celery Workers | 0% | No task definitions |
| Frontend Auth | 0% | No login/register pages |
| OAuth Integrations | 0% | No platform connectors |
| Docker Compose | 0% | No containerization |
| CI/CD | 0% | No pipeline |
| E2E Tests | 0% | Unit tests only |

---

## Week 1 (Mar 16–20): Database & API Foundation

**Goal:** Production-ready database with migrations; core API scaffolding.

### Deliverables
- [ ] Initialize Alembic with async PostgreSQL driver
- [ ] Generate initial migration from all existing models (User, Organization, Campaign, Metrics, Report, Insight, Recommendation)
- [ ] Enable Row-Level Security policies for workspace_id isolation
- [ ] Set up FastAPI APIRouter structure matching `backend/api_design.md`
- [ ] Implement response envelope (`{"data": ..., "meta": ...}`) and error format (RFC 7807)
- [ ] Add health check endpoint (`GET /api/v1/health`)
- [ ] Add request ID middleware and structured logging

### Acceptance Criteria
- `alembic upgrade head` creates all tables with RLS policies
- `GET /api/v1/health` returns 200 with DB connectivity check
- All responses use envelope format

---

## Week 2 (Mar 23–27): Auth API & User Management

**Goal:** Complete authentication flow with API endpoints.

### Deliverables
- [ ] `POST /api/v1/auth/register` — create user + workspace
- [ ] `POST /api/v1/auth/login` — issue JWT access + HttpOnly refresh cookie
- [ ] `POST /api/v1/auth/refresh` — rotate refresh token
- [ ] `POST /api/v1/auth/logout` — revoke refresh token
- [ ] `GET /api/v1/users/me` — current user profile
- [ ] `PUT /api/v1/users/me` — update profile
- [ ] Rate limiting on auth endpoints (5 req/min for login)
- [ ] Auth dependency injection (`get_current_user`, `get_current_workspace`)
- [ ] Tests: auth flow (register → login → refresh → protected route → logout)

### Acceptance Criteria
- Full auth lifecycle works via API
- Protected endpoints return 401 without valid token
- All queries scoped to workspace_id

---

## Week 3 (Mar 30–Apr 3): Data Platform & Campaign APIs

**Goal:** CRUD endpoints for platforms, campaigns, and metrics.

### Deliverables
- [ ] `POST /api/v1/platforms` — register a platform connection (store OAuth placeholder)
- [ ] `GET /api/v1/platforms` — list connected platforms
- [ ] `DELETE /api/v1/platforms/{id}` — disconnect platform
- [ ] `GET /api/v1/campaigns` — list campaigns with pagination, filtering (platform, status, tier)
- [ ] `GET /api/v1/campaigns/{id}` — campaign detail with metrics
- [ ] `GET /api/v1/metrics/summary` — KPI summary for date range
- [ ] `GET /api/v1/metrics/daily` — daily metrics time series
- [ ] `GET /api/v1/metrics/by-platform` — platform breakdown
- [ ] Input validation with Pydantic v2 (query params, request bodies)
- [ ] Tests: CRUD operations, pagination, workspace isolation

### Acceptance Criteria
- All endpoints enforce workspace_id scoping
- Pagination returns `total`, `page`, `page_size` in meta
- Platform filter works on campaigns and metrics

---

## Week 4 (Apr 6–10): Report & Insights APIs + Celery Setup

**Goal:** Report generation endpoints; background job infrastructure.

### Deliverables
- [ ] `POST /api/v1/reports` — create report (queues Celery task)
- [ ] `GET /api/v1/reports` — list reports with status filter
- [ ] `GET /api/v1/reports/{id}` — full report with insights + recommendations
- [ ] `DELETE /api/v1/reports/{id}` — soft delete
- [ ] `GET /api/v1/insights` — list insights with category/sentiment filter
- [ ] `GET /api/v1/recommendations` — list recommendations with priority filter
- [ ] Set up Celery with Redis broker
- [ ] `generate_report` Celery task — wires pipeline orchestrator to DB persistence
- [ ] Report status webhook/polling endpoint (`GET /api/v1/reports/{id}/status`)
- [ ] Tests: report creation triggers task, status transitions

### Acceptance Criteria
- `POST /reports` returns 202 with report ID in `queued` status
- Celery task runs pipeline and updates status to `completed`
- Report detail includes nested insights and recommendations

---

## Week 5 (Apr 13–17): OAuth Platform Connectors

**Goal:** Connect to Meta Ads and Google Ads APIs for data ingestion.

### Deliverables
- [ ] OAuth 2.0 flow for Meta Ads (authorization URL → callback → token storage)
- [ ] OAuth 2.0 flow for Google Ads (authorization URL → callback → token storage)
- [ ] Encrypt OAuth tokens with AES-256-GCM (envelope encryption)
- [ ] Meta Ads data fetcher — pull campaigns, ad sets, daily metrics
- [ ] Google Ads data fetcher — pull campaigns, ad groups, daily metrics
- [ ] `sync_platform_data` Celery task — fetch + normalize + store metrics
- [ ] `POST /api/v1/platforms/{id}/sync` — trigger manual sync
- [ ] Platform data normalization to unified MetricRecord format
- [ ] Tests: token encryption/decryption, data normalization

### Acceptance Criteria
- OAuth flow completes and tokens are stored encrypted
- Manual sync pulls real data and stores as normalized metrics
- Normalized data matches MetricRecord schema from pipeline

---

## Week 6 (Apr 20–24): Frontend Auth & Dashboard Integration

**Goal:** Login/register pages; connect dashboard to real API.

### Deliverables
- [ ] Login page (`/login`) with form validation (React Hook Form + Zod)
- [ ] Register page (`/register`) with workspace creation
- [ ] Auth context/provider — store access token, handle refresh, redirect on 401
- [ ] Protected route wrapper — redirect unauthenticated users to `/login`
- [ ] TanStack Query hooks: `useDashboardOverview`, `useMetricsDaily`, `useMetricsByPlatform`
- [ ] Connect Dashboard page to real API (replace demo data)
- [ ] Loading skeletons for KPI cards, charts, campaign table
- [ ] Error states with retry buttons
- [ ] Tests: auth flow renders correctly, protected routes redirect

### Acceptance Criteria
- User can register → login → see dashboard with real data
- Token refresh happens transparently
- Loading and error states display correctly

---

## Week 7 (Apr 27–May 1): Frontend Pages — Campaigns, Insights, Reports

**Goal:** Wire remaining pages to API; report generation UI.

### Deliverables
- [ ] TanStack Query hooks: `useCampaigns`, `useInsights`, `useRecommendations`, `useReports`
- [ ] Campaigns page — real data, server-side sorting/filtering
- [ ] Insights page — real data with category filter
- [ ] Reports list page — real data with status badges
- [ ] Report generation form — select date range, platforms, tone
- [ ] Report generation progress indicator (polling status endpoint)
- [ ] Report viewer page — real data from `GET /reports/{id}`
- [ ] PDF export button (client-side html2pdf or server-side)
- [ ] Tests: data fetching hooks, report generation flow

### Acceptance Criteria
- All pages show real data from API
- User can generate a report and see it complete
- Report viewer displays all sections (summary, KPIs, insights, recommendations)

---

## Week 8 (May 4–8): Settings, Integrations UI & Data Sync

**Goal:** Settings page functionality; scheduled data sync.

### Deliverables
- [ ] Settings — General: update workspace name, default report settings (API connected)
- [ ] Settings — Team: invite member (email), update role, remove member
- [ ] Settings — Integrations: OAuth connect/disconnect flow for Meta + Google Ads
- [ ] Settings — API Keys: generate/revoke API keys
- [ ] Settings — Security: change password, enable 2FA placeholder
- [ ] Celery Beat schedule — daily platform data sync (configurable per workspace)
- [ ] Sync status dashboard in Integrations settings (last sync time, record count)
- [ ] Toast/notification system for async operations (report complete, sync done)
- [ ] Tests: settings forms, integration connect/disconnect

### Acceptance Criteria
- All settings tabs functional with API persistence
- OAuth connect flow works end-to-end from UI
- Daily sync runs on schedule and shows status in UI

---

## Week 9 (May 11–15): Docker, CI/CD & Testing

**Goal:** Containerized deployment; automated testing pipeline.

### Deliverables
- [ ] `Dockerfile` for backend (Python 3.12, uvicorn)
- [ ] `Dockerfile` for frontend (Next.js standalone build)
- [ ] `Dockerfile` for Celery worker + beat
- [ ] `docker-compose.yml` — backend, frontend, PostgreSQL, Redis, Celery worker, Celery beat
- [ ] `.env.example` with all required environment variables
- [ ] GitHub Actions CI pipeline: lint → type-check → test → build
- [ ] Backend test suite: ≥70% coverage on API routes, auth, pipeline
- [ ] Frontend test suite: component tests for critical flows (auth, report generation)
- [ ] Pre-commit hooks: ruff (Python), ESLint + Prettier (TypeScript)
- [ ] Seed script — populate demo workspace with sample data for testing

### Acceptance Criteria
- `docker compose up` starts entire stack from scratch
- CI pipeline passes on clean checkout
- Seed script creates a usable demo environment

---

## Week 10 (May 18–22): Hardening, Polish & Launch Prep

**Goal:** Security audit, performance optimization, production readiness.

### Deliverables
- [ ] Security review: CORS configuration, CSP headers, rate limiting on all endpoints
- [ ] Input sanitization audit (SQL injection, XSS vectors)
- [ ] API error handling audit — all errors return RFC 7807 format
- [ ] Frontend performance: bundle analysis, lazy loading, image optimization
- [ ] LCP target validation (<1.5s on dashboard)
- [ ] Database query optimization: add missing indexes, check N+1 queries
- [ ] Production config: connection pooling, graceful shutdown, health probes
- [ ] AWS infrastructure setup: ECS task definitions, RDS instance, ElastiCache, S3 bucket
- [ ] Deployment script/GitHub Actions CD pipeline
- [ ] User acceptance testing with demo workspace
- [ ] Launch checklist sign-off

### Acceptance Criteria
- No critical/high security findings
- Dashboard LCP <1.5s, initial JS bundle <150KB
- Production deployment runs successfully
- Demo walkthrough completes without errors

---

## Risk Buffer

Weeks 9–10 include buffer for:
- OAuth API approval delays (Meta/Google review)
- AI pipeline edge cases found during integration
- Performance issues requiring query optimization
- Security findings requiring remediation

If OAuth approvals are delayed, use mock platform data for launch and enable real connectors post-launch.

---

## Sprint Velocity Assumptions

- 1 engineer, ~40 hours/week
- Backend-heavy weeks (1–5): ~3–5 API endpoints per day
- Frontend-heavy weeks (6–8): ~1–2 pages per day with API integration
- Infrastructure weeks (9–10): focused on integration and polish
- Each week includes writing tests for that week's deliverables

## Dependencies

| Dependency | Needed By | Status |
|-----------|-----------|--------|
| Meta Ads API access | Week 5 | Not started |
| Google Ads API access | Week 5 | Not started |
| Anthropic API key | Week 4 | Configured in settings |
| AWS account | Week 10 | Not confirmed |
| Domain name | Week 10 | Not confirmed |

---

*Generated from DEVELOPMENT_ROADMAP.md Phase 8 (sub-phases 8.1–8.8), adjusted for current codebase state.*
