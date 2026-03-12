# InsightFlow — API Design

## 1. API Conventions

### Base URL
```
Production:  https://api.insightflow.ai/v1
Staging:     https://api-staging.insightflow.ai/v1
Development: http://localhost:8000/v1
```

### Standards
- **Protocol:** REST over HTTPS
- **Format:** JSON (application/json)
- **Versioning:** URL path prefix (`/v1/`)
- **Authentication:** Bearer token (JWT) in Authorization header
- **Pagination:** Cursor-based for lists (limit + cursor)
- **Filtering:** Query parameters
- **Sorting:** `?sort=field&order=asc|desc`
- **Errors:** RFC 7807 Problem Details format

### Request Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
X-Request-ID: <uuid>  (client-generated, for tracing)
X-Workspace-ID: <workspace_id>  (after workspace selection)
```

### Response Envelope
```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-12T10:30:00Z"
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date range: start_date must be before end_date",
    "details": [
      {
        "field": "start_date",
        "message": "Must be before end_date"
      }
    ]
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-12T10:30:00Z"
  }
}
```

### HTTP Status Codes
| Code | Usage |
|------|-------|
| 200 | Successful GET, PUT, PATCH |
| 201 | Successful POST (resource created) |
| 204 | Successful DELETE |
| 400 | Validation error, bad request |
| 401 | Missing or invalid authentication |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate resource) |
| 422 | Unprocessable entity |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## 2. API Endpoints

### 2.1 Authentication

```
POST   /v1/auth/register          # Create account
POST   /v1/auth/login             # Email/password login
POST   /v1/auth/logout            # Invalidate session
POST   /v1/auth/refresh           # Refresh access token
POST   /v1/auth/forgot-password   # Request password reset
POST   /v1/auth/reset-password    # Reset password with token
POST   /v1/auth/verify-email      # Verify email address
GET    /v1/auth/me                # Get current user profile
PUT    /v1/auth/me                # Update profile
GET    /v1/auth/oauth/google      # Initiate Google OAuth
GET    /v1/auth/oauth/google/callback  # Google OAuth callback
```

#### POST /v1/auth/register
```json
// Request
{
  "email": "jane@agency.com",
  "password": "SecureP@ssw0rd123",
  "full_name": "Jane Smith",
  "agency_name": "Smith Marketing"
}

// Response 201
{
  "data": {
    "user": {
      "id": "usr_abc123",
      "email": "jane@agency.com",
      "full_name": "Jane Smith",
      "email_verified": false
    },
    "workspace": {
      "id": "ws_def456",
      "name": "Smith Marketing"
    }
  }
}
```

#### POST /v1/auth/login
```json
// Request
{
  "email": "jane@agency.com",
  "password": "SecureP@ssw0rd123"
}

