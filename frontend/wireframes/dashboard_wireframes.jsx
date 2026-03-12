/**
 * InsightFlow — UI Wireframe Reference (JSX)
 *
 * This file is a VISUAL REFERENCE ONLY — it is not imported or rendered
 * by the application. It documents the target layout for every screen
 * so that any engineer can open it side-by-side while building.
 *
 * Screens:
 *   1. Dashboard Overview
 *   2. Campaign Performance
 *   3. Insights
 *   4. Report Builder
 *   5. Report Viewer
 *   6. Client Portal
 *
 * Design tokens (from wireframe spec):
 *   Primary:   #2563EB (Blue 600)
 *   Success:   #16A34A (Green 600)
 *   Danger:    #DC2626 (Red 600)
 *   Warning:   #D97706 (Amber 600)
 *   BG:        #F9FAFB (Neutral 50)
 *   Card BG:   #FFFFFF
 *   Text:      #111827 (Neutral 900)
 *   Muted:     #6B7280 (Neutral 500)
 *   Font:      Inter
 *   Radius:    12px (cards), 8px (inputs/buttons), 9999px (badges)
 *   Shadow:    0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)
 */

// ─────────────────────────────────────────────────────────
// SHARED LAYOUT SHELL
// ─────────────────────────────────────────────────────────

export function AppShell() {
  return (
    <div className="flex h-screen bg-neutral-50">
      {/* ── Sidebar (240px, collapsible to 64px) ── */}
      <aside className="flex w-60 flex-col border-r border-neutral-200 bg-white">
        {/* Logo */}
        <div className="flex h-16 items-center gap-2 px-5">
          <div className="h-8 w-8 rounded-lg bg-blue-600" />
          <span className="text-lg font-bold text-neutral-900">InsightFlow</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          <NavItem icon="BarChart3" label="Dashboard" href="/dashboard" active />
          <NavItem icon="Users" label="Clients" href="/clients" />
          <NavItem icon="Lightbulb" label="Insights" href="/insights" />
          <NavItem icon="Megaphone" label="Campaigns" href="/campaigns" />
          <NavItem icon="FileText" label="Reports" href="/reports" />
          <NavItem icon="Link" label="Integrations" href="/integrations" />
          <NavItem icon="Settings" label="Settings" href="/settings" />
        </nav>

        {/* Footer */}
        <div className="border-t border-neutral-200 p-4">
          <NavItem icon="HelpCircle" label="Help & Support" href="/help" />
        </div>
      </aside>

      {/* ── Main Area ── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Topbar */}
        <header className="flex h-16 items-center justify-between border-b border-neutral-200 bg-white px-6">
          <h1 className="text-lg font-semibold text-neutral-900">Dashboard</h1>
          <div className="flex items-center gap-4">
            <SearchButton />
            <NotificationBell count={3} />
            <UserAvatar name="Jane" />
          </div>
        </header>

        {/* Scrollable Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {/* Page content goes here */}
        </main>
      </div>
    </div>
  );
}

