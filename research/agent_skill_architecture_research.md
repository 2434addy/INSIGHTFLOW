# InsightFlow — Agent + Skill Architecture Research

## Research Date: March 2026

---

## 1. Platform Analysis: How Competitors Structure AI/Analytics Systems

### AgencyAnalytics
- Serves 6,500+ agencies with 80+ integrations
- Recently added AI insights: users can ask natural language questions about data and get summarized answers
- AI surfaces hidden trends and opportunities automatically
- Architecture is **integration-first**: broad connector library is the primary moat
- Reports remain data-heavy dashboards — no narrative generation
- **Key takeaway for InsightFlow:** Their AI is bolt-on Q&A, not embedded in report generation. InsightFlow's AI-first approach (narrative generation, not just Q&A) is a genuine differentiator

### DashThis
- Simple, dashboard-focused reporting tool (34+ integrations)
- No AI capabilities whatsoever
- Per-dashboard pricing model (retiring unlimited data sources March 2026)
- Strength is simplicity and speed of setup
- **Key takeaway for InsightFlow:** DashThis proves that ease of use wins adoption. InsightFlow's onboarding (first report in <30 min) must match this simplicity while adding AI value

### Whatagraph
- Visually focused cross-channel reporting (45+ integrations)
- AI features added across all plans: summarizes report data into plain English
- Strong data blending capabilities
- Data warehouse exports to BigQuery and Looker Studio
- **Key takeaway for InsightFlow:** Whatagraph's AI "summarization" is shallow — it describes data but doesn't analyze it. InsightFlow should focus on *why* things happened, not just *what* happened

### Supermetrics
- Data pipeline tool connecting 138+ platforms to analytics destinations
- In early 2026, introduced Supermetrics AI: embedded AI Agents that automate parts of reporting and analysis
- Architecture: Extract from platforms -> Load into BigQuery/Sheets/Looker Studio -> User builds reports
- Not a reporting tool per se — a data connector with AI layered on top
- **Key takeaway for InsightFlow:** Supermetrics validates that the market is moving toward AI agents in analytics. Their approach (agents within a data pipeline) aligns with InsightFlow's agent architecture

### Looker Studio (Google)
- Free BI/dashboard tool with strong Google ecosystem integration
- No AI narrative generation
- Requires manual setup and data modeling
- Often used as the visualization layer downstream from Supermetrics
- **Key takeaway for InsightFlow:** Looker Studio is the "default" for agencies that want free dashboards. InsightFlow competes by eliminating the manual analysis and writing step entirely

### Competitive Gap Summary
No competitor fully combines: automated data ingestion + AI-powered analysis + narrative report generation + actionable recommendations in a single integrated platform. InsightFlow's target position at the intersection of high AI capability and high integration breadth remains differentiated.

---

## 2. AI Agent Architecture Best Practices

### 2.1 Multi-Agent Orchestration Patterns

Research identifies five core patterns for multi-agent systems:

**Sequential (Pipeline)**
- Tasks flow through agents in a defined order
- Each agent processes the output from the previous agent
- Best for: well-defined, linear workflows like InsightFlow's data -> analysis -> insights -> report pipeline
- InsightFlow alignment: This is the primary pattern for report generation

**Parallel (Fan-out/Fan-in)**
- Independent tasks run simultaneously across multiple agents
- Results are combined into a unified output
- Best for: analyzing data from multiple platforms simultaneously, generating multiple report sections in parallel
- InsightFlow alignment: Use for multi-platform data ingestion and multi-section report generation

**Routing (Dispatcher)**
- A central router dispatches tasks based on classification or context
- Each specialist handles its domain efficiently
- Best for: directing different types of analysis requests to specialized agents
- InsightFlow alignment: Use an orchestrator to route to the right analysis skill based on data type

**DAG-based (Directed Acyclic Graph)**
- Complex workflows with conditional branching and dependency management
- Enables workflows where some steps depend on others while some can run in parallel
- Best for: the overall report generation pipeline with its mix of sequential and parallel steps
- InsightFlow alignment: The report pipeline is fundamentally a DAG

