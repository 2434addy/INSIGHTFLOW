# InsightFlow Security Architecture — Post-Review Update

> **Version:** 1.1 — Architecture review additions
> **Complements:** `security/security_architecture.md` (original design)

---

## 1. Security Layers Implemented

### 1.1 Authentication
- **JWT Access Tokens** (HS256, 15-min expiry)
- **Refresh Tokens** (7-day expiry, HttpOnly cookies)
- **Bcrypt Password Hashing** (cost factor 12)
- **Account Lockout** — 5 failed attempts triggers lock
- **Password Policy** — min 12 chars, upper, lower, digit, special char
- **Generic Error Messages** — no user enumeration on login failure

### 1.2 Authorization
- **Role-Based Access Control** — owner, admin, member, viewer
- **Organization Membership** — verified via `get_current_organization()` dependency
- **Role Checking** — `require_role()` dependency factory
- **Tenant Isolation** — all queries scoped to `organization_id`

### 1.3 Middleware Security Stack

Request processing order (outermost → innermost):

| Order | Middleware | Purpose |
|-------|-----------|---------|
| 1 | **CORSMiddleware** | Cross-origin access control |
| 2 | **SecurityHeadersMiddleware** | OWASP security headers |
| 3 | **RateLimiterMiddleware** | Sliding-window rate limiting |
| 4 | **RequestContextMiddleware** | Request ID + distributed tracing |

### 1.4 Security Headers (NEW)

Added via `SecurityHeadersMiddleware`:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS protection (legacy) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | URL leak prevention |
| `Permissions-Policy` | `camera=(), microphone=()...` | Disable unused APIs |
| `Content-Security-Policy` | `default-src 'none'` | CSP for API responses |
| `Strict-Transport-Security` | `max-age=31536000` | HSTS (production only) |

### 1.5 Rate Limiting (NEW)

Added via `RateLimiterMiddleware`:

| Category | Limit | Endpoints |
|----------|-------|-----------|
| **Auth** | 5 per 15 minutes | `/v1/auth/*` |
| **API** | 100 per minute | All `/v1/*` endpoints |
| **Report Generation** | 10 per hour | `/v1/reports/*/generate` |
| **Exempt** | No limit | `/v1/health`, `/docs` |

Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 2. Data Protection

### 2.1 Encryption at Rest
- **OAuth Tokens** — AES-256-GCM envelope encryption (`utils/encryption.py`)
  - Random 12-byte nonce per encryption
  - Master key from application SECRET_KEY (production: AWS KMS)
  - Tamper detection via GCM authentication tag
- **Database** — PostgreSQL TDE + AWS RDS encryption
- **Backups** — S3 server-side encryption (AES-256)

### 2.2 Encryption in Transit
- **TLS 1.3** required on all external connections
- **HSTS** enforced in production (1-year max-age + preload)
- **Internal** — VPC-internal connections via private subnets

### 2.3 Safe Logging (NEW)

`utils/sanitize.py` provides:

| Function | Purpose |
|----------|---------|
| `sanitize_dict()` | Recursively redacts sensitive keys (password, token, secret, etc.) |
| `sanitize_url()` | Removes credentials from database/service URLs |
| `sanitize_headers()` | Redacts Authorization, Cookie, API key headers |

**Rule:** All request/response payloads MUST be sanitized before logging.

---

## 3. Input Validation

### 3.1 API Layer
- **Pydantic schemas** validate all request bodies with strict mode
- **FastAPI dependencies** validate query parameters (pagination limits, UUIDs)
- **RFC 7807** error responses for validation failures

### 3.2 Pipeline Layer
- **Stage 1 (Data Validation)** validates all metric records before processing
- **Pydantic models** enforce type safety between all pipeline stages
- **Max record limit** (50,000) prevents resource exhaustion

### 3.3 Database Layer
- **SQLAlchemy ORM only** — no raw SQL with user input
- **Parameterized queries** — all values bound as parameters
- **Row-Level Security** — PostgreSQL enforces tenant isolation at DB level

---

## 4. Error Handling Security

- **Unhandled exceptions** return generic "An unexpected error occurred" (no stack traces)
- **Application errors** return structured codes (NOT_FOUND, FORBIDDEN, etc.)
- **Error logging** captures full context internally but never exposes to client
- **Request ID** in every response for support correlation without exposing internals

---

## 5. Production Hardening Checklist

| Item | Status |
|------|--------|
| JWT secret key rotation | Configured via env vars |
| Password hashing (bcrypt, cost 12) | ✅ Implemented |
| Account lockout | ✅ Implemented |
| CORS restricted to configured origins | ✅ Implemented |
| Rate limiting | ✅ Implemented (in-memory; Redis for multi-worker) |
| Security headers (OWASP) | ✅ Implemented |
| Input validation (Pydantic) | ✅ Implemented |
| Safe logging (no secrets) | ✅ Implemented |
| OAuth token encryption | ✅ Implemented |
| Cursor-based pagination | ✅ Implemented |
| SQL injection prevention (ORM only) | ✅ Implemented |
| Swagger/ReDoc disabled in production | ✅ Implemented |
| Generic login error messages | ✅ Implemented |
| HSTS in production | ✅ Implemented |
| RLS enforcement | Design complete, migration pending |
| Redis-backed rate limiting | TODO for multi-worker deploy |
| Token revocation list | TODO |
| Audit logging | TODO |
| IP allowlisting (admin endpoints) | TODO |

---

## 6. Threat Mitigations

| Threat | Mitigation |
|--------|-----------|
| **Credential Stuffing** | Rate limiting (5/15min on auth) + account lockout |
| **JWT Theft** | Short expiry (15min) + HttpOnly refresh cookies |
| **SQL Injection** | ORM-only queries, no raw SQL |
| **XSS** | API-only backend (no HTML), CSP headers |
| **Clickjacking** | X-Frame-Options: DENY |
| **CSRF** | SameSite cookies + Bearer token auth |
| **Tenant Data Leak** | Organization-scoped queries + PostgreSQL RLS |
| **Secret Exposure** | Sanitized logging + env-based config |
| **Token Tampering** | AES-256-GCM with authentication tag |
| **DDoS** | Rate limiting + CloudFlare WAF (infrastructure) |