function NavItem({ icon, label, href, active }) {
  return (
    <a
      href={href}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? "bg-blue-50 text-blue-700"
          : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900"
      }`}
    >
      <span className="h-5 w-5">{/* {icon} */}</span>
      {label}
    </a>
  );
}

function SearchButton() {
  return (
    <button className="flex items-center gap-2 rounded-lg border border-neutral-200 px-3 py-1.5 text-sm text-neutral-500 hover:bg-neutral-50">
      <span>Search...</span>
      <kbd className="rounded border border-neutral-300 bg-neutral-100 px-1.5 py-0.5 text-xs">
        Ctrl K
      </kbd>
    </button>
  );
}

function NotificationBell({ count }) {
  return (
    <button className="relative rounded-lg p-2 hover:bg-neutral-100">
      {/* Bell icon */}
      <span className="h-5 w-5 text-neutral-600">{/* Bell */}</span>
      {count > 0 && (
        <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white">
          {count}
        </span>
      )}
    </button>
  );
}

function UserAvatar({ name }) {
  return (
    <button className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-neutral-100">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-medium text-blue-700">
        {name[0]}
      </div>
      <span className="text-sm font-medium text-neutral-700">{name}</span>
      <span className="text-neutral-400">{/* ChevronDown */}</span>
    </button>
  );
}

// ─────────────────────────────────────────────────────────
// 1. DASHBOARD OVERVIEW
// ─────────────────────────────────────────────────────────

export function DashboardWireframe() {
  return (
    <div className="space-y-8">
      {/* ── Page Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">
            Performance Overview
          </h1>
          <p className="text-sm text-neutral-500">
            Welcome back, Jane. Here's how your clients are doing.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <DateRangePicker label="Last 30 days" />
          <RefreshButton />
        </div>
      </div>

      {/* ── KPI Cards (4-column grid) ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          label="Total Spend"
          value="$47,832"
          change={+12.3}
          icon="DollarSign"
        />
        <KPICard
          label="Conversions"
          value="2,341"
          change={+8.7}
          icon="ShoppingCart"
        />
        <KPICard
          label="Avg ROAS"
          value="4.2x"
          change={+5.1}
          icon="TrendingUp"
        />
        <KPICard
          label="Avg CPA"
          value="$20.43"
          change={-3.2}
          icon="MousePointerClick"
          invertColor
        />
      </div>

      {/* ── Charts Row ── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Spend & Conversions Over Time (2/3 width) */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Spend & Conversions Over Time</CardTitle>
              <p className="text-sm text-neutral-500">Daily trend for selected period</p>
            </CardHeader>
            <CardContent>
              {/*
                Recharts dual Y-axis LineChart
                Left axis:  Spend ($) — blue line
                Right axis: Conversions — green line
                X axis:     Date labels
                Tooltip:    Shows both values on hover
                Legend:      Bottom, toggleable
              */}
              <div className="flex h-72 items-center justify-center rounded-lg bg-neutral-100 text-sm text-neutral-400">
                [Dual-Axis Line Chart: Spend + Conversions]
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Spend by Platform (1/3 width) */}
        <Card>
          <CardHeader>
            <CardTitle>Spend by Platform</CardTitle>
          </CardHeader>
          <CardContent>
            {/*
              Recharts PieChart / Donut
              Segments: Meta Ads (#3B82F6), Google Ads (#F59E0B), Shopify (#10B981)
              Center:   Total spend
              Legend:    Below chart with percentages
            */}
            <div className="flex h-72 items-center justify-center rounded-lg bg-neutral-100 text-sm text-neutral-400">
              [Donut Chart: Platform Distribution]
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Top Campaigns Table ── */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Top Campaigns</CardTitle>
            <a
              href="/campaigns"
              className="text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              View all
            </a>
          </div>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 text-left text-neutral-500">
                <th className="pb-3 font-medium">Campaign</th>
                <th className="pb-3 font-medium">Platform</th>
                <th className="pb-3 font-medium text-right">Spend</th>
                <th className="pb-3 font-medium text-right">Conv.</th>
                <th className="pb-3 font-medium text-right">ROAS</th>
                <th className="pb-3 font-medium">Tier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              <CampaignRow name="Summer Sale - Retargeting" platform="Meta Ads" spend="$8,200" conversions="340" roas="5.20x" tier="star" />
              <CampaignRow name="Brand Awareness - Video" platform="Google Ads" spend="$6,100" conversions="180" roas="3.90x" tier="strong" />
              <CampaignRow name="Holiday Promo" platform="Meta Ads" spend="$4,500" conversions="210" roas="4.80x" tier="star" />
              <CampaignRow name="Search - Generic Terms" platform="Google Ads" spend="$5,200" conversions="95" roas="1.80x" tier="average" />
              <CampaignRow name="Display Prospecting" platform="Google Ads" spend="$3,100" conversions="22" roas="0.70x" tier="waster" />
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 2. CAMPAIGN PERFORMANCE
// ─────────────────────────────────────────────────────────

export function CampaignPerformanceWireframe() {
  return (
    <div className="space-y-8">
      {/* ── Page Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">
          Campaign Performance
        </h1>
        <p className="text-sm text-neutral-500">
          Performance metrics and tier classification for all campaigns
        </p>
      </div>

      {/* ── Summary KPIs ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard label="Active Campaigns" value="7" icon="Megaphone" />
        <KPICard label="Total Spend" value="$35,600" icon="DollarSign" />
        <KPICard label="Total Conversions" value="1,075" icon="ShoppingCart" />
        <KPICard label="Weighted ROAS" value="3.52x" icon="TrendingUp" />
      </div>

      {/* ── Tier Distribution Filter ── */}
      <Card>
        <CardHeader>
          <CardTitle>Tier Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          {/*
            Pill / chip buttons for filtering by tier.
            Active tier is blue-filled; others are outlined.
            Each shows count: "Star (2)", "Strong (2)", etc.
          */}
          <div className="flex flex-wrap gap-3">
            <TierFilterChip label="All" count={8} active />
            <TierFilterChip label="Star" count={2} color="green" />
            <TierFilterChip label="Strong" count={2} color="blue" />
            <TierFilterChip label="Average" count={2} color="amber" />
            <TierFilterChip label="Underperformer" count={1} color="orange" />
            <TierFilterChip label="Waster" count={1} color="red" />
          </div>
        </CardContent>
      </Card>

      {/* ── Sortable Campaign Table ── */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-200 text-left text-neutral-500">
                  <th className="p-4 font-medium">Campaign</th>
                  <th className="p-4 font-medium">Platform</th>
                  <th className="p-4 font-medium">Tier</th>
                  <th className="p-4 font-medium">
                    <SortableHeader label="Spend" />
                  </th>
                  <th className="p-4 font-medium">
                    <SortableHeader label="Conv." />
                  </th>
                  <th className="p-4 font-medium">CTR</th>
                  <th className="p-4 font-medium">
                    <SortableHeader label="CPA" />
                  </th>
                  <th className="p-4 font-medium">
                    <SortableHeader label="ROAS" />
                  </th>
                  <th className="p-4 font-medium">
                    <SortableHeader label="Score" active />
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {/*
                  Each row:
                  - Campaign name + status subtitle
                  - Platform label
                  - Tier badge (color-coded)
                  - Spend, Conversions, CTR, CPA, ROAS (right-aligned numbers)
                  - Efficiency score: mini progress bar + numeric value
                    - >= 0.7 → green bar
                    - >= 0.4 → amber bar
                    - <  0.4 → red bar
                */}
                <CampaignTableRow
                  name="Summer Sale - Retargeting"
                  status="active"
                  platform="Meta Ads"
                  tier="star"
                  spend="$8,200"
                  conversions="340"
                  ctr="3.0%"
                  cpa="$24.12"
                  roas="5.20x"
                  score={92}
                />
                <CampaignTableRow
                  name="Holiday Promo"
                  status="active"
                  platform="Meta Ads"
                  tier="star"
                  spend="$4,500"
                  conversions="210"
                  ctr="3.0%"
                  cpa="$21.43"
                  roas="4.80x"
                  score={88}
                />
                <CampaignTableRow
                  name="Brand Awareness - Video"
                  status="active"
                  platform="Google Ads"
                  tier="strong"
                  spend="$6,100"
                  conversions="180"
                  ctr="2.0%"
                  cpa="$33.89"
                  roas="3.90x"
                  score={74}
                />
                <CampaignTableRow
                  name="Shopping - Best Sellers"
                  status="active"
                  platform="Google Ads"
                  tier="strong"
                  spend="$3,800"
                  conversions="145"
                  ctr="3.0%"
                  cpa="$26.21"
                  roas="3.60x"
                  score={71}
                />
                <CampaignTableRow
                  name="Search - Generic Terms"
                  status="active"
                  platform="Google Ads"
                  tier="average"
                  spend="$5,200"
                  conversions="95"
                  ctr="2.0%"
                  cpa="$54.74"
                  roas="1.80x"
                  score={45}
                />
                <CampaignTableRow
                  name="Social - Interest Targeting"
                  status="active"
                  platform="Meta Ads"
                  tier="average"
                  spend="$2,900"
                  conversions="68"
                  ctr="2.5%"
                  cpa="$42.65"
                  roas="2.10x"
                  score={38}
                />
                <CampaignTableRow
                  name="Display - Remarketing"
                  status="paused"
                  platform="Google Ads"
                  tier="underperformer"
                  spend="$1,800"
                  conversions="15"
                  ctr="1.0%"
                  cpa="$120.00"
                  roas="0.90x"
                  score={18}
                />
                <CampaignTableRow
                  name="Display Prospecting"
                  status="active"
                  platform="Google Ads"
                  tier="waster"
                  spend="$3,100"
                  conversions="22"
                  ctr="1.0%"
                  cpa="$140.91"
                  roas="0.70x"
                  score={8}
                />
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 3. INSIGHTS
// ─────────────────────────────────────────────────────────

export function InsightsWireframe() {
  return (
    <div className="space-y-8">
      {/* ── Page Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">
          AI-Generated Insights
        </h1>
        <p className="text-sm text-neutral-500">
          Key findings from your latest analysis
        </p>
      </div>

      {/* ── Category Filters ── */}
      {/*
        Rounded pill buttons — active pill is solid blue, inactive is gray.
        Each filter shows a count badge.
        Categories: All, Performance, Efficiency, Anomaly, Opportunity, Risk
      */}
      <div className="flex flex-wrap gap-2">
        <FilterPill label="All" active />
        <FilterPill label="Performance" count={1} />
        <FilterPill label="Efficiency" count={1} />
        <FilterPill label="Anomaly" count={1} />
        <FilterPill label="Opportunity" count={1} />
        <FilterPill label="Risk" count={1} />
      </div>

      {/* ── Insights List ── */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-neutral-900">Insights (5)</h3>

        {/*
          InsightCard layout:
          ┌─────────────────────────────────────────────────────┐
          │  [Icon]  HEADLINE                    [Badge: type]  │
          │          Detail paragraph text...                    │
          │          Confidence: 95%  •  Platform: Meta Ads     │
          └─────────────────────────────────────────────────────┘

          Sentiment styles:
          - positive  → green left border, green icon
          - attention → amber left border, amber icon
          - neutral   → blue left border, blue icon
        */}
        <InsightCard
          category="performance"
          sentiment="positive"
          headline="Conversions up 12.5% month-over-month"
          detail="Total conversions increased from 1,618 to 1,820, driven by Meta retargeting campaigns with a 23% lift in conversion rate."
          confidence={95}
          platform="Meta Ads"
        />
        <InsightCard
          category="efficiency"
          sentiment="positive"
          headline="CPA decreased by 5.4% to $24.85"
          detail="Cost per acquisition improved across all platforms. Google Ads saw the biggest improvement at -8.2%."
          confidence={92}
        />
        <InsightCard
          category="anomaly"
          sentiment="attention_needed"
          headline="Unusual spike in Google Ads CPC on Feb 18"
          detail="CPC jumped 340% above the rolling average ($3.42 vs expected $0.95). Coincided with increased competitor bidding."
          confidence={88}
          platform="Google Ads"
        />
        <InsightCard
          category="opportunity"
          sentiment="neutral"
          headline="Meta retargeting audience shows expansion potential"
          detail="Retargeting has 5.2x ROAS with only 18% of total budget. Increasing allocation could yield more high-quality conversions."
          confidence={85}
          platform="Meta Ads"
        />
        <InsightCard
          category="risk"
          sentiment="attention_needed"
          headline="Display Prospecting campaign burning budget"
          detail="0.7x ROAS with $3,100 in spend. Only 22 conversions, significantly below the account average of 60 per campaign."
          confidence={93}
          platform="Google Ads"
        />
      </div>

      {/* ── Recommendations List ── */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-neutral-900">
          Recommendations (3)
        </h3>

        {/*
          RecommendationCard layout:
          ┌─────────────────────────────────────────────────────┐
          │  TITLE                                              │
          │  [Priority: HIGH]  [Effort: LOW]                    │
          │                                                     │
          │  Description text...                                │
          │                                                     │
          │  Expected Impact: +$12,400 additional revenue       │
          │                                                     │
          │  Action Items:                                      │
          │  ☐ Pause Display Prospecting campaign               │
          │  ☐ Increase retargeting daily budget by $100        │
          │  ☐ Monitor performance for 7 days                   │
          └─────────────────────────────────────────────────────┘

          Priority badge colors:
          - high   → red
          - medium → amber
          - low    → green
        */}
        <RecommendationCard
          title="Reallocate $3,100 from Display Prospecting"
          description="Pause Display Prospecting (0.7x ROAS) and redirect to Summer Sale Retargeting (5.2x ROAS)."
          priority="high"
          effort="low"
          expectedImpact="+$12,400 in additional revenue"
          actionItems={[
            "Pause Display Prospecting campaign",
            "Increase Summer Sale Retargeting daily budget by $100",
            "Monitor performance for 7 days",
          ]}
        />
        <RecommendationCard
          title="Refresh Google Ads creative to address CPC spike"
          description="The Feb 18th CPC spike suggests ad fatigue or increased competition. Refresh ad copy and test new variations."
          priority="medium"
          effort="medium"
          expectedImpact="Reduce CPC by 15-20%"
          actionItems={[
            "Create 3 new ad variations",
            "A/B test headlines and descriptions",
            "Review competitor ad library for positioning gaps",
          ]}
        />
        <RecommendationCard
          title="Expand Meta lookalike audiences"
          description="Current retargeting success suggests strong audience signal. Create 1-3% lookalikes from recent converters."
          priority="medium"
          effort="low"
          expectedImpact="+15% conversion volume at similar CPA"
          actionItems={[
            "Export last 90 days converter list",
            "Create 1%, 2%, and 3% lookalike audiences",
            "Launch test campaign with $50/day budget",
          ]}
        />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 4. REPORT BUILDER
// ─────────────────────────────────────────────────────────

export function ReportBuilderWireframe() {
  return (
    <div className="space-y-8">
      {/* ── Page Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">
          Generate Report
        </h1>
        <p className="text-sm text-neutral-500">
          Configure and generate an AI-powered performance report
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* ── Configuration Panel (2/3 width) ── */}
        <div className="space-y-6 lg:col-span-2">
          {/* Client Selection */}
          <Card>
            <CardHeader>
              <CardTitle>1. Select Client</CardTitle>
            </CardHeader>
            <CardContent>
              {/*
                Searchable dropdown with client avatars.
                Shows connected platforms as icons next to each name.
              */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-neutral-700">
                  Client
                </label>
                <select className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm">
                  <option>Acme Corp (Meta Ads, Google Ads)</option>
                  <option>Beta Inc (Meta Ads)</option>
                  <option>Gamma Ltd (Google Ads)</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Date Range */}
          <Card>
            <CardHeader>
              <CardTitle>2. Date Range</CardTitle>
            </CardHeader>
            <CardContent>
              {/*
                Preset buttons: Last 7 days, Last 30 days, Last quarter, Custom
                Custom shows a calendar range picker.
                Comparison toggle: "Compare with previous period"
              */}
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-lg border border-neutral-200 px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-50">
                    Last 7 days
                  </button>
                  <button className="rounded-lg border border-blue-600 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700">
                    Last 30 days
                  </button>
                  <button className="rounded-lg border border-neutral-200 px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-50">
                    Last quarter
                  </button>
                  <button className="rounded-lg border border-neutral-200 px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-50">
                    Custom
                  </button>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-neutral-600">Feb 1 – Feb 28, 2026</span>
                  <span className="text-xs text-neutral-400">vs Jan 2 – Jan 31, 2026</span>
                </div>
                <label className="flex items-center gap-2 text-sm text-neutral-700">
                  <input type="checkbox" defaultChecked className="rounded border-neutral-300" />
                  Compare with previous period
                </label>
              </div>
            </CardContent>
          </Card>

          {/* Platforms */}
          <Card>
            <CardHeader>
              <CardTitle>3. Platforms</CardTitle>
            </CardHeader>
            <CardContent>
              {/*
                Checkbox cards for each connected platform.
                Shows last sync time and record count.
              */}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <PlatformCheckbox
                  name="Meta Ads"
                  icon="meta"
                  lastSync="2 min ago"
                  records="12,400"
                  checked
                />
                <PlatformCheckbox
                  name="Google Ads"
                  icon="google"
                  lastSync="5 min ago"
                  records="9,800"
                  checked
                />
                <PlatformCheckbox
                  name="Shopify"
                  icon="shopify"
                  lastSync="1 hr ago"
                  records="3,200"
                />
                <PlatformCheckbox
                  name="GA4"
                  icon="ga4"
                  status="Not connected"
                  disabled
                />
              </div>
            </CardContent>
          </Card>

          {/* Report Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>4. Report Options</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Tone */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-neutral-700">
                    Tone
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button className="rounded-lg border border-blue-600 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700">
                      Executive
                    </button>
                    <button className="rounded-lg border border-neutral-200 px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-50">
                      Technical
                    </button>
                    <button className="rounded-lg border border-neutral-200 px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-50">
                      Casual
                    </button>
                  </div>
                </div>

                {/* Sections to include */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-neutral-700">
                    Sections
                  </label>
                  <div className="space-y-2">
                    <SectionToggle label="Executive Summary" checked />
                    <SectionToggle label="KPI Overview" checked />
                    <SectionToggle label="Performance Trends" checked />
                    <SectionToggle label="Campaign Breakdown" checked />
                    <SectionToggle label="AI Insights" checked />
                    <SectionToggle label="Recommendations" checked />
                    <SectionToggle label="Platform Comparison" />
                  </div>
                </div>

                {/* AI Model */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-neutral-700">
                    AI Quality
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button className="rounded-lg border border-blue-600 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700">
                      Standard (Sonnet)
                    </button>
                    <button className="rounded-lg border border-neutral-200 px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-50">
                      Premium (Opus) — deeper analysis
                    </button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Preview / Summary Sidebar (1/3 width) ── */}
        <div className="space-y-6">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle>Report Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm">
                <SummaryRow label="Client" value="Acme Corp" />
                <SummaryRow label="Period" value="Feb 1 – Feb 28, 2026" />
                <SummaryRow label="Platforms" value="Meta Ads, Google Ads" />
                <SummaryRow label="Tone" value="Executive" />
                <SummaryRow label="Sections" value="6 selected" />
                <SummaryRow label="AI Model" value="Standard (Sonnet)" />
                <SummaryRow label="Est. Time" value="~30 seconds" />

                <hr className="border-neutral-200" />

                <button className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700">
                  Generate Report
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Generation Progress (shown after clicking Generate) */}
          <Card>
            <CardHeader>
              <CardTitle>Generation Progress</CardTitle>
            </CardHeader>
            <CardContent>
              {/*
                Progress bar + stage labels.
                Pipeline stages show as a vertical stepper.
                Each stage: icon + label + status (pending/running/done)
              */}
              <div className="space-y-3">
                <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-200">
                  <div className="h-full w-3/4 rounded-full bg-blue-600 transition-all" />
                </div>
                <p className="text-xs text-neutral-500">75% — Generating insights...</p>

                <div className="space-y-2 pt-2">
                  <PipelineStep label="Data Validation" status="done" />
                  <PipelineStep label="KPI Computation" status="done" />
                  <PipelineStep label="Trend Detection" status="done" />
                  <PipelineStep label="Anomaly Detection" status="done" />
                  <PipelineStep label="Campaign Evaluation" status="done" />
                  <PipelineStep label="Insight Generation" status="running" />
                  <PipelineStep label="Recommendations" status="pending" />
                  <PipelineStep label="Report Assembly" status="pending" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 5. REPORT VIEWER
// ─────────────────────────────────────────────────────────

export function ReportViewerWireframe() {
  return (
    <div className="space-y-6">
      {/* ── Toolbar ── */}
      <div className="flex items-center gap-4">
        <a
          href="/reports"
          className="flex items-center gap-1 rounded-lg p-2 text-neutral-600 hover:bg-neutral-100"
        >
          {/* ArrowLeft icon */}
          <span className="text-sm">Back to Reports</span>
        </a>
        <div className="flex-1" />
        <div className="flex gap-2">
          <button className="rounded-lg border border-neutral-200 px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50">
            Share
          </button>
          <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            Export PDF
          </button>
        </div>
      </div>

      {/* ── Report Metadata ── */}
      <div className="flex items-center gap-3">
        <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
          Completed
        </span>
        <span className="rounded-full border border-neutral-200 px-3 py-1 text-xs font-medium text-neutral-600">
          Executive Tone
        </span>
        <span className="rounded-full border border-neutral-200 px-3 py-1 text-xs font-medium text-neutral-600">
          Meta Ads
        </span>
        <span className="rounded-full border border-neutral-200 px-3 py-1 text-xs font-medium text-neutral-600">
          Google Ads
        </span>
        <span className="text-sm text-neutral-500">
          Generated Mar 1, 2026 at 10:32 AM
        </span>
      </div>

      {/* ── Report Title ── */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">
          February 2026 Performance Report
        </h1>
        <p className="text-sm text-neutral-500">
          Feb 1 – Feb 28, 2026 vs. previous period
        </p>
      </div>

      {/* ── Executive Summary ── */}
      <Card>
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none text-neutral-700">
            <p>
              February delivered strong performance improvements across all key
              metrics. Total conversions rose 12.5% to 1,820 while ROAS improved
              to 4.03x from 3.91x in the prior period, reflecting better budget
              allocation toward high-performing retargeting campaigns.
            </p>
            <p>
              Meta Ads continues to outperform with a 4.2x ROAS, though Google
              Ads showed the biggest CPA improvement at -8.2%. The Display
              Prospecting campaign remains the primary efficiency drag with
              $3,100 spent at just 0.7x ROAS.
            </p>
            <p>
              Looking ahead, expanding retargeting audience reach and refreshing
              Google Ads creative should sustain the positive momentum into March.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* ── KPI Summary ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard label="Total Spend" value="$45,230" change={+8.2} icon="DollarSign" />
        <KPICard label="Conversions" value="1,820" change={+12.5} icon="ShoppingCart" />
        <KPICard label="ROAS" value="4.03x" change={+3.1} icon="TrendingUp" />
        <KPICard label="CPA" value="$24.85" change={-5.4} icon="MousePointerClick" invertColor />
      </div>

      {/* ── Performance Trend Chart ── */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Performance Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-72 items-center justify-center rounded-lg bg-neutral-100 text-sm text-neutral-400">
            [Dual-Axis Line Chart: Spend + Conversions over 28 days]
          </div>
        </CardContent>
      </Card>

      {/* ── Key Insights ── */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-neutral-900">Key Insights</h3>
        <InsightCard
          category="performance"
          sentiment="positive"
          headline="Conversions up 12.5% month-over-month"
          detail="Driven by Meta retargeting campaigns with a 23% lift in conversion rate."
          confidence={95}
        />
        <InsightCard
          category="risk"
          sentiment="attention_needed"
          headline="Display Prospecting campaign has 0.7x ROAS"
          detail="$3,100 spent with only 22 conversions. Recommend pausing and reallocating."
          confidence={93}
        />
        <InsightCard
          category="opportunity"
          sentiment="neutral"
          headline="Retargeting budget can be expanded profitably"
          detail="5.2x ROAS with only 18% of budget. Increasing allocation could yield more conversions."
          confidence={85}
        />
      </div>

      {/* ── Recommendations ── */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-neutral-900">
          Recommendations
        </h3>
        <RecommendationCard
          title="Reallocate $3,100 from Display Prospecting to retargeting"
          description="Pause Display Prospecting (0.7x ROAS) and redirect to Summer Sale Retargeting (5.2x ROAS)."
          priority="high"
          effort="low"
          expectedImpact="+$12,400 additional revenue"
          actionItems={[
            "Pause Display Prospecting campaign",
            "Increase retargeting daily budget by $100",
          ]}
        />
        <RecommendationCard
          title="Refresh Google Ads creative"
          description="Address CPC spike by testing new ad variations and reviewing competitor positioning."
          priority="medium"
          effort="medium"
          expectedImpact="Reduce CPC by 15-20%"
          actionItems={[
            "Create 3 new ad variations",
            "A/B test headlines",
          ]}
        />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 6. CLIENT PORTAL
// ─────────────────────────────────────────────────────────

export function ClientPortalWireframe() {
  return (
    <div className="space-y-8">
      {/* ── Page Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Clients</h1>
          <p className="text-sm text-neutral-500">
            Manage your clients and their platform connections
          </p>
        </div>
        <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700">
          + Add Client
        </button>
      </div>

      {/* ── Search & Filter Bar ── */}
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search clients..."
            className="w-full max-w-md rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          />
        </div>
        <select className="rounded-lg border border-neutral-300 px-3 py-2 text-sm text-neutral-600">
          <option>All Platforms</option>
          <option>Meta Ads</option>
          <option>Google Ads</option>
        </select>
        <select className="rounded-lg border border-neutral-300 px-3 py-2 text-sm text-neutral-600">
          <option>Sort: Performance</option>
          <option>Sort: Name A-Z</option>
          <option>Sort: Spend High-Low</option>
        </select>
      </div>

      {/* ── Client Cards Grid ── */}
      {/*
        Each client card:
        ┌─────────────────────────────────────────────┐
        │  [Avatar] Client Name            [••• menu] │
        │  Meta Ads • Google Ads                      │
        │                                             │
        │  Spend        Conversions       ROAS        │
        │  $12,400      543               4.5x        │
        │  ▲ 15.2%      ▲ 8.3%           ▲ 3.1%      │
        │                                             │
        │  [Last report: Mar 1, 2026]                 │
        │                                             │
        │  [Generate Report]  [View Details →]        │
        └─────────────────────────────────────────────┘
      */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <ClientCard
          name="Acme Corp"
          platforms={["Meta Ads", "Google Ads"]}
          spend="$12,400"
          spendChange={+15.2}
          conversions="543"
          conversionsChange={+8.3}
          roas="4.5x"
          roasChange={+3.1}
          lastReport="Mar 1, 2026"
        />
        <ClientCard
          name="Beta Inc"
          platforms={["Meta Ads"]}
          spend="$8,200"
          spendChange={+5.8}
          conversions="312"
          conversionsChange={+12.1}
          roas="3.8x"
          roasChange={-1.2}
          lastReport="Feb 28, 2026"
        />
        <ClientCard
          name="Gamma Ltd"
          platforms={["Google Ads"]}
          spend="$5,100"
          spendChange={-2.4}
          conversions="198"
          conversionsChange={+4.5}
          roas="3.2x"
          roasChange={+6.8}
          lastReport="Feb 27, 2026"
        />
        <ClientCard
          name="Delta Co"
          platforms={["Meta Ads", "Google Ads"]}
          spend="$15,800"
          spendChange={+22.1}
          conversions="720"
          conversionsChange={+18.4}
          roas="4.8x"
          roasChange={+7.2}
          lastReport="Mar 2, 2026"
        />
        <ClientCard
          name="Epsilon Group"
          platforms={["Meta Ads"]}
          spend="$3,400"
          spendChange={+1.1}
          conversions="105"
          conversionsChange={-3.8}
          roas="2.1x"
          roasChange={-5.4}
          lastReport="Feb 25, 2026"
        />
        <ClientCardEmpty />
      </div>

      {/* ── Client Detail View (expanded / separate page) ── */}
      <div className="border-t border-neutral-200 pt-8">
        <h2 className="mb-6 text-xl font-bold text-neutral-900">
          Client Detail View — Acme Corp
        </h2>

        {/* Back Navigation */}
        <a
          href="/clients"
          className="mb-4 inline-flex items-center gap-1 text-sm text-neutral-600 hover:text-neutral-900"
        >
          {/* ArrowLeft */} Back to Clients
        </a>

        {/* Client Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Acme Corp</h1>
            <p className="text-sm text-neutral-500">
              Meta Ads, Google Ads — Last synced: 2 min ago
            </p>
          </div>
          <div className="flex gap-2">
            <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              Generate Report
            </button>
            <button className="rounded-lg border border-neutral-200 px-3 py-2 text-sm text-neutral-600 hover:bg-neutral-50">
              Settings
            </button>
          </div>
        </div>

        {/* Client KPIs */}
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KPICard label="Total Spend" value="$12,400" change={+15.2} icon="DollarSign" />
          <KPICard label="Conversions" value="543" change={+8.3} icon="ShoppingCart" />
          <KPICard label="ROAS" value="4.5x" change={+3.1} icon="TrendingUp" />
          <KPICard label="CPA" value="$22.84" change={-6.1} icon="MousePointerClick" invertColor />
        </div>

        {/* Client Performance Chart */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Performance Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-64 items-center justify-center rounded-lg bg-neutral-100 text-sm text-neutral-400">
              [Client-specific dual-axis line chart]
            </div>
          </CardContent>
        </Card>

        {/* Campaign Breakdown */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Campaign Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-200 text-left text-neutral-500">
                  <th className="pb-3 font-medium">Campaign</th>
                  <th className="pb-3 font-medium text-right">Spend</th>
                  <th className="pb-3 font-medium text-right">Impressions</th>
                  <th className="pb-3 font-medium text-right">Conv.</th>
                  <th className="pb-3 font-medium text-right">ROAS</th>
                  <th className="pb-3 font-medium">Tier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                <tr className="hover:bg-neutral-50">
                  <td className="py-3 font-medium text-neutral-900">Summer Sale - Retargeting</td>
                  <td className="py-3 text-right">$4,200</td>
                  <td className="py-3 text-right">89,000</td>
                  <td className="py-3 text-right">234</td>
                  <td className="py-3 text-right">5.1x</td>
                  <td className="py-3"><TierBadge tier="star" /></td>
                </tr>
                <tr className="hover:bg-neutral-50">
                  <td className="py-3 font-medium text-neutral-900">Brand Awareness - Video</td>
                  <td className="py-3 text-right">$3,100</td>
                  <td className="py-3 text-right">120,000</td>
                  <td className="py-3 text-right">156</td>
                  <td className="py-3 text-right">3.8x</td>
                  <td className="py-3"><TierBadge tier="strong" /></td>
                </tr>
                <tr className="hover:bg-neutral-50">
                  <td className="py-3 font-medium text-neutral-900">Display Prospecting</td>
                  <td className="py-3 text-right">$1,800</td>
                  <td className="py-3 text-right">95,000</td>
                  <td className="py-3 text-right">12</td>
                  <td className="py-3 text-right">0.7x</td>
                  <td className="py-3"><TierBadge tier="waster" /></td>
                </tr>
              </tbody>
            </table>
          </CardContent>
        </Card>

        {/* Recent Reports */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Reports</CardTitle>
              <a href="/reports" className="text-sm font-medium text-blue-600 hover:text-blue-700">
                View all
              </a>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <ReportListItem
                title="March 2026 Performance Report"
                date="Mar 1, 2026"
                status="completed"
              />
              <ReportListItem
                title="February 2026 Performance Report"
                date="Feb 1, 2026"
                status="completed"
              />
              <ReportListItem
                title="January 2026 Performance Report"
                date="Jan 2, 2026"
                status="completed"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// SHARED WIREFRAME COMPONENTS
// (reference building blocks — not real implementations)
// ─────────────────────────────────────────────────────────

function Card({ children, className = "" }) {
  return (
    <div className={`rounded-xl border border-neutral-200 bg-white shadow-sm ${className}`}>
      {children}
    </div>
  );
}

function CardHeader({ children }) {
  return <div className="border-b border-neutral-100 px-6 py-4">{children}</div>;
}

function CardTitle({ children }) {
  return <h3 className="text-base font-semibold text-neutral-900">{children}</h3>;
}

function CardContent({ children, className = "" }) {
  return <div className={`px-6 py-4 ${className}`}>{children}</div>;
}

function KPICard({ label, value, change, icon, invertColor = false }) {
  const isPositive = invertColor ? change < 0 : change > 0;
  const changeColor = change == null
    ? "text-neutral-500"
    : isPositive
      ? "text-green-600"
      : "text-red-600";
  const arrow = change > 0 ? "+" : "";

  return (
    <Card>
      <div className="p-5">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-neutral-500">{label}</span>
          <span className="rounded-lg bg-neutral-100 p-2 text-neutral-600">
            {/* {icon} */}
          </span>
        </div>
        <p className="mt-2 text-2xl font-bold text-neutral-900">{value}</p>
        {change != null && (
          <p className={`mt-1 text-sm font-medium ${changeColor}`}>
            {arrow}{change}% vs prev period
          </p>
        )}
      </div>
    </Card>
  );
}

function DateRangePicker({ label }) {
  return (
    <button className="flex items-center gap-2 rounded-lg border border-neutral-200 px-3 py-2 text-sm text-neutral-700 hover:bg-neutral-50">
      {/* Calendar icon */}
      {label}
      {/* ChevronDown */}
    </button>
  );
}

function RefreshButton() {
  return (
    <button className="rounded-lg border border-neutral-200 p-2 text-neutral-600 hover:bg-neutral-50">
      {/* RefreshCw icon */}
    </button>
  );
}

function CampaignRow({ name, platform, spend, conversions, roas, tier }) {
  return (
    <tr className="hover:bg-neutral-50">
      <td className="py-3 font-medium text-neutral-900">{name}</td>
      <td className="py-3 text-neutral-600">{platform}</td>
      <td className="py-3 text-right text-neutral-900">{spend}</td>
      <td className="py-3 text-right text-neutral-900">{conversions}</td>
      <td className="py-3 text-right text-neutral-900">{roas}</td>
      <td className="py-3"><TierBadge tier={tier} /></td>
    </tr>
  );
}

function CampaignTableRow({ name, status, platform, tier, spend, conversions, ctr, cpa, roas, score }) {
  const barColor = score >= 70 ? "bg-green-500" : score >= 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <tr className="hover:bg-neutral-50">
      <td className="p-4">
        <p className="font-medium text-neutral-900">{name}</p>
        <p className="text-xs text-neutral-500">{status}</p>
      </td>
      <td className="p-4 text-neutral-600">{platform}</td>
      <td className="p-4"><TierBadge tier={tier} /></td>
      <td className="p-4 text-right text-neutral-900">{spend}</td>
      <td className="p-4 text-right text-neutral-900">{conversions}</td>
      <td className="p-4 text-right text-neutral-900">{ctr}</td>
      <td className="p-4 text-right text-neutral-900">{cpa}</td>
      <td className="p-4 text-right text-neutral-900">{roas}</td>
      <td className="p-4 text-right">
        <div className="flex items-center justify-end gap-2">
          <div className="h-2 w-16 overflow-hidden rounded-full bg-neutral-200">
            <div className={`h-full rounded-full ${barColor}`} style={{ width: `${score}%` }} />
          </div>
          <span className="text-neutral-600">{score}</span>
        </div>
      </td>
    </tr>
  );
}

function TierBadge({ tier }) {
  const styles = {
    star: "bg-green-100 text-green-700",
    strong: "bg-blue-100 text-blue-700",
    average: "bg-neutral-100 text-neutral-700",
    underperformer: "bg-amber-100 text-amber-700",
    waster: "bg-red-100 text-red-700",
  };
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[tier]}`}>
      {tier.charAt(0).toUpperCase() + tier.slice(1)}
    </span>
  );
}

