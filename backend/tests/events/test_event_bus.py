"""Tests for the internal event bus."""

from uuid import uuid4

import pytest

from app.events.event_bus import (
    DomainEvent,
    EventBus,
    ReportCompleted,
    ReportRequested,
)


class TestEventBus:
    """Event bus tests."""

    @pytest.mark.asyncio
    async def test_publish_to_handler(self):
        bus = EventBus()
        received = []

        async def handler(event: DomainEvent):
            received.append(event)

        bus.subscribe(ReportCompleted, handler)
        event = ReportCompleted(report_id=uuid4(), organization_id=uuid4())
        await bus.publish(event)

        assert len(received) == 1
        assert received[0] is event

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        bus = EventBus()
        count = {"a": 0, "b": 0}

        async def handler_a(event):
            count["a"] += 1

        async def handler_b(event):
            count["b"] += 1

        bus.subscribe(ReportCompleted, handler_a)
        bus.subscribe(ReportCompleted, handler_b)
        await bus.publish(ReportCompleted(report_id=uuid4(), organization_id=uuid4()))

        assert count["a"] == 1
        assert count["b"] == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(ReportCompleted, handler)
        bus.unsubscribe(ReportCompleted, handler)
        await bus.publish(ReportCompleted(report_id=uuid4(), organization_id=uuid4()))

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_handler_error_does_not_propagate(self):
        bus = EventBus()
        received = []

        async def failing_handler(event):
            raise RuntimeError("Handler failure")

        async def good_handler(event):
            received.append(event)

        bus.subscribe(ReportCompleted, failing_handler)
        bus.subscribe(ReportCompleted, good_handler)
        await bus.publish(ReportCompleted(report_id=uuid4(), organization_id=uuid4()))

        # Good handler should still execute
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_no_handlers_does_nothing(self):
        bus = EventBus()
        # Should not raise
        await bus.publish(ReportRequested(report_id=uuid4(), organization_id=uuid4()))

    @pytest.mark.asyncio
    async def test_different_event_types_isolated(self):
        bus = EventBus()
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(ReportCompleted, handler)
        await bus.publish(ReportRequested(report_id=uuid4(), organization_id=uuid4()))

        assert len(received) == 0  # Handler only listens to ReportCompleted
