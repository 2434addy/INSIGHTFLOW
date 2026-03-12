# InsightFlow — Infrastructure Overview

## 1. Cloud Architecture (AWS)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AWS Account                                  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  CloudFlare (External)                                         │  │
│  │  • DNS management                                              │  │
│  │  • DDoS protection                                             │  │
│  │  • WAF rules                                                   │  │
│  │  • CDN for static assets                                       │  │
│  └───────────────────────────┬────────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────┴────────────────────────────────────┐  │
│  │  VPC (10.0.0.0/16)                                             │  │
│  │                                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────┐   │  │
│  │  │  Public Subnet (10.0.1.0/24, 10.0.2.0/24)              │   │  │
│  │  │  • ALB (Application Load Balancer)                       │   │  │
│  │  │  • NAT Gateway                                           │   │  │
│  │  └────────────────────────┬────────────────────────────────┘   │  │
│  │                           │                                    │  │
│  │  ┌────────────────────────┴────────────────────────────────┐   │  │
│  │  │  Private Subnet (10.0.10.0/24, 10.0.11.0/24)           │   │  │
│  │  │                                                          │   │  │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                │   │  │
│  │  │  │ ECS     │  │ ECS     │  │ ECS     │                │   │  │
│  │  │  │ API     │  │ Worker  │  │ Frontend│                │   │  │
│  │  │  │ Service │  │ Service │  │ (or     │                │   │  │
│  │  │  │ (Fargate│  │ (Fargate│  │ Vercel) │                │   │  │
│  │  │  └─────────┘  └─────────┘  └─────────┘                │   │  │
│  │  └────────────────────────┬────────────────────────────────┘   │  │
│  │                           │                                    │  │
│  │  ┌────────────────────────┴────────────────────────────────┐   │  │
│  │  │  Data Subnet (10.0.20.0/24, 10.0.21.0/24)              │   │  │
│  │  │                                                          │   │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │  │
│  │  │  │ RDS          │  │ ElastiCache  │  │ S3           │  │   │  │
│  │  │  │ PostgreSQL   │  │ Redis        │  │ (reports,    │  │   │  │
│  │  │  │ Multi-AZ     │  │ Cluster      │  │  assets)     │  │   │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │  │
│  │  └─────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Supporting Services                                            │ │
│  │  • Secrets Manager (credentials, API keys)                      │ │
│  │  • KMS (encryption keys)                                        │ │
│  │  • SES (transactional email)                                    │ │
│  │  • CloudWatch (logs, metrics, alarms)                           │ │
│  │  • ECR (container registry)                                     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

## 2. Environment Strategy

| Environment | Infrastructure | Purpose |
|------------|---------------|---------|
| Local (dev) | Docker Compose | Individual developer setup |
| Staging | AWS (scaled down) | Integration testing, QA |
| Production | AWS (full scale) | Live users |

### Local Development Stack (Docker Compose)
```yaml
services:
  api:        # FastAPI application
  worker:     # Celery worker
  frontend:   # Next.js dev server
  postgres:   # PostgreSQL 16
  redis:      # Redis 7
  mailhog:    # Email testing
```

## 3. Deployment Strategy

### Blue/Green Deployment
1. New version deployed to "green" target group
2. Health checks pass on green
3. ALB switches traffic to green
4. Old "blue" kept running for 30 minutes (rollback window)
5. Blue terminated after successful verification

### Rollback Procedure
- Automated: If health checks fail post-deploy, auto-rollback to blue
- Manual: `terraform apply` with previous image tag, or ALB target group switch

## 4. Scaling Policies

| Service | Min | Max | Scale Trigger |
|---------|-----|-----|--------------|
| API (Fargate) | 2 | 20 | CPU > 60% or request count > 1000/min |
| Worker (Fargate) | 1 | 10 | Queue depth > 50 |
| RDS | 1 writer + 1 reader | 1 writer + 5 readers | CPU > 70% |
| Redis | 1 node | 6 nodes (cluster) | Memory > 75% |

## 5. Monitoring & Alerting

### Dashboards
- **System health:** CPU, memory, disk, network across all services
- **Application:** Request rate, latency (p50/p95/p99), error rate
- **Business:** Report generations/day, active users, data syncs
- **Cost:** AWS spend by service, AI API costs

### Alert Severity
| Severity | Response Time | Examples |
|----------|--------------|---------|
| P1 - Critical | 15 min | Service down, data breach, 5xx > 10% |
| P2 - High | 1 hour | Degraded performance, sync failures > 50% |
| P3 - Medium | 4 hours | Elevated error rates, disk > 80% |
| P4 - Low | Next business day | Non-critical warnings, cost anomalies |

## 6. Backup & Recovery

| Data | Backup Frequency | Retention | RTO | RPO |
|------|-----------------|-----------|-----|-----|
| PostgreSQL | Continuous (WAL) + daily snapshot | 30 days | 1 hour | 5 minutes |
| Redis | Hourly snapshot | 7 days | 15 min | 1 hour |
| S3 (reports) | Versioning enabled | 90 days | Immediate | 0 (versioned) |
| Secrets | Versioned in Secrets Manager | All versions | Immediate | 0 |

## 7. Cost Estimate (MVP)

| Service | Monthly Cost (Est.) |
|---------|-------------------|
| ECS Fargate (API + Workers) | $150–300 |
| RDS PostgreSQL (db.t3.medium) | $70 |
| ElastiCache Redis (cache.t3.micro) | $25 |
| S3 + CloudFront | $20 |
| Secrets Manager + KMS | $10 |
| CloudWatch | $30 |
| SES (email) | $10 |
| Claude API (AI reports) | $50–200 |
| CloudFlare (Pro) | $20 |
| Domain + SSL | $15 |
| **Total** | **$400–700/mo** |
