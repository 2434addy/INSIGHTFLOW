"""
Insight Summarization skill — prompt engineering, templates, output parsing.

Constructs prompts for Claude API, parses AI responses, and provides
template-based fallbacks when AI generation fails.
"""

from __future__ import annotations

import json
import re

from app.pipeline.schemas import (
    AnomalyAnalysis,
    CampaignEvaluationResult,
    GeneratedInsight,
    InsightCategory,
    InsightSentiment,
    KPIResult,
    TrendAnalysis,
)


class InsightPromptBuilder:
    """Builds prompts for Claude API insight generation."""

    def build_system_prompt(self, tone: str = "executive") -> str:
        base = (
            "You are a senior digital marketing analyst generating insights "
            "for a client performance report. Your audience is marketing agency "
            "account managers presenting to their clients.\n\n"
            "RULES:\n"
            "1. ONLY reference data explicitly provided in the data context\n"
            "2. Every number you mention MUST match the source data exactly\n"
            "3. Explain WHY metrics changed, not just WHAT changed\n"
            "4. Each insight must be specific — no generic marketing advice\n"
            "5. Classify each insight sentiment: positive, neutral, or attention_needed\n"
            "6. Prioritize by business impact (revenue > efficiency > volume)\n"
            "7. Never speculate or invent data points\n"
            "8. Reference platform names when relevant\n"
        )
        tone_instructions = {
            "executive": "\nTONE: Keep language concise and business-focused. 2-3 sentences per insight.",
            "detailed": "\nTONE: Provide thorough analysis with supporting detail. 4-6 sentences per insight.",
            "casual": "\nTONE: Use conversational, accessible language. Avoid jargon.",
        }
        return base + tone_instructions.get(tone, tone_instructions["executive"])

    def build_data_context(
        self,
        kpis: KPIResult,
        trends: TrendAnalysis,
        anomalies: AnomalyAnalysis,
        evaluation: CampaignEvaluationResult,
    ) -> str:
        """Build structured data context as JSON for the AI prompt."""
        context = {
            "current_period": kpis.current_period.model_dump(),
            "previous_period": kpis.previous_period.model_dump() if kpis.previous_period else None,
            "comparison": kpis.comparison.model_dump() if kpis.comparison else None,
            "by_platform": {k: v.model_dump() for k, v in kpis.by_platform.items()},
            "trends": [t.model_dump() for t in trends.trends],
            "anomalies": [a.model_dump() for a in anomalies.point_anomalies[:5]],
            "top_performers": [c.model_dump() for c in evaluation.top_performers[:5]],
            "bottom_performers": [c.model_dump() for c in evaluation.bottom_performers[:5]],
            "budget_assessment": evaluation.budget_assessment.model_dump(),
        }
        return json.dumps(context, indent=2, default=str)

    def build_insight_prompt(
        self,
        data_context: str,
    ) -> str:
        return (
            f"Analyze the following marketing performance data and generate insights.\n\n"
            f"DATA:\n{data_context}\n\n"
            f"Generate 5-8 insights. Respond with a JSON object:\n"
            f'{{\n'
            f'  "insights": [\n'
            f'    {{\n'
            f'      "category": "performance|efficiency|growth|anomaly|opportunity|risk",\n'
            f'      "sentiment": "positive|neutral|attention_needed",\n'
            f'      "priority": 1,\n'
            f'      "headline": "Short headline (< 15 words)",\n'
            f'      "detail": "2-3 sentence explanation with specific numbers",\n'
            f'      "confidence": 0.95\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n'
        )

    def build_executive_summary_prompt(
        self,
        data_context: str,
        insights_json: str,
    ) -> str:
        return (
            f"Given the following data and insights, write an executive summary.\n\n"
            f"DATA:\n{data_context}\n\n"
            f"KEY INSIGHTS:\n{insights_json}\n\n"
            f"REQUIREMENTS:\n"
            f"- 2-3 paragraphs\n"
            f"- Lead with the most impactful finding\n"
            f"- Include specific numbers (spend, conversions, ROAS)\n"
            f"- Compare to previous period\n"
            f"- End with a forward-looking statement\n"
            f"- Do NOT include any data not in the DATA section\n\n"
            f"OUTPUT: Plain text only."
        )

    def build_recommendation_prompt(
        self,
        data_context: str,
        insights_json: str,
    ) -> str:
        return (
            f"Based on the following data and insights, generate actionable "
            f"optimization recommendations.\n\n"
            f"DATA:\n{data_context}\n\n"
            f"INSIGHTS:\n{insights_json}\n\n"
            f"Generate 3-6 recommendations. Respond with a JSON object:\n"
            f'{{\n'
            f'  "recommendations": [\n'
            f'    {{\n'
            f'      "category": "budget|targeting|creative|bidding|scheduling",\n'
            f'      "priority": "critical|high|medium|low",\n'
            f'      "title": "Short action title",\n'
            f'      "description": "2-3 sentence explanation",\n'
            f'      "expected_impact": "Estimated impact description",\n'
            f'      "estimated_impact_value": 15.0,\n'
            f'      "effort": "low|medium|high",\n'
            f'      "action_items": ["Step 1", "Step 2"]\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n'
        )


