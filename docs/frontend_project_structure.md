# InsightFlow — Frontend Project Structure

## Framework & Tooling

| Layer | Tool | Version |
|-------|------|---------|
| Framework | Next.js (App Router) | 14.2 |
| Language | TypeScript (strict) | 5.x |
| Styling | Tailwind CSS | 3.4 |
| UI Primitives | shadcn/ui (CVA + Radix) | — |
| Server State | TanStack React Query | 5.x |
| Client State | Zustand | 4.x |
| Tables | TanStack React Table | 8.x |
| Forms | React Hook Form + Zod | 7.x / 3.x |
| Charts | Recharts | 2.x |
| Icons | lucide-react | 0.577 |
| Auth | NextAuth.js (v5 beta) | 5.0 |
| CSS Utils | clsx + tailwind-merge | — |

---

## Path Aliases

```jsonc
// tsconfig.json
{ "paths": { "@/*": ["./src/*"] } }
```

All imports use `@/` prefix — e.g. `import { Button } from "@/components/ui/button"`.

---

## Complete File Tree

Legend: `[E]` = exists, `[P]` = planned, `[SC]` = Server Component, `[CC]` = Client Component

```
frontend/
│
├── .eslintrc.json                          [E] ESLint — extends next/core-web-vitals, next/typescript
├── .gitignore                              [E] Ignores node_modules, .next, .env*.local
├── next.config.mjs                         [E] Next.js config (empty — defaults)
├── next-env.d.ts                           [E] Next.js auto-generated type declarations
├── package.json                            [E] Dependencies & scripts (dev, build, start, lint)
├── package-lock.json                       [E] Lockfile
├── postcss.config.mjs                      [E] PostCSS — tailwindcss plugin
├── tailwind.config.ts                      [E] Tailwind — Inter font, design tokens, content paths
├── tsconfig.json                           [E] TypeScript strict, @/* path alias
│
├── public/                                 [P] Static assets served at /
│   ├── favicon.ico                         [P] App favicon (currently in src/app/)
│   ├── logo.svg                            [P] InsightFlow logo for sidebar & auth pages
│   └── og-image.png                        [P] Open Graph preview image
│
├── wireframes/
│   └── dashboard_wireframes.jsx            [E] JSX wireframe reference (6 screens, not rendered)
│
└── src/
    │
    ├── app/                                ─── ROUTES (Next.js App Router) ───
    │   │
    │   ├── layout.tsx                      [E][SC] Root layout — Inter font, <Providers> wrapper
    │   ├── page.tsx                        [E][SC] / → redirect("/dashboard")
    │   ├── globals.css                     [E]     Tailwind @layer base/components/utilities, CSS vars
    │   ├── favicon.ico                     [E]     Favicon (move to public/)
    │   ├── fonts/
    │   │   ├── GeistVF.woff               [E]     Geist variable font (bundled)
    │   │   └── GeistMonoVF.woff           [E]     Geist Mono variable font (bundled)
    │   │
    │   ├── (auth)/                         ─── Auth route group (no sidebar) ───
    │   │   ├── layout.tsx                  [P][SC] Centered card layout, logo, no sidebar
    │   │   ├── login/
    │   │   │   └── page.tsx               [P][SC] Login page shell → <LoginForm />
    │   │   └── register/
    │   │       └── page.tsx               [P][SC] Register page shell → <RegisterForm />
    │   │
    │   ├── (onboarding)/                   ─── Onboarding route group ───
    │   │   ├── layout.tsx                  [P][SC] Minimal layout — logo + progress bar
    │   │   └── onboarding/
    │   │       └── page.tsx               [P][CC] Multi-step wizard (workspace → platforms → first report)
    │   │
    │   └── (dashboard)/                    ─── Main app route group (sidebar + topbar) ───
    │       │
    │       ├── layout.tsx                  [E][CC] Sidebar + main content with responsive margin
    │       │
    │       ├── dashboard/
    │       │   ├── page.tsx               [E][SC] Metadata: "Dashboard", renders <DashboardContent />
    │       │   ├── dashboard-content.tsx   [E][CC] KPI cards, charts, campaign table (demo data)
    │       │   └── loading.tsx            [P][SC] Skeleton grid: 4 KPI + chart + table placeholders
    │       │
    │       ├── clients/
    │       │   ├── page.tsx               [P][SC] Metadata: "Clients", renders <ClientsContent />
    │       │   ├── clients-content.tsx    [P][CC] Search, filters, client card grid, add-client CTA
    │       │   ├── loading.tsx            [P][SC] Skeleton card grid
    │       │   └── [id]/
    │       │       ├── page.tsx           [P][SC] Metadata: dynamic client name
    │       │       ├── client-detail-content.tsx [P][CC] KPIs, chart, campaign table, recent reports
    │       │       └── loading.tsx        [P][SC] Skeleton detail layout
    │       │
    │       ├── insights/
    │       │   ├── page.tsx               [E][SC] Metadata: "Insights", renders <InsightsContent />
    │       │   ├── insights-content.tsx   [E][CC] Category filter pills, insight cards, rec cards
    │       │   └── loading.tsx            [P][SC] Skeleton pill row + card list
    │       │
    │       ├── campaigns/
    │       │   ├── page.tsx               [E][SC] Metadata: "Campaign Performance"
    │       │   ├── campaigns-content.tsx  [E][CC] Tier filter, sortable table, KPI row
    │       │   └── loading.tsx            [P][SC] Skeleton KPIs + table
    │       │
    │       ├── reports/
    │       │   ├── page.tsx               [E][SC] Metadata: "Reports", renders <ReportsListContent />
    │       │   ├── reports-list-content.tsx [E][CC] Report cards, status badges, generate button
    │       │   ├── loading.tsx            [P][SC] Skeleton report cards
    │       │   ├── generate/
    │       │   │   ├── page.tsx           [P][SC] Metadata: "Generate Report"
    │       │   │   └── report-builder-content.tsx [P][CC] Config form, summary sidebar, pipeline progress
    │       │   └── [id]/
    │       │       ├── page.tsx           [E][SC] Metadata: "Report", receives params.id
    │       │       ├── report-content.tsx [E][CC] Executive summary, KPIs, chart, insights, recs
    │       │       └── loading.tsx        [P][SC] Skeleton report layout
    │       │
    │       ├── integrations/
    │       │   ├── page.tsx               [P][SC] Metadata: "Integrations"
    │       │   └── integrations-content.tsx [P][CC] Platform cards, OAuth connect flow, sync status
    │       │
    │       └── settings/
    │           ├── page.tsx               [E][SC] Metadata: "Settings", renders <SettingsContent />
    │           └── settings-content.tsx   [E][CC] 5-tab layout (General, Team, Integrations, API, Security)
    │
    ├── components/                         ─── SHARED COMPONENTS ───
    │   │
    │   ├── layout/                         ─── App shell ───
    │   │   ├── sidebar.tsx                [E][CC] Collapsible nav (240px/64px), 7 items, active state
    │   │   ├── topbar.tsx                 [E][CC] Page title, search, notifications, user menu
    │   │   └── command-menu.tsx           [P][CC] Ctrl+K palette — search clients, reports, nav
    │   │
    │   ├── auth/                           ─── Authentication ───
    │   │   ├── login-form.tsx             [P][CC] Email/password, remember me, forgot link
    │   │   ├── register-form.tsx          [P][CC] Name, email, password, workspace name
    │   │   └── auth-guard.tsx             [P][CC] Token check, redirect to /login, silent refresh
    │   │
    │   ├── dashboard/                      ─── Dashboard widgets ───
    │   │   ├── kpi-card.tsx               [E]     Label, value, % change, trend icon
    │   │   └── date-range-picker.tsx      [P][CC] Presets + calendar popover + compare toggle
    │   │
    │   ├── charts/                         ─── Recharts wrappers (all "use client") ───
    │   │   ├── performance-chart.tsx       [E][CC] Dual Y-axis line chart (spend + conversions)
    │   │   ├── platform-chart.tsx          [E][CC] Donut chart — spend by platform
    │   │   └── bar-chart.tsx              [P][CC] Vertical/stacked bar — generic wrapper
    │   │
    │   ├── tables/                         ─── Data tables ───
    │   │   ├── data-table.tsx             [P][CC] Generic sortable table with Column<T> config
    │   │   ├── sort-button.tsx            [P][CC] Sortable column header (ArrowUpDown icon)
    │   │   └── efficiency-bar.tsx         [P]     Score 0–1 → colored progress bar + label
    │   │
    │   ├── insights/                       ─── Insight & recommendation display ───
    │   │   ├── insight-card.tsx            [E]     Sentiment border, category icon, headline, detail
    │   │   ├── recommendation-card.tsx     [E]     Priority/effort badges, impact, action checklist
    │   │   └── filter-pills.tsx           [P][CC] Generic pill row — active/inactive, optional count
    │   │
    │   ├── reports/                         ─── Report builder & viewer ───
    │   │   ├── report-card.tsx            [P]     Report list item — title, dates, status, platforms
    │   │   ├── report-status-badge.tsx    [P]     Completed/Generating/Failed badge
    │   │   ├── report-config-form.tsx     [P][CC] 4-step config (client, dates, platforms, options)
    │   │   ├── pipeline-progress.tsx      [P][CC] Progress bar + 8-stage vertical stepper
    │   │   └── executive-summary.tsx      [P]     Card with prose paragraphs from AI content
    │   │
    │   ├── clients/                        ─── Client portal ───
    │   │   ├── client-card.tsx            [P]     Avatar, metrics, platforms, report/detail actions
    │   │   └── add-client-card.tsx        [P]     Dashed border "+" placeholder card
    │   │
    │   ├── common/                         ─── Cross-cutting ───
    │   │   ├── providers.tsx              [E][CC] QueryClientProvider (5-min stale, no window refetch)
    │   │   ├── page-header.tsx            [E]     Title + description + optional action slot
    │   │   ├── empty-state.tsx            [E]     Icon + title + message + optional CTA
    │   │   └── error-boundary.tsx         [P][CC] Catch render errors, show retry UI
    │   │
    │   └── ui/                             ─── Shared primitives (shadcn/ui style) ───
    │       ├── badge.tsx                  [E]     CVA variants: default/success/warning/danger/neutral/outline
    │       ├── button.tsx                 [E]     CVA variants: default/secondary/outline/ghost/danger, sizes
    │       ├── card.tsx                   [E]     Card, CardHeader, CardTitle, CardDescription, CardContent
    │       ├── skeleton.tsx               [E]     Animated pulse placeholder
    │       ├── input.tsx                  [P]     Text input with focus ring + error message
    │       ├── textarea.tsx               [P]     Multi-line input (report editing)
    │       ├── select.tsx                 [P]     Single-select dropdown with search
    │       ├── checkbox.tsx               [P]     Checkmark input (platform selection, sections)
    │       ├── switch.tsx                 [P]     Toggle (2FA, settings booleans)
    │       ├── tabs.tsx                   [P]     Tab nav + TabPanel (settings page)
    │       ├── progress.tsx               [P]     Horizontal bar (pipeline, efficiency)
    │       ├── toast.tsx                  [P]     Sonner-based notifications (success/error/info)
    │       ├── toaster.tsx                [P]     Toast container (mounted in root layout)
    │       ├── alert-dialog.tsx           [P]     Confirmation modal for destructive actions
    │       ├── dialog.tsx                 [P]     Generic modal (add client, API key display)
    │       ├── dropdown-menu.tsx          [P]     User menu, row actions (Radix-based)
    │       ├── popover.tsx                [P]     Date picker, filter popovers
    │       ├── calendar.tsx               [P]     Date picker calendar (used by DateRangePicker)
    │       ├── avatar.tsx                 [P]     User/client initials or image
    │       ├── separator.tsx              [P]     Horizontal/vertical divider
    │       └── label.tsx                  [P]     Form field label with htmlFor
    │
    ├── hooks/                              ─── CUSTOM HOOKS ───
    │   │
    │   │   ── Auth ──
    │   ├── use-auth.ts                    [P] Auth state: user, login(), logout(), isAuthenticated
    │   │
    │   │   ── Data fetching (TanStack Query) ──
    │   ├── use-dashboard.ts               [P] useQuery → GET /api/v1/metrics/summary + daily + platform
    │   ├── use-campaigns.ts               [P] useQuery → GET /api/v1/campaigns (sort, filter, pagination)
    │   ├── use-insights.ts                [P] useQuery → GET /api/v1/insights (category filter)
    │   ├── use-reports.ts                 [P] useQuery → GET /api/v1/reports (list)
    │   ├── use-report.ts                  [P] useQuery → GET /api/v1/reports/{id} (detail)
    │   ├── use-generate-report.ts         [P] useMutation → POST /api/v1/reports + status polling
    │   ├── use-clients.ts                 [P] useQuery → GET /api/v1/clients
    │   ├── use-client.ts                  [P] useQuery → GET /api/v1/clients/{id} (detail)
    │   ├── use-platforms.ts               [P] useQuery → GET /api/v1/platforms (connected integrations)
    │   │
    │   │   ── Utility ──
    │   ├── use-media-query.ts             [P] Responsive breakpoint detection
    │   └── use-debounce.ts                [P] Debounced value for search inputs
    │
    ├── stores/                             ─── ZUSTAND STORES ───
    │   ├── ui-store.ts                    [E] sidebarCollapsed, toggleSidebar(), setSidebarCollapsed()
    │   ├── auth-store.ts                  [P] user, accessToken, setAuth(), clearAuth()
    │   └── onboarding-store.ts            [P] step, workspaceId, connectedPlatforms[], nextStep()
    │
    ├── lib/                                ─── UTILITIES & SERVICES ───
    │   ├── utils.ts                       [E] cn() (clsx+twMerge), formatCurrency/Number/Percent/Compact
    │   ├── api-client.ts                  [E] ApiError class, request() with token injection, CRUD methods
    │   ├── constants.ts                   [P] Platform colors, tier thresholds, nav items, date presets
    │   ├── validations.ts                 [P] Zod schemas: loginSchema, registerSchema, reportConfigSchema
    │   └── query-keys.ts                  [P] TanStack Query key factory: queryKeys.reports.list(), etc.
    │
    ├── types/                              ─── TYPE DEFINITIONS ───
    │   ├── api.ts                         [E] Platform, ReportStatus, InsightCategory, InsightSentiment,
    │   │                                      CampaignTier, TrendDirection, User, Organization,
    │   │                                      KPISummary, PeriodComparison, DashboardOverview,
    │   │                                      DailyMetric, CampaignPerformance, Insight,
    │   │                                      Recommendation, Report, PaginatedResponse<T>
    │   └── next-auth.d.ts                 [P] Module augmentation for NextAuth session/JWT types
    │
    └── middleware.ts                       [P] Next.js middleware — auth redirect, route protection
```

