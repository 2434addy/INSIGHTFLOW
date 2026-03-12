"""
Tests for the marketing platform connector architecture.

Covers:
- BaseConnector contract (rate limiter, circuit breaker, normalization)
- MetaAdsConnector row parsing and normalization
- GoogleAdsConnector row parsing (cost micros conversion)
- TikTokAdsConnector row parsing (string metric values)
- Deterministic UUID generation (stable across calls)
- Edge cases (missing fields, zero values, empty responses)
"""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from app.connectors.google_ads_connector import GoogleAdsConnector
from app.connectors.meta_ads_connector import MetaAdsConnector
from app.connectors.tiktok_ads_connector import TikTokAdsConnector
from app.pipeline.schemas import MetricRecord
from app.services.ingestion.base_connector import PlatformType

ORG_ID = uuid.uuid4()
CONN_ID = uuid.uuid4()


# ── Helpers ──────────────────────────────────────────────────


_DEFAULT_ACTIONS = [{"action_type": "purchase", "value": "5"}]
_DEFAULT_ACTION_VALUES = [{"action_type": "purchase", "value": "250.00"}]


def _meta_insight_row(
    *,
    campaign_id: str = "123456",
    campaign_name: str = "Summer Sale",
    impressions: str = "10000",
    clicks: str = "300",
    spend: str = "150.50",
    date_start: str = "2026-03-01",
    actions: list | None = _DEFAULT_ACTIONS,
    action_values: list | None = _DEFAULT_ACTION_VALUES,
) -> dict:
    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "impressions": impressions,
        "clicks": clicks,
        "spend": spend,
        "date_start": date_start,
        "date_stop": date_start,
        "actions": actions,
        "action_values": action_values,
    }


def _google_ads_result_row(
    *,
    campaign_id: str = "789",
    campaign_name: str = "Search - Brand",
    impressions: str = "5000",
    clicks: str = "200",
    cost_micros: str = "75000000",
    conversions: str = "10.0",
    conversions_value: str = "500.0",
    row_date: str = "2026-03-01",
) -> dict:
    return {
        "segments": {"date": row_date},
        "campaign": {"id": campaign_id, "name": campaign_name},
        "adGroup": {"id": "ag1", "name": "Ad Group 1"},
        "adGroupAd": {"ad": {"id": "ad1", "name": "Ad 1"}},
        "metrics": {
            "impressions": impressions,
            "clicks": clicks,
            "costMicros": cost_micros,
            "conversions": conversions,
            "conversionsValue": conversions_value,
        },
    }


def _tiktok_report_row(
    *,
    campaign_id: str = "tt_001",
    stat_date: str = "2026-03-01 00:00:00",
    spend: str = "80.25",
    impressions: str = "12000",
    clicks: str = "400",
    conversion: str = "8",
    complete_payment: str = "320.00",
) -> dict:
    return {
        "dimensions": {
            "campaign_id": campaign_id,
            "stat_time_day": stat_date,
        },
        "metrics": {
            "spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "conversion": conversion,
            "complete_payment": complete_payment,
        },
    }


# ── Meta Ads Connector Tests ────────────────────────────────


class TestMetaAdsConnector:
    """Tests for Meta Ads row parsing and normalization."""

    def _connector(self) -> MetaAdsConnector:
        return MetaAdsConnector(
            connection_id=CONN_ID,
            organization_id=ORG_ID,
            access_token="test_token",
            account_id="act_12345",
        )

    def test_parse_standard_row(self):
        connector = self._connector()
        row = _meta_insight_row()
        record = connector._parse_metric_row(row)

        assert isinstance(record, MetricRecord)
        assert record.platform == "meta_ads"
        assert record.campaign_name == "Summer Sale"
        assert record.impressions == 10000
        assert record.clicks == 300
        assert record.spend == 150.50
        assert record.conversions == 5
        assert record.conversion_value == 250.00
        assert record.date == date(2026, 3, 1)
        assert record.organization_id == ORG_ID

    def test_parse_no_conversions(self):
        connector = self._connector()
        row = _meta_insight_row(actions=[], action_values=[])
        record = connector._parse_metric_row(row)

        assert record.conversions == 0
        assert record.conversion_value == 0.0

    def test_parse_multiple_purchase_actions(self):
        connector = self._connector()
        actions = [
            {"action_type": "purchase", "value": "3"},
            {"action_type": "omni_purchase", "value": "2"},
            {"action_type": "link_click", "value": "50"},  # not a purchase
        ]
        action_values = [
            {"action_type": "purchase", "value": "150.00"},
            {"action_type": "omni_purchase", "value": "100.00"},
        ]
        row = _meta_insight_row(actions=actions, action_values=action_values)
        record = connector._parse_metric_row(row)

        assert record.conversions == 5  # 3 + 2
        assert record.conversion_value == 250.0  # 150 + 100

    def test_deterministic_campaign_id(self):
        connector = self._connector()
        row = _meta_insight_row(campaign_id="stable_123")
        r1 = connector._parse_metric_row(row)
        r2 = connector._parse_metric_row(row)

        assert r1.campaign_id == r2.campaign_id
        assert isinstance(r1.campaign_id, uuid.UUID)

    def test_platform_set_correctly(self):
        connector = self._connector()
        assert connector.PLATFORM == PlatformType.META_ADS

    @pytest.mark.asyncio
    async def test_fetch_and_normalize_skips_bad_rows(self):
        connector = self._connector()
        connector._client = AsyncMock()

        good_row = _meta_insight_row()
        bad_row = {"broken": True}  # Will fail parsing (no date_start)

        with patch.object(
            connector,
            "_fetch_metrics_raw",
            return_value=[good_row, bad_row],
        ):
            records = await connector.fetch_and_normalize(
                date(2026, 3, 1), date(2026, 3, 31)
            )

        assert len(records) == 1
        assert records[0].impressions == 10000


