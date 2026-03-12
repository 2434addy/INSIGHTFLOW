"""Tests for the metrics normalization layer."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.services.ingestion.base_connector import PlatformType, RawRecord
from app.services.ingestion.normalizer import MetricsNormalizer


ORG_ID = uuid4()
CONN_ID = uuid4()


def _make_normalizer() -> MetricsNormalizer:
    return MetricsNormalizer(organization_id=ORG_ID, connection_id=CONN_ID)


def _make_raw(
    impressions: int = 1000,
    clicks: int = 50,
    spend: float = 100.0,
    conversions: int = 5,
    conversion_value: float = 500.0,
    platform: PlatformType = PlatformType.META_ADS,
    campaign_id: str = "camp_123",
) -> RawRecord:
    return RawRecord(
        platform=platform,
        date=date(2026, 3, 1),
        campaign_id=campaign_id,
        campaign_name="Test Campaign",
        impressions=impressions,
        clicks=clicks,
        spend=spend,
        conversions=conversions,
        conversion_value=conversion_value,
    )


def test_normalize_computes_derived_metrics():
    """Derived metrics (CTR, CPC, CPA, ROAS) are computed correctly."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([_make_raw()])

    assert result.rejected_count == 0
    assert len(result.valid_records) == 1

    rec = result.valid_records[0]
    assert rec.impressions == 1000
    assert rec.clicks == 50
    assert rec.spend == Decimal("100.0")
    assert rec.conversions == 5
    assert rec.conversion_value == Decimal("500.0")

    # CTR = 50 / 1000 = 0.05
    assert rec.ctr == Decimal("50") / Decimal("1000")
    # CPC = 100 / 50 = 2.0
    assert rec.cpc == Decimal("100.0") / Decimal("50")
    # CPA = 100 / 5 = 20.0
    assert rec.cpa == Decimal("100.0") / Decimal("5")
    # ROAS = 500 / 100 = 5.0
    assert rec.roas == Decimal("500.0") / Decimal("100.0")


def test_normalize_handles_zero_impressions():
    """CTR is None when impressions are zero."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([_make_raw(impressions=0, clicks=0)])

    rec = result.valid_records[0]
    assert rec.ctr is None


def test_normalize_handles_zero_clicks():
    """CPC is None when clicks are zero."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([_make_raw(clicks=0)])

    rec = result.valid_records[0]
    assert rec.cpc is None


def test_normalize_handles_zero_conversions():
    """CPA is None when conversions are zero."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([_make_raw(conversions=0)])

    rec = result.valid_records[0]
    assert rec.cpa is None


def test_normalize_handles_zero_spend():
    """ROAS is None when spend is zero."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([_make_raw(spend=0.0)])

    rec = result.valid_records[0]
    assert rec.roas is None


def test_validate_rejects_negative_impressions():
    """Records with negative impressions are rejected."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([_make_raw(impressions=-100)])

    assert result.rejected_count == 1
    assert len(result.valid_records) == 0


def test_validate_rejects_negative_spend():
    """Records with negative spend are rejected."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([_make_raw(spend=-50.0)])

    assert result.rejected_count == 1
    assert len(result.valid_records) == 0


def test_validate_rejects_missing_campaign_id():
    """Records without a campaign_id are rejected."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([_make_raw(campaign_id="")])

    assert result.rejected_count == 1


def test_validate_rejects_clicks_exceeding_impressions():
    """For ad platforms, clicks > impressions is rejected."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([
        _make_raw(impressions=10, clicks=100, platform=PlatformType.META_ADS)
    ])

    assert result.rejected_count == 1


def test_validate_allows_clicks_exceeding_impressions_for_ga4():
    """GA4 sessions/pageviews can have pageviews > sessions, which is valid."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([
        _make_raw(impressions=10, clicks=100, platform=PlatformType.GA4)
    ])

    assert result.rejected_count == 0
    assert len(result.valid_records) == 1


def test_normalize_batch_mixed_valid_and_invalid():
    """Batch with both valid and invalid records processes correctly."""
    normalizer = _make_normalizer()
    records = [
        _make_raw(campaign_id="good_1"),
        _make_raw(campaign_id="", spend=-1),  # Two violations
        _make_raw(campaign_id="good_2"),
    ]
    result = normalizer.normalize_batch(records)

    assert len(result.valid_records) == 2
    assert result.rejected_count == 1


def test_normalize_sets_platform_and_metadata():
    """Normalized record preserves platform and organization context."""
    normalizer = _make_normalizer()
    result = normalizer.normalize_batch([_make_raw()])

    rec = result.valid_records[0]
    assert rec.platform == "meta_ads"
    assert rec.organization_id == ORG_ID
    assert rec.connection_id == CONN_ID
    assert rec.date == date(2026, 3, 1)
    assert rec.granularity == "daily"
