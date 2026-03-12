"""
In-process event bus for domain events.

Supports async handlers with fire-and-forget or await-all semantics.
Used to decouple pipeline stages, trigger side effects (notifications,
cache invalidation), and integrate with the worker layer.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, Coroutine
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# Type alias for async event handlers
EventHandler = Callable[["DomainEvent"], Coroutine[Any, Any, None]]


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = ""


@dataclass
class ReportRequested(DomainEvent):
    """Emitted when a user requests report generation."""
    report_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    requested_by: UUID = field(default_factory=uuid4)
    source: str = "report_service"


@dataclass
class ReportCompleted(DomainEvent):
    """Emitted when pipeline finishes report generation."""
    report_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    total_tokens: int = 0
    ai_cost: float = 0.0
    source: str = "pipeline"


@dataclass
class ReportFailed(DomainEvent):
    """Emitted when pipeline fails during report generation."""
    report_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    error: str = ""
    stage: str = ""
    source: str = "pipeline"


@dataclass
class DataSyncCompleted(DomainEvent):
    """Emitted when a data source sync completes."""
    connection_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    platform: str = ""
    records_synced: int = 0
    source: str = "ingestion"


@dataclass
class DataSyncFailed(DomainEvent):
    """Emitted when a data source sync fails."""
    connection_id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)
    platform: str = ""
    error: str = ""
    source: str = "ingestion"


class EventBus:
    """
    Simple in-process event bus with async handler support.

    Usage:
        bus = EventBus()
        bus.subscribe(ReportCompleted, notify_user_handler)
        bus.subscribe(ReportCompleted, invalidate_cache_handler)
        await bus.publish(ReportCompleted(report_id=..., organization_id=...))
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """Register an async handler for a specific event type."""
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """Remove a handler for a specific event type."""
        self._handlers[event_type] = [
            h for h in self._handlers[event_type] if h is not handler
        ]

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all registered handlers.

        Handlers run concurrently. Failures in one handler don't affect others.
        """
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            return

        logger.debug(
            "Publishing %s to %d handlers",
            type(event).__name__,
            len(handlers),
        )

        results = await asyncio.gather(
            *(handler(event) for handler in handlers),
            return_exceptions=True,
        )

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Event handler failed for %s: %s",
                    type(event).__name__,
                    result,
                )


# Global event bus singleton
event_bus = EventBus()
