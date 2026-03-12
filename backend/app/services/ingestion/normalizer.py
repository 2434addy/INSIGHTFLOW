"""
Metrics normalization layer.

Transforms raw platform-specific records into the unified Metrics model.
Handles:
- Field mapping across platforms
- Derived metric computation (CTR, CPC, CPA, ROAS)
- Data quality validation
- Deduplication via upsert logic
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.services.ingestion.base_connector import PlatformType, RawRecord

logger = get_logger(__name__)


@dataclass
class NormalizedRecord:
    """A validated, normalized metrics record ready for database persistence."""

    organization_id: UUID
    connection_id: UUID
    campaign_id: str
    campaign_name: str
    ad_set_id: str | None
    ad_set_name: str | None
    ad_id: str | None
    ad_name: str | None
    platform: str
    date: date
    granularity: str
    impressions: int
    clicks: int
    spend: Decimal
    conversions: int
    conversion_value: Decimal
    ctr: Decimal | None
    cpc: Decimal | None
    cpa: Decimal | None
    roas: Decimal | None
    platform_data: dict[str, Any]


@dataclass
class ValidationResult:
    """Result of data quality validation on a batch of records."""

    valid_records: list[NormalizedRecord]
    rejected_count: int
    warnings: list[str]


class MetricsNormalizer:
    """
    Normalizes raw platform records into a unified metrics schema.

    Applies the Semantic Metric Layer definitions:
    - CTR = clicks / impressions
    - CPC = spend / clicks
    - CPA = spend / conversions
    - ROAS = conversion_value / spend
    """

    def __init__(
        self,
        organization_id: UUID,
        connection_id: UUID,
    ) -> None:
        self.organization_id = organization_id
        self.connection_id = connection_id

    def normalize_batch(
        self,
        raw_records: list[RawRecord],
        granularity: str = "daily",
    ) -> ValidationResult:
        """
        Normalize and validate a batch of raw records.

        Returns validated records and counts of rejections.
        """
        valid: list[NormalizedRecord] = []
        rejected = 0
        warnings: list[str] = []

        for raw in raw_records:
            issues = self._validate_raw(raw)
            if issues:
                rejected += 1
                warnings.extend(issues)
                continue

            normalized = self._normalize_record(raw, granularity)
            valid.append(normalized)

        if rejected > 0:
            logger.warning(
                "Records rejected during normalization",
                rejected=rejected,
                total=len(raw_records),
                sample_warnings=warnings[:5],
            )

        return ValidationResult(
            valid_records=valid,
            rejected_count=rejected,
            warnings=warnings,
        )

    def _normalize_record(
        self,
        raw: RawRecord,
        granularity: str,
    ) -> NormalizedRecord:
        """Transform a single raw record into a normalized record."""
        spend = Decimal(str(raw.spend))
        conversion_value = Decimal(str(raw.conversion_value))
        impressions = raw.impressions
        clicks = raw.clicks
        conversions = raw.conversions

        # Compute derived metrics with safe division
        ctr = (Decimal(clicks) / Decimal(impressions)) if impressions > 0 else None
        cpc = (spend / Decimal(clicks)) if clicks > 0 else None
        cpa = (spend / Decimal(conversions)) if conversions > 0 else None
        roas = (conversion_value / spend) if spend > 0 else None

        return NormalizedRecord(
            organization_id=self.organization_id,
            connection_id=self.connection_id,
            campaign_id=raw.campaign_id,
            campaign_name=raw.campaign_name,
            ad_set_id=raw.ad_set_id,
            ad_set_name=raw.ad_set_name,
            ad_id=raw.ad_id,
            ad_name=raw.ad_name,
            platform=raw.platform.value,
            date=raw.date,
            granularity=granularity,
            impressions=impressions,
            clicks=clicks,
            spend=spend,
            conversions=conversions,
            conversion_value=conversion_value,
            ctr=ctr,
            cpc=cpc,
            cpa=cpa,
            roas=roas,
            platform_data=raw.extra,
        )

    def _validate_raw(self, raw: RawRecord) -> list[str]:
        """
        Validate a raw record for data quality issues.

        Returns a list of validation issue descriptions (empty = valid).
        """
        issues: list[str] = []

        # Null checks on required fields
        if not raw.campaign_id:
            issues.append(f"Missing campaign_id on {raw.date}")

        # Negative value checks
        if raw.impressions < 0:
            issues.append(f"Negative impressions ({raw.impressions}) for {raw.campaign_id}")
        if raw.clicks < 0:
            issues.append(f"Negative clicks ({raw.clicks}) for {raw.campaign_id}")
        if raw.spend < 0:
            issues.append(f"Negative spend ({raw.spend}) for {raw.campaign_id}")
        if raw.conversions < 0:
            issues.append(f"Negative conversions ({raw.conversions}) for {raw.campaign_id}")

        # Cross-field consistency: clicks should not exceed impressions
        # (for ad platforms where both are tracked)
        if raw.platform in (PlatformType.META_ADS, PlatformType.GOOGLE_ADS):
            if raw.impressions > 0 and raw.clicks > raw.impressions:
                issues.append(
                    f"Clicks ({raw.clicks}) exceed impressions ({raw.impressions}) "
                    f"for {raw.campaign_id}"
                )

        # Date range sanity check
        if raw.date.year < 2020:
            issues.append(f"Suspiciously old date ({raw.date}) for {raw.campaign_id}")

        return issues
