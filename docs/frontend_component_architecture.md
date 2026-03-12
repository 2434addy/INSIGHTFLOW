# InsightFlow — Frontend Component Architecture

## Overview

This document defines the reusable component map for the InsightFlow frontend built with **Next.js 14 (App Router)**, **TypeScript (strict)**, **Tailwind CSS**, and **shadcn/ui**. Components are grouped by domain and responsibility. Each entry specifies its props contract, rendering pattern, and data dependencies.

**Source of truth:** `frontend/wireframes/dashboard_wireframes.jsx`

---

## Design Principles

1. **Server Components by default** — only add `"use client"` for interactivity (state, effects, browser APIs)
2. **Composition over inheritance** — small, single-responsibility components composed together
3. **Props over context** — explicit data flow; context reserved for cross-cutting concerns (auth, theme)
4. **Co-location** — page-specific components live next to their route; shared components live in `src/components/`
5. **Type-safe contracts** — every component has a TypeScript props interface

---

## Design Tokens

| Token | Value | Tailwind Class |
|-------|-------|----------------|
| Primary | `#2563EB` | `blue-600` |
| Primary Hover | `#1D4ED8` | `blue-700` |
| Success | `#16A34A` | `green-600` |
| Danger | `#DC2626` | `red-600` |
| Warning | `#D97706` | `amber-600` |
| Background | `#F9FAFB` | `neutral-50` |
| Card BG | `#FFFFFF` | `white` |
| Text Primary | `#111827` | `neutral-900` |
| Text Secondary | `#6B7280` | `neutral-500` |
| Border | `#E5E7EB` | `neutral-200` |
| Font | Inter | `font-sans` (via CSS var) |
| Card Radius | `12px` | `rounded-xl` |
| Button/Input Radius | `8px` | `rounded-lg` |
| Badge Radius | `9999px` | `rounded-full` |

---

## Directory Structure

```
src/
├── app/
│   ├── layout.tsx                          # Root layout (Inter font, Providers)
│   ├── page.tsx                            # Redirect → /dashboard
│   ├── globals.css                         # Tailwind layers + CSS variables
│   ├── (auth)/
│   │   ├── login/page.tsx                  # Login page
│   │   └── register/page.tsx               # Register page
│   └── (dashboard)/
│       ├── layout.tsx                      # Sidebar + main content wrapper
│       ├── dashboard/
│       │   ├── page.tsx                    # Server Component shell
│       │   └── dashboard-content.tsx       # Client Component — KPIs, charts, table
│       ├── clients/
│       │   ├── page.tsx                    # Client list (portal)
│       │   ├── clients-content.tsx         # Client cards grid
│       │   └── [id]/
│       │       ├── page.tsx               # Client detail
│       │       └── client-detail-content.tsx
│       ├── insights/
│       │   ├── page.tsx
│       │   └── insights-content.tsx        # Filters + insight/rec cards
│       ├── campaigns/
│       │   ├── page.tsx
│       │   └── campaigns-content.tsx       # Tier filter + sortable table
│       ├── reports/
│       │   ├── page.tsx                    # Report list
│       │   ├── reports-list-content.tsx
│       │   ├── generate/
│       │   │   ├── page.tsx               # Report builder
│       │   │   └── report-builder-content.tsx
│       │   └── [id]/
│       │       ├── page.tsx               # Report viewer
│       │       └── report-content.tsx
│       └── settings/
│           ├── page.tsx
│           └── settings-content.tsx        # Tab-based settings
│
├── components/
│   ├── layout/                             # App shell components
│   ├── dashboard/                          # Dashboard-specific widgets
│   ├── charts/                             # Recharts wrappers
│   ├── tables/                             # Data table components
│   ├── insights/                           # Insight & recommendation cards
│   ├── reports/                            # Report builder & viewer components
│   └── ui/                                 # Shared primitives (shadcn-based)
│
├── hooks/                                  # Custom React hooks
├── stores/                                 # Zustand stores
├── lib/                                    # Utilities, API client
└── types/                                  # TypeScript type definitions
```

---

## 1. Layout Components

**Directory:** `src/components/layout/`

These components form the persistent app shell visible on every authenticated page.

### Sidebar

