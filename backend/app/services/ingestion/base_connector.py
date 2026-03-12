"""
Base connector with rate limiting, exponential backoff retries, and circuit breaker.

All platform connectors inherit from BaseConnector and implement the
abstract methods for their specific API.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

import httpx

from app.core.exceptions import ExternalServiceError, RateLimitError
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlatformType(str, Enum):
    META_ADS = "meta_ads"
    GOOGLE_ADS = "google_ads"
    TIKTOK_ADS = "tiktok_ads"
    SHOPIFY = "shopify"
    GA4 = "ga4"


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RateLimiter:
    """Token-bucket rate limiter."""

    max_calls: int
    period_seconds: float
    _calls: list[float] = field(default_factory=list)

    async def acquire(self) -> None:
        """Wait until a call slot is available."""
        now = time.monotonic()
        # Purge expired timestamps
        self._calls = [t for t in self._calls if now - t < self.period_seconds]

        if len(self._calls) >= self.max_calls:
            sleep_time = self.period_seconds - (now - self._calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            self._calls = self._calls[1:]

        self._calls.append(time.monotonic())


@dataclass
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures on external APIs.

    CLOSED → OPEN after failure_threshold consecutive failures.
    OPEN → HALF_OPEN after recovery_timeout seconds.
    HALF_OPEN → CLOSED on success, OPEN on failure.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        # HALF_OPEN: allow one probe request
        return True


@dataclass
class RawRecord:
    """A single raw record from a platform API before normalization."""

    platform: PlatformType
    date: date
    campaign_id: str
    campaign_name: str
    ad_set_id: str | None = None
    ad_set_name: str | None = None
    ad_id: str | None = None
    ad_name: str | None = None
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    conversions: int = 0
    conversion_value: float = 0.0
    currency: str = "USD"
    extra: dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """
    Abstract base connector for marketing platform APIs.

    Subclasses implement:
    - _fetch_campaigns(): List campaigns from the platform
    - _fetch_metrics(): Fetch raw metric data for a date range
    - _refresh_token(): Refresh OAuth access token
    """

    PLATFORM: PlatformType

    def __init__(
        self,
        connection_id: UUID,
        organization_id: UUID,
        access_token: str,
        refresh_token: str | None = None,
        account_id: str = "",
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

    async def __aenter__(self) -> "BaseConnector":
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Connector must be used as async context manager")
        return self._client

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make an HTTP request with rate limiting, retries, and circuit breaker.

        Raises ExternalServiceError after exhausting retries.
        """
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

                # Handle rate limit responses
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    await logger.awarning(
                        "Rate limited by platform",
                        platform=self.PLATFORM.value,
                        retry_after=retry_after,
                        attempt=attempt,
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(retry_after)
                        continue
                    raise RateLimitError(retry_after=retry_after)

                # Handle server errors with retry
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
                await logger.awarning(
                    "Platform API request failed",
                    platform=self.PLATFORM.value,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(exc),
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

    # ── Abstract methods ──────────────────────────────────

    @abstractmethod
    async def fetch_campaigns(self) -> list[dict[str, Any]]:
        """Fetch all campaigns from the platform."""
        ...

    @abstractmethod
    async def fetch_metrics(
        self,
        date_start: date,
        date_end: date,
        campaign_ids: list[str] | None = None,
    ) -> list[RawRecord]:
        """Fetch raw metric data for the given date range."""
        ...

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Test that the connection credentials are still valid."""
        ...
