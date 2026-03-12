# InsightFlow — Dashboard Wireframe Specifications

## 1. Layout System

### Responsive Breakpoints
- **Desktop:** 1280px+ (primary design target)
- **Tablet:** 768px–1279px
- **Mobile:** 320px–767px (limited dashboard, full report viewing)

### Grid System
- 12-column grid with 24px gutters
- Sidebar: 240px (collapsible to 64px icon-only)
- Main content: fluid, max-width 1440px

## 2. Global Navigation

```
┌────────────────────────────────────────────────────────────────┐
│  [Logo]  InsightFlow          🔍 Search    🔔 3    👤 Jane ▾  │
├──────────┬─────────────────────────────────────────────────────┤
│          │                                                     │
│  ── NAV ─│                                                     │
│          │                                                     │
│  📊 Dash │                    CONTENT AREA                     │
│  👥 Clients                                                    │
│  📄 Reports                                                    │
│  🔗 Connect                                                    │
│  ⚙ Settings                                                   │
│  👤 Team │                                                     │
│          │                                                     │
│  ─────── │                                                     │
│  ? Help  │                                                     │
│          │                                                     │
└──────────┴─────────────────────────────────────────────────────┘
```

### Navigation Items
| Item | Icon | Route | Description |
|------|------|-------|-------------|
| Dashboard | chart-bar | /dashboard | Overview KPIs and trends |
| Clients | users | /clients | Client list and management |
| Reports | file-text | /reports | Report history and generation |
| Integrations | link | /integrations | Platform connections |
| Settings | settings | /settings | Workspace configuration |
| Team | user-plus | /team | Team member management |

## 3. Dashboard Overview Page

### Header Section
```
┌────────────────────────────────────────────────────────────┐
│  Dashboard                          [Last 30 days ▾]  🔄   │
│  Welcome back, Jane. Here's how your clients are doing.    │
└────────────────────────────────────────────────────────────┘
```

### KPI Cards Row
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Total Spend │  │  Conversions │  │  Avg ROAS    │  │  Avg CPA     │
│              │  │              │  │              │  │              │
│  $47,832     │  │  2,341       │  │  4.2x        │  │  $20.43      │
│  ▲ 12.3%     │  │  ▲ 8.7%     │  │  ▲ 5.1%     │  │  ▼ 3.2%     │
│  vs prev     │  │  vs prev     │  │  vs prev     │  │  vs prev     │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

### KPI Card Specification
- **Size:** Flexible, min 200px, equal distribution across row
- **Content:** Metric name, value (large), trend indicator (▲▼), comparison text
- **Colors:** Green for positive trends, Red for negative, Gray for neutral
- **Interaction:** Click → drill down to metric detail view

### Charts Section
```
┌─────────────────────────────────────────┐  ┌────────────────────────┐
│  Spend & Conversions Over Time          │  │  Spend by Platform     │
│                                         │  │                        │
│  ▓▓                                     │  │    ┌───┐               │
│  ▓▓▓▓                                   │  │    │   │  Meta: 62%    │
│  ▓▓▓▓▓▓     ▓▓                          │  │    │   │  Google: 38%  │
│  ▓▓▓▓▓▓▓▓   ▓▓▓▓                        │  │    └───┘               │
│  ▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓                      │  │                        │
│  ──────────────────                      │  │                        │
│  Week 1  Week 2  Week 3  Week 4         │  │                        │
│                                         │  │                        │
│  ── Spend  ── Conversions               │  │                        │
└─────────────────────────────────────────┘  └────────────────────────┘
```

### Chart Specifications
- **Primary chart:** Line/area chart showing spend and conversions over time (dual Y-axis)
- **Secondary chart:** Donut chart showing spend distribution by platform
- **Interactions:** Hover for tooltips, click legend to toggle series, date range affects all charts
- **Library:** Recharts or Chart.js (SSR-compatible)

### Client Performance Table
```
┌──────────────────────────────────────────────────────────────────┐
│  Client Performance                    [Search...] [Filter ▾]    │
├────────┬──────────┬───────┬──────┬──────┬────────┬──────────────┤
│ Client │ Platforms│ Spend │ Conv │ ROAS │ Trend  │ Actions      │
├────────┼──────────┼───────┼──────┼──────┼────────┼──────────────┤
│ Acme   │ 🟦🟥    │ $12K  │ 543  │ 4.5x │ ▲ 15%  │ [Report] [→] │
│ Beta   │ 🟦      │ $8.2K │ 312  │ 3.8x │ ▼ 2%   │ [Report] [→] │
│ Gamma  │ 🟥      │ $5.1K │ 198  │ 3.2x │ ▲ 8%   │ [Report] [→] │
│ ...    │         │       │      │      │        │              │
└────────┴──────────┴───────┴──────┴──────┴────────┴──────────────┘
```