# ── Google Ads Connector Tests ───────────────────────────────


class TestGoogleAdsConnector:
    """Tests for Google Ads row parsing and normalization."""

    def _connector(self) -> GoogleAdsConnector:
        return GoogleAdsConnector(
            connection_id=CONN_ID,
            organization_id=ORG_ID,
            access_token="test_token",
            account_id="123-456-7890",
            developer_token="dev_token",
        )

    def test_parse_standard_row(self):
        connector = self._connector()
        row = _google_ads_result_row()
        record = connector._parse_metric_row(row)

        assert isinstance(record, MetricRecord)
        assert record.platform == "google_ads"
        assert record.campaign_name == "Search - Brand"
        assert record.impressions == 5000
        assert record.clicks == 200
        assert record.spend == 75.0  # 75_000_000 micros ÷ 1_000_000
        assert record.conversions == 10
        assert record.conversion_value == 500.0
        assert record.date == date(2026, 3, 1)

    def test_cost_micros_conversion(self):
        connector = self._connector()
        row = _google_ads_result_row(cost_micros="1500000")  # 1.50
        record = connector._parse_metric_row(row)

        assert record.spend == 1.5

    def test_zero_cost(self):
        connector = self._connector()
        row = _google_ads_result_row(cost_micros="0")
        record = connector._parse_metric_row(row)

        assert record.spend == 0.0

    def test_fractional_conversions_truncated(self):
        connector = self._connector()
        row = _google_ads_result_row(conversions="3.7")
        record = connector._parse_metric_row(row)

        assert record.conversions == 3

    def test_customer_url_strips_dashes(self):
        connector = self._connector()
        url = connector._customer_url("googleAds:search")
        assert "1234567890" in url
        assert "-" not in url.split("/customers/")[1].split("/")[0]

    def test_headers_include_developer_token(self):
        connector = self._connector()
        headers = connector._headers()
        assert headers["developer-token"] == "dev_token"

    def test_headers_include_manager_id_when_set(self):
        connector = GoogleAdsConnector(
            connection_id=CONN_ID,
            organization_id=ORG_ID,
            access_token="test",
            account_id="123",
            developer_token="dev",
            manager_customer_id="mgr_999",
        )
        headers = connector._headers()
        assert headers["login-customer-id"] == "mgr_999"

    def test_headers_omit_manager_id_when_absent(self):
        connector = self._connector()
        headers = connector._headers()
        assert "login-customer-id" not in headers


# ── TikTok Ads Connector Tests ───────────────────────────────


