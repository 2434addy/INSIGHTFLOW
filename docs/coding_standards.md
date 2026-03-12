# InsightFlow — Coding Standards

## 1. Python (Backend)

### Style & Formatting
- **Formatter:** Ruff (format)
- **Linter:** Ruff (lint)
- **Type checker:** mypy (strict mode)
- **Line length:** 100 characters
- **Python version:** 3.12+

### Naming Conventions
```python
# Variables and functions: snake_case
user_email = "jane@agency.com"
def calculate_roas(revenue: Decimal, spend: Decimal) -> Decimal: ...

# Classes: PascalCase
class ReportService: ...
class MetaAdsClient: ...

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_PAGE_SIZE = 20

# Private: leading underscore
def _validate_date_range(start: date, end: date) -> None: ...

# Module-level: descriptive, no abbreviations
# Good: report_generator.py, metric_normalizer.py
# Bad: rpt_gen.py, norm.py
```

### Type Hints
```python
# Required on all public function signatures
from decimal import Decimal
from uuid import UUID

async def generate_report(
    client_id: UUID,
    date_range: DateRange,
    options: ReportOptions,
) -> Report:
    ...

# Use Pydantic for all API schemas
class CreateClientRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    industry: str | None = None
    website: HttpUrl | None = None
```

### FastAPI Patterns
```python
# Router organization
router = APIRouter(prefix="/clients", tags=["clients"])

@router.get("", response_model=PaginatedResponse[ClientResponse])
async def list_clients(
    workspace: Workspace = Depends(get_current_workspace),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ClientResponse]:
    """List clients in the current workspace."""
    service = ClientService(db)
    return await service.list_clients(workspace.id, pagination)

# Always use dependency injection for:
# - Database sessions
# - Current user / workspace
# - Pagination parameters
# - Feature flags
```

### Database Patterns
```python
# Always scope queries to workspace
async def get_client(self, workspace_id: UUID, client_id: UUID) -> Client:
    result = await self.db.execute(
        select(Client)
        .where(Client.workspace_id == workspace_id)
        .where(Client.id == client_id)
        .where(Client.deleted_at.is_(None))
    )
    client = result.scalar_one_or_none()
    if not client:
        raise NotFoundError(f"Client {client_id} not found")
    return client

# Never construct raw SQL from user input
# Never skip the workspace_id filter
```

### Error Handling
```python
# Use specific exceptions, not generic Exception
# Good
raise NotFoundError(f"Report {report_id} not found")

# Bad
raise Exception("Not found")

# Handle expected errors explicitly
try:
    token = await meta_client.refresh_token(refresh_token)
except OAuthTokenExpiredError:
    await connection_service.mark_expired(connection_id)
    raise ExternalAPIError("Meta Ads token expired. Please reconnect.")
```

## 2. TypeScript (Frontend)

### Style & Formatting
- **Formatter:** Prettier
- **Linter:** ESLint (with Next.js config)
- **Line length:** 100 characters
- **TypeScript:** Strict mode enabled

### Naming Conventions
```typescript
// Variables and functions: camelCase
const userName = "Jane";
function calculateRoas(revenue: number, spend: number): number { ... }

// Components: PascalCase
function KPICard({ value, label, trend }: KPICardProps) { ... }

// Types and interfaces: PascalCase
interface ClientResponse { ... }
type ReportStatus = "generating" | "completed" | "failed";

// Constants: UPPER_SNAKE_CASE
const MAX_FILE_SIZE = 5 * 1024 * 1024;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

// Hooks: use prefix
function useClients(params: ClientListParams) { ... }

// Files: kebab-case
// kpi-card.tsx, use-clients.ts, api-client.ts
```

### Component Patterns
```typescript
// Props interface defined above component
interface KPICardProps {
  value: string | number;
  label: string;
  trend: number;
  trendDirection: "up" | "down" | "neutral";
  icon?: React.ReactNode;
}

// Prefer function declarations for components
function KPICard({ value, label, trend, trendDirection, icon }: KPICardProps) {
  return (
    <Card>
      <CardContent>
        {icon && <div className="text-muted-foreground">{icon}</div>}
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
        <TrendBadge value={trend} direction={trendDirection} />
      </CardContent>
    </Card>
  );
}

// Export at bottom
export { KPICard };
export type { KPICardProps };
```

### Server vs Client Components
```typescript
// Server Component (default) — no "use client" directive
// Use for: data fetching, static content, SEO-critical content
async function ClientsPage() {
  const clients = await getClients();
  return <ClientTable initialData={clients} />;
}

// Client Component — add "use client" directive
// Use for: interactivity, browser APIs, hooks, event handlers
"use client";
function ClientTable({ initialData }: { initialData: Client[] }) {
  const [search, setSearch] = useState("");
  // ...
}
```

### API Calls
```typescript
// Centralized API client with error handling
const apiClient = {
  async get<T>(url: string, config?: RequestConfig): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
        "Content-Type": "application/json",
        "X-Request-ID": crypto.randomUUID(),
      },
      ...config,
    });

    if (!response.ok) {
      throw await ApiError.fromResponse(response);
    }

    const json = await response.json();
    return json.data;
  },
};
```

### Zod Validation
```typescript
// Shared validation schemas (match backend Pydantic models)
const createClientSchema = z.object({
  name: z.string().min(1).max(255),
  industry: z.string().optional(),
  website: z.string().url().optional(),
});

type CreateClientInput = z.infer<typeof createClientSchema>;
```

## 3. General Standards

### Security Checklist (Every PR)
- [ ] No secrets or credentials in code
- [ ] User input validated before use
- [ ] Database queries scoped to workspace
- [ ] Auth/permissions checked on new endpoints
- [ ] No raw SQL or unsanitized HTML rendering
- [ ] External data sanitized before AI prompts

### Performance Checklist
- [ ] No N+1 database queries
- [ ] Pagination on list endpoints
- [ ] Appropriate indexes for new queries
- [ ] No unnecessary re-renders (React)
- [ ] Heavy operations are async (Celery tasks)

### Code Review Shorthand
| Tag | Meaning |
|-----|---------|
| `nit:` | Minor style issue, non-blocking |
| `suggestion:` | Alternative approach, non-blocking |
| `question:` | Need clarification |
| `blocker:` | Must fix before merge |
| `security:` | Security concern, treated as blocker |
| `perf:` | Performance concern |
