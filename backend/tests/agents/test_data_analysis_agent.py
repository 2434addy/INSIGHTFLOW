"""
Tests for DataAnalysisAgent — composite agent that computes KPIs,
detects trends, and detects anomalies using skills.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.agents.data_analysis_agent import DataAnalysisAgent, DataAnalysisInput
from app.pipeline.schemas import MetricRecord

ORG_ID = uuid.uuid4()


def _make_records(
    num_days: int = 60,
    num_campaigns: int = 3,
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
            base_spend = 100 + day_offset * 0.5
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


class TestDataAnalysisAgentEndToEnd:
    """End-to-end tests for the composite agent."""

    @pytest.mark.asyncio
    async def test_returns_all_three_sections(self):
        records = _make_records(num_days=60, num_campaigns=3)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
        ))

        assert result.kpis is not None
        assert result.trends is not None
        assert result.anomalies is not None

    @pytest.mark.asyncio
    async def test_kpis_populated(self):
        records = _make_records(num_days=60, num_campaigns=3)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
        ))

        kpis = result.kpis
        assert kpis.current_period.spend > 0
        assert kpis.current_period.impressions > 0
        assert kpis.current_period.clicks > 0
        assert kpis.current_period.ctr is not None
        assert kpis.current_period.cpc is not None
        assert kpis.current_period.roas is not None

    @pytest.mark.asyncio
    async def test_period_comparison_computed(self):
        records = _make_records(num_days=60, num_campaigns=3)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
        ))

        assert result.kpis.previous_period is not None
        assert result.kpis.comparison is not None
        assert result.kpis.comparison.spend_change_pct is not None

    @pytest.mark.asyncio
    async def test_platform_and_campaign_aggregation(self):
        records = _make_records(num_days=60, num_campaigns=3)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
        ))

        assert len(result.kpis.by_platform) > 0
        assert len(result.kpis.by_campaign) > 0

    @pytest.mark.asyncio
    async def test_trends_detected(self):
        records = _make_records(num_days=60, num_campaigns=3)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
        ))

        assert len(result.trends.trends) > 0
        metrics_with_trends = {t.metric for t in result.trends.trends}
        assert "spend" in metrics_with_trends
        assert "clicks" in metrics_with_trends

    @pytest.mark.asyncio
    async def test_moving_averages_computed(self):
        records = _make_records(num_days=60, num_campaigns=3)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
        ))

        assert len(result.trends.moving_averages) > 0
        for ma in result.trends.moving_averages:
            assert len(ma.windows) > 0

    @pytest.mark.asyncio
    async def test_anomalies_structure(self):
        records = _make_records(num_days=60, num_campaigns=3)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 2, 1),
            date_range_end=date(2026, 2, 28),
        ))

        # Anomaly result should be well-formed even if no anomalies found
        assert result.anomalies.point_anomalies is not None
        assert result.anomalies.correlation_anomalies is not None
        assert result.anomalies.missing_dates is not None


class TestDataAnalysisAgentKPIs:
    """Focused tests for KPI computation via the agent."""

    @pytest.mark.asyncio
    async def test_ctr_cpc_cpa_roas_computed(self):
        records = _make_records(num_days=30, num_campaigns=2)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 1, 1),
            date_range_end=date(2026, 1, 30),
        ))

        kpis = result.kpis
        assert kpis.current_period.ctr > 0   # CTR
        assert kpis.current_period.cpc > 0   # CPC
        assert kpis.current_period.cpa > 0   # CPA
        assert kpis.current_period.roas > 0  # ROAS

    @pytest.mark.asyncio
    async def test_records_have_derived_metrics(self):
        records = _make_records(num_days=30, num_campaigns=1)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 1, 1),
            date_range_end=date(2026, 1, 30),
        ))

        for r in result.kpis.records:
            assert r.ctr is not None
            assert r.cpc is not None
            assert r.roas is not None


class TestDataAnalysisAgentEdgeCases:
    """Edge case and boundary tests."""

    @pytest.mark.asyncio
    async def test_minimal_data(self):
        """Should handle a small dataset without errors."""
        records = _make_records(num_days=5, num_campaigns=1, start_date=date(2026, 1, 5))
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 1, 5),
            date_range_end=date(2026, 1, 9),
        ))

        assert result.kpis.current_period.spend > 0
        # With only 5 data points, trends may show insufficient_data
        assert result.trends is not None

    @pytest.mark.asyncio
    async def test_no_previous_period_data(self):
        """When records don't cover the previous period, comparison is None."""
        start = date(2026, 3, 1)
        records = _make_records(num_days=10, num_campaigns=1, start_date=start)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=start,
            date_range_end=start + timedelta(days=9),
        ))

        assert result.kpis.previous_period is None
        assert result.kpis.comparison is None

    @pytest.mark.asyncio
    async def test_single_campaign(self):
        records = _make_records(num_days=30, num_campaigns=1)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 1, 1),
            date_range_end=date(2026, 1, 30),
        ))

        assert len(result.kpis.by_campaign) == 1

    @pytest.mark.asyncio
    async def test_budget_pacing(self):
        """When budget is provided, pacing analysis should be included."""
        records = _make_records(num_days=30, num_campaigns=2)
        agent = DataAnalysisAgent()
        result = await agent.run(DataAnalysisInput(
            records=records,
            date_range_start=date(2026, 1, 1),
            date_range_end=date(2026, 1, 30),
            budget=10000.0,
            days_in_period=30,
        ))

        assert result.trends.pacing is not None
        assert result.trends.pacing.budget == 10000.0
        assert result.trends.pacing.status in ("on_track", "underspending", "overspending")
