# InsightFlow Backend — Security Architecture

## Overview

This document describes the security measures implemented in the InsightFlow backend. All security decisions prioritize defense-in-depth: multiple overlapping layers so that no single failure compromises the system.

---

## 1. Secrets & Environment

| Measure | Implementation |
|---------|---------------|
| Configuration via env vars | `pydantic-settings` loads all config from environment variables |
| No hardcoded secrets | `SECRET_KEY`, `DATABASE_URL`, `ANTHROPIC_API_KEY` all from env |
| Production startup validation | App **refuses to start** if `SECRET_KEY` is the default placeholder, too short (<64 chars), `DEBUG=True`, or `ALLOWED_HOSTS=["*"]` |
| `.env` excluded from VCS | `.gitignore` blocks `.env`, `.env.*`, credential files (`*.pem`, `*.key`, `credentials.json`) |
| `.env.example` with guidance | Placeholder values with comments explaining how to generate real secrets |
| Secret masking in logs | `app/utils/sanitize.py` redacts passwords, tokens, API keys from structured log output |

**Key file:** `app/core/config.py` — `Settings._validate_production_safety()`

---

## 2. Authentication & JWT

| Measure | Implementation |
|---------|---------------|
| Password hashing | bcrypt, configurable rounds (default 12) |
| Password policy | 12+ chars, uppercase, lowercase, digit, special character |
| Access tokens | JWT HS256, 15-minute expiry, unique `jti` claim |
| Refresh tokens | JWT HS256, 7-day expiry, stored as **HttpOnly/Secure/SameSite=Strict** cookie |
| Token rotation | New refresh token issued on every `/auth/refresh`; old one revoked |
| Token revocation | In-memory blacklist via `jti` claim (replace with Redis for multi-worker) |
| Logout | Both access and refresh tokens revoked, cookie cleared |
| Account lockout | 30-minute lockout after 5 failed login attempts |
| No user enumeration | Same error message for wrong email and wrong password |
| Email validation | Pydantic `EmailStr` with `email-validator` library |

**Key files:**
- `app/core/security.py` — token creation, verification, revocation
- `app/services/auth_service.py` — login, register, lockout logic
- `app/api/v1/endpoints/auth.py` — endpoints with cookie handling

---

## 3. API Security

| Measure | Implementation |
|---------|---------------|
| JWT required on all endpoints | `get_current_user()` dependency validates Bearer token (except `/health`, `/auth/login`, `/auth/register`) |
| Organization isolation | `X-Organization-ID` header + membership verification |
| Role-based access control | `require_role()` dependency factory for owner/admin/member/viewer |
| Request ID tracing | `X-Request-ID` header generated or forwarded, bound to structlog |
| Input validation | Pydantic strict mode on all request schemas |
| Request body size limit | `RequestSizeLimitMiddleware` rejects bodies > 1 MB (configurable) |
| No stack traces in production | `unhandled_error_handler` returns generic "An unexpected error occurred" |
| No internal IDs leaked | Response schemas explicitly define which fields are exposed |
| CORS restricted | Only configured origins allowed (`CORS_ORIGINS`), never wildcard `*` |
| Swagger UI disabled in production | `docs_url=None`, `redoc_url=None`, `openapi_url=None` |

**Key files:**
- `app/api/deps.py` — auth dependencies
- `app/middleware/error_handler.py` — error masking
- `app/middleware/request_size.py` — body size limit

---

## 4. Database Security

| Measure | Implementation |
|---------|---------------|
| No raw SQL | All queries via SQLAlchemy ORM (parameterized) |
| Connection pooling | Pool size 20, max overflow 10, timeout 30s |
| Connection verification | `pool_pre_ping=True` detects stale connections |
| SSL support | `DB_SSL_REQUIRED` setting enforces encrypted connections |
| Soft-delete filtering | All repository queries filter `WHERE deleted_at IS NULL` |
| Multi-tenant isolation | All data scoped by `organization_id` |
| RLS designed | PostgreSQL Row-Level Security policies specified in schema |

**Key file:** `app/core/database.py`

**Note:** Database user privileges should follow least-privilege principle. The application user should have `SELECT, INSERT, UPDATE, DELETE` only on application tables — no `CREATE`, `DROP`, `ALTER`, or superuser permissions.

---

## 5. Rate Limiting & DDoS Protection