---

## Route Architecture

### Route Groups

| Group | Layout | Purpose |
|-------|--------|---------|
| `(auth)` | Centered card, no sidebar | Login, Register |
| `(onboarding)` | Minimal shell + progress | First-time setup wizard |
| `(dashboard)` | Sidebar + Topbar | All authenticated pages |

### Route Table

| Path | Page File | Content Component | Rendering |
|------|-----------|-------------------|-----------|
| `/` | `app/page.tsx` | — (redirect) | SSG |
| `/login` | `app/(auth)/login/page.tsx` | `LoginForm` | SSG |
| `/register` | `app/(auth)/register/page.tsx` | `RegisterForm` | SSG |
| `/onboarding` | `app/(onboarding)/onboarding/page.tsx` | `OnboardingWizard` | CSR |
| `/dashboard` | `app/(dashboard)/dashboard/page.tsx` | `DashboardContent` | SSG + CSR |
| `/clients` | `app/(dashboard)/clients/page.tsx` | `ClientsContent` | SSG + CSR |
| `/clients/[id]` | `app/(dashboard)/clients/[id]/page.tsx` | `ClientDetailContent` | SSR |
| `/insights` | `app/(dashboard)/insights/page.tsx` | `InsightsContent` | SSG + CSR |
| `/campaigns` | `app/(dashboard)/campaigns/page.tsx` | `CampaignsContent` | SSG + CSR |
| `/reports` | `app/(dashboard)/reports/page.tsx` | `ReportsListContent` | SSG + CSR |
| `/reports/generate` | `app/(dashboard)/reports/generate/page.tsx` | `ReportBuilderContent` | CSR |
| `/reports/[id]` | `app/(dashboard)/reports/[id]/page.tsx` | `ReportContent` | SSR |
| `/integrations` | `app/(dashboard)/integrations/page.tsx` | `IntegrationsContent` | SSG + CSR |
| `/settings` | `app/(dashboard)/settings/page.tsx` | `SettingsContent` | SSG + CSR |