| Field | Value |
|-------|-------|
| File | `sidebar.tsx` |
| Directive | `"use client"` |
| Status | **Exists** |

```typescript
// No props — reads collapse state from useUIStore
export function Sidebar(): JSX.Element
```

**Renders:** Logo, 7 nav items (Dashboard, Clients, Insights, Campaigns, Reports, Integrations, Settings), Help footer. Collapsible between 240px and 64px. Active item highlighted via `usePathname()`.

**Nav items:**

| Label | Icon | Route |
|-------|------|-------|
| Dashboard | `BarChart3` | `/dashboard` |
| Clients | `Users` | `/clients` |
| Insights | `Lightbulb` | `/insights` |
| Campaigns | `Megaphone` | `/campaigns` |
| Reports | `FileText` | `/reports` |
| Integrations | `Link` | `/integrations` |
| Settings | `Settings` | `/settings` |

**Depends on:** `useUIStore` (Zustand), `usePathname()` (Next.js)

---

### Topbar

| Field | Value |
|-------|-------|
| File | `topbar.tsx` |
| Directive | `"use client"` |
| Status | **Exists** |

```typescript
interface TopbarProps {
  title: string;
}
export function Topbar({ title }: TopbarProps): JSX.Element
```

**Renders:** Page title (left), search trigger (Ctrl+K), notification bell with count badge, user avatar with dropdown.

---

### CommandMenu *(planned)*

| Field | Value |
|-------|-------|
| File | `command-menu.tsx` |
| Directive | `"use client"` |
| Status | **Not built** |

```typescript
export function CommandMenu(): JSX.Element
```

**Renders:** Full-screen command palette (cmdk / shadcn Command). Triggered by Ctrl+K from Topbar. Searches clients, reports, campaigns, and navigation items.

**Depends on:** `cmdk` library, API search endpoint

---

## 2. Dashboard Components

**Directory:** `src/components/dashboard/`

Widgets used on the main dashboard and reused across client detail and report pages.

### KPICard

| Field | Value |
|-------|-------|
| File | `kpi-card.tsx` |
| Directive | Server-safe |
| Status | **Exists** |

```typescript
interface KPICardProps {
  label: string;
  value: string;
  change?: number | null;       // % change — green if positive, red if negative
  changeLabel?: string;         // e.g. "vs prev period"
  icon?: ReactNode;
  invertColor?: boolean;        // true for CPA where decrease = good
}
export function KPICard(props: KPICardProps): JSX.Element
```

**Used in:** Dashboard (4 cards), Campaign Performance (4 cards), Report Viewer (4 cards), Client Detail (4 cards)

---

### DateRangePicker *(planned)*

| Field | Value |
|-------|-------|
| File | `date-range-picker.tsx` |
| Directive | `"use client"` |
| Status | **Not built** |

```typescript
interface DateRangePickerProps {
  value: { from: Date; to: Date };
  onChange: (range: { from: Date; to: Date }) => void;
  presets?: Array<{ label: string; from: Date; to: Date }>;
  compareEnabled?: boolean;
}
export function DateRangePicker(props: DateRangePickerProps): JSX.Element
```

**Renders:** Preset buttons (Last 7d, 30d, Quarter, Custom) + calendar popover for custom range. Optional "Compare with previous period" checkbox.

**Used in:** Dashboard header, Report Builder step 2

---

## 3. Chart Components

**Directory:** `src/components/charts/`

All chart components wrap Recharts and require `"use client"` because Recharts uses DOM APIs.

### PerformanceChart

| Field | Value |
|-------|-------|
| File | `performance-chart.tsx` |
| Directive | `"use client"` |
| Current location | `src/components/dashboard/performance-chart.tsx` |
| Status | **Exists** — move to `charts/` |

```typescript
interface PerformanceChartProps {
  data: DailyMetric[];
  title?: string;               // defaults to "Spend & Conversions Over Time"
}
export function PerformanceChart(props: PerformanceChartProps): JSX.Element
```

**Renders:** Dual Y-axis `LineChart`. Left axis = Spend (blue `#2563EB`), Right axis = Conversions (green `#16A34A`). Responsive container, tooltip on hover, date X-axis labels.

**Used in:** Dashboard, Report Viewer, Client Detail

