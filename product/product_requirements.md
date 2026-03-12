# InsightFlow — Product Requirements Document (PRD)

## 1. Product Vision

InsightFlow is an AI-powered client report generator for marketing agencies. It connects to marketing platforms (Meta Ads, Google Ads, Shopify, GA4), ingests performance data, and automatically generates client-ready reports enriched with AI-driven insights and recommendations.

**Mission:** Eliminate the 5–10 hours per week agencies spend manually building client reports, replacing them with intelligent, automated, always-accurate deliverables.

## 2. Target Users

| Persona | Description |
|---------|-------------|
| Agency Owner | Manages 10–200 clients, needs scalable reporting |
| Account Manager | Prepares weekly/monthly reports per client |
| Marketing Analyst | Digs into data, wants AI-assisted trend detection |
| Client Stakeholder | Receives polished, branded reports (read-only) |

## 3. Core Problem Statement

Marketing agencies waste significant billable hours on:
- Logging into multiple ad platforms per client
- Exporting CSVs and copying data into slides/docs
- Writing narrative summaries of performance
- Generating recommendations manually
- Formatting and branding reports for each client

## 4. Functional Requirements

### 4.1 Platform Integrations
- **Meta Ads (Facebook/Instagram):** Campaign, ad set, and ad-level metrics
- **Google Ads:** Search, Display, Shopping, Performance Max campaigns
- **Google Analytics 4:** Traffic, conversions, audience data
- **Shopify:** Revenue, orders, AOV, product performance
- Future: TikTok Ads, LinkedIn Ads, Pinterest Ads, HubSpot

### 4.2 Data Ingestion & Processing
- OAuth 2.0 connections to each platform
- Scheduled data syncs (configurable: hourly, daily, weekly)
- Data normalization across platforms into a unified schema
- Historical data backfill on initial connection
- Data validation and anomaly flagging

### 4.3 AI Report Generation
- Automated narrative generation from structured data
- Trend detection and period-over-period analysis
- Anomaly detection with explanations
- Actionable recommendations based on performance patterns
- Customizable report templates (executive summary, deep dive, etc.)
- Multi-language support for report narratives

### 4.4 Report Management
- Template builder with drag-and-drop sections
- White-label branding (agency logo, colors, fonts)
- Scheduled report generation and delivery
- PDF and interactive web report formats
- Report approval workflow before client delivery
- Version history and audit trail

### 4.5 Client Portal
- Read-only branded portal for clients
- Real-time dashboard with key metrics
- Report archive and download
- Commenting and feedback on reports

### 4.6 Team & Workspace Management
- Multi-tenant architecture (one workspace per agency)
- Role-based access control (Owner, Admin, Manager, Viewer)
- Client grouping and tagging
- Activity logging and audit trail

## 5. Non-Functional Requirements

### 5.1 Performance
- API response time: < 200ms (p95) for read operations
- Report generation: < 60 seconds for standard reports
- Data sync latency: < 5 minutes from platform to dashboard
- Support 100 concurrent report generations per tenant

### 5.2 Security
- SOC 2 Type II compliance pathway
- End-to-end encryption (TLS 1.3 in transit, AES-256 at rest)
- OAuth token encryption with per-tenant encryption keys
- GDPR and CCPA compliance
- Regular penetration testing

### 5.3 Scalability
- Horizontal scaling to 100K+ tenants
- Multi-region deployment capability
- Event-driven architecture for async processing

### 5.4 Reliability
- 99.9% uptime SLA
- Automated failover and disaster recovery
- Data backup with point-in-time recovery

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| Time saved per report | > 80% reduction |
| Report accuracy | > 95% data accuracy |
| User activation (first report generated) | < 30 minutes from signup |
| Monthly churn | < 5% |
| NPS | > 50 |

## 7. Constraints & Assumptions

- Initial launch targets English-speaking markets (US, UK, AU, CA)
- API rate limits from third-party platforms must be respected
- AI model costs must stay below 15% of subscription revenue
- MVP targets agencies with 5–50 clients