### Table Specifications
- **Columns:** Client name, connected platforms (icons), spend, conversions, ROAS, trend, actions
- **Sorting:** Click column headers to sort
- **Filtering:** By platform, by performance (top/bottom), by trend
- **Pagination:** 20 rows per page, infinite scroll option
- **Actions:** Quick-generate report button, navigate to client detail

## 4. Client Detail Page

```
┌────────────────────────────────────────────────────────────┐
│  ← Back to Clients                                         │
│                                                            │
│  Acme Corp                    [Generate Report]  [⚙]      │
│  Meta Ads • Google Ads        Last synced: 2 min ago       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [KPI Cards - client specific]                             │
│                                                            │
│  [Performance Chart - client specific]                     │
│                                                            │
│  [Campaign Breakdown Table]                                │
│  ┌──────────┬───────┬──────┬──────┬──────┐                │
│  │ Campaign │ Spend │ Impr │ Conv │ ROAS │                │
│  ├──────────┼───────┼──────┼──────┼──────┤                │
│  │ Summer   │ $4.2K │ 89K  │ 234  │ 5.1x │                │
│  │ Brand    │ $3.1K │ 120K │ 156  │ 3.8x │                │
│  └──────────┴───────┴──────┴──────┴──────┘                │
│                                                            │
│  [Recent Reports]                                          │
│  ┌──────────────────────────────────────┐                  │
│  │ 📄 March 2026 Performance Report    │                  │
│  │ 📄 February 2026 Performance Report │                  │
│  └──────────────────────────────────────┘                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 5. Report View Page

```
┌────────────────────────────────────────────────────────────┐
│  ← Back to Reports                    [Edit] [PDF] [Share] │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                                                      │  │
│  │  ACME CORP                                           │  │
│  │  Monthly Performance Report                          │  │
│  │  March 2026                                          │  │
│  │                                                      │  │
│  │  ─────────────────────────────────────────────────   │  │
│  │                                                      │  │
│  │  Executive Summary                                   │  │
│  │  ─────────────────                                   │  │
│  │  This month, Acme Corp's marketing campaigns         │  │
│  │  delivered strong performance across both Meta and    │  │
│  │  Google Ads, with total conversions up 15% month-    │  │
│  │  over-month...                                       │  │
│  │                                                      │  │
│  │  Key Metrics                                         │  │
│  │  ────────────                                        │  │
│  │  [KPI visual cards]                                  │  │
│  │                                                      │  │
│  │  Performance Trends                                  │  │
│  │  ──────────────────                                  │  │
│  │  [Charts]                                            │  │
│  │                                                      │  │
│  │  AI Insights                                         │  │
│  │  ───────────                                         │  │
│  │  1. Your Meta retargeting campaigns are...           │  │
│  │  2. Google Search CPA decreased by...               │  │
│  │  3. Weekend performance shows...                     │  │
│  │                                                      │  │
│  │  Recommendations                                     │  │
│  │  ───────────────                                     │  │
│  │  1. Consider increasing budget for...                │  │
│  │  2. Test new ad creative for...                      │  │
│  │  3. Optimize bidding strategy on...                  │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 6. Design Tokens

### Colors
| Token | Value | Usage |
|-------|-------|-------|
| --primary | #2563EB (Blue 600) | Primary actions, links |
| --primary-dark | #1D4ED8 (Blue 700) | Hover states |
| --success | #16A34A (Green 600) | Positive trends, success states |
| --danger | #DC2626 (Red 600) | Negative trends, errors |
| --warning | #D97706 (Amber 600) | Warnings, attention |
| --neutral-50 | #F9FAFB | Page background |
| --neutral-100 | #F3F4F6 | Card backgrounds |
| --neutral-900 | #111827 | Primary text |
| --neutral-500 | #6B7280 | Secondary text |

### Typography
| Element | Font | Size | Weight |
|---------|------|------|--------|
| H1 | Inter | 30px | 700 |
| H2 | Inter | 24px | 600 |
| H3 | Inter | 18px | 600 |
| Body | Inter | 14px | 400 |
| Small | Inter | 12px | 400 |
| KPI Value | Inter | 32px | 700 |
| KPI Label | Inter | 12px | 500 |

### Spacing
- Base unit: 4px
- Component padding: 16px (4 units)
- Card padding: 24px (6 units)
- Section gap: 32px (8 units)
- Page padding: 32px desktop, 16px mobile

### Shadows
- Card: `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)`
- Dropdown: `0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)`
- Modal: `0 25px 50px rgba(0,0,0,0.25)`

### Border Radius
- Button: 8px
- Card: 12px
- Input: 8px
- Badge: 9999px (pill)