**Rendering legend:**
- **SSG** — Static shell generated at build time (Server Component)
- **SSR** — Server-rendered per request (dynamic params like `[id]`)
- **CSR** — Client-side data fetching via TanStack Query inside `"use client"` content component

### Pattern: Server Component Shell + Client Content

Every dashboard route follows this pattern:

```
page.tsx          → Server Component (metadata export, static shell)
*-content.tsx     → "use client" (state, effects, data fetching)
loading.tsx       → Server Component (skeleton fallback for Suspense)
```

This keeps metadata and SEO on the server while allowing full interactivity in the content component.

---

## Component Directory Map

### `components/ui/` — Primitives

Foundational building blocks. No business logic. Accept `className` for composition. Follow shadcn/ui conventions (CVA + `forwardRef` + Radix where needed).

```
ui/
├── alert-dialog.tsx       Destructive action confirmation
├── avatar.tsx             User/client initials or image
├── badge.tsx              Status/category labels (6 color variants)
├── button.tsx             Primary CTA (5 variants, 4 sizes)
├── calendar.tsx           Month calendar for date pickers
├── card.tsx               Container: Card/Header/Title/Description/Content
├── checkbox.tsx           Binary toggle input
├── dialog.tsx             Generic modal container
├── dropdown-menu.tsx      Context menus (user menu, row actions)
├── input.tsx              Text/email/password input with error state
├── label.tsx              Form field label
├── popover.tsx            Floating content (date pickers, filters)
├── progress.tsx           Horizontal progress bar (0–100)
├── select.tsx             Single-value dropdown
├── separator.tsx          Visual divider
├── skeleton.tsx           Animated loading placeholder
├── switch.tsx             On/off toggle
├── tabs.tsx               Tab navigation + panels
├── textarea.tsx           Multi-line text input
├── toast.tsx              Notification component
└── toaster.tsx            Toast container (mount in root layout)
```

