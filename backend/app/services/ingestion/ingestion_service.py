"""
Ingestion orchestration service.

Coordinates platform connectors and the normalization layer to sync
marketing data from external platforms into the InsightFlow database.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ExternalServiceError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.campaign import Campaign
from app.models.data_source_connection import DataSourceConnection
from app.models.metrics import Metrics
from app.services.ingestion.base_connector import BaseConnector, PlatformType, RawRecord
from app.services.ingestion.google_ads import GoogleAdsConnector
from app.services.ingestion.google_analytics import GoogleAnalyticsConnector
from app.services.ingestion.meta_ads import MetaAdsConnector
from app.services.ingestion.normalizer import MetricsNormalizer, NormalizedRecord
from app.services.ingestion.shopify import ShopifyConnector

logger = get_logger(__name__)


class IngestionService:
    """
    Orchestrates data ingestion from marketing platforms.

    Responsibilities:
    - Resolve connection credentials and create the right connector
    - Run connector to fetch raw data
    - Normalize raw records
    - Upsert campaigns and metrics into the database
    - Track sync job status
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def sync_connection(
        self,
        connection_id: UUID,
        date_start: date,
        date_end: date,
        campaign_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Run a full sync for a data source connection.

        Steps:
        1. Load connection credentials
        2. Create platform connector
        3. Fetch campaigns and metrics
        4. Normalize raw data
        5. Upsert to database

        Returns sync result summary.
        """
        # Load connection
        connection = await self._get_connection(connection_id)

        await logger.ainfo(
            "Starting data sync",
            connection_id=str(connection_id),
            platform=connection.platform,
            date_start=date_start.isoformat(),
            date_end=date_end.isoformat(),
        )

        # Create connector and fetch data
        connector = self._create_connector(connection)

        async with connector:
            # Validate connection is still alive
            is_valid = await connector.validate_connection()
            if not is_valid:
                await self._mark_connection_error(connection, "Token validation failed")
                raise ExternalServiceError(
                    connection.platform,
                    "Connection credentials are invalid or expired",
                )

            # Fetch and sync campaigns
            raw_campaigns = await connector.fetch_campaigns()
            campaigns_synced = await self._upsert_campaigns(
                connection, raw_campaigns
            )

            # Fetch raw metrics
            raw_records = await connector.fetch_metrics(
                date_start, date_end, campaign_ids
            )

            # Normalize
            normalizer = MetricsNormalizer(
                organization_id=connection.organization_id,
                connection_id=connection.id,
            )
            result = normalizer.normalize_batch(raw_records)

            # Persist normalized metrics
            metrics_upserted = await self._upsert_metrics(
                connection, result.valid_records
            )

            # Update connection sync timestamp
            connection.last_synced_at = datetime.now(UTC)
            connection.status = "active"
            await self.db.flush()

        summary = {
            "connection_id": str(connection_id),
            "platform": connection.platform,
            "date_range": f"{date_start} to {date_end}",
            "campaigns_synced": campaigns_synced,
            "raw_records_fetched": len(raw_records),
            "records_normalized": len(result.valid_records),
            "records_rejected": result.rejected_count,
            "metrics_upserted": metrics_upserted,
        }

        await logger.ainfo("Data sync completed", **summary)
        return summary

    async def validate_connection(self, connection_id: UUID) -> bool:
        """Test if a connection's credentials are still valid."""
        connection = await self._get_connection(connection_id)
        connector = self._create_connector(connection)

        async with connector:
            return await connector.validate_connection()

    # ── Private helpers ───────────────────────────────────

    async def _get_connection(self, connection_id: UUID) -> DataSourceConnection:
        """Load a data source connection by ID."""
        result = await self.db.execute(
            select(DataSourceConnection)
            .where(DataSourceConnection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        if not connection:
            raise NotFoundError("DataSourceConnection", str(connection_id))
        return connection

    def _create_connector(self, connection: DataSourceConnection) -> BaseConnector:
        """Factory: create the right connector based on platform type."""
        # In production, tokens would be decrypted from encrypted_access_token
        # using the wrapped_dek. For now we use a placeholder.
        access_token = self._decrypt_token(connection.encrypted_access_token)
        refresh_token = (
            self._decrypt_token(connection.encrypted_refresh_token)
            if connection.encrypted_refresh_token
            else None
        )

        platform = connection.platform
        config = connection.config or {}

        if platform == PlatformType.META_ADS.value:
            return MetaAdsConnector(
                connection_id=connection.id,
                organization_id=connection.organization_id,
                access_token=access_token,
                refresh_token=refresh_token,
                account_id=connection.account_id,
            )
        elif platform == PlatformType.GOOGLE_ADS.value:
            return GoogleAdsConnector(
                connection_id=connection.id,
                organization_id=connection.organization_id,
                access_token=access_token,
                refresh_token=refresh_token,
                account_id=connection.account_id,
                developer_token=config.get("developer_token", ""),
                manager_customer_id=config.get("manager_customer_id"),
            )
        elif platform == PlatformType.SHOPIFY.value:
            return ShopifyConnector(
                connection_id=connection.id,
                organization_id=connection.organization_id,
                access_token=access_token,
                refresh_token=refresh_token,
                account_id=connection.account_id,
            )
        elif platform == PlatformType.GA4.value:
            return GoogleAnalyticsConnector(
                connection_id=connection.id,
                organization_id=connection.organization_id,
                access_token=access_token,
                refresh_token=refresh_token,
                account_id=connection.account_id,
            )
        else:
            raise ValidationError(f"Unsupported platform: {platform}")

    def _decrypt_token(self, encrypted: bytes) -> str:
        """
        Decrypt an OAuth token.

        TODO: Implement AES-256-GCM decryption using the wrapped DEK.
        For now, treat the bytes as a plain UTF-8 string for development.
        """
        return encrypted.decode("utf-8")

    async def _upsert_campaigns(
        self,
        connection: DataSourceConnection,
        raw_campaigns: list[dict[str, Any]],
    ) -> int:
        """Upsert campaigns from platform data into the database."""
        count = 0

        for raw in raw_campaigns:
            platform_id = str(raw.get("id", ""))
            if not platform_id:
                continue

            # Check if campaign already exists
            result = await self.db.execute(
                select(Campaign)
                .where(Campaign.connection_id == connection.id)
                .where(Campaign.platform_campaign_id == platform_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing campaign
                existing.name = raw.get("name", existing.name)
                existing.status = raw.get("status", existing.status)
                existing.campaign_type = raw.get(
                    "channel_type",
                    raw.get("objective", existing.campaign_type),
                )
            else:
                # Create new campaign
                campaign = Campaign(
                    organization_id=connection.organization_id,
                    connection_id=connection.id,
                    platform=connection.platform,
                    platform_campaign_id=platform_id,
                    name=raw.get("name", f"Campaign {platform_id}"),
                    status=raw.get("status"),
                    campaign_type=raw.get("channel_type", raw.get("objective")),
                )
                self.db.add(campaign)
                count += 1

        await self.db.flush()
        return count

    async def _upsert_metrics(
        self,
        connection: DataSourceConnection,
        records: list[NormalizedRecord],
    ) -> int:
        """
        Upsert normalized metrics into the database.

        Uses campaign_id + date + granularity as the natural key for upserts.
        """
        count = 0

        # Build a campaign lookup: platform_campaign_id → Campaign.id
        campaign_lookup = await self._build_campaign_lookup(connection.id)

        for record in records:
            db_campaign_id = campaign_lookup.get(record.campaign_id)

            # Check for existing metric row
            query = (
                select(Metrics)
                .where(Metrics.connection_id == connection.id)
                .where(Metrics.date == record.date)
                .where(Metrics.granularity == record.granularity)
                .where(Metrics.platform == record.platform)
            )
            if db_campaign_id:
                query = query.where(Metrics.campaign_id == db_campaign_id)

            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing metrics
                existing.impressions = record.impressions
                existing.clicks = record.clicks
                existing.spend = record.spend
                existing.conversions = record.conversions
                existing.conversion_value = record.conversion_value
                existing.ctr = record.ctr
                existing.cpc = record.cpc
                existing.cpa = record.cpa
                existing.roas = record.roas
                existing.platform_data = record.platform_data
            else:
                # Create new metrics row
                metric = Metrics(
                    organization_id=record.organization_id,
                    campaign_id=db_campaign_id,
                    connection_id=record.connection_id,
                    platform=record.platform,
                    date=record.date,
                    granularity=record.granularity,
                    impressions=record.impressions,
                    clicks=record.clicks,
                    spend=record.spend,
                    conversions=record.conversions,
                    conversion_value=record.conversion_value,
                    ctr=record.ctr,
                    cpc=record.cpc,
                    cpa=record.cpa,
                    roas=record.roas,
                    platform_data=record.platform_data,
                )
                self.db.add(metric)
                count += 1

        await self.db.flush()
        return count

    async def _build_campaign_lookup(
        self, connection_id: UUID
    ) -> dict[str, UUID]:
        """Build a lookup from platform campaign ID → database UUID."""
        result = await self.db.execute(
            select(Campaign.platform_campaign_id, Campaign.id)
            .where(Campaign.connection_id == connection_id)
        )
        return {row[0]: row[1] for row in result.all()}

    async def _mark_connection_error(
        self, connection: DataSourceConnection, error: str
    ) -> None:
        """Mark a connection as errored."""
        connection.status = "error"
        await self.db.flush()
        await logger.aerror(
            "Connection marked as error",
            connection_id=str(connection.id),
            platform=connection.platform,
            error=error,
        )
