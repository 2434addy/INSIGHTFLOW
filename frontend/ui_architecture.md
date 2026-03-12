# InsightFlow — UI Architecture

## 1. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | Next.js 14 (App Router) | SSR, RSC, file-based routing |
| Language | TypeScript 5.x (strict mode) | Type safety |
| Styling | Tailwind CSS 3.x | Utility-first CSS |
| Components | shadcn/ui | Accessible, composable primitives |
| State (server) | TanStack Query v5 | Server state, caching, sync |
| State (client) | Zustand | Lightweight client-side state |
| Forms | React Hook Form + Zod | Performance, type-safe validation |
| Charts | Recharts | SSR-compatible, composable |
| Tables | TanStack Table | Headless, performant |
| Auth | NextAuth.js v5 | OAuth, JWT session management |
| Testing | Vitest + Testing Library + Playwright | Unit, component, E2E |

## 2. Project Structure

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (auth)/                   # Auth route group (no layout chrome)
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   ├── forgot-password/page.tsx
│   │   │   └── layout.tsx            # Minimal auth layout
│   │   ├── (dashboard)/              # Dashboard route group
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── clients/
│   │   │   │   ├── page.tsx          # Client list
│   │   │   │   └── [id]/page.tsx     # Client detail
│   │   │   ├── reports/
│   │   │   │   ├── page.tsx          # Report list
│   │   │   │   ├── [id]/page.tsx     # Report view
│   │   │   │   └── generate/page.tsx # Report generation
│   │   │   ├── integrations/page.tsx
│   │   │   ├── settings/page.tsx
│   │   │   ├── team/page.tsx
│   │   │   └── layout.tsx            # Dashboard layout (sidebar + topbar)
│   │   ├── onboarding/               # Onboarding wizard
│   │   │   ├── page.tsx
│   │   │   └── layout.tsx
│   │   ├── layout.tsx                # Root layout
│   │   ├── page.tsx                  # Landing page (marketing)
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                       # shadcn/ui primitives
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── table.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...
│   │   ├── layout/
│   │   │   ├── sidebar.tsx
│   │   │   ├── topbar.tsx
│   │   │   ├── breadcrumbs.tsx
│   │   │   └── mobile-nav.tsx
│   │   ├── dashboard/
│   │   │   ├── kpi-card.tsx
│   │   │   ├── overview-chart.tsx
│   │   │   ├── client-table.tsx
│   │   │   └── date-range-picker.tsx
│   │   ├── reports/
│   │   │   ├── report-preview.tsx
│   │   │   ├── report-section.tsx
│   │   │   ├── generation-progress.tsx
│   │   │   └── report-config-form.tsx
│   │   ├── integrations/
│   │   │   ├── platform-card.tsx
│   │   │   ├── connection-status.tsx
│   │   │   └── oauth-button.tsx
│   │   └── common/
│   │       ├── loading-skeleton.tsx
│   │       ├── empty-state.tsx
│   │       ├── error-boundary.tsx
│   │       └── page-header.tsx
│   ├── hooks/
│   │   ├── use-auth.ts
│   │   ├── use-clients.ts
│   │   ├── use-reports.ts
│   │   ├── use-metrics.ts
│   │   ├── use-integrations.ts
│   │   └── use-websocket.ts
│   ├── lib/
│   │   ├── api-client.ts             # Axios/fetch wrapper with auth
│   │   ├── auth.ts                   # NextAuth config
│   │   ├── utils.ts                  # Utility functions
│   │   ├── constants.ts              # App constants
│   │   └── validations.ts            # Zod schemas (shared with backend)
│   ├── stores/
│   │   ├── workspace-store.ts        # Current workspace state
│   │   ├── ui-store.ts               # Sidebar state, theme, etc.
│   │   └── onboarding-store.ts       # Onboarding wizard state
│   └── types/
│       ├── api.ts                    # API response types
│       ├── models.ts                 # Domain model types
│       └── enums.ts                  # Shared enums
├── public/
│   ├── images/
│   └── fonts/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## 3. Rendering Strategy

| Route | Strategy | Rationale |
|-------|----------|-----------|
| Landing page | SSG | Static marketing content |
| Login/Register | SSR | SEO, fast initial load |
| Dashboard | SSR + Client | Server-rendered shell, client-side data updates |
| Client detail | SSR + Client | Initial data server-rendered, real-time updates |
| Report view | SSR | Full content rendered server-side for performance |
| Report generation | Client | Interactive wizard, WebSocket progress |
| Settings | Client | Interactive forms |

## 4. Data Fetching Patterns

### Server Components (RSC)
```typescript
// app/(dashboard)/dashboard/page.tsx
async function DashboardPage() {
  const overview = await getOverview();  // Server-side fetch
  return (
    <div>
      <KPICards data={overview.kpis} />
      <OverviewChart data={overview.trends} />  {/* Client component */}
      <ClientTable initialData={overview.clients} />
    </div>
  );
}
```

### Client Components (TanStack Query)
```typescript
// hooks/use-clients.ts
export function useClients(params: ClientListParams) {
  return useQuery({
    queryKey: ['clients', params],
    queryFn: () => apiClient.get('/clients', { params }),
    staleTime: 5 * 60 * 1000,  // 5 minutes
  });
}
```

## 5. Authentication Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Browser  │────▶│  NextAuth    │────▶│  Backend API │
│           │     │  Middleware   │     │  /auth/*     │
│  Cookie:  │     │              │     │              │
│  session  │◀────│  JWT verify  │◀────│  Issue JWT   │
└──────────┘     └──────────────┘     └──────────────┘
```

- NextAuth handles session cookie on the frontend
- Backend API handles JWT issuance and validation
- Middleware protects all `/(dashboard)` routes
- Redirect to `/login` if unauthenticated

## 6. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| LCP (Largest Contentful Paint) | < 1.5s | Dashboard initial load |
| FID (First Input Delay) | < 100ms | Any interaction |
| CLS (Cumulative Layout Shift) | < 0.1 | All pages |
| TTI (Time to Interactive) | < 2s | Dashboard |
| Bundle size (initial) | < 150KB gzipped | First load JS |

### Optimization Strategies
- **Code splitting:** Automatic via Next.js App Router
- **Image optimization:** Next.js `<Image>` component, WebP format
- **Font optimization:** `next/font` with Inter, subset loading
- **Prefetching:** Next.js link prefetch for likely navigation paths
- **Lazy loading:** Charts, heavy components loaded on viewport entry
- **Memoization:** `React.memo`, `useMemo`, `useCallback` for expensive renders

## 7. Accessibility Standards

- **WCAG 2.1 AA** compliance target
- All interactive elements keyboard navigable
- ARIA labels on all non-text controls
- Color contrast ratio ≥ 4.5:1 (normal text), ≥ 3:1 (large text)
- Screen reader tested (VoiceOver, NVDA)
- Focus management on route changes and modal opens
- shadcn/ui provides accessible primitives by default
