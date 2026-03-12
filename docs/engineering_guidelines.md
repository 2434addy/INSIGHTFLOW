# InsightFlow — Engineering Guidelines

## 1. Development Principles

1. **Security by default.** Every feature starts with a threat model consideration.
2. **Ship incrementally.** Small PRs, feature flags, continuous deployment.
3. **Test what matters.** Focus on behavior, not implementation details.
4. **Automate everything.** If you do it twice, automate the third time.
5. **Document decisions.** Code explains *what*; comments and ADRs explain *why*.

## 2. Git Workflow

### Branch Strategy
- **main:** Production-ready code. Protected, requires PR + review.
- **develop:** Integration branch. Feature branches merge here first.
- **feature/<ticket-id>-<short-description>:** Feature development.
- **fix/<ticket-id>-<short-description>:** Bug fixes.
- **hotfix/<description>:** Emergency production fixes (branch from main).

### Commit Messages
Follow Conventional Commits:
```
<type>(<scope>): <short description>

<body — explain WHY, not what>

<footer — ticket references>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `security`

Examples:
```
feat(reports): add PDF export for generated reports

Agencies need to download reports for offline client meetings.
PDF uses WeasyPrint for server-side HTML-to-PDF conversion.

Closes #142
```

### Pull Requests
- **Title:** Follows commit message format
- **Description:** What, Why, How, Testing, Screenshots (if UI)
- **Size:** < 400 lines changed (split large features into stacked PRs)
- **Reviews:** 1 required approval minimum; 2 for security-sensitive changes
- **CI:** All checks must pass before merge
- **Merge:** Squash merge to keep history clean

## 3. Code Review Standards

### What Reviewers Check
- [ ] Correctness: Does it do what it claims?
- [ ] Security: Any new attack surfaces? Input validation? Auth checks?
- [ ] Performance: N+1 queries? Unnecessary re-renders? Missing indexes?
- [ ] Tenant isolation: Is workspace_id enforced in all queries?
- [ ] Error handling: What happens when things fail?
- [ ] Tests: Are edge cases covered?
- [ ] Naming: Are variables, functions, and files named clearly?

### Review Turnaround
- Aim to review within 4 hours during business hours
- Blocking feedback: respond within 1 hour
- Use conventional comments: `nit:`, `suggestion:`, `question:`, `blocker:`

## 4. Testing Strategy

### Testing Pyramid
```
          ┌─────┐
          │ E2E │  ~10% — Critical user journeys
         ┌┴─────┴┐
         │ Integ. │  ~30% — API endpoints, DB queries, service interactions
        ┌┴───────┴┐
        │  Unit    │  ~60% — Business logic, utilities, pure functions
        └─────────┘
```

### Backend Testing
| Type | Tool | Coverage Target |
|------|------|----------------|
| Unit | pytest | Business logic: 90%+ |
| Integration | pytest + TestClient | All API endpoints |
| Database | pytest + test DB | All queries, RLS policies |
| Security | pytest + custom | Auth, permissions, tenant isolation |

### Frontend Testing
| Type | Tool | Coverage Target |
|------|------|----------------|
| Unit | Vitest | Hooks, utilities: 90%+ |
| Component | Vitest + Testing Library | Interactive components |
| E2E | Playwright | Critical flows (sign up, connect, generate report) |
| Visual | Playwright screenshots | Key pages, responsive breakpoints |

### Mandatory Test Cases
Every PR that touches data access MUST include:
- Test that verifies tenant isolation (user A cannot access user B's data)
- Test that verifies permission enforcement (member cannot perform admin actions)

## 5. CI/CD Pipeline

```
PR Created
  │
  ├── Lint (Ruff for Python, ESLint for TS)
  ├── Type Check (mypy for Python, tsc for TS)
  ├── Unit Tests
  ├── Integration Tests
  ├── Security Scan (Snyk / Trivy)
  └── Build Check
  │
  ▼
PR Approved + Merged to develop
  │
  ├── Full Test Suite
  ├── Build Docker Images
  ├── Push to ECR
  └── Deploy to Staging
  │
  ▼
Staging Verified (manual or automated smoke tests)
  │
  └── Merge develop → main
      │
      ├── Full Test Suite
      ├── Build Production Images
      ├── Deploy to Production (blue/green)
      └── Post-deploy Smoke Tests
```

## 6. Environment Management

| Environment | Purpose | Data | URL |
|------------|---------|------|-----|
| Local | Development | Seeded test data | localhost:3000 / localhost:8000 |
| Staging | Pre-production testing | Anonymized prod-like data | staging.insightflow.ai |
| Production | Live users | Real data | app.insightflow.ai |

### Environment Variables
- **Never** commit secrets to git
- Use `.env.example` with placeholder values (committed)
- Use `.env.local` for actual values (gitignored)
- Production secrets in AWS Secrets Manager
- All env vars validated at startup (fail fast if missing)

## 7. Error Handling

### Backend
```python
# Custom exception hierarchy
class InsightFlowError(Exception): ...
class NotFoundError(InsightFlowError): ...    # → 404
class ForbiddenError(InsightFlowError): ...   # → 403
class ValidationError(InsightFlowError): ...  # → 422
class ExternalAPIError(InsightFlowError): ... # → 502

# Global exception handler converts to RFC 7807 responses
```

### Frontend
- **API errors:** Caught in TanStack Query `onError`, displayed via toast
- **Render errors:** React Error Boundaries with fallback UI
- **Unhandled errors:** Global handler → error reporting service (Sentry)

## 8. Logging Standards

### Structured Logging (JSON)
```python
logger.info(
    "Report generated",
    extra={
        "workspace_id": workspace_id,
        "client_id": client_id,
        "report_id": report_id,
        "duration_ms": duration,
        "ai_tokens": tokens_used,
    }
)
```

### Log Levels
| Level | When to Use |
|-------|------------|
| ERROR | Unexpected failures requiring investigation |
| WARN | Degraded operation, recoverable issues |
| INFO | Significant business events (report generated, user signed up) |
| DEBUG | Detailed flow information (dev only, never in prod) |

### Never Log
- Passwords, tokens, API keys, PII
- Full request/response bodies (use truncation)
- Stack traces for expected errors (4xx responses)

## 9. Dependency Management

- Pin exact versions in lock files (poetry.lock, pnpm-lock.yaml)
- Automated dependency updates via Dependabot (weekly)
- Review all dependency updates for breaking changes
- Audit new dependencies for: maintenance health, security history, license compatibility
- Prefer well-maintained libraries with > 1000 GitHub stars
- No dependencies for trivial operations (don't install a library to check if a string is empty)
