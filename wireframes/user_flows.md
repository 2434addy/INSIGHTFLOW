# InsightFlow — User Flows

## 1. Signup & Onboarding Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Landing     │────▶│  Sign Up      │────▶│  Email Verify   │
│  Page        │     │  (Email/Google)│     │  (if email)     │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Create          │
                                          │  Workspace       │
                                          │  (Agency Name)   │
                                          └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Connect First   │
                                          │  Platform        │
                                          │  (Meta or Google)│
                                          └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Select Ad       │
                                          │  Accounts /      │
                                          │  Clients         │
                                          └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Data Sync       │
                                          │  (background)    │
                                          └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Generate First  │
                                          │  Report (guided) │
                                          └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Dashboard       │
                                          │  (onboarding     │
                                          │   complete)      │
                                          └─────────────────┘
```

### Key Design Decisions
- **Time to first report: < 30 minutes** — the entire flow must be completable within this window
- OAuth flow opens in a popup to avoid losing onboarding context
- Data sync runs in background — user can proceed while historical data loads
- First report uses auto-detected date range (last 30 days)

## 2. Platform Connection Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Settings /   │────▶│  Select       │────▶│  OAuth        │
│  Integrations │     │  Platform     │     │  Consent      │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                          ┌───────┴───────┐
                                          │               │
                                          ▼               ▼
                                   ┌────────────┐  ┌────────────┐
                                   │  Success    │  │  Failure   │
                                   │  ─ Select   │  │  ─ Retry   │
                                   │    accounts │  │  ─ Help    │
                                   └─────┬──────┘  └────────────┘
                                         │
                                         ▼
                                   ┌────────────┐
                                   │  Map to     │
                                   │  Clients    │
                                   └─────┬──────┘
                                         │
                                         ▼
                                   ┌────────────┐
                                   │  Configure  │
                                   │  Sync       │
                                   │  Schedule   │
                                   └─────┬──────┘
                                         │
                                         ▼
                                   ┌────────────┐
                                   │  Initial    │
                                   │  Data Sync  │
                                   └────────────┘
```

## 3. Report Generation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Select       │────▶│  Choose       │────▶│  Configure   │
│  Client       │     │  Date Range   │     │  Report      │
└──────────────┘     └──────────────┘     │  Options     │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  AI           │
                                          │  Processing   │
                                          │  (30-60 sec)  │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  Review       │
                                          │  Report       │
                                          │  (preview)    │
                                          └──────┬───────┘
                                                 │
                                          ┌──────┴──────┐
                                          │             │
                                          ▼             ▼
                                   ┌──────────┐  ┌──────────┐
                                   │  Edit /   │  │  Export   │
                                   │  Refine   │  │  PDF      │
                                   └──────────┘  └──────────┘
```

### Report Configuration Options (MVP)
- Date range: Last 7 days, Last 30 days, Last quarter, Custom
- Comparison period: Previous period, Same period last year
- Platforms to include: All connected, or select specific
- Report sections: Executive summary, Channel breakdown, Insights, Recommendations
- Tone: Executive (concise), Detailed (comprehensive)

## 4. Dashboard Navigation Flow

```
┌─────────────────────────────────────────────────────┐
│  Top Nav: Logo │ Search │ Notifications │ Profile    │
├─────────┬───────────────────────────────────────────┤
│         │                                            │
│  Side   │   Main Content Area                       │
│  Nav    │                                            │
│         │   ┌─────────────────────────────────┐     │
│  □ Dash │   │  KPI Cards (Spend, Conv, ROAS)  │     │
│  □ Clients   │                                 │     │
│  □ Reports   └─────────────────────────────────┘     │
│  □ Connect│                                          │
│  □ Settings   ┌─────────────────────────────────┐   │
│  □ Team  │   │  Charts (Trend lines)            │   │
│         │   └─────────────────────────────────┘     │
│         │                                            │
│         │   ┌─────────────────────────────────┐     │
│         │   │  Client List / Recent Reports    │     │
│         │   └─────────────────────────────────┘     │
│         │                                            │
└─────────┴───────────────────────────────────────────┘
```

## 5. Error & Edge Case Flows

### OAuth Token Expiry
1. Background sync detects expired token
2. System sends notification to user: "Your Meta Ads connection needs re-authorization"
3. User clicks notification → taken to re-auth flow
4. On success → automatic re-sync of missed data

### Report Generation Failure
1. AI service timeout or error during generation
2. User sees: "Report generation encountered an issue. Retrying..."
3. Auto-retry once with exponential backoff
4. If retry fails: "We couldn't generate your report. Please try again or contact support."
5. Error logged for engineering team

### Empty Data State
1. Client has no data for selected period
2. Show: "No data available for [date range]. Try a different period or check your connection."
3. Suggest alternative date ranges with available data

## 6. Key Interaction Patterns

| Pattern | Implementation |
|---------|---------------|
| Loading states | Skeleton screens for dashboards, progress bar for report generation |
| Empty states | Helpful illustrations with clear CTAs |
| Error states | Friendly language, retry options, help links |
| Success states | Subtle toast notifications, confetti on first report |
| Confirmation dialogs | Only for destructive actions (delete client, disconnect platform) |