function TierFilterChip({ label, count, active, color }) {
  return (
    <button
      className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
        active
          ? "border-blue-600 bg-blue-50 text-blue-700"
          : "border-neutral-200 text-neutral-600 hover:bg-neutral-50"
      }`}
    >
      {label} ({count})
    </button>
  );
}

function FilterPill({ label, count, active }) {
  return (
    <button
      className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-blue-600 text-white"
          : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200"
      }`}
    >
      {label}
      {count != null && <span className="ml-1.5">{count}</span>}
    </button>
  );
}

function InsightCard({ category, sentiment, headline, detail, confidence, platform }) {
  const borderColor = {
    positive: "border-l-green-500",
    attention_needed: "border-l-amber-500",
    neutral: "border-l-blue-500",
  }[sentiment];

  const iconColor = {
    positive: "text-green-600",
    attention_needed: "text-amber-600",
    neutral: "text-blue-600",
  }[sentiment];

  const categoryLabel = category.charAt(0).toUpperCase() + category.slice(1);

  return (
    <Card className={`border-l-4 ${borderColor}`}>
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <span className={`mt-0.5 h-5 w-5 ${iconColor}`}>{/* Category icon */}</span>
            <div>
              <p className="font-medium text-neutral-900">{headline}</p>
              <p className="mt-1 text-sm text-neutral-600">{detail}</p>
              <div className="mt-2 flex items-center gap-3 text-xs text-neutral-500">
                <span>Confidence: {confidence}%</span>
                {platform && <span>Platform: {platform}</span>}
              </div>
            </div>
          </div>
          <span className="rounded-full bg-neutral-100 px-2.5 py-0.5 text-xs font-medium text-neutral-600">
            {categoryLabel}
          </span>
        </div>
      </div>
    </Card>
  );
}

