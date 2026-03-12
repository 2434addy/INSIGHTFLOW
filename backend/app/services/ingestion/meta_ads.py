"""
Meta (Facebook) Ads API connector.

Implements the Marketing API v21.0 for campaign and metrics ingestion.
Rate limit: 200 calls/hour per ad account.
Pagination: cursor-based.
"""

from datetime import date
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.services.ingestion.base_connector import BaseConnector, PlatformType, RawRecord

logger = get_logger(__name__)

META_API_VERSION = "v21.0"
META_API_BASE = f"https://graph.facebook.com/{META_API_VERSION}"

# Fields to request from the Insights API
CAMPAIGN_FIELDS = "id,name,status,objective,daily_budget,lifetime_budget,configured_status"
INSIGHT_FIELDS = (
    "campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,"
    "impressions,clicks,spend,actions,action_values,date_start,date_stop"
)


class MetaAdsConnector(BaseConnector):
    """
    Connector for Meta (Facebook/Instagram) Ads API.

    Uses the Marketing API Insights endpoint for metrics retrieval.
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

    async def validate_connection(self) -> bool:
        """Verify the access token is valid by fetching account info."""
        try:
            await self._get(
                f"{META_API_BASE}/act_{self.account_id}",
                headers=self._headers(),
                params={"fields": "id,name,account_status"},
            )
            return True
        except Exception:
            return False

    async def fetch_campaigns(self) -> list[dict[str, Any]]:
        """Fetch all campaigns from the Meta ad account."""
        campaigns: list[dict[str, Any]] = []
        url = f"{META_API_BASE}/act_{self.account_id}/campaigns"
        params: dict[str, Any] = {
            "fields": CAMPAIGN_FIELDS,
            "limit": 500,
        }

        while url:
            data = await self._get(url, headers=self._headers(), params=params)
            campaigns.extend(data.get("data", []))

            # Cursor-based pagination
            paging = data.get("paging", {})
            url = paging.get("next")
            params = {}  # Next URL already includes params

            await logger.ainfo(
                "Fetched Meta campaigns page",
                account_id=self.account_id,
                batch_size=len(data.get("data", [])),
                total_so_far=len(campaigns),
            )

        return campaigns

    async def fetch_metrics(
        self,
        date_start: date,
        date_end: date,
        campaign_ids: list[str] | None = None,
    ) -> list[RawRecord]:
        """
        Fetch daily insights from Meta Ads Insights API.

        Uses the ad account-level insights endpoint with campaign
        breakdown for efficient batch retrieval.
        """
        records: list[RawRecord] = []
        url = f"{META_API_BASE}/act_{self.account_id}/insights"
        params: dict[str, Any] = {
            "fields": INSIGHT_FIELDS,
            "time_range": f'{{"since":"{date_start.isoformat()}","until":"{date_end.isoformat()}"}}',
            "time_increment": 1,  # Daily breakdown
            "level": "ad",
            "limit": 500,
        }

        if campaign_ids:
            filtering = [{"field": "campaign.id", "operator": "IN", "value": campaign_ids}]
            params["filtering"] = str(filtering)

        while url:
            data = await self._get(url, headers=self._headers(), params=params)

            for row in data.get("data", []):
                records.append(self._parse_insight_row(row))

            paging = data.get("paging", {})
            url = paging.get("next")
            params = {}

        await logger.ainfo(
            "Fetched Meta metrics",
            account_id=self.account_id,
            date_start=date_start.isoformat(),
            date_end=date_end.isoformat(),
            record_count=len(records),
        )
        return records

    def _parse_insight_row(self, row: dict[str, Any]) -> RawRecord:
        """Parse a single Meta Insights API row into a RawRecord."""
        # Extract conversions from the 'actions' array
        conversions = 0
        conversion_value = 0.0
        actions = row.get("actions") or []
        action_values = row.get("action_values") or []

        for action in actions:
            if action.get("action_type") in (
                "offsite_conversion.fb_pixel_purchase",
                "purchase",
                "omni_purchase",
            ):
                conversions += int(action.get("value", 0))

        for action_val in action_values:
            if action_val.get("action_type") in (
                "offsite_conversion.fb_pixel_purchase",
                "purchase",
                "omni_purchase",
            ):
                conversion_value += float(action_val.get("value", 0))

        return RawRecord(
            platform=PlatformType.META_ADS,
            date=date.fromisoformat(row["date_start"]),
            campaign_id=row.get("campaign_id", ""),
            campaign_name=row.get("campaign_name", ""),
            ad_set_id=row.get("adset_id"),
            ad_set_name=row.get("adset_name"),
            ad_id=row.get("ad_id"),
            ad_name=row.get("ad_name"),
            impressions=int(row.get("impressions", 0)),
            clicks=int(row.get("clicks", 0)),
            spend=float(row.get("spend", 0)),
            conversions=conversions,
            conversion_value=conversion_value,
            extra={
                "actions": actions,
                "action_values": action_values,
            },
        )