// Response 200
{
  "data": {
    "access_token": "eyJhbG...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
// Refresh token set as HttpOnly cookie
```

### 2.2 Workspaces

```
GET    /v1/workspaces              # List user's workspaces
GET    /v1/workspaces/:id          # Get workspace details
PUT    /v1/workspaces/:id          # Update workspace
DELETE /v1/workspaces/:id          # Delete workspace (owner only)
```

### 2.3 Team Members

```
GET    /v1/workspaces/:id/members          # List members
POST   /v1/workspaces/:id/members/invite   # Invite member
PUT    /v1/workspaces/:id/members/:uid     # Update member role
DELETE /v1/workspaces/:id/members/:uid     # Remove member
```

### 2.4 Clients

```
GET    /v1/clients                 # List clients (paginated)
POST   /v1/clients                 # Create client
GET    /v1/clients/:id             # Get client details
PUT    /v1/clients/:id             # Update client
DELETE /v1/clients/:id             # Delete client
GET    /v1/clients/:id/metrics     # Get client metrics (with date range)
GET    /v1/clients/:id/campaigns   # Get client campaigns
```

#### GET /v1/clients?limit=20&cursor=abc&search=acme
```json
// Response 200
{
  "data": [
    {
      "id": "cli_abc123",
      "name": "Acme Corp",
      "platforms": ["meta_ads", "google_ads"],
      "status": "active",
      "total_spend_30d": 12450.00,
      "total_conversions_30d": 543,
      "roas_30d": 4.5,
      "last_synced_at": "2026-03-12T09:00:00Z"
    }
  ],
  "meta": {
    "cursor": "next_abc",
    "has_more": true,
    "total": 47
  }
}
```

#### GET /v1/clients/:id/metrics?start_date=2026-02-01&end_date=2026-02-28&granularity=daily
```json
// Response 200
{
  "data": {
    "summary": {
      "spend": 12450.00,
      "impressions": 892000,
      "clicks": 23400,
      "conversions": 543,
      "revenue": 56025.00,
      "roas": 4.5,
      "cpa": 22.93,
      "ctr": 2.62
    },
    "comparison": {
      "spend_change_pct": 8.5,
      "conversions_change_pct": 15.2,
      "roas_change_pct": 5.1
    },
    "timeseries": [
      {
        "date": "2026-02-01",
        "spend": 445.00,
        "conversions": 19,
        "roas": 4.2
      }
    ],
    "by_platform": [
      {
        "platform": "meta_ads",
        "spend": 7800.00,
        "conversions": 340,
        "roas": 4.8
      },
      {
        "platform": "google_ads",
        "spend": 4650.00,
        "conversions": 203,
        "roas": 4.0
      }
    ]
  }
}
```

### 2.5 Integrations

```
GET    /v1/integrations                   # List available platforms
GET    /v1/integrations/connections        # List active connections
POST   /v1/integrations/connect/:platform # Initiate OAuth for platform
GET    /v1/integrations/callback/:platform # OAuth callback
DELETE /v1/integrations/connections/:id    # Disconnect platform
POST   /v1/integrations/connections/:id/sync  # Trigger manual sync
GET    /v1/integrations/connections/:id/status # Get sync status
```

### 2.6 Reports

```
GET    /v1/reports                     # List reports (paginated)
POST   /v1/reports/generate            # Generate new report
GET    /v1/reports/:id                 # Get report details + content
GET    /v1/reports/:id/pdf             # Download report as PDF
DELETE /v1/reports/:id                 # Delete report
PUT    /v1/reports/:id                 # Update report (edit AI content)
```

#### POST /v1/reports/generate
```json
// Request
{
  "client_id": "cli_abc123",
  "template": "monthly_performance",
  "date_range": {
    "start_date": "2026-02-01",
    "end_date": "2026-02-28"
  },
  "comparison_period": "previous_period",
  "platforms": ["meta_ads", "google_ads"],
  "tone": "executive",
  "sections": ["executive_summary", "channel_breakdown", "insights", "recommendations"]
}

// Response 202 (Accepted - async generation)
{
  "data": {
    "report_id": "rpt_xyz789",
    "status": "generating",
    "estimated_seconds": 45
  }
}
```

#### GET /v1/reports/:id (after generation completes)
```json
// Response 200
{
  "data": {
    "id": "rpt_xyz789",
    "client_id": "cli_abc123",
    "client_name": "Acme Corp",
    "template": "monthly_performance",
    "status": "completed",
    "date_range": { "start_date": "2026-02-01", "end_date": "2026-02-28" },
    "generated_at": "2026-03-12T10:30:00Z",
    "sections": [
      {
        "type": "executive_summary",
        "title": "Executive Summary",
        "content": "In February 2026, Acme Corp's marketing campaigns delivered strong results..."
      },
      {
        "type": "metrics_overview",
        "title": "Key Metrics",
        "data": { "spend": 12450, "conversions": 543, "roas": 4.5 }
      },
      {
        "type": "insights",
        "title": "AI Insights",
        "items": [
          "Meta retargeting campaigns drove 62% of conversions at 30% lower CPA...",
          "Google Search CPA decreased 12% after bid strategy optimization...",
          "Weekend conversion rates are 23% higher than weekdays..."
        ]
      },
      {
        "type": "recommendations",
        "title": "Recommendations",
        "items": [
          "Increase Meta retargeting budget by 20% to capitalize on efficiency...",
          "Test responsive search ads on Google for brand campaigns...",
          "Shift 15% of weekday budget to weekends..."
        ]
      }
    ]
  }
}
```

### 2.7 Dashboard

```
GET    /v1/dashboard/overview      # Aggregated KPIs across all clients
GET    /v1/dashboard/trends        # Trend data for charts
GET    /v1/dashboard/alerts        # System alerts and notifications
```

## 3. WebSocket Events (Real-time Updates)

```
ws://api.insightflow.ai/v1/ws

// Events:
report.generating    → { report_id, progress_pct }
report.completed     → { report_id }
report.failed        → { report_id, error }
sync.started         → { connection_id, platform }
sync.completed       → { connection_id, records_synced }
sync.failed          → { connection_id, error }
```

## 4. Rate Limiting Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1710243600
Retry-After: 30  (only when 429)
```