class InsightParser:
    """Parses and validates AI responses into structured insights."""

    def parse_insights(self, raw_response: str) -> list[GeneratedInsight]:
        parsed = self._parse_json(raw_response)
        insights: list[GeneratedInsight] = []

        for item in parsed.get("insights", []):
            if not all(k in item for k in ["category", "headline", "detail"]):
                continue

            try:
                category = InsightCategory(item["category"])
            except ValueError:
                category = InsightCategory.PERFORMANCE

            try:
                sentiment = InsightSentiment(item.get("sentiment", "neutral"))
            except ValueError:
                sentiment = InsightSentiment.NEUTRAL

            insights.append(GeneratedInsight(
                category=category,
                sentiment=sentiment,
                priority=item.get("priority", len(insights) + 1),
                headline=item["headline"],
                detail=item["detail"],
                confidence=item.get("confidence", 0.9),
            ))

        return insights

    def parse_recommendations(self, raw_response: str) -> list[dict]:
        parsed = self._parse_json(raw_response)
        return parsed.get("recommendations", [])

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Parse JSON from AI response, handling markdown code blocks."""
        raw = raw.strip()
        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Try extracting from code blocks
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return {}


class TemplateFallback:
    """Template-based narrative generation for when AI fails."""

    TEMPLATES = {
        "performance_positive": (
            "Overall performance improved this period, with {metric} "
            "{direction} {change_pct:.1f}% from {previous} to {current}."
        ),
        "performance_negative": (
            "Performance declined this period, with {metric} "
            "{direction} {change_pct:.1f}% from {previous} to {current}. "
            "This warrants investigation."
        ),
        "anomaly_spike": (
            "An unusual spike in {metric} was detected on {date}, "
            "reaching {actual} versus an expected {expected} "
            "({deviation_pct:.1f}% above normal)."
        ),
        "anomaly_drop": (
            "A significant drop in {metric} was observed on {date}, "
            "falling to {actual} from an expected {expected} "
            "({deviation_pct:.1f}% below normal)."
        ),
        "top_performer": (
            'The top-performing campaign is "{campaign}" with a '
            "{roas:.2f}x ROAS on ${spend:,.2f} in spend."
        ),
        "waster": (
            'The campaign "{campaign}" is underperforming with a '
            "{roas:.2f}x ROAS on ${spend:,.2f} in spend and should be reviewed."
        ),
    }

    def generate(self, template_key: str, data: dict) -> str:
        template = self.TEMPLATES.get(template_key, "Performance data is available for review.")
        try:
            return template.format(**data)
        except (KeyError, ValueError):
            return "Performance data is available for review."

    def generate_fallback_insights(
        self, kpis: KPIResult, evaluation: CampaignEvaluationResult
    ) -> list[GeneratedInsight]:
        """Generate template-based insights when AI fails."""
        insights: list[GeneratedInsight] = []

        # Overall performance insight
        if kpis.comparison and kpis.comparison.spend_change_pct is not None:
            is_positive = (kpis.comparison.conversions_change_pct or 0) > 0
            insights.append(GeneratedInsight(
                category=InsightCategory.PERFORMANCE,
                sentiment=InsightSentiment.POSITIVE if is_positive else InsightSentiment.ATTENTION_NEEDED,
                priority=1,
                headline="Overall Performance " + ("Improved" if is_positive else "Declined"),
                detail=self.generate(
                    "performance_positive" if is_positive else "performance_negative",
                    {
                        "metric": "conversions",
                        "direction": "increasing" if is_positive else "decreasing",
                        "change_pct": abs(kpis.comparison.conversions_change_pct or 0),
                        "previous": kpis.previous_period.conversions if kpis.previous_period else 0,
                        "current": kpis.current_period.conversions,
                    },
                ),
                confidence=1.0,
            ))

        # Top performer insight
        if evaluation.top_performers:
            top = evaluation.top_performers[0]
            insights.append(GeneratedInsight(
                category=InsightCategory.PERFORMANCE,
                sentiment=InsightSentiment.POSITIVE,
                priority=2,
                headline=f"Top Performer: {top.campaign_name}",
                detail=self.generate("top_performer", {
                    "campaign": top.campaign_name,
                    "roas": top.roas or 0,
                    "spend": top.spend,
                }),
                confidence=1.0,
                campaign_id=top.campaign_id,
            ))

        # Waster insight
        if evaluation.bottom_performers:
            bottom = evaluation.bottom_performers[0]
            insights.append(GeneratedInsight(
                category=InsightCategory.RISK,
                sentiment=InsightSentiment.ATTENTION_NEEDED,
                priority=3,
                headline=f"Underperforming: {bottom.campaign_name}",
                detail=self.generate("waster", {
                    "campaign": bottom.campaign_name,
                    "roas": bottom.roas or 0,
                    "spend": bottom.spend,
                }),
                confidence=1.0,
                campaign_id=bottom.campaign_id,
            ))

        return insights