---

### PlatformChart

| Field | Value |
|-------|-------|
| File | `platform-chart.tsx` |
| Directive | `"use client"` |
| Current location | `src/components/dashboard/platform-chart.tsx` |
| Status | **Exists** — move to `charts/` |

```typescript
interface PlatformChartProps {
  data: Record<string, KPISummary>;
}
export function PlatformChart(props: PlatformChartProps): JSX.Element
```

**Renders:** Donut `PieChart` showing spend distribution. Platform colors: Meta `#3B82F6`, Google `#F59E0B`, GA4 `#8B5CF6`, Shopify `#10B981`. Legend below with platform name + percentage.

**Used in:** Dashboard

---

### BarChart *(planned)*

| Field | Value |
|-------|-------|
| File | `bar-chart.tsx` |
| Directive | `"use client"` |
| Status | **Not built** |

```typescript
interface BarChartProps {
  data: Array<Record<string, unknown>>;
  xKey: string;
  yKeys: string[];
  colors?: string[];
  stacked?: boolean;
}
export function BarChart(props: BarChartProps): JSX.Element
```

**Renders:** Vertical or stacked bar chart. Generic wrapper for campaign comparisons and platform breakdowns.

**Used in:** Client Detail (campaign spend comparison)

---

## 4. Table Components

**Directory:** `src/components/tables/`

### DataTable *(planned)*

| Field | Value |
|-------|-------|
| File | `data-table.tsx` |
| Directive | `"use client"` |
| Status | **Not built** — currently tables are inline in page content |

```typescript
interface Column<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  align?: "left" | "right";
  render?: (value: T[keyof T], row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  sortKey?: keyof T;
  sortAsc?: boolean;
  onSort?: (key: keyof T) => void;
  emptyMessage?: string;
}
export function DataTable<T>(props: DataTableProps<T>): JSX.Element
```

**Renders:** Full-width table with sortable column headers (`ArrowUpDown` icon), hover rows, responsive horizontal scroll. Used as the base for campaign and client tables.

**Used in:** Campaign Performance, Dashboard (top campaigns), Client Detail (campaign breakdown)

---

### SortButton

| Field | Value |
|-------|-------|
| File | `sort-button.tsx` |
| Directive | `"use client"` |
| Status | **Exists** (inline in campaigns-content.tsx) — extract |

```typescript
interface SortButtonProps {
  label: string;
  active: boolean;
  asc?: boolean;
  onClick: () => void;
}
export function SortButton(props: SortButtonProps): JSX.Element
```

**Renders:** Column header button with `ArrowUpDown` icon. Active state turns icon blue.

---

### EfficiencyBar

| Field | Value |
|-------|-------|
| File | `efficiency-bar.tsx` |
| Directive | Server-safe |
| Status | **Not built** — currently inline in campaigns-content.tsx |

```typescript
interface EfficiencyBarProps {
  score: number;                // 0–1
  showLabel?: boolean;          // show numeric value next to bar
}
export function EfficiencyBar(props: EfficiencyBarProps): JSX.Element
```

**Renders:** 64px-wide progress bar. Color: green (>=0.7), amber (>=0.4), red (<0.4). Optional numeric label.

**Used in:** Campaign Performance table score column

---

## 5. Insight Components

**Directory:** `src/components/insights/`

### InsightCard

| Field | Value |
|-------|-------|
| File | `insight-card.tsx` |
| Directive | Server-safe |
| Current location | `src/components/reports/insight-card.tsx` |
| Status | **Exists** — move to `insights/` |

```typescript
interface InsightCardProps {
  insight: Insight;
}
export function InsightCard({ insight }: InsightCardProps): JSX.Element
```

**Renders:** Card with colored left border (sentiment), category icon, headline, detail text, confidence %, optional platform badge.

| Sentiment | Left Border | Icon Color |
|-----------|-------------|------------|
| `positive` | `green-500` | `green-600` |
| `attention_needed` | `amber-500` | `amber-600` |
| `neutral` | `blue-500` | `blue-600` |

| Category | Icon |
|----------|------|
| `performance` | `TrendingUp` |
| `efficiency` | `Zap` |
| `anomaly` | `AlertTriangle` |
| `opportunity` | `Lightbulb` |
| `risk` | `Shield` |
| `growth` | `ArrowUpRight` |

