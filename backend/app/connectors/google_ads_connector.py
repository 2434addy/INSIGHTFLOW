"""
Google Ads API connector.

Uses the Google Ads API v17 with GAQL (Google Ads Query Language).
Normalizes responses directly into ``MetricRecord``.

Rate limit: 1 000 operations/day per developer token.
Pagination: page-token based (up to 10 000 rows/request).
Cost values: returned in **micros** (÷ 1 000 000 for actual amount).
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

GOOGLE_ADS_API_VERSION = "v17"
GOOGLE_ADS_BASE = f"https://googleads.googleapis.com/{GOOGLE_ADS_API_VERSION}"

CAMPAIGN_QUERY = """
    SELECT
        campaign.id,
        campaign.name,
        campaign.status,
        campaign.advertising_channel_type,
        campaign.bidding_strategy_type,
        campaign_budget.amount_micros
    FROM campaign
    WHERE campaign.status != 'REMOVED'
    ORDER BY campaign.id
"""

METRICS_QUERY_TEMPLATE = """
    SELECT
        segments.date,
        campaign.id,
        campaign.name,
        ad_group.id,
        ad_group.name,
        ad_group_ad.ad.id,
        ad_group_ad.ad.name,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.conversions,
        metrics.conversions_value
    FROM ad_group_ad
    WHERE segments.date BETWEEN '{date_start}' AND '{date_end}'
    ORDER BY segments.date, campaign.id
"""


class GoogleAdsConnector(BaseConnector):
    """
    Connector for Google Ads.

    Uses GAQL queries via the ``googleAds:search`` endpoint.
    Cost values are returned in micros (÷ 1 000 000).
    """

    PLATFORM = PlatformType.GOOGLE_ADS

    def __init__(
        self,
        connection_id: UUID,
        organization_id: UUID,
        access_token: str,
        refresh_token: str | None = None,
        account_id: str = "",
        developer_token: str = "",
        manager_customer_id: str | None = None,
    ) -> None:
        super().__init__(
            connection_id=connection_id,
            organization_id=organization_id,
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=account_id,
            rate_limit_calls=1000,
            rate_limit_period=86400.0,
        )
        self.developer_token = developer_token
        self.manager_customer_id = manager_customer_id

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "developer-token": self.developer_token,
        }
        if self.manager_customer_id:
            headers["login-customer-id"] = self.manager_customer_id
        return headers

    def _customer_url(self, path: str) -> str:
        customer_id = self.account_id.replace("-", "")
        return f"{GOOGLE_ADS_BASE}/customers/{customer_id}/{path}"

    # ── Connection validation ─────────────────────────────────

    async def validate_connection(self) -> bool:
        try:
            await self._get(
                f"{GOOGLE_ADS_BASE}/customers:listAccessibleCustomers",
                headers=self._headers(),
            )
            return True
        except Exception:
            return False

    # ── Campaign listing ──────────────────────────────────────

    async def _fetch_campaigns_raw(self) -> list[dict[str, Any]]:
        campaigns: list[dict[str, Any]] = []
        url = self._customer_url("googleAds:search")
        payload: dict[str, Any] = {"query": CAMPAIGN_QUERY, "pageSize": 1000}

        while True:
            data = await self._post(url, headers=self._headers(), json=payload)

            for result in data.get("results", []):
                campaign = result.get("campaign", {})
                budget = result.get("campaignBudget", {})
                campaigns.append({
                    "id": campaign.get("id"),
                    "name": campaign.get("name"),
                    "status": campaign.get("status"),
                    "channel_type": campaign.get("advertisingChannelType"),
                    "bidding_strategy": campaign.get("biddingStrategyType"),
                    "budget_micros": budget.get("amountMicros"),
                })

            if not data.get("nextPageToken"):
                break
            payload["pageToken"] = data["nextPageToken"]

        logger.info(
            "Google Ads: fetched %d campaigns for account %s",
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
        url = self._customer_url("googleAds:search")

        query = METRICS_QUERY_TEMPLATE.format(
            date_start=date_start.strftime("%Y-%m-%d"),
            date_end=date_end.strftime("%Y-%m-%d"),
        )

        if campaign_ids:
            ids_str = ", ".join(campaign_ids)
            query = query.replace(
                "ORDER BY segments.date",
                f"AND campaign.id IN ({ids_str})\n    ORDER BY segments.date",
            )

        payload: dict[str, Any] = {"query": query, "pageSize": 10000}

        while True:
            data = await self._post(url, headers=self._headers(), json=payload)
            rows.extend(data.get("results", []))

            if not data.get("nextPageToken"):
                break
            payload["pageToken"] = data["nextPageToken"]

        logger.info(
            "Google Ads: fetched %d metric rows for %s → %s",
            len(rows),
            date_start,
            date_end,
        )
        return rows

    # ── Row normalization ─────────────────────────────────────

    def _parse_metric_row(self, row: dict[str, Any]) -> MetricRecord:
        segments = row.get("segments", {})
        campaign = row.get("campaign", {})
        metrics = row.get("metrics", {})

        campaign_id_str = str(campaign.get("id", ""))
        cost_micros = int(metrics.get("costMicros", 0))

        return MetricRecord(
            campaign_id=_deterministic_uuid(self.PLATFORM.value, campaign_id_str),
            campaign_name=campaign.get("name", ""),
            platform=self.PLATFORM.value,
            date=date.fromisoformat(segments.get("date", "1970-01-01")),
            organization_id=self.organization_id,
            impressions=int(metrics.get("impressions", 0)),
            clicks=int(metrics.get("clicks", 0)),
            spend=cost_micros / 1_000_000,
            conversions=int(float(metrics.get("conversions", 0))),
            conversion_value=float(metrics.get("conversionsValue", 0)),
        )


def _deterministic_uuid(namespace: str, external_id: str) -> uuid.UUID:
    """Derive a stable UUID from a platform + external campaign ID."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"{namespace}:{external_id}")
