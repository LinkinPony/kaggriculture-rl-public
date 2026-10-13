"""Fresh-process complete matches for frozen public notebook agents."""

from __future__ import annotations

import hashlib
import importlib.metadata
import time
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import orjson

from kagg_revue.core.backend import load_backend
from kagg_revue.opponents.public import PublicAgentRecord, PublicAgentRuntime

_FINGERPRINT_HORIZONS = (24, 96, 200, 400, 719)


@dataclass(frozen=True)
class MatchJob:
    """Serializable identity of one seat-specific complete match."""

    repository_root: str
    engine: str
    environment: dict[str, object]
    act_timeout_seconds: float
    remaining_overage_seconds: float
    agent_a: dict[str, object]
    agent_b: dict[str, object]
    seed: int
    agent_a_seat: int


def _pass_action(observation: Mapping[str, Any]) -> dict[str, Any]:
    player = int(observation["player"])
    farms = cast(list[Mapping[str, Any]], observation["farms"])
    hands = cast(list[object], farms[player]["hands"])
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in hands],
        "market": [],
    }


class _TimedAgent:
    """One episode-local notebook runtime with timing and action fingerprints."""

    def __init__(
        self,
        record: PublicAgentRecord,
        repository_root: Path,
        configuration: Mapping[str, Any],
        act_timeout_seconds: float,
        remaining_overage_seconds: float,
    ) -> None:
        started = time.perf_counter_ns()
        self._runtime: PublicAgentRuntime | None = None
        self.error: str | None = None
        try:
            self._runtime = PublicAgentRuntime(record, repository_root, configuration)
        except Exception as error:  # Public notebook code is an untyped boundary.
            self.error = f"{type(error).__name__}: {error}"
        self.initialization_ns = time.perf_counter_ns() - started
        self._act_timeout_ns = int(act_timeout_seconds * 1_000_000_000)
        self._remaining_overage_ns = int(remaining_overage_seconds * 1_000_000_000)
        self._digest = hashlib.sha256()
        self._fingerprints: dict[str, str] = {}
        self._action_count = 0
        self.samples_ns: list[int] = []

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one action, falling back to PASS after a recorded failure."""
        action: dict[str, Any]
        if self.error is not None or self._runtime is None:
            action = _pass_action(observation)
        else:
            started = time.perf_counter_ns()
            try:
                action = self._runtime.act(observation)
            except Exception as error:  # Public notebook code is an untyped boundary.
                self.error = f"{type(error).__name__}: {error}"
                action = _pass_action(observation)
            elapsed = time.perf_counter_ns() - started
            self.samples_ns.append(elapsed)
            self._remaining_overage_ns -= max(0, elapsed - self._act_timeout_ns)
            if self._remaining_overage_ns < 0 and self.error is None:
                self.error = "ActionTimeout: remaining overage exhausted"
                action = _pass_action(observation)
        self._record_action(action)
        return action

    def _record_action(self, action: Mapping[str, Any]) -> None:
        self._digest.update(orjson.dumps(action, option=orjson.OPT_SORT_KEYS))
        self._digest.update(b"\0")
        self._action_count += 1
        if self._action_count in _FINGERPRINT_HORIZONS:
            self._fingerprints[str(self._action_count)] = self._digest.copy().hexdigest()[:16]

    def summary(self) -> dict[str, object]:
        """Return bounded per-game diagnostics, excluding raw timing samples."""
        return {
            "error": self.error,
            "initialization_seconds": self.initialization_ns / 1_000_000_000,
            "calls": len(self.samples_ns),
            "total_act_seconds": sum(self.samples_ns) / 1_000_000_000,
            "remaining_overage_seconds": self._remaining_overage_ns / 1_000_000_000,
            "action_fingerprints": self._fingerprints,
        }


def _outcomes(money: tuple[float, float], errors: tuple[str | None, str | None]) -> tuple[int, int]:
    if errors[0] is not None and errors[1] is None:
        return -1, 1
    if errors[1] is not None and errors[0] is None:
        return 1, -1
    if errors[0] is not None:
        return 0, 0
    outcome = int(money[0] > money[1]) - int(money[0] < money[1])
    return outcome, -outcome


def _result(
    job: MatchJob,
    records: tuple[PublicAgentRecord, PublicAgentRecord],
    runtimes: tuple[_TimedAgent, _TimedAgent],
    money: tuple[float, float],
    statuses: tuple[str, str],
    transitions: int,
    wall_seconds: float,
    engine_identity: dict[str, object],
) -> dict[str, object]:
    seat_ids = (records[0].agent_id, records[1].agent_id)
    errors = cast(tuple[str | None, str | None], tuple(runtime.error for runtime in runtimes))
    outcomes = _outcomes(money, errors)
    return {
        "agent_a_id": PublicAgentRecord.model_validate(job.agent_a).agent_id,
        "agent_b_id": PublicAgentRecord.model_validate(job.agent_b).agent_id,
        "seed": job.seed,
        "agent_a_seat": job.agent_a_seat,
        "seat_agent_ids": list(seat_ids),
        "money": {seat_ids[seat]: money[seat] for seat in (0, 1)},
        "margin": {seat_ids[seat]: money[seat] - money[1 - seat] for seat in (0, 1)},
        "outcome": {seat_ids[seat]: outcomes[seat] for seat in (0, 1)},
        "status": {seat_ids[seat]: statuses[seat] for seat in (0, 1)},
        "timing": {seat_ids[seat]: runtimes[seat].summary() for seat in (0, 1)},
        "transitions": transitions,
        "match_wall_seconds": wall_seconds,
        "engine_identity": engine_identity,
        "_timing_samples_ns": {seat_ids[seat]: runtimes[seat].samples_ns for seat in (0, 1)},
    }


def _seat_records(job: MatchJob) -> tuple[PublicAgentRecord, PublicAgentRecord]:
    agent_a = PublicAgentRecord.model_validate(job.agent_a)
    agent_b = PublicAgentRecord.model_validate(job.agent_b)
    if job.agent_a_seat == 0:
        return agent_a, agent_b
    if job.agent_a_seat == 1:
        return agent_b, agent_a
    raise ValueError("agent_a_seat must be 0 or 1")


def _run_native(job: MatchJob) -> dict[str, object]:
    root = Path(job.repository_root)
    backend = load_backend(root)
    engine = backend.engine(seed=job.seed, configuration=dict(job.environment))
    configuration = cast(dict[str, Any], dict(engine.configuration))
    records = _seat_records(job)
    runtimes = tuple(
        _TimedAgent(
            record,
            root,
            configuration,
            job.act_timeout_seconds,
            job.remaining_overage_seconds,
        )
        for record in records
    )
    started = time.perf_counter()
    transitions = 0
    while not bool(engine.done):
        observations = (engine.observation(0), engine.observation(1))
        actions = tuple(runtimes[seat].act(observations[seat]) for seat in (0, 1))
        engine.step(actions[0], actions[1])
        transitions += 1
    wall_seconds = time.perf_counter() - started
    money = (float(engine.money(0)), float(engine.money(1)))
    return _result(
        job,
        records,
        cast(tuple[_TimedAgent, _TimedAgent], runtimes),
        money,
        ("DONE", "DONE"),
        transitions,
        wall_seconds,
        backend.identity,
    )


def _official_money(state: Any, seat: int) -> float:
    observation = cast(Mapping[str, Any], state.observation)
    farms = cast(list[Mapping[str, Any]], observation["farms"])
    return float(farms[seat]["money"])


def _run_official(job: MatchJob) -> dict[str, object]:
    make = import_module("kaggle_environments").make

    root = Path(job.repository_root)
    configuration = dict(job.environment)
    configuration.update(
        {
            "seed": job.seed,
            "actTimeout": job.act_timeout_seconds,
        }
    )
    environment = make("kaggriculture", configuration=configuration, debug=True)
    resolved = cast(dict[str, Any], dict(environment.configuration))
    records = _seat_records(job)
    runtimes = tuple(
        _TimedAgent(
            record,
            root,
            resolved,
            job.act_timeout_seconds,
            job.remaining_overage_seconds,
        )
        for record in records
    )

    def seat_zero(observation: Mapping[str, Any], _: Mapping[str, Any]) -> dict[str, Any]:
        return runtimes[0].act(observation)

    def seat_one(observation: Mapping[str, Any], _: Mapping[str, Any]) -> dict[str, Any]:
        return runtimes[1].act(observation)

    started = time.perf_counter()
    environment.run([seat_zero, seat_one])
    wall_seconds = time.perf_counter() - started
    final = environment.steps[-1]
    statuses = (str(final[0].status), str(final[1].status))
    for seat, status in enumerate(statuses):
        if status != "DONE" and runtimes[seat].error is None:
            runtimes[seat].error = f"EnvironmentStatus: {status}"
    money = (_official_money(final[0], 0), _official_money(final[1], 1))
    return _result(
        job,
        records,
        cast(tuple[_TimedAgent, _TimedAgent], runtimes),
        money,
        statuses,
        len(environment.steps) - 1,
        wall_seconds,
        {
            "implementation": "kaggle_environments",
            "version": importlib.metadata.version("kaggle-environments"),
        },
    )


def run_match_job(job: MatchJob) -> dict[str, object]:
    """Execute one complete match in a fresh worker process."""
    if job.engine == "native":
        return _run_native(job)
    if job.engine == "official":
        return _run_official(job)
    raise ValueError(f"unsupported benchmark engine: {job.engine}")


__all__ = ["MatchJob", "run_match_job"]