**Hierarchical (Supervisor)**
- A supervisor agent delegates to and monitors sub-agents
- Provides oversight, error recovery, and quality control
- Best for: production systems needing reliability and human-in-the-loop escalation
- InsightFlow alignment: A Report Orchestrator agent supervising specialist agents

### 2.2 Framework Comparison and Recommendation

**CrewAI**
- Role-driven multi-agent orchestration
- Beginner-friendly, fast to prototype
- Multi-agent workflows start in minutes with role-based mental model
- Limitation: Less fine-grained control over execution flow

**LangGraph**
- Graph-based workflow design treating agent interactions as nodes in a directed graph
- Exceptional flexibility for complex decision-making pipelines
- Manages state persistence and uses reducer logic to merge concurrent updates
- Supports cycles (important for iterative refinement loops)
- Durable execution: agents persist through failures and resume from exactly where they left off
- Best for: production systems needing precise control over execution order, branching, and error recovery

**AutoGen**
- Conversational agent architecture emphasizing natural language interactions
- Best for: human-in-the-loop workflows and flexible collaboration

**Recommendation for InsightFlow:**
Use **LangGraph** as the primary orchestration framework for the following reasons:
1. InsightFlow's report pipeline is fundamentally a DAG with conditional branches (e.g., skip channel breakdown if only one platform)
2. State management is critical — report generation involves multiple steps with shared state
3. Durable execution prevents data loss on failures (important for long-running report generation)
4. Production-grade reliability with built-in error recovery
5. Industry convergence: even CrewAI and AutoGen are adopting graph-based models

Consider **CrewAI** patterns for the *conceptual model* (role-based agent definitions) while implementing on LangGraph's runtime.

### 2.3 Bounded Autonomy Architecture
Leading organizations implement "bounded autonomy" with:
- Clear operational limits per agent
- Escalation paths to humans for high-stakes decisions
- Comprehensive audit trails of agent actions
- **InsightFlow application:** Agents should never fabricate data, always validate outputs against source, and flag low-confidence results for human review

---

## 3. Data Pipeline Patterns

### 3.1 ETL vs ELT for Marketing Data

**ELT is the recommended pattern for InsightFlow:**

| Factor | ETL | ELT | InsightFlow Choice |
|--------|-----|-----|-------------------|
| Transform location | Before loading | After loading in warehouse | ELT — transform in PostgreSQL |
| Schema flexibility | Rigid upfront | Flexible, evolving | ELT — marketing APIs change frequently |
| Raw data preservation | Transformed data only | Raw data preserved | ELT — keep raw for reprocessing |
| Complexity | Higher pipeline complexity | Simpler extraction | ELT — fewer moving parts for MVP |

**Recommended pipeline:**
```
Extract (platform APIs) -> Load (raw data into PostgreSQL staging tables) -> Transform (normalize into unified schema via SQL/Python)
```

This aligns with InsightFlow's existing `data_sync` module design but adds a staging layer:
```
Platform API -> Raw Staging Table -> Normalizer -> Unified Metrics Table
```

Benefits of adding a staging layer:
- Re-run normalization without re-fetching from APIs (avoids rate limits)
- Debug data quality issues against raw data
- Handle API format changes by updating only the transform step

### 3.2 Cross-Platform Data Normalization

Research confirms InsightFlow's existing unified metric mapping approach is industry-standard. Additional recommendations:

**Semantic Layer Architecture:**
The semantic layer is emerging as the critical infrastructure for AI-powered analytics. It maps business terms like "ROAS" or "conversion rate" to specific data fields, reducing ambiguity and ensuring AI retrieves the right data.

For InsightFlow, implement a semantic layer as:
```python
# Semantic metric definitions
METRIC_DEFINITIONS = {
    "roas": {
        "name": "Return on Ad Spend",
        "formula": "revenue / spend",
        "unit": "ratio",
        "direction": "higher_is_better",
        "benchmark_ranges": {
            "poor": (0, 1.0),
            "below_average": (1.0, 2.0),
            "average": (2.0, 4.0),
            "good": (4.0, 8.0),
            "excellent": (8.0, float("inf"))
        },
        "platform_mappings": {
            "meta_ads": "purchase_roas",
            "google_ads": "conversions_value / cost",
        }
    }
}
```

