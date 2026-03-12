"""
End-to-end test for the InsightFlow analytics pipeline.

Tests the full pipeline with synthetic data, verifying each stage
produces correct output without requiring external services.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import date, timedelta

import pytest

from app.agents.anomaly_detection_agent import AnomalyDetectionAgent, AnomalyDetectionInput
from app.agents.campaign_evaluation_agent import CampaignEvaluationAgent, CampaignEvaluationInput
from app.agents.data_validation_agent import DataValidationAgent, DataValidationInput
from app.agents.kpi_computation_agent import KPIComputationAgent, KPIComputationInput
from app.agents.trend_detection_agent import TrendDetectionAgent, TrendDetectionInput
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.schemas import (
    MetricRecord,
    PipelineProgress,
    PipelineStage,
    ReportRequest,
)
from app.skills.anomaly_detection import ZScoreDetector
from app.skills.campaign_evaluation import TierClassifier
from app.skills.data_quality_validation import RawDataValidator
from app.skills.kpi_computation import Aggregator, KPIComputer, safe_divide
from app.skills.semantic_metric_layer import SemanticMetricLayer
from app.skills.trend_detection import TrendClassifier, linear_regression


# ── Fixtures ────────────────────────────────────────────────────

ORG_ID = uuid.uuid4()
USER_ID = uuid.uuid4()


def _make_records(
    num_days: int = 60,
    num_campaigns: int = 5,
    start_date: date | None = None,
) -> list[MetricRecord]:
    """Generate synthetic metric records for testing."""
    start = start_date or date(2026, 1, 1)
    campaigns = [
        (uuid.uuid4(), f"Campaign {i}", ["meta_ads", "google_ads"][i % 2])
        for i in range(num_campaigns)
    ]
    records = []
    for day_offset in range(num_days):
        d = start + timedelta(days=day_offset)
        for cid, cname, platform in campaigns:
            # Create realistic-looking data with some variation
            base_spend = 100 + day_offset * 0.5  # slight upward trend
            records.append(MetricRecord(
                campaign_id=cid,
                campaign_name=cname,
                platform=platform,
                date=d,
                organization_id=ORG_ID,
                impressions=int(base_spend * 100 + day_offset * 10),
                clicks=int(base_spend * 3 + day_offset),
                spend=round(base_spend + (day_offset % 7) * 5, 2),
                conversions=int(base_spend * 0.1 + day_offset * 0.05),
                conversion_value=round(base_spend * 0.4 + day_offset * 0.2, 2),
            ))
    return records


# ── Skill Tests ─────────────────────────────────────────────────


class TestSemanticMetricLayer:
    def test_get_metric(self):
        sml = SemanticMetricLayer()
        m = sml.get_metric("ctr")
        assert m.name == "Click-Through Rate"
        assert m.direction == "higher_is_better"

    def test_format_value(self):
        sml = SemanticMetricLayer()
        assert sml.format_value("spend", 1234.56) == "$1,234.56"
        assert sml.format_value("ctr", 2.5) == "2.50%"
        assert sml.format_value("roas", 4.5) == "4.50x"
        assert sml.format_value("impressions", 1234567) == "1,234,567"

    def test_format_none(self):
        sml = SemanticMetricLayer()
        assert sml.format_value("spend", None) == "N/A"

    def test_unknown_metric(self):
        sml = SemanticMetricLayer()
        with pytest.raises(KeyError):
            sml.get_metric("nonexistent")

    def test_list_metrics(self):
        sml = SemanticMetricLayer()
        all_metrics = sml.list_metrics()
        assert len(all_metrics) == 12  # 5 core + 7 derived


class TestKPIComputation:
    def test_safe_divide(self):
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) is None
        assert safe_divide(None, 5) is None

    def test_compute_derived(self):
        computer = KPIComputer()
        record = MetricRecord(
            campaign_id=uuid.uuid4(),
            platform="meta_ads",
            date=date(2026, 1, 1),
            organization_id=ORG_ID,
            impressions=10000,
            clicks=200,
            spend=100.0,
            conversions=10,
            conversion_value=500.0,
        )
        result = computer.compute_derived(record)
        assert result.ctr == pytest.approx(2.0, rel=0.01)
        assert result.cpc == pytest.approx(0.50, rel=0.01)
        assert result.cpa == pytest.approx(10.0, rel=0.01)
        assert result.roas == pytest.approx(5.0, rel=0.01)

    def test_aggregate_summary(self):
        agg = Aggregator()
        records = _make_records(num_days=10, num_campaigns=2)
        summary = agg.aggregate_summary(records)
        assert summary.spend > 0
        assert summary.impressions > 0
        assert summary.ctr is not None


class TestTrendDetection:
    def test_linear_regression(self):
        # Perfect upward trend
        slope, intercept, r_sq = linear_regression([1, 2, 3, 4, 5])
        assert slope == pytest.approx(1.0, rel=0.01)
        assert r_sq == pytest.approx(1.0, rel=0.01)

    def test_trend_classification(self):
        classifier = TrendClassifier()
        # Strong upward trend
        values = [float(i) for i in range(30)]
        result = classifier.classify(values, metric_name="spend")
        assert result.direction.value in ("increasing", "accelerating")
        assert result.strength > 0

    def test_stable_trend(self):
        classifier = TrendClassifier()
        values = [100.0] * 30  # Flat
        result = classifier.classify(values, metric_name="spend")
        assert result.direction.value == "stable"

    def test_insufficient_data(self):
        classifier = TrendClassifier()
        result = classifier.classify([1, 2, 3], metric_name="spend")
        assert result.direction.value == "insufficient_data"


class TestAnomalyDetection:
    def test_zscore_detection(self):
        detector = ZScoreDetector()
        # Normal values with one spike — need variation for stdev > 0
        values = [10.0 + (i % 3) * 0.1 for i in range(35)]
        values.append(200.0)  # extreme spike
        anomalies = detector.detect(values, metric_name="spend", rolling_window=30)
        assert len(anomalies) > 0
        assert anomalies[0].type.value == "spike"

    def test_no_anomalies(self):
        detector = ZScoreDetector()
        values = [10.0 + i * 0.01 for i in range(50)]  # smooth trend
        anomalies = detector.detect(values, metric_name="spend")
        assert len(anomalies) == 0


class TestDataValidation:
    def test_valid_records(self):
        validator = RawDataValidator()
        records = _make_records(num_days=5, num_campaigns=1)
        result = validator.validate(records)
        assert result.is_valid
        assert result.total_records == 5

    def test_negative_spend(self):
        validator = RawDataValidator()
        record = MetricRecord(
            campaign_id=uuid.uuid4(),
            platform="meta_ads",
            date=date(2026, 1, 1),
            organization_id=ORG_ID,
            spend=-100.0,
        )
        result = validator.validate([record])
        assert not result.is_valid
        assert any("Negative" in e.message for e in result.errors)


class TestCampaignEvaluation:
    def test_tier_classification(self):
        classifier = TierClassifier(min_spend=1.0)
        records = _make_records(num_days=30, num_campaigns=10)
        # Compute derived metrics first
        computer = KPIComputer()
        records = computer.compute_all(records)
        tiered = classifier.classify(records)
        total = sum(len(v) for v in tiered.values())
        assert total > 0


# ── Agent Tests ─────────────────────────────────────────────────


class TestAgents:
    @pytest.fixture
    def records(self):
        return _make_records(num_days=60, num_campaigns=5)

    @pytest.mark.asyncio
    async def test_data_validation_agent(self, records):
        agent = DataValidationAgent()
        result = await agent.run(DataValidationInput(records=records))
        assert result.total_records == len(records)
        assert result.is_valid

    @pytest.mark.asyncio
    async def test_kpi_computation_agent(self, records):
        agent = KPIComputationAgent()
        result = await agent.run(KPIComputationInput(
            records=records,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
            comparison_period="previous_period",
        ))
        assert result.current_period.spend > 0
        assert result.previous_period is not None
        assert result.comparison is not None

    @pytest.mark.asyncio
    async def test_trend_detection_agent(self, records):
        agent = TrendDetectionAgent()
        result = await agent.run(TrendDetectionInput(records=records))
        assert len(result.trends) > 0
        assert len(result.moving_averages) > 0

    @pytest.mark.asyncio
    async def test_anomaly_detection_agent(self, records):
        agent = AnomalyDetectionAgent()
        result = await agent.run(AnomalyDetectionInput(records=records))
        # May or may not find anomalies in synthetic data
        assert result is not None

    @pytest.mark.asyncio
    async def test_campaign_evaluation_agent(self, records):
        # First compute KPIs
        kpi_agent = KPIComputationAgent()
        kpis = await kpi_agent.run(KPIComputationInput(
            records=records,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
        ))
        agent = CampaignEvaluationAgent()
        result = await agent.run(CampaignEvaluationInput(kpis=kpis))
        total_campaigns = sum(len(v) for v in result.tiered_campaigns.values())
        assert total_campaigns > 0


# ── Full Pipeline Test ──────────────────────────────────────────


class TestPipelineOrchestrator:
    @pytest.mark.asyncio
    async def test_full_pipeline_without_ai(self):
        """Run full pipeline without AI client (uses template fallback)."""
        records = _make_records(num_days=60, num_campaigns=5)

        request = ReportRequest(
            organization_id=ORG_ID,
            generated_by=USER_ID,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
            comparison_period="previous_period",
            platforms=["meta_ads", "google_ads"],
            tone="executive",
            title="February Performance Report",
        )

        progress_stages: list[PipelineStage] = []

        def on_progress(progress: PipelineProgress):
            progress_stages.append(progress.stage)

        orchestrator = PipelineOrchestrator(anthropic_client=None)
        result = await orchestrator.execute(
            request=request,
            records=records,
            progress_callback=on_progress,
        )

        # Verify all stages completed
        assert result.report_id == request.report_id
        assert result.validation.total_records > 0
        assert result.kpis.current_period.spend > 0
        assert len(result.trends.trends) > 0
        assert len(result.insights.insights) > 0  # Template fallback
        assert len(result.recommendations.recommendations) > 0  # Template fallback
        assert result.total_tokens_used == 0  # No AI calls

        # Verify progress callbacks were fired
        assert PipelineStage.DATA_VALIDATION in progress_stages
        assert PipelineStage.REPORT_ASSEMBLY in progress_stages
