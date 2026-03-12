"""Tests for the ingestion orchestration service."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.data_source_connection import DataSourceConnection
from app.models.metrics import Metrics
from app.models.organization import Organization
from app.models.user import User
from app.services.ingestion.ingestion_service import IngestionService


@pytest_asyncio.fixture
async def org_with_connection(db_session: AsyncSession, test_user: User, test_organization: Organization):
    """Create a data source connection for testing."""
    connection = DataSourceConnection(
        id=uuid4(),
        organization_id=test_organization.id,
        platform="meta_ads",
        account_id="act_12345",
        account_name="Test Ad Account",
        encrypted_access_token=b"test_access_token",
        encrypted_refresh_token=b"test_refresh_token",
        wrapped_dek=b"test_dek",
        status="active",
        sync_frequency="daily",
    )
    db_session.add(connection)
    await db_session.commit()
    return test_organization, connection


@pytest.mark.asyncio
async def test_upsert_campaigns(db_session: AsyncSession, org_with_connection):
    """IngestionService upserts campaigns into the database."""
    org, connection = org_with_connection
    service = IngestionService(db_session)

    raw_campaigns = [
        {"id": "camp_001", "name": "Summer Sale", "status": "ACTIVE", "objective": "CONVERSIONS"},
        {"id": "camp_002", "name": "Winter Promo", "status": "PAUSED"},
    ]

    count = await service._upsert_campaigns(connection, raw_campaigns)
    assert count == 2

    # Verify campaigns are in the database
    from sqlalchemy import select
    result = await db_session.execute(
        select(Campaign).where(Campaign.connection_id == connection.id)
    )
    campaigns = result.scalars().all()
    assert len(campaigns) == 2
    assert {c.platform_campaign_id for c in campaigns} == {"camp_001", "camp_002"}


@pytest.mark.asyncio
async def test_upsert_campaigns_updates_existing(db_session: AsyncSession, org_with_connection):
    """Re-syncing campaigns updates existing ones without duplicates."""
    org, connection = org_with_connection
    service = IngestionService(db_session)

    # First sync
    await service._upsert_campaigns(
        connection,
        [{"id": "camp_001", "name": "Original Name", "status": "ACTIVE"}],
    )

    # Second sync with updated name
    count = await service._upsert_campaigns(
        connection,
        [{"id": "camp_001", "name": "Updated Name", "status": "PAUSED"}],
    )
    assert count == 0  # No new campaigns

    from sqlalchemy import select
    result = await db_session.execute(
        select(Campaign)
        .where(Campaign.connection_id == connection.id)
        .where(Campaign.platform_campaign_id == "camp_001")
    )
    campaign = result.scalar_one()
    assert campaign.name == "Updated Name"
    assert campaign.status == "PAUSED"


@pytest.mark.asyncio
async def test_upsert_metrics(db_session: AsyncSession, org_with_connection):
    """IngestionService persists normalized metrics."""
    org, connection = org_with_connection
    service = IngestionService(db_session)

    # Create a campaign first
    campaign = Campaign(
        id=uuid4(),
        organization_id=org.id,
        connection_id=connection.id,
        platform="meta_ads",
        platform_campaign_id="camp_001",
        name="Test Campaign",
    )
    db_session.add(campaign)
    await db_session.commit()

    from app.services.ingestion.normalizer import NormalizedRecord
    records = [
        NormalizedRecord(
            organization_id=org.id,
            connection_id=connection.id,
            campaign_id="camp_001",
            campaign_name="Test Campaign",
            ad_set_id=None,
            ad_set_name=None,
            ad_id=None,
            ad_name=None,
            platform="meta_ads",
            date=date(2026, 3, 1),
            granularity="daily",
            impressions=1000,
            clicks=50,
            spend=Decimal("100.00"),
            conversions=5,
            conversion_value=Decimal("500.00"),
            ctr=Decimal("0.05"),
            cpc=Decimal("2.00"),
            cpa=Decimal("20.00"),
            roas=Decimal("5.00"),
            platform_data={"actions": []},
        ),
    ]

    count = await service._upsert_metrics(connection, records)
    assert count == 1

    from sqlalchemy import select
    result = await db_session.execute(
        select(Metrics).where(Metrics.connection_id == connection.id)
    )
    metric = result.scalar_one()
    assert metric.impressions == 1000
    assert metric.clicks == 50
    assert metric.spend == Decimal("100.00")
    assert metric.roas == Decimal("5.00")


@pytest.mark.asyncio
async def test_build_campaign_lookup(db_session: AsyncSession, org_with_connection):
    """Campaign lookup maps platform IDs to database UUIDs."""
    org, connection = org_with_connection
    service = IngestionService(db_session)

    camp_id = uuid4()
    campaign = Campaign(
        id=camp_id,
        organization_id=org.id,
        connection_id=connection.id,
        platform="meta_ads",
        platform_campaign_id="camp_ext_001",
        name="Lookup Test",
    )
    db_session.add(campaign)
    await db_session.commit()

    lookup = await service._build_campaign_lookup(connection.id)
    assert "camp_ext_001" in lookup
    assert lookup["camp_ext_001"] == camp_id


@pytest.mark.asyncio
async def test_get_connection_not_found(db_session: AsyncSession):
    """Loading a non-existent connection raises NotFoundError."""
    service = IngestionService(db_session)

    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        await service._get_connection(uuid4())
