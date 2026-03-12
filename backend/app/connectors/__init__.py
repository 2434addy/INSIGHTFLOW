"""
Marketing platform data connectors.

Each connector fetches campaign metrics from a platform API and
normalizes them into ``MetricRecord`` — the unified schema consumed
by the analytics pipeline.

Usage::

    async with MetaAdsConnector(credentials) as connector:
        records = await connector.fetch_and_normalize(date_start, date_end)
"""

from app.connectors.base_connector import BaseConnector
from app.connectors.google_ads_connector import GoogleAdsConnector
from app.connectors.meta_ads_connector import MetaAdsConnector
from app.connectors.tiktok_ads_connector import TikTokAdsConnector

__all__ = [
    "BaseConnector",
    "GoogleAdsConnector",
    "MetaAdsConnector",
    "TikTokAdsConnector",
]