### `components/layout/` — App Shell

Persistent across all dashboard pages. Mounted in `(dashboard)/layout.tsx`.

```
layout/
├── sidebar.tsx            Navigation, collapse, active state
├── topbar.tsx             Title, search trigger, notifications, user
└── command-menu.tsx       Ctrl+K search palette
```

### `components/auth/` — Authentication

Used in `(auth)` route group pages.

```
auth/
├── login-form.tsx         Email + password form
├── register-form.tsx      Signup form with workspace creation
└── auth-guard.tsx         Route protection wrapper
```

### `components/dashboard/` — Dashboard Widgets

Reused across Dashboard, Client Detail, and Report pages.

```
dashboard/
├── kpi-card.tsx           Metric card: label, value, change %, icon
└── date-range-picker.tsx  Presets + calendar + compare toggle
```

### `components/charts/` — Data Visualization

All require `"use client"` (Recharts uses DOM APIs).

```
charts/
├── performance-chart.tsx  Dual Y-axis line chart (spend + conversions)
├── platform-chart.tsx     Donut chart (spend by platform)
└── bar-chart.tsx          Generic vertical/stacked bar
```

### `components/tables/` — Tabular Data

Generic table infrastructure for campaigns, clients, reports.

```
tables/
├── data-table.tsx         Column<T> config, sorting, responsive scroll
├── sort-button.tsx        Sortable column header with icon
└── efficiency-bar.tsx     Score → colored progress bar
```