**Used in:** Insights page, Report Viewer

---

### RecommendationCard

| Field | Value |
|-------|-------|
| File | `recommendation-card.tsx` |
| Directive | Server-safe |
| Current location | `src/components/reports/recommendation-card.tsx` |
| Status | **Exists** — move to `insights/` |

```typescript
interface RecommendationCardProps {
  recommendation: Recommendation;
}
export function RecommendationCard({ recommendation }: RecommendationCardProps): JSX.Element
```

**Renders:** Card with title, priority badge (red/amber/green), effort badge, description, expected impact (blue), action items checklist.

| Priority | Badge Variant |
|----------|---------------|
| `critical` | `danger` |
| `high` | `warning` |
| `medium` | `default` |
| `low` | `neutral` |

**Used in:** Insights page, Report Viewer

---

### FilterPills

| Field | Value |
|-------|-------|
| File | `filter-pills.tsx` |
| Directive | `"use client"` |
| Status | **Not built** — currently inline in insights-content.tsx |

```typescript
interface FilterOption<T extends string> {
  label: string;
  value: T;
  count?: number;
}

interface FilterPillsProps<T extends string> {
  options: FilterOption<T>[];
  value: T;
  onChange: (value: T) => void;
}
export function FilterPills<T extends string>(props: FilterPillsProps<T>): JSX.Element
```

**Renders:** Horizontal row of rounded-full buttons. Active pill is solid blue; inactive is gray-100. Each shows optional count badge.

**Used in:** Insights page (category filter), Campaign Performance (tier filter)

---

## 6. Report Components

**Directory:** `src/components/reports/`

### ReportCard

| Field | Value |
|-------|-------|
| File | `report-card.tsx` |
| Directive | Server-safe |
| Status | **Exists** (inline in reports-list-content.tsx) — extract |

```typescript
interface ReportCardProps {
  report: Report;
}
export function ReportCard({ report }: ReportCardProps): JSX.Element
```

**Renders:** Card with file icon, title, date range, platform badges, insights count, created date, status badge. Links to `/reports/{id}`.

**Used in:** Reports list, Client Detail (recent reports)

---

### ReportStatusBadge

| Field | Value |
|-------|-------|
| File | `report-status-badge.tsx` |
| Directive | Server-safe |
| Status | **Not built** |

```typescript
interface ReportStatusBadgeProps {
  status: ReportStatus;
}
export function ReportStatusBadge({ status }: ReportStatusBadgeProps): JSX.Element
```

| Status | Badge Variant | Label |
|--------|---------------|-------|
| `completed` | `success` | Completed |
| `generating` | `default` + pulse | Generating... |
| `failed` | `danger` | Failed |

---

### PipelineProgress *(planned)*

| Field | Value |
|-------|-------|
| File | `pipeline-progress.tsx` |
| Directive | `"use client"` |
| Status | **Not built** |

```typescript
type StageStatus = "pending" | "running" | "done" | "error";

interface PipelineStage {
  label: string;
  status: StageStatus;
}

interface PipelineProgressProps {
  stages: PipelineStage[];
  percent: number;
}
export function PipelineProgress(props: PipelineProgressProps): JSX.Element
```

**Renders:** Overall progress bar + vertical stepper with 8 pipeline stages. Each stage shows a colored dot (gray=pending, blue+pulse=running, green=done, red=error) and label.

**Stages:** Data Validation → KPI Computation → Trend Detection → Anomaly Detection → Campaign Evaluation → Insight Generation → Recommendations → Report Assembly

**Used in:** Report Builder (generation progress sidebar)

---

### ReportConfigForm *(planned)*

| Field | Value |
|-------|-------|
| File | `report-config-form.tsx` |
| Directive | `"use client"` |
| Status | **Not built** |

```typescript
interface ReportConfig {
  clientId: string;
  dateRange: { from: Date; to: Date };
  platforms: Platform[];
  tone: "executive" | "technical" | "casual";
  sections: string[];
  aiModel: "standard" | "premium";
  comparePrevious: boolean;
}

interface ReportConfigFormProps {
  onSubmit: (config: ReportConfig) => void;
  isGenerating: boolean;
}
export function ReportConfigForm(props: ReportConfigFormProps): JSX.Element
```