| Measure | Implementation |
|---------|---------------|
| Auth endpoints | 5 requests / 15 minutes per IP |
| Report generation | 10 requests / hour per IP |
| General API | 100 requests / minute per IP |
| Health endpoints | Exempt (for load balancer health checks) |
| Rate limit headers | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` |
| Retry-After header | Included in 429 responses |
| Request body limit | 1 MB max (configurable via `MAX_REQUEST_BODY_BYTES`) |
| Gunicorn limits | `--limit-request-line 8190`, `--limit-request-fields 100` |

**Key file:** `app/middleware/rate_limiter.py`

**Production note:** Replace in-memory rate limiter with Redis-backed implementation for multi-worker deployments.

---

## 6. Security Headers

Every response includes these OWASP-recommended headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS protection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer leakage |
| `Permissions-Policy` | `camera=(), microphone=(), ...` | Disable unused browser APIs |
| `X-Permitted-Cross-Domain-Policies` | `none` | Block Adobe cross-domain |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` | Strict CSP for API routes |
| `Cache-Control` | `no-store, no-cache, must-revalidate` | Prevent caching of sensitive data |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | HSTS (production only) |

**CSP relaxation:** `/docs` and `/redoc` in development mode use a relaxed CSP that allows Swagger UI resources from `cdn.jsdelivr.net`. These paths are disabled in production.

**Key file:** `app/middleware/security_headers.py`

---

## 7. Logging & Monitoring

| Measure | Implementation |
|---------|---------------|
| Structured logging | structlog with JSON output in production |
| Request context binding | `request_id`, `method`, `path` auto-bound to all log entries |
| Auth event logging | Login success/failure, registration, account lockout logged |
| Sensitive data redaction | `sanitize_dict()`, `sanitize_url()`, `sanitize_headers()` |
| No passwords in logs | Password fields never logged; auth service logs user_id only |
| Error logging | All unhandled exceptions logged with full context |

**Key files:**
- `app/core/logging.py` — structured logging setup
- `app/utils/sanitize.py` — sensitive data redaction
- `app/middleware/request_context.py` — request context binding

---

## 8. Encryption

| Measure | Implementation |
|---------|---------------|
| OAuth token encryption | AES-256-GCM (authenticated encryption) |
| Per-encryption nonce | 12-byte random nonce for each encryption |
| Safe serialization | base64url encoding (nonce + ciphertext + tag) |

**Key file:** `app/utils/encryption.py`

**Production note:** Replace the master key derivation with AWS KMS integration. Use per-connection DEKs wrapped with a KMS-managed master key.

---

## 9. Container Security

| Measure | Implementation |
|---------|---------------|
| Multi-stage Docker build | Separate builder and production stages |
| Non-root user | `appuser` with no shell (`/bin/false`) |
| Minimal base image | `python:3.12-slim` |
| No secrets in image | `.env` files removed in Dockerfile; `.dockerignore` excludes them |
| Health check | `curl -f http://localhost:8000/v1/health` |
| Request limits | Gunicorn `--limit-request-line`, `--limit-request-fields` |
| Graceful shutdown | `--graceful-timeout 30` |

**Key file:** `Dockerfile`

---

## 10. Dependency Security

Security-critical dependencies:
- `pyjwt[crypto]>=2.10.1` — JWT with cryptographic verification
- `bcrypt>=4.2.1` — Password hashing
- `cryptography>=44.0.0` — AES-256-GCM encryption
- `email-validator>=2.2.0` — Email format validation
- `ruff` with `flake8-bandit` (S rules) — Static security analysis

**Update strategy:** Pin all dependencies in `requirements.txt`. Run `pip audit` or `safety check` before each release. Update security-critical packages within 48 hours of CVE disclosure.

---

## 11. Responsible Disclosure

Security contact information is available at `/.well-known/security.txt` per RFC 9116.

---

## Known Limitations & Production Recommendations

1. **Token blacklist is in-memory** — Replace with Redis `SETNX` + TTL for multi-worker deployments
2. **Rate limiter is in-memory** — Replace with Redis-backed sliding window for horizontal scaling
3. **Encryption uses derived master key** — Integrate AWS KMS for proper key management
4. **No CSRF tokens** — Not needed for pure-API with JWT Bearer auth, but add if serving HTML forms
5. **RLS policies designed but not enforced** — Call `SET LOCAL app.current_workspace_id` in session middleware
6. **No email verification flow** — `email_verified` field exists but is unused
7. **No password reset flow** — Schema exists (`ForgotPasswordRequest`, `ResetPasswordRequest`) but endpoints not implemented
