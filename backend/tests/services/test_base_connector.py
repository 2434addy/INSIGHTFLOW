"""Tests for the base connector: rate limiter, circuit breaker, retry logic."""

import asyncio
import time

import pytest

from app.services.ingestion.base_connector import (
    CircuitBreaker,
    CircuitState,
    RateLimiter,
)


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit():
    """Requests within the limit proceed immediately."""
    limiter = RateLimiter(max_calls=5, period_seconds=1.0)

    start = time.monotonic()
    for _ in range(5):
        await limiter.acquire()
    elapsed = time.monotonic() - start

    # Should complete almost instantly (well under 1 second)
    assert elapsed < 0.5


@pytest.mark.asyncio
async def test_rate_limiter_throttles_over_limit():
    """Requests over the limit are delayed."""
    limiter = RateLimiter(max_calls=2, period_seconds=0.5)

    await limiter.acquire()
    await limiter.acquire()
    # Third call should wait ~0.5s
    start = time.monotonic()
    await limiter.acquire()
    elapsed = time.monotonic() - start

    assert elapsed >= 0.3  # Allow some tolerance


def test_circuit_breaker_starts_closed():
    """Circuit breaker starts in CLOSED state."""
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True


def test_circuit_breaker_opens_after_threshold():
    """Circuit opens after reaching failure threshold."""
    cb = CircuitBreaker(failure_threshold=3)

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False


def test_circuit_breaker_resets_on_success():
    """A success resets the failure count and closes the circuit."""
    cb = CircuitBreaker(failure_threshold=3)

    cb.record_failure()
    cb.record_failure()
    cb.record_success()

    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_transitions_to_half_open():
    """Circuit transitions from OPEN to HALF_OPEN after recovery timeout."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False

    # Wait for recovery timeout
    time.sleep(0.15)
    assert cb.allow_request() is True
    assert cb.state == CircuitState.HALF_OPEN


def test_circuit_breaker_half_open_closes_on_success():
    """HALF_OPEN → CLOSED on successful probe."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    cb.record_failure()
    cb.record_failure()
    time.sleep(0.15)
    cb.allow_request()  # Transition to HALF_OPEN

    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_half_open_opens_on_failure():
    """HALF_OPEN → OPEN on failed probe."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    cb.record_failure()
    cb.record_failure()
    time.sleep(0.15)
    cb.allow_request()  # Transition to HALF_OPEN

    cb.record_failure()
    assert cb.state == CircuitState.OPEN