**Renders:** 4-step form: (1) Client selector, (2) Date range with presets, (3) Platform checkboxes with sync status, (4) Report options — tone selector, section toggles, AI model picker. Sticky summary sidebar with Generate button.

**Depends on:** `react-hook-form` + `zod` for validation, `DateRangePicker`

**Used in:** Report Builder page

---

### ExecutiveSummary

| Field | Value |
|-------|-------|
| File | `executive-summary.tsx` |
| Directive | Server-safe |
| Status | **Not built** — currently inline prose in report-content.tsx |

```typescript
interface ExecutiveSummaryProps {
  content: string;              // AI-generated prose text
}
export function ExecutiveSummary({ content }: ExecutiveSummaryProps): JSX.Element
```

**Renders:** Card with "Executive Summary" title. Content rendered as `prose prose-sm` styled paragraphs. Splits on double newlines for paragraph breaks.

**Used in:** Report Viewer

---

## 7. Shared UI Components

**Directory:** `src/components/ui/`

These are shadcn/ui-style primitives. Server-safe unless noted.

### Card

| File | Status | Exports |
|------|--------|---------|
| `card.tsx` | **Exists** | `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent` |

All are `forwardRef` components accepting `HTMLDivElement` attributes. Card uses `rounded-xl border border-gray-200 bg-white shadow-sm`.

---

### Button

| File | Status | Exports |
|------|--------|---------|
| `button.tsx` | **Exists** | `Button`, `buttonVariants` |

```typescript
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "default" | "lg" | "icon";
}
```

---

### Badge

| File | Status | Exports |
|------|--------|---------|
| `badge.tsx` | **Exists** | `Badge`, `badgeVariants` |

```typescript
interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "danger" | "neutral" | "outline";
}
```

---

### Skeleton

| File | Status | Exports |
|------|--------|---------|
| `skeleton.tsx` | **Exists** | `Skeleton` |

Animated pulse placeholder. Used for loading states on KPI cards, charts, tables.

---

### Input *(planned)*

| File | Status |
|------|--------|
| `input.tsx` | **Not built** |

```typescript
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}
export const Input = forwardRef<HTMLInputElement, InputProps>(...)
```

Standard text input with `rounded-lg`, focus ring, optional error message. Required for auth forms, settings, search.

---

### Select *(planned)*

| File | Status |
|------|--------|
| `select.tsx` | **Not built** |

```typescript
interface SelectProps {
  options: Array<{ label: string; value: string }>;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}
export function Select(props: SelectProps): JSX.Element
```

---

### Switch *(planned)*

| File | Status |
|------|--------|
| `switch.tsx` | **Not built** |

Toggle switch for settings (2FA, comparison period, section toggles).

---

### Tabs *(planned)*

| File | Status |
|------|--------|
| `tabs.tsx` | **Not built** |

```typescript
interface TabsProps {
  tabs: Array<{ label: string; value: string }>;
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
}
export function Tabs(props: TabsProps): JSX.Element
export function TabPanel({ value, children }: { value: string; children: ReactNode }): JSX.Element
```

Used in Settings page (General, Team, Integrations, API, Security).

---

### Toast *(planned)*

| File | Status |
|------|--------|
| `toast.tsx` | **Not built** |

Notification toasts via `sonner`. Variants: success, error, info, warning. Auto-dismiss after 5s.

---

### Progress *(planned)*

| File | Status |
|------|--------|
| `progress.tsx` | **Not built** |

```typescript
interface ProgressProps {
  value: number;                // 0–100
  className?: string;
}
export function Progress(props: ProgressProps): JSX.Element
```

Thin horizontal bar. Used in PipelineProgress and EfficiencyBar.

---

### AlertDialog *(planned)*

| File | Status |
|------|--------|
| `alert-dialog.tsx` | **Not built** |

Confirmation modal for destructive actions (delete report, disconnect integration, remove team member).

---

## 8. Common Components

**Directory:** `src/components/common/`

### PageHeader

| File | Status |
|------|--------|
| `page-header.tsx` | **Exists** |

