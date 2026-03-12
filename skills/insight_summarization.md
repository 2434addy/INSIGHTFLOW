# Skill: Insight Summarization

## Overview

Provides prompt engineering patterns, narrative templates, and AI output structuring for generating human-readable marketing insights from structured data. Handles AI prompt construction, output parsing, and fallback template logic.

## Skill Tier: Composite

Composed from the Semantic Metric Layer and KPI Computation skills. Used by the Insight Generation Agent and Report Writer Agent.

## Capabilities

### 1. Prompt Construction

```python
class InsightPromptBuilder:
    def build_system_prompt(self, tone: str = "executive") -> str:
        """Build the system prompt for insight generation."""
        base = """You are a senior digital marketing analyst generating insights
for a client performance report. Your audience is marketing agency account
managers presenting to their clients.

RULES:
1. ONLY reference data explicitly provided in the data context
2. Every number you mention MUST match the source data exactly
3. Explain WHY metrics changed, not just WHAT changed
4. Each insight must be specific — no generic marketing advice
5. Classify each insight sentiment: positive, neutral, or attention_needed
6. Prioritize by business impact (revenue > efficiency > volume)
7. Never speculate or invent data points
8. Reference platform names (e.g., "your Meta retargeting campaigns")
"""
        tone_instructions = {
            "executive": "Keep language concise and business-focused. 2-3 sentences per insight.",
            "detailed": "Provide thorough analysis with supporting detail. 4-6 sentences per insight.",
            "casual": "Use conversational, accessible language. Avoid jargon.",
        }
        return base + f"\nTONE: {tone_instructions.get(tone, tone_instructions['executive'])}"

    def build_data_context(
        self,
        analysis: AnalysisOutput,
        anomalies: list[Anomaly],
        segmentation: SegmentationResult,
        client: ClientContext,
    ) -> str:
        """
        Build structured data context for the AI prompt.
        Uses JSON format to minimize ambiguity.
        """
        context = {
            "client": {
                "name": client.name,
                "industry": client.industry,
                "platforms": client.platforms,
            },
            "period": {
                "current": analysis.summary.current_period.__dict__,
                "previous": analysis.summary.previous_period.__dict__,
                "comparison": analysis.summary.comparison.__dict__,
            },
            "trends": [t.__dict__ for t in analysis.trends],
            "anomalies": [a.__dict__ for a in anomalies[:5]],
            "top_performers": [c.__dict__ for c in analysis.rankings.top],
            "bottom_performers": [c.__dict__ for c in analysis.rankings.bottom],
            "platform_comparison": analysis.platform_comparison,
            "segmentation_summary": {
                "star_count": segmentation.tiers["star"].count,
                "waster_count": segmentation.tiers["waster"].count,
                "waster_spend_share": segmentation.tiers["waster"].spend_share,
            },
        }
        return json.dumps(context, indent=2, default=str)

    def build_output_schema(self) -> str:
        """Define the expected JSON output structure."""
        return """
Respond with a JSON object matching this schema:
{
  "insights": [
    {
      "category": "performance|efficiency|growth|anomaly|opportunity|risk",
      "sentiment": "positive|neutral|attention_needed",
      "priority": 1,  // 1 = highest priority
      "headline": "Short headline (< 15 words)",
      "detail": "2-3 sentence explanation with specific numbers",
      "supporting_data": {
        "metric": "the primary metric",
        "value": 0.0,
        "comparison_value": 0.0,
        "source_field": "path in data context"
      },
      "confidence": 0.95  // Your confidence this insight is accurate (0-1)
    }
  ]
}
"""
```

### 2. Executive Summary Generation

```python
class ExecutiveSummaryBuilder:
    def build_prompt(
        self,
        analysis: AnalysisOutput,
        insights: list[Insight],
        tone: str = "executive",
    ) -> str:
        """
        Build prompt for executive summary that synthesizes insights.
        Summary should lead with the most important finding.
        """
        return f"""
Given the following analysis data and generated insights, write an executive
summary for the client performance report.

DATA:
{json.dumps(analysis.summary.__dict__, indent=2, default=str)}

KEY INSIGHTS:
{json.dumps([i.__dict__ for i in insights[:3]], indent=2, default=str)}

REQUIREMENTS:
- 2-3 paragraphs
- Lead with the most impactful finding
- Include specific numbers (spend, conversions, ROAS)
- Compare to previous period
- End with a forward-looking statement or key action item
- Do NOT include any data not present in the DATA section above

OUTPUT: Plain text (no JSON wrapper for this section)
"""
```

### 3. Template Fallback

```python
class TemplateFallback:
    """
    When AI confidence is below threshold or AI generation fails,
    use template-based narrative as fallback.
    """

    def generate_insight(
        self, category: str, data: dict
    ) -> str:
        templates = {
            "performance_positive": (
                "Overall performance improved this period, with {metric} "
                "{direction} {change_pct}% from {previous} to {current}."
            ),
            "performance_negative": (
                "Performance declined this period, with {metric} "
                "{direction} {change_pct}% from {previous} to {current}. "
                "This warrants investigation."
            ),
            "anomaly_spike": (
                "An unusual spike in {metric} was detected on {date}, "
                "reaching {actual} versus an expected {expected} "
                "({deviation_pct}% above normal)."
            ),
            "anomaly_drop": (
                "A significant drop in {metric} was observed on {date}, "
                "falling to {actual} from an expected {expected} "
                "({deviation_pct}% below normal)."
            ),
            "top_performer": (
                "The top-performing campaign is \"{campaign}\" with a "
                "{roas}x ROAS on ${spend} in spend."
            ),
            "waster": (
                "The campaign \"{campaign}\" is underperforming with a "
                "{roas}x ROAS on ${spend} in spend and should be reviewed."
            ),
        }
        template = templates.get(category, "Performance data is available for review.")
        return template.format(**data)
```

### 4. Output Parsing & Validation

```python
class InsightParser:
    def parse_ai_response(
        self, raw_response: str, source_data: dict
    ) -> tuple[list[Insight], list[ValidationError]]:
        """
        Parse AI response, validate structure, and flag issues.
        Returns (parsed_insights, validation_errors).
        """
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            parsed = extract_json_from_markdown(raw_response)

        insights = []
        errors = []

        for item in parsed.get("insights", []):
            # Validate required fields
            if not all(k in item for k in ["category", "headline", "detail"]):
                errors.append(ValidationError("missing_fields", item))
                continue

            # Validate confidence threshold
            if item.get("confidence", 0) < 0.7:
                errors.append(ValidationError("low_confidence", item))

            insights.append(Insight(**item))

        return insights, errors
```

## Used By

| Agent | Purpose |
|-------|---------|
| Insight Generation Agent | Prompt construction, output parsing |
| Report Writer Agent | Executive summary generation |
| Validation Agent | Template fallback on validation failure |
