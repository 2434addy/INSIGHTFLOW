"""
KPI Computation Agent — Stage 2 of the analytics pipeline.

Computes derived metrics, aggregates by platform/campaign, and performs
period-over-period comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.agents.base import BaseAgent
from app.pipeline.schemas import KPIResult, MetricRecord
from app.skills.kpi_computation import Aggregator, KPIComputer, PeriodComparer


@dataclass
class KPIComputationInput:
    records: list[MetricRecord]
    date_range_start: date
    date_range_end: date
    comparison_period: str = "previous_period"  # previous_period | previous_year


class KPIComputationAgent(BaseAgent[KPIComputationInput, KPIResult]):
    """Computes all KPIs, aggregations, and period comparisons."""

    name = "kpi_computation_agent"

    def __init__(self) -> None:
        self._computer = KPIComputer()
        self._aggregator = Aggregator()
        self._comparer = PeriodComparer()

    async def execute(self, input_data: KPIComputationInput) -> KPIResult:
        # Split records into current and previous period
        current_records = [
            r for r in input_data.records
            if input_data.date_range_start <= r.date <= input_data.date_range_end
        ]
        previous_records = self._get_previous_records(
            input_data.records,
            input_data.date_range_start,
            input_data.date_range_end,
            input_data.comparison_period,
        )

        # Compute derived metrics
        current_records = self._computer.compute_all(current_records)
        if previous_records:
            previous_records = self._computer.compute_all(previous_records)

        # Aggregate current period
        current_summary = self._aggregator.aggregate_summary(current_records)
        by_platform = self._aggregator.aggregate_by(current_records, "platform")
        by_campaign = self._aggregator.aggregate_by(current_records, "campaign_id")

        # Period comparison
        previous_summary = None
        comparison = None
        if previous_records:
            previous_summary = self._aggregator.aggregate_summary(previous_records)
            comparison = self._comparer.compare(current_summary, previous_summary)

        return KPIResult(
            current_period=current_summary,
            previous_period=previous_summary,
            comparison=comparison,
            by_platform=by_platform,
            by_campaign=by_campaign,
            records=current_records,
        )

    @staticmethod
    def _get_previous_records(
        all_records: list[MetricRecord],
        start: date,
        end: date,
        comparison_period: str,
    ) -> list[MetricRecord]:
        period_length = (end - start).days + 1

        if comparison_period == "previous_year":
            prev_end = start.replace(year=start.year - 1) + timedelta(days=period_length - 1)
            prev_start = start.replace(year=start.year - 1)
        else:  # previous_period
            prev_end = start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=period_length - 1)

        return [r for r in all_records if prev_start <= r.date <= prev_end]