```typescript
interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
}
```

**Used in:** Every page as the top-level heading.

---

### EmptyState

| File | Status |
|------|--------|
| `empty-state.tsx` | **Exists** |

```typescript
interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}
```

Centered card with icon, heading, message, and optional CTA button.

---

### Providers

| File | Status |
|------|--------|
| `providers.tsx` | **Exists** |

Wraps app with `QueryClientProvider` (TanStack Query). Configured: 5-min staleTime, refetchOnWindowFocus disabled.

---

### ErrorBoundary *(planned)*

| File | Status |
|------|--------|
| `error-boundary.tsx` | **Not built** |

```typescript
interface ErrorBoundaryProps {
  fallback?: ReactNode;
  children: ReactNode;
}
```

Catches render errors. Shows retry button + error message. Wraps page content components.

---

## 9. Client Portal Components *(planned)*

**Directory:** `src/components/clients/`

### ClientCard

| File | Status |
|------|--------|
| `client-card.tsx` | **Not built** |

```typescript
interface ClientCardProps {
  client: {
    id: string;
    name: string;
    platforms: Platform[];
    spend: number;
    spendChange: number;
    conversions: number;
    conversionsChange: number;
    roas: number;
    roasChange: number;
    lastReportDate?: string;
  };
}
export function ClientCard({ client }: ClientCardProps): JSX.Element
```

**Renders:** Avatar + name, platform labels, 3 mini-metrics (spend, conversions, ROAS with % change), last report date, "Report" and "Details" action buttons.

**Used in:** Client Portal page (grid layout)

---

### AddClientCard

| File | Status |
|------|--------|
| `add-client-card.tsx` | **Not built** |

```typescript
export function AddClientCard(): JSX.Element
```

Dashed border placeholder card with "+" icon. Triggers add client flow.

---

## 10. Auth Components *(planned)*

**Directory:** `src/components/auth/`

### LoginForm

```typescript
interface LoginFormProps {
  onSuccess: () => void;
}
```

Email + password fields, "Remember me" checkbox, submit button, "Forgot password?" link. Validates with Zod.

### RegisterForm

```typescript
interface RegisterFormProps {
  onSuccess: () => void;
}
```

Name, email, password, workspace name fields. Creates user + workspace in one step.

### AuthGuard

```typescript
interface AuthGuardProps {
  children: ReactNode;
}
```

Wraps `(dashboard)` layout. Checks for valid access token; redirects to `/login` on 401. Handles silent refresh.

---

## 11. Hooks

**Directory:** `src/hooks/`

| Hook | Status | Purpose |
|------|--------|---------|
| `useAuth` | **Not built** | Auth state: user, login(), logout(), isAuthenticated |
| `useDashboard` | **Not built** | `useQuery` wrapper for `GET /api/v1/metrics/summary` + daily + platform |
| `useCampaigns` | **Not built** | `useQuery` for `GET /api/v1/campaigns` with sort/filter params |
| `useInsights` | **Not built** | `useQuery` for `GET /api/v1/insights` with category filter |
| `useReports` | **Not built** | `useQuery` for `GET /api/v1/reports` list |
| `useReport` | **Not built** | `useQuery` for `GET /api/v1/reports/{id}` detail |
| `useGenerateReport` | **Not built** | `useMutation` for `POST /api/v1/reports` + status polling |
| `useClients` | **Not built** | `useQuery` for `GET /api/v1/clients` |
| `useMediaQuery` | **Not built** | Responsive breakpoint detection |
| `useDebounce` | **Not built** | Debounced value for search inputs |

---

## 12. Stores

**Directory:** `src/stores/`

| Store | Status | State |
|-------|--------|-------|
| `useUIStore` | **Exists** | `sidebarCollapsed`, `toggleSidebar()`, `setSidebarCollapsed()` |
| `useAuthStore` | **Not built** | `user`, `accessToken`, `setAuth()`, `clearAuth()` |
| `useOnboardingStore` | **Not built** | `step`, `workspaceId`, `connectedPlatforms[]`, `nextStep()`, `reset()` |

---

## 13. Component → Screen Mapping

Shows which components each wireframe screen uses.

### Dashboard

