"""
Base agent class — common interface for all pipeline agents.

Each agent receives typed input, processes it using skills, and returns
typed output. Agents handle their own error recovery and logging.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base for all pipeline agents.

    Subclasses implement `execute()` with their specific logic.
    The base class provides retry, timing, and error handling.
    """

    name: str = "base_agent"
    max_retries: int = 1

    async def run(self, input_data: InputT) -> OutputT:
        """Run the agent with retry and timing logic."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                start = time.monotonic()
                result = await self.execute(input_data)
                elapsed_ms = int((time.monotonic() - start) * 1000)
                logger.info(
                    "Agent %s completed in %dms (attempt %d)",
                    self.name, elapsed_ms, attempt + 1,
                )
                return result
            except Exception as e:
                last_error = e
                logger.warning(
                    "Agent %s failed (attempt %d/%d): %s",
                    self.name, attempt + 1, self.max_retries + 1, str(e),
                )
                if attempt < self.max_retries:
                    continue

        # All retries exhausted — try fallback
        logger.error("Agent %s exhausted retries, attempting fallback", self.name)
        return await self.fallback(input_data, last_error)

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """Core agent logic — subclasses must implement this."""
        ...

    async def fallback(self, input_data: InputT, error: Exception | None) -> OutputT:
        """
        Fallback when all retries fail. Override in subclasses
        that can produce degraded results.
        """
        raise RuntimeError(
            f"Agent {self.name} failed with no fallback: {error}"
        ) from error
