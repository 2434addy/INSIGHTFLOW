"""
Pipeline stage executors.

Each stage implements the ``BaseStage`` interface:

    class MyStage(BaseStage):
        name = "my_stage"

        async def run(self, context: PipelineContext) -> OutputType:
            ...

The runner calls ``stage.run(context)`` for every stage.  Stages pull
their upstream dependencies from ``context.get_stage_output(name)``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.pipeline.pipeline_context import PipelineContext


class BaseStage(ABC):
    """Abstract base class for all pipeline stages."""

    name: str  # Must be set by each subclass

    @abstractmethod
    async def run(self, context: PipelineContext) -> Any:
        """
        Execute the stage and return its result.

        Args:
            context: Shared pipeline context carrying input data,
                     configuration, dependencies, and previous stage
                     outputs (via ``context.get_stage_output()``).

        Returns:
            The typed stage output (e.g. ``ValidationResult``, ``KPIResult``).
        """
        ...
