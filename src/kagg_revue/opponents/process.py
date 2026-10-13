"""Process-isolated execution of stateful public notebook opponents."""

from __future__ import annotations

import multiprocessing
import os
from collections.abc import Mapping
from contextlib import suppress
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, cast

from kagg_revue.opponents.public import PublicAgentRecord, PublicAgentRuntime

_CLOSE_TIMEOUT_SECONDS = 5.0


def _serve_public_agent(
    record_payload: dict[str, object],
    repository_root: str,
    configuration: dict[str, Any],
    connection: Connection,
) -> None:
    """Run one episode-local notebook instance behind a duplex pipe."""
    # Notebook dependencies must not silently multiply BLAS thread pools across
    # dozens of opponent processes.
    for variable in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[variable] = "1"
    try:
        record = PublicAgentRecord.model_validate(record_payload)
        runtime: PublicAgentRuntime | None = None
        connection.send(("ready", None))
        while True:
            command, payload = cast(tuple[str, object], connection.recv())
            if command == "close":
                connection.send(("closed", None))
                return
            if command != "act" or not isinstance(payload, Mapping):
                raise ValueError(f"unsupported public-agent command: {command}")
            if runtime is None:
                runtime = PublicAgentRuntime(record, Path(repository_root), configuration)
            action = runtime.act(cast(Mapping[str, Any], payload))
            connection.send(("action", action))
    except BaseException as error:  # The parent must receive child failures.
        with suppress(BrokenPipeError, EOFError, OSError):
            connection.send(("error", {"type": type(error).__name__, "message": str(error)}))
    finally:
        connection.close()


class PublicAgentProcess:
    """One public notebook runtime isolated in a dedicated spawned process."""

    def __init__(
        self,
        record: PublicAgentRecord,
        repository_root: Path,
        configuration: Mapping[str, Any],
    ) -> None:
        """Start one bounded worker without inheriting the CUDA context."""
        context = multiprocessing.get_context("forkserver")
        parent, child = context.Pipe(duplex=True)
        process = context.Process(
            target=_serve_public_agent,
            args=(
                record.model_dump(mode="json"),
                str(repository_root),
                dict(configuration),
                child,
            ),
            name=f"public-agent-{record.agent_id}",
            daemon=True,
        )
        process.start()
        child.close()
        self._connection = parent
        self._process = process
        self._closed = False
        self._ready = False

    def _receive(self) -> tuple[str, object]:
        try:
            response = self._connection.recv()
        except (BrokenPipeError, EOFError, OSError) as error:
            raise RuntimeError(
                f"public agent process exited with code {self._process.exitcode}"
            ) from error
        if (
            not isinstance(response, tuple)
            or len(response) != 2
            or not isinstance(response[0], str)
        ):
            raise RuntimeError("public agent process returned an invalid response")
        status, payload = cast(tuple[str, object], response)
        if status == "error":
            raise RuntimeError(f"public agent process failed: {payload}")
        return status, payload

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one action while retaining episode state in the child."""
        if self._closed:
            raise RuntimeError("public agent process is closed")
        if not self._ready:
            status, payload = self._receive()
            if status != "ready":
                raise RuntimeError(f"public agent failed during startup: {payload}")
            self._ready = True
        self._connection.send(("act", dict(observation)))
        status, payload = self._receive()
        if status != "action" or not isinstance(payload, Mapping):
            raise RuntimeError(f"public agent returned an invalid response: {status}")
        return dict(payload)

    def close(self) -> None:
        """Stop the episode worker, forcefully only if graceful shutdown stalls."""
        if self._closed:
            return
        self._closed = True
        if self._process.is_alive():
            try:
                self._connection.send(("close", None))
                if self._connection.poll(_CLOSE_TIMEOUT_SECONDS):
                    self._receive()
            except (BrokenPipeError, EOFError, OSError, RuntimeError):
                pass
        self._process.join(timeout=_CLOSE_TIMEOUT_SECONDS)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=_CLOSE_TIMEOUT_SECONDS)
        self._connection.close()

    def __enter__(self) -> PublicAgentProcess:
        """Return the live process wrapper."""
        return self

    def __exit__(self, *_: object) -> None:
        """Release the worker at an episode boundary."""
        self.close()


__all__ = ["PublicAgentProcess"]