### `components/insights/` — AI Insights

Display components for pipeline-generated insights and recommendations.

```
insights/
├── insight-card.tsx       Sentiment border, category icon, confidence
├── recommendation-card.tsx Priority/effort badges, action items
└── filter-pills.tsx       Generic filter chip row with counts
```

### `components/reports/` — Report System

Report builder, viewer, and list components.

```
reports/
├── report-card.tsx        List item: title, dates, status, platforms
├── report-status-badge.tsx  Completed / Generating / Failed
├── report-config-form.tsx 4-step builder form
├── pipeline-progress.tsx  8-stage progress stepper
└── executive-summary.tsx  AI prose display card
```

### `components/clients/` — Client Portal

Client management UI.

```
clients/
├── client-card.tsx        Avatar, metrics, platforms, actions
└── add-client-card.tsx    Dashed border "+" CTA
```

### `components/common/` — Cross-Cutting

Used across multiple feature areas.

```
common/
├── providers.tsx          QueryClientProvider wrapper
├── page-header.tsx        Title + description + actions slot
├── empty-state.tsx        Icon + message + CTA for empty lists
└── error-boundary.tsx     Catch errors, show retry UI
```

---

## State Management Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Component Tree                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  TanStack React Query (Server State)                   │ │
│  │                                                        │ │
│  │  • Dashboard metrics, campaigns, insights, reports     │ │
│  │  • Cache: 5-min staleTime, background refetch         │ │
│  │  • Mutations with optimistic updates                   │ │
│  │  • Key factory in lib/query-keys.ts                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Zustand (Client State)                                │ │
│  │                                                        │ │
│  │  • ui-store: sidebar collapse, theme                   │ │
│  │  • auth-store: user, tokens                            │ │
│  │  • onboarding-store: wizard progress                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  URL State (Navigation)                                │ │
│  │                                                        │ │
│  │  • useSearchParams: filters, date ranges, sort         │ │
│  │  • useParams: client ID, report ID                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  React Hook Form (Form State)                          │ │
│  │                                                        │ │
│  │  • Login, register, settings, report config forms      │ │
│  │  • Zod schemas in lib/validations.ts                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
API Server
    │
    ▼
