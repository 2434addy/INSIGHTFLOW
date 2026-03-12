"""
Base connector — abstract interface for all marketing platform connectors.

Provides:
- Async HTTP client lifecycle (context manager)
- Token-bucket rate limiting
- Circuit breaker (CLOSED → OPEN → HALF_OPEN)
- Exponential-backoff retries
- Built-in normalization from platform-specific responses to ``MetricRecord``

Subclasses implement three hooks:
    ``_fetch_campaigns_raw``  — platform-specific campaign listing
    ``_fetch_metrics_raw``    — platform-specific metric retrieval
    ``_parse_metric_row``     — convert one API row into a ``MetricRecord``
    ``validate_connection``   — verify OAuth credentials are live
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import date
from typing import Any
from uuid import UUID

import httpx

from app.core.exceptions import ExternalServiceError, RateLimitError
from app.pipeline.schemas import MetricRecord
from app.services.ingestion.base_connector import (
    CircuitBreaker,
    PlatformType,
    RateLimiter,
)

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Abstract base connector for marketing platform APIs.

    Subclasses must set ``PLATFORM`` and implement the four abstract
    methods listed above.  All public methods return data already
    normalized into the pipeline's ``MetricRecord`` schema.
    """

    PLATFORM: PlatformType

    def __init__(
        self,
        connection_id: UUID,
        organization_id: UUID,
        access_token: str,
        refresh_token: str | None = None,
        account_id: str = "",
        *,
        rate_limit_calls: int = 100,
        rate_limit_period: float = 3600.0,
        max_retries: int = 3,
        base_retry_delay: float = 1.0,
    ) -> None:
        self.connection_id = connection_id
        self.organization_id = organization_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.account_id = account_id
        self.max_retries = max_retries
        self.base_retry_delay = base_retry_delay

        self._rate_limiter = RateLimiter(
            max_calls=rate_limit_calls,
            period_seconds=rate_limit_period,
        )
        self._circuit_breaker = CircuitBreaker()
        self._client: httpx.AsyncClient | None = None

    # ── Async context manager ─────────────────────────────────

    async def __aenter__(self) -> BaseConnector:
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Connector must be used as an async context manager")
        return self._client

    # ── Public API ────────────────────────────────────────────

    async def fetch_and_normalize(
        self,
        date_start: date,
        date_end: date,
        campaign_ids: list[str] | None = None,
    ) -> list[MetricRecord]:
        """
        Fetch metrics from the platform and normalize to ``MetricRecord``.

        This is the primary entry point that downstream code should call.
        """
        raw_rows = await self._fetch_metrics_raw(date_start, date_end, campaign_ids)

        records: list[MetricRecord] = []
        for row in raw_rows:
            try:
                record = self._parse_metric_row(row)
                records.append(record)
            except Exception:
                logger.warning(
                    "Skipping unparseable row from %s: %s",
                    self.PLATFORM.value,
                    row,
                    exc_info=True,
                )

        logger.info(
            "Connector %s: normalized %d / %d rows for %s → %s",
            self.PLATFORM.value,
            len(records),
            len(raw_rows),
            date_start,
            date_end,
        )
        return records

    async def fetch_campaigns(self) -> list[dict[str, Any]]:
        """Fetch the list of campaigns from the platform."""
        return await self._fetch_campaigns_raw()

    # ── HTTP helpers (rate limiting + retries + circuit breaker) ──

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if not self._circuit_breaker.allow_request():
            raise ExternalServiceError(
                self.PLATFORM.value,
                "Circuit breaker is open — platform API is unavailable",
            )

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            await self._rate_limiter.acquire()

            try:
                response = await self.client.request(method, url, **kwargs)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    logger.warning(
                        "Rate limited by %s (retry_after=%ds, attempt=%d)",
                        self.PLATFORM.value,
                        retry_after,
                        attempt,
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(retry_after)
                        continue
                    raise RateLimitError(retry_after=retry_after)

                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                response.raise_for_status()
                self._circuit_breaker.record_success()
                return response.json()

            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
                last_error = exc
                self._circuit_breaker.record_failure()
                logger.warning(
                    "%s request failed (attempt %d/%d): %s",
                    self.PLATFORM.value,
                    attempt + 1,
                    self.max_retries + 1,
                    str(exc),
                )
                if attempt < self.max_retries:
                    delay = self.base_retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        raise ExternalServiceError(
            self.PLATFORM.value,
            f"Failed after {self.max_retries + 1} attempts: {last_error}",
        )

    async def _get(self, url: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("GET", url, **kwargs)

    async def _post(self, url: str, **kwargs: Any) -> dict[str, Any]:
        return await self._request("POST", url, **kwargs)

    # ── Abstract hooks ────────────────────────────────────────

    @abstractmethod
    async def _fetch_campaigns_raw(self) -> list[dict[str, Any]]:
        """Fetch raw campaign list from the platform API."""
        ...

    @abstractmethod
    async def _fetch_metrics_raw(
        self,
        date_start: date,
        date_end: date,
        campaign_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch raw metric rows from the platform API."""
        ...

    @abstractmethod
    def _parse_metric_row(self, row: dict[str, Any]) -> MetricRecord:
        """Convert one platform-specific API row into a ``MetricRecord``."""
        ...

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Return True if the current credentials are still valid."""
        ...
