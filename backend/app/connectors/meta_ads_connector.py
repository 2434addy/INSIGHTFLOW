"""
Meta (Facebook / Instagram) Ads connector.

Implements the Marketing API v21.0 for campaign and metrics ingestion.
Normalizes responses directly into ``MetricRecord``.

Rate limit: 200 calls/hour per ad account.
Pagination: cursor-based (``paging.next``).
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

META_API_VERSION = "v21.0"
META_API_BASE = f"https://graph.facebook.com/{META_API_VERSION}"

CAMPAIGN_FIELDS = "id,name,status,objective,daily_budget,lifetime_budget,configured_status"
INSIGHT_FIELDS = (
    "campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,"
    "impressions,clicks,spend,actions,action_values,date_start,date_stop"
)

# Action types that represent purchase conversions
PURCHASE_ACTIONS = frozenset({
    "offsite_conversion.fb_pixel_purchase",
    "purchase",
    "omni_purchase",
})


class MetaAdsConnector(BaseConnector):
    """
    Connector for Meta (Facebook / Instagram) Ads.

    Uses the account-level Insights endpoint with ad-level breakdown
    for efficient batch retrieval.
    """

    PLATFORM = PlatformType.META_ADS

    def __init__(
        self,
        connection_id: UUID,
        organization_id: UUID,
        access_token: str,
        refresh_token: str | None = None,
        account_id: str = "",
    ) -> None:
        super().__init__(
            connection_id=connection_id,
            organization_id=organization_id,
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=account_id,
            rate_limit_calls=200,
            rate_limit_period=3600.0,
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    # ── Connection validation ─────────────────────────────────

    async def validate_connection(self) -> bool:
        try:
            await self._get(
                f"{META_API_BASE}/act_{self.account_id}",
                headers=self._headers(),
                params={"fields": "id,name,account_status"},
            )
            return True
        except Exception:
            return False

    # ── Campaign listing ──────────────────────────────────────

    async def _fetch_campaigns_raw(self) -> list[dict[str, Any]]:
        campaigns: list[dict[str, Any]] = []
        url: str | None = f"{META_API_BASE}/act_{self.account_id}/campaigns"
        params: dict[str, Any] = {"fields": CAMPAIGN_FIELDS, "limit": 500}

        while url:
            data = await self._get(url, headers=self._headers(), params=params)
            campaigns.extend(data.get("data", []))
            url = data.get("paging", {}).get("next")
            params = {}  # Next URL already includes params

        logger.info(
            "Meta: fetched %d campaigns for account %s",
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
        url: str | None = f"{META_API_BASE}/act_{self.account_id}/insights"
        params: dict[str, Any] = {
            "fields": INSIGHT_FIELDS,
            "time_range": (
                f'{{"since":"{date_start.isoformat()}",'
                f'"until":"{date_end.isoformat()}"}}'
            ),
            "time_increment": 1,
            "level": "ad",
            "limit": 500,
        }

        if campaign_ids:
            filtering = [
                {"field": "campaign.id", "operator": "IN", "value": campaign_ids}
            ]
            params["filtering"] = str(filtering)

        while url:
            data = await self._get(url, headers=self._headers(), params=params)
            rows.extend(data.get("data", []))
            url = data.get("paging", {}).get("next")
            params = {}

        logger.info(
            "Meta: fetched %d insight rows for %s → %s",
            len(rows),
            date_start,
            date_end,
        )
        return rows

    # ── Row normalization ─────────────────────────────────────

    def _parse_metric_row(self, row: dict[str, Any]) -> MetricRecord:
        conversions = 0
        conversion_value = 0.0

        for action in row.get("actions") or []:
            if action.get("action_type") in PURCHASE_ACTIONS:
                conversions += int(action.get("value", 0))

        for action_val in row.get("action_values") or []:
            if action_val.get("action_type") in PURCHASE_ACTIONS:
                conversion_value += float(action_val.get("value", 0))

        campaign_id_str = row.get("campaign_id", "")

        return MetricRecord(
            campaign_id=_deterministic_uuid(self.PLATFORM.value, campaign_id_str),
            campaign_name=row.get("campaign_name", ""),
            platform=self.PLATFORM.value,
            date=date.fromisoformat(row["date_start"]),
            organization_id=self.organization_id,
            impressions=int(row.get("impressions", 0)),
            clicks=int(row.get("clicks", 0)),
            spend=float(row.get("spend", 0)),
            conversions=conversions,
            conversion_value=conversion_value,
        )


def _deterministic_uuid(namespace: str, external_id: str) -> uuid.UUID:
    """Derive a stable UUID from a platform + external campaign ID."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"{namespace}:{external_id}")