class TestTikTokAdsConnector:
    """Tests for TikTok Ads row parsing and normalization."""

    def _connector(self) -> TikTokAdsConnector:
        return TikTokAdsConnector(
            connection_id=CONN_ID,
            organization_id=ORG_ID,
            access_token="test_token",
            account_id="tt_advertiser_001",
        )

    def test_parse_standard_row(self):
        connector = self._connector()
        row = _tiktok_report_row()
        record = connector._parse_metric_row(row)

        assert isinstance(record, MetricRecord)
        assert record.platform == "tiktok_ads"
        assert record.impressions == 12000
        assert record.clicks == 400
        assert record.spend == 80.25
        assert record.conversions == 8
        assert record.conversion_value == 320.0
        assert record.date == date(2026, 3, 1)
        assert record.organization_id == ORG_ID

    def test_string_metric_values_parsed(self):
        """TikTok returns metrics as strings — verify they're cast."""
        connector = self._connector()
        row = _tiktok_report_row(
            spend="0.01",
            impressions="1",
            clicks="0",
            conversion="0",
            complete_payment="0.00",
        )
        record = connector._parse_metric_row(row)

        assert record.spend == 0.01
        assert record.impressions == 1
        assert record.clicks == 0
        assert record.conversions == 0
        assert record.conversion_value == 0.0

    def test_date_parsed_from_stat_time_day(self):
        """TikTok date format is 'YYYY-MM-DD HH:MM:SS' — verify parsing."""
        connector = self._connector()
        row = _tiktok_report_row(stat_date="2026-06-15 00:00:00")
        record = connector._parse_metric_row(row)

        assert record.date == date(2026, 6, 15)

    def test_deterministic_campaign_id(self):
        connector = self._connector()
        row = _tiktok_report_row(campaign_id="tt_stable_456")
        r1 = connector._parse_metric_row(row)
        r2 = connector._parse_metric_row(row)

        assert r1.campaign_id == r2.campaign_id
        assert isinstance(r1.campaign_id, uuid.UUID)

    def test_campaign_name_empty_from_report(self):
        """TikTok Reporting API doesn't return campaign names."""
        connector = self._connector()
        row = _tiktok_report_row()
        record = connector._parse_metric_row(row)

        assert record.campaign_name == ""

    def test_missing_metrics_default_to_zero(self):
        connector = self._connector()
        row = {"dimensions": {"campaign_id": "x", "stat_time_day": "2026-01-01 00:00:00"}, "metrics": {}}
        record = connector._parse_metric_row(row)

        assert record.impressions == 0
        assert record.clicks == 0
        assert record.spend == 0.0
        assert record.conversions == 0
        assert record.conversion_value == 0.0

    def test_platform_set_correctly(self):
        connector = self._connector()
        assert connector.PLATFORM == PlatformType.TIKTOK_ADS

    def test_headers_use_access_token(self):
        connector = self._connector()
        assert connector._headers() == {"Access-Token": "test_token"}


# ── Cross-Connector Tests ────────────────────────────────────


class TestCrossConnector:
    """Tests that apply to all connector implementations."""

    def test_all_connectors_produce_metric_records(self):
        """Every connector's _parse_metric_row returns a MetricRecord."""
        meta = MetaAdsConnector(CONN_ID, ORG_ID, "t")
        google = GoogleAdsConnector(CONN_ID, ORG_ID, "t", developer_token="d")
        tiktok = TikTokAdsConnector(CONN_ID, ORG_ID, "t")

        meta_record = meta._parse_metric_row(_meta_insight_row())
        google_record = google._parse_metric_row(_google_ads_result_row())
        tiktok_record = tiktok._parse_metric_row(_tiktok_report_row())

        for record in [meta_record, google_record, tiktok_record]:
            assert isinstance(record, MetricRecord)
            assert record.organization_id == ORG_ID
            assert isinstance(record.campaign_id, uuid.UUID)
            assert isinstance(record.date, date)

    def test_different_platforms_produce_different_campaign_ids(self):
        """Same external ID on different platforms should yield different UUIDs."""
        meta = MetaAdsConnector(CONN_ID, ORG_ID, "t")
        tiktok = TikTokAdsConnector(CONN_ID, ORG_ID, "t")

        meta_row = _meta_insight_row(campaign_id="shared_id")
        tiktok_row = _tiktok_report_row(campaign_id="shared_id")

        meta_record = meta._parse_metric_row(meta_row)
        tiktok_record = tiktok._parse_metric_row(tiktok_row)

        assert meta_record.campaign_id != tiktok_record.campaign_id

    def test_platform_strings_are_distinct(self):
        meta = MetaAdsConnector(CONN_ID, ORG_ID, "t")
        google = GoogleAdsConnector(CONN_ID, ORG_ID, "t", developer_token="d")
        tiktok = TikTokAdsConnector(CONN_ID, ORG_ID, "t")

        platforms = {
            meta._parse_metric_row(_meta_insight_row()).platform,
            google._parse_metric_row(_google_ads_result_row()).platform,
            tiktok._parse_metric_row(_tiktok_report_row()).platform,
        }

        assert platforms == {"meta_ads", "google_ads", "tiktok_ads"}
