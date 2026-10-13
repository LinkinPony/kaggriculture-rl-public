"""Overlap native script decisions with GPU inference on the same immutable turn."""

import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from types import TracebackType


class ScriptPrefetch:
    """Finish every native decision before advancing or destroying its game batch."""

    def __init__(self, prepare: Callable[[], None] | None) -> None:
        """Allocate one coordinator only when native script sessions exist."""
        self.prepare = prepare
        self.executor = ThreadPoolExecutor(max_workers=1) if prepare is not None else None
        self.pending: Future[float] | None = None
        self.compute_seconds = 0.0
        self.wait_seconds = 0.0

    def __enter__(self) -> "ScriptPrefetch":
        """Start the lifetime protected against concurrent batch destruction."""
        return self

    def __exit__(
        self,
        error_type: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Join native work even when GPU inference raises an exception."""
        if self.executor is not None:
            self.executor.shutdown(wait=True)

    def start(self) -> None:
        """Read the immutable turn in C++ alongside observation encoding and inference."""
        if self.pending is not None:
            raise RuntimeError("previous script decisions have not been consumed")
        if self.executor is not None:
            self.pending = self.executor.submit(self._prepare)

    def wait(self) -> None:
        """Propagate native errors before any game state changes."""
        if self.pending is not None:
            started = time.perf_counter()
            self.compute_seconds += self.pending.result()
            self.wait_seconds += time.perf_counter() - started
            self.pending = None

    def _prepare(self) -> float:
        started = time.perf_counter()
        assert self.prepare is not None
        self.prepare()
        return time.perf_counter() - started