```
Topbar
PageHeader (actions: Generate Report button)
├── KPICard × 4 (Spend, Conversions, ROAS, CPA)
├── PerformanceChart (dual-axis line)
├── PlatformChart (donut)
└── DataTable (top campaigns — name, platform, spend, conv, ROAS, tier badge)
```

### Campaign Performance

```
Topbar
PageHeader
├── KPICard × 4 (Active, Spend, Conversions, ROAS)
├── FilterPills (tier distribution)
└── DataTable (full campaign table)
    ├── SortButton (spend, conv, CPA, ROAS, score)
    ├── Badge (tier)
    └── EfficiencyBar (score column)
```

### Insights

```
Topbar
PageHeader
├── FilterPills (category filter)
├── InsightCard × N
└── RecommendationCard × N
```

### Report Builder

```
Topbar
PageHeader
├── ReportConfigForm
│   ├── Select (client)
│   ├── DateRangePicker
│   ├── PlatformCheckbox × N
│   ├── FilterPills (tone)
│   ├── Switch × N (sections)
│   └── FilterPills (AI model)
├── Summary sidebar
│   └── Button (Generate)
└── PipelineProgress (after generate)
```

### Report Viewer

```
Topbar
├── Button (Back)
├── Button (Share)
├── Button (Export PDF)
├── Badge × N (status, tone, platforms)
├── ExecutiveSummary
├── KPICard × 4
├── PerformanceChart
├── InsightCard × N
└── RecommendationCard × N
```

### Client Portal

```
Topbar
PageHeader (actions: Add Client button)
├── Input (search)
├── Select (platform filter)
├── Select (sort)
├── ClientCard × N
└── AddClientCard
```

### Client Detail

```
Topbar
├── Button (Back)
├── Button (Generate Report)
├── KPICard × 4
├── PerformanceChart
├── DataTable (campaign breakdown)
└── ReportCard × N (recent reports)
```

---

## 14. Build Priority

Ordered by sprint plan dependency. Components needed for API integration (Weeks 6–7) should be extracted and generalized first.

| Priority | Components | Sprint |
|----------|-----------|--------|
| **P0** | `Input`, `Select`, `Tabs`, `LoginForm`, `RegisterForm`, `AuthGuard` | Week 6 |
| **P0** | `useAuth`, `useAuthStore`, `useDashboard` hooks | Week 6 |
| **P1** | `DataTable`, `SortButton`, `EfficiencyBar`, `FilterPills` | Week 7 |
| **P1** | `useCampaigns`, `useInsights`, `useReports`, `useReport` hooks | Week 7 |
| **P1** | `ReportCard`, `ReportStatusBadge`, `ExecutiveSummary` | Week 7 |
| **P2** | `ReportConfigForm`, `PipelineProgress`, `DateRangePicker` | Week 7 |
| **P2** | `useGenerateReport` hook | Week 7 |
| **P3** | `ClientCard`, `AddClientCard`, `useClients` | Week 8 |
| **P3** | `Switch`, `Toast`, `AlertDialog`, `Progress` | Week 8 |
| **P3** | `CommandMenu`, `ErrorBoundary`, `BarChart` | Week 8 |

---

## 15. Refactoring Notes

The following existing components should be reorganized to match this architecture:

| Current Location | Target Location | Action |
|------------------|----------------|--------|
| `components/dashboard/performance-chart.tsx` | `components/charts/performance-chart.tsx` | Move |
| `components/dashboard/platform-chart.tsx` | `components/charts/platform-chart.tsx` | Move |
| `components/reports/insight-card.tsx` | `components/insights/insight-card.tsx` | Move |
| `components/reports/recommendation-card.tsx` | `components/insights/recommendation-card.tsx` | Move |
| Inline `SortButton` in `campaigns-content.tsx` | `components/tables/sort-button.tsx` | Extract |
| Inline efficiency bar in `campaigns-content.tsx` | `components/tables/efficiency-bar.tsx` | Extract |
| Inline report cards in `reports-list-content.tsx` | `components/reports/report-card.tsx` | Extract |
| Inline tier filter in `campaigns-content.tsx` | `components/insights/filter-pills.tsx` | Extract + generalize |

Update all import paths after moving. No logic changes required — these are pure file reorganization moves.
