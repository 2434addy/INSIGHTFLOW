"""
TikTok Ads API connector.

Implements the TikTok Marketing API v1.3 for campaign and metrics ingestion.
Normalizes responses directly into ``MetricRecord``.

Rate limit: 600 calls / minute per app.
Pagination: page-number based (up to 1 000 rows/page).
Cost values: returned as floats in the advertiser's currency.

API docs: https://business-api.tiktok.com/marketing_api/docs
"""

from __future__ import annotations

import logging
import uuid
from datetime import date
from typing import Any
from uuid import UUID

from app.connectors.base_connector import BaseConnector
from app.pipeline.schemas import MetricRecord
from app.services.ingestion.base_connector import PlatformType

logger = logging.getLogger(__name__)

TIKTOK_API_VERSION = "v1.3"
TIKTOK_API_BASE = f"https://business-api.tiktok.com/open_api/{TIKTOK_API_VERSION}"

# Metrics requested from the Reporting API
REPORT_METRICS = [
    "spend",
    "impressions",
    "clicks",
    "conversion",
    "complete_payment",           # purchase conversions
    "total_complete_payment_rate",
    "complete_payment_roas",
    "cost_per_conversion",
]

REPORT_DIMENSIONS = ["campaign_id", "stat_time_day"]


class TikTokAdsConnector(BaseConnector):
    """
    Connector for TikTok Ads (TikTok for Business Marketing API).

    Uses the Reporting API for metrics and Campaign Management API
    for campaign listing.  Advertiser ID is required for all calls.
    """

    PLATFORM = PlatformType.TIKTOK_ADS

    def __init__(
        self,
        connection_id: UUID,
        organization_id: UUID,
        access_token: str,
        refresh_token: str | None = None,
        account_id: str = "",  # TikTok "advertiser_id"
    ) -> None:
        super().__init__(
            connection_id=connection_id,
            organization_id=organization_id,
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=account_id,
            rate_limit_calls=600,
            rate_limit_period=60.0,
        )

    def _headers(self) -> dict[str, str]:
        return {"Access-Token": self.access_token}

    # ── Connection validation ─────────────────────────────────

    async def validate_connection(self) -> bool:
        """Verify the access token by fetching advertiser info."""
        try:
            data = await self._get(
                f"{TIKTOK_API_BASE}/advertiser/info/",
                headers=self._headers(),
                params={"advertiser_ids": f'["{self.account_id}"]'},
            )
            return data.get("code") == 0
        except Exception:
            return False

    # ── Campaign listing ──────────────────────────────────────

    async def _fetch_campaigns_raw(self) -> list[dict[str, Any]]:
        campaigns: list[dict[str, Any]] = []
        page = 1
        page_size = 1000

        while True:
            data = await self._get(
                f"{TIKTOK_API_BASE}/campaign/get/",
                headers=self._headers(),
                params={
                    "advertiser_id": self.account_id,
                    "page": page,
                    "page_size": page_size,
                    "fields": '["campaign_id","campaign_name","status",'
                              '"objective_type","budget","budget_mode"]',
                },
            )

            body = data.get("data", {})
            page_list = body.get("list") or []
            campaigns.extend(page_list)

            total_page = body.get("page_info", {}).get("total_page", 1)
            if page >= total_page:
                break
            page += 1

        logger.info(
            "TikTok: fetched %d campaigns for advertiser %s",
            len(campaigns),
            self.account_id,
        )
        return campaigns

    # ── Metrics fetching ──────────────────────────────────────

    async def _fetch_metrics_raw(
        self,
        date_start: date,
        date_end: date,
        campaign_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        page = 1
        page_size = 1000

        params: dict[str, Any] = {
            "advertiser_id": self.account_id,
            "report_type": "BASIC",
            "data_level": "AUCTION_CAMPAIGN",
            "dimensions": str(REPORT_DIMENSIONS),
            "metrics": str(REPORT_METRICS),
            "start_date": date_start.strftime("%Y-%m-%d"),
            "end_date": date_end.strftime("%Y-%m-%d"),
            "page_size": page_size,
            "lifetime": False,
        }

        if campaign_ids:
            filters = [
                {
                    "field_name": "campaign_ids",
                    "filter_type": "IN",
                    "filter_value": campaign_ids,
                }
            ]
            params["filtering"] = str(filters)

        while True:
            params["page"] = page
            data = await self._get(
                f"{TIKTOK_API_BASE}/report/integrated/get/",
                headers=self._headers(),
                params=params,
            )

            body = data.get("data", {})
            page_list = body.get("list") or []
            rows.extend(page_list)

            total_page = body.get("page_info", {}).get("total_page", 1)
            if page >= total_page:
                break
            page += 1

        logger.info(
            "TikTok: fetched %d report rows for %s → %s",
            len(rows),
            date_start,
            date_end,
        )
        return rows

    # ── Row normalization ─────────────────────────────────────

    def _parse_metric_row(self, row: dict[str, Any]) -> MetricRecord:
        """
        Parse a TikTok Reporting API row.

        TikTok's response shape::

            {
                "dimensions": {"campaign_id": "...", "stat_time_day": "2026-03-01 00:00:00"},
                "metrics": {"spend": "12.50", "impressions": "1000", ...}
            }

        Metric values are returned as **strings** and must be cast.
        """
        dims = row.get("dimensions", {})
        metrics = row.get("metrics", {})

        campaign_id_str = dims.get("campaign_id", "")
        stat_date_str = dims.get("stat_time_day", "1970-01-01 00:00:00")
        row_date = date.fromisoformat(stat_date_str.split(" ")[0])

        return MetricRecord(
            campaign_id=_deterministic_uuid(self.PLATFORM.value, campaign_id_str),
            campaign_name="",  # Name not returned in reporting; resolved via campaigns list
            platform=self.PLATFORM.value,
            date=row_date,
            organization_id=self.organization_id,
            impressions=int(float(metrics.get("impressions", 0))),
            clicks=int(float(metrics.get("clicks", 0))),
            spend=float(metrics.get("spend", 0)),
            conversions=int(float(metrics.get("conversion", 0))),
            conversion_value=float(metrics.get("complete_payment", 0)),
        )


def _deterministic_uuid(namespace: str, external_id: str) -> uuid.UUID:
    """Derive a stable UUID from a platform + external campaign ID."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"{namespace}:{external_id}")
