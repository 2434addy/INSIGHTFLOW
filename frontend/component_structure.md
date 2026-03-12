# InsightFlow — Component Structure

## 1. Component Design Principles

1. **Composition over inheritance:** Small, composable components
2. **Server-first:** Default to RSC; use `"use client"` only when needed
3. **Co-location:** Styles, types, and tests near the component
4. **Props over context:** Explicit data flow; context only for cross-cutting concerns
5. **Accessibility built-in:** Every component is keyboard navigable and screen-reader friendly

## 2. Component Hierarchy

### Layout Components

```
RootLayout
├── AuthLayout                    # /login, /register routes
│   └── AuthCard
│       ├── LoginForm
│       └── RegisterForm
│
├── OnboardingLayout              # /onboarding route
│   └── OnboardingWizard
│       ├── Step1_CreateWorkspace
│       ├── Step2_ConnectPlatform
│       ├── Step3_SelectAccounts
│       └── Step4_GenerateReport
│
└── DashboardLayout               # All authenticated routes
    ├── Sidebar
    │   ├── SidebarLogo
    │   ├── SidebarNav
    │   │   └── NavItem (× n)
    │   └── SidebarFooter
    ├── Topbar
    │   ├── Breadcrumbs
    │   ├── SearchCommand (⌘K)
    │   ├── NotificationBell
    │   └── UserMenu
    └── MainContent
        └── [Page Content]
```

### Page Components

```
DashboardPage
├── PageHeader ("Dashboard", date range picker)
├── KPICardRow
│   ├── KPICard (Total Spend)
│   ├── KPICard (Conversions)
│   ├── KPICard (Avg ROAS)
│   └── KPICard (Avg CPA)
├── ChartsSection
│   ├── SpendConversionsChart (line/area)
│   └── PlatformDistributionChart (donut)
└── ClientPerformanceTable
    ├── TableHeader (sortable columns)
    ├── TableRow (× n)
    │   ├── ClientName + PlatformIcons
    │   ├── MetricCells
    │   ├── TrendBadge
    │   └── ActionButtons
    └── TablePagination

ClientDetailPage
├── PageHeader (client name, back link)
├── ClientKPICards
├── ClientPerformanceChart
├── CampaignTable
│   ├── CampaignRow (× n)
│   └── CampaignPagination
└── RecentReportsList
    └── ReportListItem (× n)

ReportViewPage
├── ReportToolbar (Edit, Export PDF, Share)
├── ReportDocument
│   ├── ReportCover (title, client, date)
│   ├── ExecutiveSummary (AI text)
│   ├── MetricsOverview (KPI cards + charts)
│   ├── ChannelBreakdown (per-platform analysis)
│   ├── InsightsList (AI insights)
│   └── RecommendationsList (AI recommendations)
└── ReportFooter

ReportGeneratePage
├── ClientSelector
├── DateRangePicker
├── PlatformSelector
├── ReportConfigOptions
│   ├── TemplateSelector
│   ├── ToneSelector
│   └── SectionSelector
├── GenerateButton
└── GenerationProgress
    ├── ProgressBar
    ├── StatusMessages
    └── PreviewLink (on complete)
```

## 3. Core UI Components (shadcn/ui based)

### Data Display
| Component | Source | Props |
|-----------|--------|-------|
| `KPICard` | Custom | value, label, trend, trendDirection, icon |
| `DataTable` | shadcn + TanStack | columns, data, sorting, filtering, pagination |
| `Badge` | shadcn | variant (success, warning, error, neutral) |
| `Avatar` | shadcn | src, fallback, size |
| `Skeleton` | shadcn | width, height, variant |
| `EmptyState` | Custom | icon, title, description, action |

### Charts
| Component | Library | Props |
|-----------|---------|-------|
| `LineChart` | Recharts | data, xKey, yKeys, colors |
| `AreaChart` | Recharts | data, xKey, yKeys, gradient |
| `DonutChart` | Recharts | data, nameKey, valueKey |
| `BarChart` | Recharts | data, xKey, yKeys, stacked |

### Forms & Inputs
| Component | Source | Notes |
|-----------|--------|-------|
| `Input` | shadcn | Text, email, password |
| `Select` | shadcn | Single select with search |
| `DateRangePicker` | Custom (shadcn Calendar) | Presets + custom range |
| `Checkbox` | shadcn | |
| `Switch` | shadcn | Toggle settings |
| `Textarea` | shadcn | Report editing |

### Navigation
| Component | Source | Notes |
|-----------|--------|-------|
| `Sidebar` | Custom | Collapsible, responsive |
| `Breadcrumbs` | Custom | Auto-generated from route |
| `Tabs` | shadcn | Page sub-navigation |
| `CommandMenu` | shadcn (cmdk) | ⌘K search |

### Feedback
| Component | Source | Notes |
|-----------|--------|-------|
| `Toast` | shadcn (sonner) | Success, error, info |
| `AlertDialog` | shadcn | Destructive confirmations |
| `Progress` | shadcn | Report generation progress |
| `LoadingSpinner` | Custom | Inline loading states |

## 4. State Management Architecture

```
┌───────────────────────────────────────────────┐
│                 Component Tree                 │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  TanStack Query (Server State)           │ │
│  │  • API data (clients, reports, metrics)  │ │
│  │  • Cache management                       │ │
│  │  • Optimistic updates                     │ │
│  │  • Background refetch                     │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  Zustand Stores (Client State)            │ │
│  │  • workspaceStore: current workspace     │ │
│  │  • uiStore: sidebar, theme, modals       │ │
│  │  • onboardingStore: wizard progress      │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  React Context (Scoped State)             │ │
│  │  • AuthContext: session, user             │ │
│  │  • ThemeContext: color scheme             │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  URL State (Navigation State)             │ │
│  │  • Search params: filters, date ranges   │ │
│  │  • Path params: client ID, report ID     │ │
│  └──────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```

## 5. API Client Architecture

```typescript
// lib/api-client.ts
const apiClient = {
  baseURL: process.env.NEXT_PUBLIC_API_URL,

  // Automatic token refresh on 401
  // Request/response interceptors
  // Request ID injection
  // Error normalization

  get: <T>(url, config?) => Promise<ApiResponse<T>>,
  post: <T>(url, data, config?) => Promise<ApiResponse<T>>,
  put: <T>(url, data, config?) => Promise<ApiResponse<T>>,
  delete: <T>(url, config?) => Promise<ApiResponse<T>>,
};
```

## 6. Error Handling Strategy

| Error Type | UI Response |
|-----------|------------|
| Network error | Toast: "Connection lost. Retrying..." + auto-retry |
| 401 Unauthorized | Redirect to /login with return URL |
| 403 Forbidden | Inline: "You don't have permission" |
| 404 Not Found | Full page: "Not found" with navigation |
| 422 Validation | Inline field errors on form |
| 429 Rate Limited | Toast: "Too many requests. Please wait." |
| 500 Server Error | Toast: "Something went wrong" + retry button |
| Report generation failure | Inline with retry option |