lib/api-client.ts          Fetch wrapper: base URL, auth headers, error normalization
    │
    ▼
hooks/use-*.ts             TanStack Query hooks: caching, refetch, loading/error states
    │
    ▼
*-content.tsx              Page content components: compose UI from shared components
    │
    ▼
components/**              Presentational components: render data via props
```

**Key rules:**
- Components in `components/` never call API directly — they receive data via props
- Data fetching happens only in hooks (`hooks/use-*.ts`) or page content components
- API client injects auth token from `auth-store` automatically
- Mutations invalidate related query keys for cache consistency

---

## Configuration Files

| File | Purpose |
|------|---------|
| `next.config.mjs` | Next.js settings (images domains, redirects, headers) |
| `tailwind.config.ts` | Design tokens, content paths, Inter font, custom radius |
| `tsconfig.json` | Strict mode, `@/*` path alias, bundler resolution |
| `.eslintrc.json` | next/core-web-vitals + next/typescript |
| `postcss.config.mjs` | Tailwind CSS plugin |
| `package.json` | Scripts: `dev`, `build`, `start`, `lint` |

### Environment Variables

```bash
# .env.local (not committed)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1    # Backend API base URL
NEXT_PUBLIC_APP_URL=http://localhost:3000            # Frontend URL (for OAuth redirects)

# Server-only (Next.js middleware / API routes)
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<random-32-char-string>

# OAuth (if using NextAuth providers)
META_CLIENT_ID=
META_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

---

## Import Conventions

### Component imports use `@/` alias

```typescript
import { Button } from "@/components/ui/button";
import { KPICard } from "@/components/dashboard/kpi-card";
import { InsightCard } from "@/components/insights/insight-card";
import { useDashboard } from "@/hooks/use-dashboard";
import { useUIStore } from "@/stores/ui-store";
import { cn, formatCurrency } from "@/lib/utils";
import type { Report, Insight } from "@/types/api";
```

### Import order (enforced by ESLint)

```typescript
// 1. React / Next.js
import { useState } from "react";
import Link from "next/link";

// 2. Third-party libraries
import { useQuery } from "@tanstack/react-query";

// 3. Internal: components
import { Card } from "@/components/ui/card";

// 4. Internal: hooks, stores, utils
import { useDashboard } from "@/hooks/use-dashboard";

// 5. Types (always type-only imports)
import type { DailyMetric } from "@/types/api";
```

---

## File Naming Conventions

| Pattern | Convention | Example |
|---------|-----------|---------|
| Components | `kebab-case.tsx` | `kpi-card.tsx`, `insight-card.tsx` |
| Hooks | `use-kebab-case.ts` | `use-dashboard.ts`, `use-auth.ts` |
| Stores | `kebab-case-store.ts` | `ui-store.ts`, `auth-store.ts` |
| Types | `kebab-case.ts` | `api.ts` |
| Utilities | `kebab-case.ts` | `utils.ts`, `api-client.ts` |
| Pages | `page.tsx` (Next.js convention) | — |
| Layouts | `layout.tsx` (Next.js convention) | — |
| Loading | `loading.tsx` (Next.js convention) | — |
| Errors | `error.tsx` (Next.js convention) | — |
| Content | `*-content.tsx` | `dashboard-content.tsx` |

### Export conventions

- Components: **named exports** (no default exports)
- Pages/layouts: **default exports** (Next.js requires this)
- Hooks: **named exports** prefixed with `use`
- Types: **named exports** with `type` keyword

---

## Performance Targets

| Metric | Target | Measured on |
|--------|--------|-------------|
| LCP | < 1.5s | Dashboard page |
| FID | < 100ms | Any interactive page |
| CLS | < 0.1 | All pages |
| TTI | < 2.0s | Dashboard page |
| JS bundle (initial) | < 150KB | gzipped |

### Optimization strategies

- **Code splitting** — Dynamic imports for charts (`next/dynamic` with `ssr: false`)
- **Image optimization** — `next/image` for logos, avatars
- **Font optimization** — `next/font` with Inter (subset, swap)
- **Prefetching** — `<Link prefetch>` on sidebar nav items
- **Lazy loading** — `loading.tsx` Suspense boundaries per route
- **Bundle analysis** — `@next/bundle-analyzer` in dev