function RecommendationCard({ title, description, priority, effort, expectedImpact, actionItems }) {
  const priorityStyles = {
    high: "bg-red-100 text-red-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-green-100 text-green-700",
  };
  const effortStyles = {
    low: "bg-green-100 text-green-700",
    medium: "bg-amber-100 text-amber-700",
    high: "bg-red-100 text-red-700",
  };

  return (
    <Card>
      <div className="p-4">
        <p className="font-medium text-neutral-900">{title}</p>

        <div className="mt-2 flex gap-2">
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${priorityStyles[priority]}`}>
            Priority: {priority.toUpperCase()}
          </span>
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${effortStyles[effort]}`}>
            Effort: {effort}
          </span>
        </div>

        <p className="mt-3 text-sm text-neutral-600">{description}</p>

        <p className="mt-2 text-sm font-medium text-green-700">
          Expected Impact: {expectedImpact}
        </p>

        <div className="mt-3">
          <p className="text-xs font-medium text-neutral-500">Action Items:</p>
          <ul className="mt-1 space-y-1">
            {actionItems.map((item, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-neutral-700">
                <input type="checkbox" className="rounded border-neutral-300" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  );
}

function SortableHeader({ label, active }) {
  return (
    <button className="inline-flex items-center gap-1 hover:text-neutral-900">
      {label}
      <span className={`h-3.5 w-3.5 ${active ? "text-blue-600" : "text-neutral-400"}`}>
        {/* ArrowUpDown icon */}
      </span>
    </button>
  );
}

function PlatformCheckbox({ name, icon, lastSync, records, checked, disabled, status }) {
  return (
    <label
      className={`flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-colors ${
        disabled
          ? "border-neutral-200 bg-neutral-50 opacity-60"
          : checked
            ? "border-blue-300 bg-blue-50"
            : "border-neutral-200 hover:bg-neutral-50"
      }`}
    >
      <input type="checkbox" defaultChecked={checked} disabled={disabled} className="mt-0.5 rounded border-neutral-300" />
      <div>
        <p className="text-sm font-medium text-neutral-900">{name}</p>
        {lastSync && (
          <p className="text-xs text-neutral-500">
            Synced {lastSync} — {records} records
          </p>
        )}
        {status && <p className="text-xs text-neutral-400">{status}</p>}
      </div>
    </label>
  );
}

function SectionToggle({ label, checked }) {
  return (
    <label className="flex items-center gap-3 text-sm text-neutral-700">
      <input type="checkbox" defaultChecked={checked} className="rounded border-neutral-300" />
      {label}
    </label>
  );
}

function SummaryRow({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-neutral-500">{label}</span>
      <span className="font-medium text-neutral-900">{value}</span>
    </div>
  );
}

function PipelineStep({ label, status }) {
  const styles = {
    done: { dot: "bg-green-500", text: "text-neutral-900", icon: "check" },
    running: { dot: "bg-blue-500 animate-pulse", text: "text-blue-700 font-medium", icon: "spinner" },
    pending: { dot: "bg-neutral-300", text: "text-neutral-400", icon: "circle" },
  };
  const s = styles[status];

  return (
    <div className="flex items-center gap-3">
      <div className={`h-2.5 w-2.5 rounded-full ${s.dot}`} />
      <span className={`text-xs ${s.text}`}>{label}</span>
    </div>
  );
}

function ClientCard({ name, platforms, spend, spendChange, conversions, conversionsChange, roas, roasChange, lastReport }) {
  return (
    <Card>
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">
              {name[0]}
            </div>
            <div>
              <p className="font-semibold text-neutral-900">{name}</p>
              <p className="text-xs text-neutral-500">{platforms.join(" + ")}</p>
            </div>
          </div>
          <button className="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600">
            {/* MoreHorizontal icon */}
          </button>
        </div>

        {/* Metrics */}
        <div className="mt-4 grid grid-cols-3 gap-4">
          <MiniMetric label="Spend" value={spend} change={spendChange} />
          <MiniMetric label="Conv." value={conversions} change={conversionsChange} />
          <MiniMetric label="ROAS" value={roas} change={roasChange} />
        </div>

        {/* Footer */}
        <div className="mt-4 flex items-center justify-between border-t border-neutral-100 pt-3">
          <span className="text-xs text-neutral-500">Last report: {lastReport}</span>
          <div className="flex gap-2">
            <button className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700">
              Report
            </button>
            <button className="rounded-lg border border-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-600 hover:bg-neutral-50">
              Details
            </button>
          </div>
        </div>
      </div>
    </Card>
  );
}

function ClientCardEmpty() {
  return (
    <button className="flex items-center justify-center rounded-xl border-2 border-dashed border-neutral-300 p-8 text-sm text-neutral-500 hover:border-blue-400 hover:text-blue-600">
      + Add New Client
    </button>
  );
}

function MiniMetric({ label, value, change }) {
  const changeColor = change >= 0 ? "text-green-600" : "text-red-600";
  const arrow = change >= 0 ? "+" : "";
  return (
    <div>
      <p className="text-xs text-neutral-500">{label}</p>
      <p className="text-sm font-semibold text-neutral-900">{value}</p>
      <p className={`text-xs font-medium ${changeColor}`}>
        {arrow}{change}%
      </p>
    </div>
  );
}

function ReportListItem({ title, date, status }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-neutral-200 p-3 hover:bg-neutral-50">
      <div className="flex items-center gap-3">
        <span className="text-neutral-400">{/* FileText icon */}</span>
        <div>
          <p className="text-sm font-medium text-neutral-900">{title}</p>
          <p className="text-xs text-neutral-500">{date}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
          {status}
        </span>
        <button className="text-sm text-blue-600 hover:text-blue-700">View</button>
      </div>
    </div>
  );
}
