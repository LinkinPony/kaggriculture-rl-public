"""Shared low-overhead observability for training and evaluation runs."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from types import TracebackType
from typing import Any

import torch
from pydantic import BaseModel, ConfigDict, Field


class ObservabilitySettings(BaseModel):
    """Validated coarse-grained logging settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tensorboard: bool
    flush_seconds: int = Field(gt=0)
    max_queue: int = Field(gt=0)


def numeric_metrics(values: Mapping[str, object]) -> dict[str, float]:
    """Flatten nested numeric metrics into TensorBoard scalar names."""
    flattened: dict[str, float] = {}

    def visit(prefix: str, value: object) -> None:
        if isinstance(value, bool | int | float):
            flattened[prefix] = float(value)
        elif isinstance(value, Mapping):
            for name, child in value.items():
                child_prefix = f"{prefix}/{name}" if prefix else str(name)
                visit(child_prefix, child)

    for name, value in values.items():
        visit(str(name), value)
    return flattened


def synchronize(device: torch.device) -> None:
    """Synchronize only at a coarse measurement boundary."""
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def throughput(items: int | float, elapsed_seconds: float) -> float:
    """Return a finite item rate for a completed stage."""
    if elapsed_seconds <= 0.0:
        return 0.0
    return float(items) / elapsed_seconds


class ScalarLogger:
    """Asynchronous TensorBoard scalar writer with a no-op disabled mode."""

    def __init__(
        self,
        output_dir: Path,
        settings: ObservabilitySettings,
        *,
        run_metadata: Mapping[str, object] | None = None,
    ) -> None:
        """Create an optional writer under the immutable run directory."""
        self.log_dir = output_dir / "tensorboard"
        self._writer: Any | None = None
        if settings.tensorboard:
            try:
                from torch.utils.tensorboard import SummaryWriter
            except ImportError as error:  # pragma: no cover - packaging guard.
                raise RuntimeError(
                    "TensorBoard logging is enabled but tensorboard is not installed"
                ) from error
            self._writer = SummaryWriter(
                log_dir=str(self.log_dir),
                max_queue=settings.max_queue,
                flush_secs=settings.flush_seconds,
            )
            if run_metadata is not None:
                self._writer.add_text(
                    "run/metadata",
                    f"```json\n{json.dumps(run_metadata, indent=2, sort_keys=True)}\n```",
                    global_step=0,
                )

    @property
    def enabled(self) -> bool:
        """Whether TensorBoard events are being emitted."""
        return self._writer is not None

    def scalars(self, namespace: str, values: Mapping[str, object], step: int) -> None:
        """Queue numeric scalars without forcing a device synchronization."""
        if self._writer is None:
            return
        for name, value in numeric_metrics(values).items():
            self._writer.add_scalar(f"{namespace}/{name}", value, step)

    def close(self) -> None:
        """Flush pending events at the end of a coarse run phase."""
        if self._writer is not None:
            self._writer.close()

    def __enter__(self) -> ScalarLogger:
        """Return this logger for a bounded phase."""
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the writer regardless of phase outcome."""
        self.close()


def observability_report(logger: ScalarLogger) -> dict[str, object]:
    """Describe the bounded logging surface in an artifact report."""
    return {
        "tensorboard_enabled": logger.enabled,
        "tensorboard_log_dir": str(logger.log_dir) if logger.enabled else None,
        "cadence": "BC epoch or RL update boundary",
        "histograms": False,
        "model_graph": False,
    }


__all__ = [
    "ObservabilitySettings",
    "ScalarLogger",
    "numeric_metrics",
    "observability_report",
    "synchronize",
    "throughput",
]
