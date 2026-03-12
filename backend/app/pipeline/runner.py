"""
Backward-compatibility re-export.

The canonical implementation now lives in ``pipeline_runner.py``.
This module re-exports the public API so that existing imports
(``from app.pipeline.runner import PipelineRunner``) keep working.
"""

from app.pipeline.pipeline_runner import (  # noqa: F401
    STAGE_DEPS,
    STAGE_PROGRESS,
    PipelineError,
    PipelineRunner,
    PipelineTimeoutError,
    PipelineValidationError,
)
