"""
Google Analytics 4 (GA4) Data API connector.

Uses the GA4 Data API v1 for website analytics metrics.
Rate limit: 10 concurrent requests per property.
Pagination: offset-based with row limits.
"""

from datetime import date
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.services.ingestion.base_connector import BaseConnector, PlatformType, RawRecord

logger = get_logger(__name__)

GA4_API_BASE = "https://analyticsdata.googleapis.com/v1beta"

# Core dimensions and metrics for marketing analytics
GA4_DIMENSIONS = [
    "date",
    "sessionCampaignName",
    "sessionCampaignId",
    "sessionSource",
    "sessionMedium",
]

GA4_METRICS = [
    "sessions",
    "totalUsers",
    "screenPageViews",
    "conversions",
    "ecommercePurchases",
    "totalRevenue",
    "bounceRate",
    "averageSessionDuration",
]


class GoogleAnalyticsConnector(BaseConnector):
    """
    Connector for Google Analytics 4 Data API.

    GA4 uses a request-based API (not query language). Dimensions and metrics
    are specified per request. Results are paginated by row offset.
    """

    PLATFORM = PlatformType.GA4

    def __init__(
        self,
        connection_id: UUID,
        organization_id: UUID,
        access_token: str,
        refresh_token: str | None = None,
        account_id: str = "",  # GA4 property ID (e.g., "properties/123456789")
    ) -> None:
        super().__init__(
            connection_id=connection_id,
            organization_id=organization_id,
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=account_id,
            rate_limit_calls=10,
            rate_limit_period=1.0,  # 10 concurrent per second
        )

    @property
    def _property_id(self) -> str:
        """Ensure property ID is in the correct format."""
        if self.account_id.startswith("properties/"):
            return self.account_id
        return f"properties/{self.account_id}"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    async def validate_connection(self) -> bool:
        """Verify credentials by running a minimal report."""
        try:
            await self._post(
                f"{GA4_API_BASE}/{self._property_id}:runReport",
                headers=self._headers(),
                json={
                    "dateRanges": [{"startDate": "yesterday", "endDate": "yesterday"}],
                    "metrics": [{"name": "sessions"}],
                    "limit": 1,
                },
            )
            return True
        except Exception:
            return False

    async def fetch_campaigns(self) -> list[dict[str, Any]]:
        """
        Fetch distinct campaign names from GA4.

        GA4 doesn't have a campaigns endpoint — we derive campaigns from
        report data using the sessionCampaignName dimension.
        """
        data = await self._post(
            f"{GA4_API_BASE}/{self._property_id}:runReport",
            headers=self._headers(),
            json={
                "dateRanges": [{"startDate": "90daysAgo", "endDate": "today"}],
                "dimensions": [
                    {"name": "sessionCampaignName"},
                    {"name": "sessionCampaignId"},
                    {"name": "sessionSource"},
                    {"name": "sessionMedium"},
                ],
                "metrics": [{"name": "sessions"}],
                "limit": 10000,
            },
        )

        campaigns: list[dict[str, Any]] = []
        seen: set[str] = set()

        for row in data.get("rows", []):
            dims = row.get("dimensionValues", [])
            campaign_name = dims[0].get("value", "(not set)") if len(dims) > 0 else "(not set)"
            campaign_id = dims[1].get("value", "") if len(dims) > 1 else ""

            if campaign_name not in seen and campaign_name != "(not set)":
                seen.add(campaign_name)
                campaigns.append({
                    "id": campaign_id or campaign_name,
                    "name": campaign_name,
                    "source": dims[2].get("value", "") if len(dims) > 2 else "",
                    "medium": dims[3].get("value", "") if len(dims) > 3 else "",
                })

        await logger.ainfo(
            "Fetched GA4 campaigns",
            property_id=self._property_id,
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
        Fetch daily metrics from GA4 Data API.

        Retrieves sessions, pageviews, conversions, and revenue
        broken down by date and campaign.
        """
        records: list[RawRecord] = []
        offset = 0
        page_size = 10000

        request_body: dict[str, Any] = {
            "dateRanges": [{
                "startDate": date_start.isoformat(),
                "endDate": date_end.isoformat(),
            }],
            "dimensions": [{"name": d} for d in GA4_DIMENSIONS],
            "metrics": [{"name": m} for m in GA4_METRICS],
            "limit": page_size,
            "offset": offset,
        }

        if campaign_ids:
            request_body["dimensionFilter"] = {
                "filter": {
                    "fieldName": "sessionCampaignId",
                    "inListFilter": {"values": campaign_ids},
                },
            }

        while True:
            request_body["offset"] = offset
            data = await self._post(
                f"{GA4_API_BASE}/{self._property_id}:runReport",
                headers=self._headers(),
                json=request_body,
            )

            rows = data.get("rows", [])
            if not rows:
                break

            for row in rows:
                record = self._parse_report_row(row)
                if record:
                    records.append(record)

            total_rows = int(data.get("rowCount", 0))
            offset += page_size
            if offset >= total_rows:
                break

        await logger.ainfo(
            "Fetched GA4 metrics",
            property_id=self._property_id,
            date_start=date_start.isoformat(),
            date_end=date_end.isoformat(),
            record_count=len(records),
        )
        return records

    def _parse_report_row(self, row: dict[str, Any]) -> RawRecord | None:
        """Parse a GA4 report row into a RawRecord."""
        dims = row.get("dimensionValues", [])
        mets = row.get("metricValues", [])

        if len(dims) < 5 or len(mets) < 8:
            return None

        row_date = dims[0].get("value", "")
        campaign_name = dims[1].get("value", "(not set)")
        campaign_id = dims[2].get("value", "")
        source = dims[3].get("value", "")
        medium = dims[4].get("value", "")

        if campaign_name == "(not set)":
            campaign_name = f"{source}/{medium}" if source else "direct"
            campaign_id = campaign_id or campaign_name

        sessions = int(mets[0].get("value", 0))
        total_users = int(mets[1].get("value", 0))
        pageviews = int(mets[2].get("value", 0))
        conversions = int(mets[3].get("value", 0))
        purchases = int(mets[4].get("value", 0))
        revenue = float(mets[5].get("value", 0))
        bounce_rate = float(mets[6].get("value", 0))
        avg_session_duration = float(mets[7].get("value", 0))

        # GA4 maps to our unified metrics:
        # impressions → sessions (closest equivalent)
        # clicks → pageviews
        # conversions → ecommerce purchases (or events)
        # conversion_value → totalRevenue

        # Parse date from YYYYMMDD format
        try:
            parsed_date = date(
                int(row_date[:4]),
                int(row_date[4:6]),
                int(row_date[6:8]),
            )
        except (ValueError, IndexError):
            return None

        return RawRecord(
            platform=PlatformType.GA4,
            date=parsed_date,
            campaign_id=campaign_id or campaign_name,
            campaign_name=campaign_name,
            impressions=sessions,  # Sessions as proxy for impressions
            clicks=pageviews,
            spend=0.0,  # GA4 doesn't track ad spend
            conversions=purchases or conversions,
            conversion_value=revenue,
            extra={
                "sessions": sessions,
                "total_users": total_users,
                "pageviews": pageviews,
                "ga4_conversions": conversions,
                "ecommerce_purchases": purchases,
                "bounce_rate": bounce_rate,
                "avg_session_duration": avg_session_duration,
                "source": source,
                "medium": medium,
            },
        )