This semantic layer serves dual purposes:
1. **Data normalization**: ensures consistent metric computation across platforms
2. **AI grounding**: gives the AI agent precise definitions to prevent hallucination

### 3.3 Real-time vs Batch Processing

| Processing Mode | Use Case | InsightFlow Application |
|----------------|----------|------------------------|
| Batch (daily sync) | Standard reporting | MVP — daily automated sync per connection |
| Near-real-time (hourly) | Dashboard freshness | Phase 2 — configurable sync frequency |
| Event-driven | Anomaly alerting | Phase 3 — triggered when metrics deviate beyond threshold |

**Recommendation:** Start with batch (daily), add configurable frequency in Phase 2, and event-driven anomaly alerts in Phase 3. This matches InsightFlow's existing phased approach.

### 3.4 Anomaly Detection Approaches

**Recommended layered approach for InsightFlow:**

**Layer 1: Statistical (MVP)**
- Z-score based detection (already in InsightFlow's design at threshold 2.0)
- Day-of-week seasonality adjustment (compare Monday to other Mondays, not to Sunday)
- Period-over-period deviation detection

**Layer 2: Contextual (Phase 2)**
- Holiday/event calendar integration (Valentine's Day spend spikes are expected, not anomalous)
- Campaign lifecycle awareness (new campaign launches naturally show volatile metrics)
- Budget change detection (spend anomalies after budget modifications are expected)

**Layer 3: Cross-metric Correlation (Phase 3)**
- Detect when metric relationships break (CTR drops while impressions spike = likely audience expansion)
- Cross-platform correlation (Meta CPA spike + Google CVR drop = potential market-level shift)
- Use isolation forests or autoencoders for multivariate anomaly detection

**Key challenge:** Distinguishing genuine anomalies from predictable variations (seasonal trends, promotions). InsightFlow should maintain an "expected events" calendar per client to reduce false positives.

---

## 4. Report Generation Best Practices

### 4.1 Anti-Hallucination Architecture

This is the single most critical quality concern for InsightFlow. Research identifies a multi-layered defense:

**Layer 1: Input Grounding**
- All metrics provided as structured JSON, never as free text
- Semantic layer defines exactly what each metric means
- System prompt explicitly states: "Only reference data provided in the context"
- Include the raw numbers in the prompt so the AI has no reason to guess

**Layer 2: Structured Output Enforcement**
- Require JSON output with explicit data references
- Each insight must include a `supporting_data` field pointing to source metrics
- Use text-to-SQL patterns where possible (AI generates queries against known data, not numbers from memory)

**Layer 3: Post-Generation Validation**
- Parse every number in the AI output
- Match each number against the source data within tolerance (1%)
- Verify percentage calculations independently
- Check that trend descriptions match statistical analysis output
- Flag any claim about data not present in the input context

**Layer 4: Confidence and Fallback**
- AI self-rates confidence per output section
- Low-confidence outputs (<0.7) trigger template-based fallback
- Template fallback produces guaranteed-accurate (if less eloquent) narratives
- Human review queue for flagged outputs

**Layer 5: Consistency Checking**
- Cross-reference insights against each other (no contradictions)
- Verify executive summary aligns with detailed insights
- Check recommendations are consistent with identified trends

InsightFlow's existing design already includes layers 1-4. **Add Layer 5 (cross-section consistency checking) as a dedicated validation agent.**

### 4.2 Template-Based vs Free-Form Generation

Research shows the best approach is a **hybrid: template structure with AI-generated content per section.**

```
Template defines:        AI generates:
- Section order          - Narrative text within each section
- Required data points   - Insight headlines and explanations
- Chart placements       - Recommendation specifics
- Tone and length        - Contextual connections between data points
```

This is exactly InsightFlow's current approach (YAML template + AI generation per section). This is validated as industry best practice.

**Enhancement: Section-level prompt isolation**
Generate each section with its own prompt call rather than one massive prompt:
- Reduces context window pollution
- Enables parallel generation of independent sections
- Allows section-specific model selection (Sonnet for standard, Opus for deep analysis)
- Makes validation easier (check each section independently)

### 4.3 Multi-Section Report Orchestration

**Recommended orchestration pattern:**

```
                    ┌──────────────────┐
                    │ Report           │
                    │ Orchestrator     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌──────────┐
     │ Data Prep  │  │ Context    │  │ Template │
     │ (parallel) │  │ Assembly   │  │ Loader   │
     └─────┬──────┘  └─────┬──────┘  └────┬─────┘
           │               │              │
           └───────────────┼──────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
     ┌──────────────┐ ┌─────────┐ ┌────────────────┐
     │ Exec Summary │ │Insights │ │Recommendations │
     │ (AI: Sonnet) │ │(AI)     │ │(AI)            │
     └──────┬───────┘ └────┬────┘ └───────┬────────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ Consistency    │
                  │ Validator      │
                  └────────┬───────┘
                           │
                  ┌────────┴────────┐
                  │                 │
                  ▼                 ▼
           ┌──────────┐     ┌──────────┐
           │ Web JSON │     │ PDF Gen  │
           └──────────┘     └──────────┘
```

Key principles:
1. Data prep and context assembly run first (dependencies for AI generation)
2. AI sections can run in parallel (executive summary, insights, recommendations are independent given the same data context)
3. Consistency validation runs after all AI sections complete
4. Output rendering (web + PDF) runs in parallel after validation

---

## 5. Skill/Capability Architecture

### 5.1 Skill Decomposition Framework

Research on agentic analytics platforms reveals a three-tier decomposition:

**Tier 1: Atomic Skills (Reusable Primitives)**
These are the smallest units of capability that can be composed into larger workflows:

| Skill | Input | Output | Reusability |
|-------|-------|--------|-------------|
| `compute_metric` | Raw data + metric definition | Computed value | Used by every analysis |
| `period_comparison` | Two time ranges of data | Absolute + percentage changes | Trend analysis, reports |
| `detect_anomalies` | Time series data + threshold | Anomaly list with severity | Analysis, alerting |
| `identify_trends` | Time series data | Trend direction + strength | Analysis, reports |
| `rank_entities` | Entity list + ranking metric | Sorted entities with scores | Top/bottom performers |
| `normalize_data` | Raw platform data + mapping | Unified schema data | Every data sync |
| `generate_narrative` | Structured data + prompt template | AI-generated text | Every report section |
| `validate_output` | AI output + source data | Validated output + confidence | Every AI generation |

**Tier 2: Composite Skills (Agent Capabilities)**
These combine multiple atomic skills into agent-level capabilities:

| Composite Skill | Composed From | Agent |
|----------------|---------------|-------|
| `analyze_performance` | compute_metric + period_comparison + rank_entities | Data Analysis Agent |
| `detect_and_explain_anomalies` | detect_anomalies + generate_narrative | Data Analysis + Insight Agent |
| `generate_insights` | analyze_performance + generate_narrative + validate_output | Insight Generation Agent |
| `write_report_section` | generate_narrative + validate_output | Report Writer Agent |
| `sync_platform_data` | API fetch + normalize_data + validate | Data Sync Module |

**Tier 3: Workflows (End-to-End Pipelines)**
These orchestrate multiple agents and composite skills:

| Workflow | Steps | Trigger |
|----------|-------|---------|
| `generate_monthly_report` | sync_data -> analyze_performance -> generate_insights -> write_report -> render_output | User request or schedule |
| `daily_anomaly_scan` | sync_data -> detect_anomalies -> generate_alerts | Daily schedule |
| `on_demand_analysis` | fetch_data -> analyze_performance -> generate_insights | User request |

### 5.2 Skill Composition Patterns

**Registry Pattern:**
```python
class SkillRegistry:
    """Central registry for all available skills."""
    _skills: dict[str, Skill] = {}

    @classmethod
    def register(cls, name: str, skill: Skill):
        cls._skills[name] = skill

    @classmethod
    def get(cls, name: str) -> Skill:
        return cls._skills[name]

    @classmethod
    def compose(cls, name: str, steps: list[str]) -> CompositeSkill:
        """Create a new composite skill from existing skills."""
        skills = [cls.get(s) for s in steps]
        return CompositeSkill(name=name, steps=skills)
```

**Skill Interface:**
```python
from abc import ABC, abstractmethod
from pydantic import BaseModel

class SkillInput(BaseModel):
    """Base class for skill inputs — validated via Pydantic."""
    pass

class SkillOutput(BaseModel):
    """Base class for skill outputs."""
    success: bool
    confidence: float = 1.0
    metadata: dict = {}

class Skill(ABC):
    """Abstract base class for all InsightFlow skills."""

    @abstractmethod
    async def execute(self, input: SkillInput) -> SkillOutput:
        """Execute the skill with validated input."""
        pass

    @abstractmethod
    def validate_input(self, input: SkillInput) -> bool:
        """Validate that the input is sufficient for execution."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def dependencies(self) -> list[str]:
        """Other skills this skill depends on."""
        return []
```

### 5.3 Marketing KPI Computation Best Practices

**Semantic Metric Layer (recommended addition to InsightFlow):**

```python
from enum import Enum
from dataclasses import dataclass

class MetricDirection(Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"

class MetricCategory(Enum):
    SPEND = "spend"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    REVENUE = "revenue"
    EFFICIENCY = "efficiency"

@dataclass
class MetricDefinition:
    id: str
    name: str
    description: str
    formula: str | None  # None for raw metrics
    unit: str            # "currency", "percentage", "ratio", "count"
    direction: MetricDirection
    category: MetricCategory
    format_pattern: str  # e.g., "${:,.2f}" for currency
    benchmark_thresholds: dict[str, tuple[float, float]]
    platform_field_mappings: dict[str, str]
    related_metrics: list[str]

# Example definitions
METRIC_CATALOG = {
    "spend": MetricDefinition(
        id="spend",
        name="Ad Spend",
        description="Total amount spent on advertising",
        formula=None,  # Raw metric
        unit="currency",
        direction=MetricDirection.NEUTRAL,
        category=MetricCategory.SPEND,
        format_pattern="${:,.2f}",
        benchmark_thresholds={},
        platform_field_mappings={
            "meta_ads": "spend",
            "google_ads": "metrics.cost_micros / 1_000_000",
        },
        related_metrics=["roas", "cpa", "cpc"],
    ),
    "roas": MetricDefinition(
        id="roas",
        name="Return on Ad Spend",
        description="Revenue generated per dollar of ad spend",
        formula="revenue / spend",
        unit="ratio",
        direction=MetricDirection.HIGHER_IS_BETTER,
        category=MetricCategory.EFFICIENCY,
        format_pattern="{:.1f}x",
        benchmark_thresholds={
            "poor": (0, 1.0),
            "below_average": (1.0, 2.0),
            "average": (2.0, 4.0),
            "good": (4.0, 8.0),
            "excellent": (8.0, float("inf")),
        },
        platform_field_mappings={
            "meta_ads": "purchase_roas",
            "google_ads": "metrics.conversions_value / metrics.cost_micros * 1_000_000",
        },
        related_metrics=["spend", "revenue", "conversions"],
    ),
    "cpa": MetricDefinition(
        id="cpa",
        name="Cost per Acquisition",
        description="Average cost to acquire one conversion",
        formula="spend / conversions",
        unit="currency",
        direction=MetricDirection.LOWER_IS_BETTER,
        category=MetricCategory.EFFICIENCY,
        format_pattern="${:,.2f}",
        benchmark_thresholds={
            "excellent": (0, 10),
            "good": (10, 25),
            "average": (25, 50),
            "below_average": (50, 100),
            "poor": (100, float("inf")),
        },
        platform_field_mappings={
            "meta_ads": "cost_per_action_type[purchase]",
            "google_ads": "metrics.cost_per_conversion",
        },
        related_metrics=["spend", "conversions", "roas"],
    ),
}
```

This catalog serves as the single source of truth for:
1. How metrics are computed (formula)
2. How to interpret them (direction, benchmarks)
3. How to format them for display (format_pattern)
4. How they map from each platform (platform_field_mappings)
5. What related context to include in AI prompts (related_metrics)

---

## 6. Recommended InsightFlow Agent + Skill Architecture

### 6.1 Revised Agent Architecture

Based on research, here is the recommended evolution of InsightFlow's agent architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER (LangGraph)               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Report Orchestrator Agent                     │   │
│  │  (DAG-based workflow manager, state machine)              │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│           ┌───────────────┼───────────────┐                     │
│           │               │               │                     │
│           ▼               ▼               ▼                     │
│  ┌────────────────┐ ┌──────────────┐ ┌────────────────────┐    │
│  │ Data Analysis  │ │ Insight      │ │ Report Writer      │    │
│  │ Agent          │ │ Generation   │ │ Agent              │    │
│  │                │ │ Agent        │ │                    │    │
│  │ Skills:        │ │ Skills:      │ │ Skills:            │    │
│  │ • compute_kpi  │ │ • interpret  │ │ • write_narrative  │    │
│  │ • compare_     │ │ • explain_   │ │ • format_section   │    │
│  │   periods      │ │   anomaly    │ │ • render_pdf       │    │
│  │ • detect_trend │ │ • recommend  │ │ • assemble_report  │    │
│  │ • detect_      │ │ • correlate_ │ │                    │    │
│  │   anomaly      │ │   cross_plat │ │                    │    │
│  │ • rank_entities│ │              │ │                    │    │
│  └────────┬───────┘ └──────┬───────┘ └─────────┬──────────┘    │
│           │                │                    │               │
│           └────────────────┼────────────────────┘               │
│                            │                                     │
│  ┌─────────────────────────┴────────────────────────────────┐   │
│  │              Validation Agent                              │   │
│  │  (cross-section consistency, anti-hallucination checks)   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                    SEMANTIC LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Metric Catalog | Business Rules | Platform Mappings      │   │
│  │  Benchmark Thresholds | Formatting Rules | KPI Formulas   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                    DATA LAYER                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Raw Staging  │  │ Unified      │  │ Cache        │          │
│  │ Tables       │──▶│ Metrics      │  │ (Redis)      │          │
│  │ (ELT)       │  │ Tables       │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Key Additions vs Current Design

| Addition | Rationale | Priority |
|----------|-----------|----------|
| **Semantic Layer** | Grounds AI in precise metric definitions, prevents hallucination, enables consistent cross-platform analysis | MVP |
| **Validation Agent** | Dedicated cross-section consistency checking after all AI sections are generated | MVP |
| **Skill Registry** | Enables composition, reuse, and testing of individual capabilities | MVP |
| **Raw Staging Tables** | ELT pattern — preserve raw API responses for reprocessing and debugging | MVP |
| **LangGraph Orchestration** | DAG-based workflow with state management, error recovery, and parallel execution | Phase 2 |
| **Event-driven Anomaly Alerts** | Real-time anomaly detection triggered by data syncs | Phase 3 |

### 6.3 Implementation Priority

**Phase 1 (MVP):**
1. Implement the Semantic Metric Layer (metric catalog with definitions, formulas, benchmarks, platform mappings)
2. Add raw staging tables to the data sync pipeline
3. Build the Skill interface and registry pattern
4. Implement atomic skills as Python classes with Pydantic I/O validation
5. Add the Validation Agent for post-generation consistency checking
6. Use simple sequential orchestration (Celery tasks) for the report pipeline

**Phase 2:**
1. Migrate orchestration from Celery sequential tasks to LangGraph DAG
2. Enable parallel AI section generation
3. Add contextual anomaly detection (event calendar)
4. Implement composite skill composition

**Phase 3:**
1. Event-driven anomaly alerting pipeline
2. Cross-metric correlation analysis
3. Industry benchmarking from aggregated data
4. Custom skill creation (user-defined analysis types)

---

## 7. Sources

- [AgencyAnalytics alternatives and competitors - Whatagraph](https://whatagraph.com/blog/articles/agencyanalytics-alternatives-and-competitors)
- [AI Marketing Analytics Dashboard Platforms - Madgicx](https://madgicx.com/blog/ai-marketing-analytics-dashboard-platforms)
- [How to Build Multi-Agent Systems: Complete 2026 Guide - DEV Community](https://dev.to/eira-wexford/how-to-build-multi-agent-systems-complete-2026-guide-1io6)
- [Multi-Agent AI Systems: Enterprise Guide 2026 - Neomanex](https://neomanex.com/posts/multi-agent-ai-systems-orchestration)
- [Developer's Guide to Multi-Agent Patterns in ADK - Google Developers Blog](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [Best Practices for AI Agent Implementations - OneReach](https://onereach.ai/blog/best-practices-for-ai-agent-implementations/)
- [CrewAI vs LangGraph vs AutoGen - DataCamp](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
- [LangGraph vs CrewAI vs AutoGen: Top AI Agent Frameworks 2026 - o-mega](https://o-mega.ai/articles/langgraph-vs-crewai-vs-autogen-top-10-agent-frameworks-2026)
- [LangGraph vs CrewAI vs AutoGen: Complete Guide 2026 - DEV Community](https://dev.to/pockit_tools/langgraph-vs-crewai-vs-autogen-the-complete-multi-agent-ai-orchestration-guide-for-2026-2d63)
- [Agent Orchestration 2026: LangGraph, CrewAI & AutoGen - Iterathon](https://iterathon.tech/blog/ai-agent-orchestration-frameworks-2026)
- [How to Use AI for Data Analytics Without Hallucinations - Narrative BI](https://www.narrative.bi/analytics/ai-hallucinations-mitigation)
- [How to Prevent LLM Hallucinations - Voiceflow](https://www.voiceflow.com/blog/prevent-llm-hallucinations)
- [AI Grounding with Agentic RAG - Moveworks](https://www.moveworks.com/us/en/resources/blog/improved-ai-grounding-with-agentic-rag)
- [ETL vs ELT: Key Differences 2026 - Improvado](https://improvado.io/blog/etl-vs-elt)
- [ETL/ELT for Marketing Data - Windsor.ai](https://windsor.ai/etl-elt-for-marketing-data/)
- [ETL Frameworks 2026 - Integrate.io](https://www.integrate.io/blog/etl-frameworks-in-2025-designing-robust-future-proof-data-pipelines/)
- [Supermetrics for Looker Studio](https://supermetrics.com/products/looker-studio)
- [Supermetrics Storage Centralizes Data in BigQuery - Google Cloud Blog](https://cloud.google.com/blog/products/data-analytics/supermetrics-storage-centralizes-cross-channel-data-in-bigquery)
- [AI Reporting Tools for Automated Analytics 2026 - Improvado](https://improvado.io/blog/ai-report-generation)
- [AI Reporting Tools 2026 - Whatagraph](https://whatagraph.com/blog/articles/ai-reporting-tools)
- [Agentic Analytics: Semantic Layers Powering AI Decision-Making - CDOTrends](https://www.cdotrends.com/story/4839/agentic-analytics-how-semantic-layers-are-powering-next-era-ai-driven-decision-making)
- [Semantic Layer: Key to Trusted Analytics and AI - ThoughtSpot](https://www.thoughtspot.com/data-trends/data-and-analytics-engineering/semantic-layer)
- [Agentic Semantic Layer - ThoughtSpot](https://www.thoughtspot.com/blog/introducing-the-agentic-semantic-layer)
- [Evolution of the Semantic Layer in Agentic AI - Tellius](https://www.tellius.com/resources/blog/from-metrics-to-meaning-the-evolution-of-the-semantic-layer-in-the-age-of-agentic-ai)
- [Building an AI Agent to Detect Anomalies in Time-Series Data - Towards Data Science](https://towardsdatascience.com/building-an-ai-agent-to-detect-and-handle-anomalies-in-time-series-data/)
- [LangGraph as a DAG: Rethinking Data Pipeline Orchestration - Medium](https://medium.com/@srikrishnan.tech/langgraph-as-a-dag-rethinking-data-pipeline-orchestration-f089ccea175b)
- [LangGraph Workflows and Agents - LangChain Docs](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [Agentic AI with LangGraph 2026 - AdSpyder](https://adspyder.io/blog/agentic-ai-with-langgraph/)
- [AI Analytics: What It Is, How It Works - Tellius](https://www.tellius.com/resources/blog/ai-analytics)
- [Future of Strategic Measurement: Enhancing KPIs with AI - MIT Sloan](https://sloanreview.mit.edu/projects/the-future-of-strategic-measurement-enhancing-kpis-with-ai/)
