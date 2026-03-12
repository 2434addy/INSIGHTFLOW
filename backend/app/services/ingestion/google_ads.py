"""
Google Ads API connector.

Uses the Google Ads API v17 with GAQL (Google Ads Query Language) for data retrieval.
Rate limit: 1000 operations/day per developer token.
Pagination: page_token based.
"""

from datetime import date
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.services.ingestion.base_connector import BaseConnector, PlatformType, RawRecord

logger = get_logger(__name__)

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
    Connector for Google Ads API.

    Uses GAQL queries via the SearchStream/Search endpoints.
    Cost values are returned in micros (÷ 1,000,000 for actual amount).
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
            rate_limit_period=86400.0,  # Daily limit
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

    async def validate_connection(self) -> bool:
        """Verify credentials by listing accessible customers."""
        try:
            await self._get(
                f"{GOOGLE_ADS_BASE}/customers:listAccessibleCustomers",
                headers=self._headers(),
            )
            return True
        except Exception:
            return False

    async def fetch_campaigns(self) -> list[dict[str, Any]]:
        """Fetch all non-removed campaigns via GAQL."""
        campaigns: list[dict[str, Any]] = []
        url = self._customer_url("googleAds:search")

        payload: dict[str, Any] = {
            "query": CAMPAIGN_QUERY,
            "pageSize": 1000,
        }

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

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
            payload["pageToken"] = next_page_token

        await logger.ainfo(
            "Fetched Google Ads campaigns",
            account_id=self.account_id,
            count=len(campaigns),
        )
        return campaigns

    async def fetch_metrics(
        self,
        date_start: date,
        date_end: date,
        campaign_ids: list[str] | None = None,
    ) -> list[RawRecord]:
        """
        Fetch daily metrics via GAQL query.

        Google Ads returns cost in micros (1,000,000 micros = 1 unit of currency).
        """
        records: list[RawRecord] = []
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

            for result in data.get("results", []):
                records.append(self._parse_result_row(result))

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
            payload["pageToken"] = next_page_token

        await logger.ainfo(
            "Fetched Google Ads metrics",
            account_id=self.account_id,
            date_start=date_start.isoformat(),
            date_end=date_end.isoformat(),
            record_count=len(records),
        )
        return records

    def _parse_result_row(self, result: dict[str, Any]) -> RawRecord:
        """Parse a single GAQL result row into a RawRecord."""
        segments = result.get("segments", {})
        campaign = result.get("campaign", {})
        ad_group = result.get("adGroup", {})
        ad = result.get("adGroupAd", {}).get("ad", {})
        metrics = result.get("metrics", {})

        cost_micros = int(metrics.get("costMicros", 0))

        return RawRecord(
            platform=PlatformType.GOOGLE_ADS,
            date=date.fromisoformat(segments.get("date", "1970-01-01")),
            campaign_id=str(campaign.get("id", "")),
            campaign_name=campaign.get("name", ""),
            ad_set_id=str(ad_group.get("id")) if ad_group.get("id") else None,
            ad_set_name=ad_group.get("name"),
            ad_id=str(ad.get("id")) if ad.get("id") else None,
            ad_name=ad.get("name"),
            impressions=int(metrics.get("impressions", 0)),
            clicks=int(metrics.get("clicks", 0)),
            spend=cost_micros / 1_000_000,
            conversions=int(float(metrics.get("conversions", 0))),
            conversion_value=float(metrics.get("conversionsValue", 0)),
            extra={
                "cost_micros": cost_micros,
                "bidding_strategy": campaign.get("biddingStrategyType"),
            },
        )
