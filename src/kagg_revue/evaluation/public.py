"""Complete official games between frozen CPU policies and reviewed public scripts."""

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from kagg_revue.artifacts.io import digest
from kagg_revue.evaluation.accounting import GameAccounting
from kagg_revue.native import _revue_core as native
from kagg_revue.native.comparison import MirrorReference
from kagg_revue.opponents.public import PublicAgentRecord, PublicAgentRuntime


@dataclass(frozen=True)
class PublicGame:
    """One complete game with identities fixed before starting the worker."""

    actor: Path
    actor_sha256: str
    environment: dict[str, int | float]
    unit_limit: int
    features: int
    quantities: tuple[int, ...]
    opponent: dict[str, Any]
    reference_directory: Path
    seed: int
    seat: int


def play(job: PublicGame) -> dict[str, Any]:
    """Use official observations for both actors and compare every native state."""
    torch.set_num_threads(1)
    if digest(job.actor) != job.actor_sha256:
        raise ValueError("public arena serialized actor identity differs")
    actor = torch.jit.load(str(job.actor), map_location="cpu").eval()  # type: ignore[no-untyped-call]
    opponent = PublicAgentRecord.model_validate(job.opponent)
    engine = native.Engine(job.seed, job.environment)
    reference = MirrorReference(job.reference_directory, job.environment, [job.seed])
    runtime = PublicAgentRuntime(opponent, Path.cwd(), engine.configuration)
    session = native.ContractSession(job.environment, job.unit_limit)
    features = np.empty((1, job.features), dtype=np.float16)
    inputs = torch.from_numpy(features)
    steps = torch.zeros(1, dtype=torch.long)
    # Pair sampling streams across checkpoint budgets, separately from world RNG.
    sample_seed = job.seed * 2 + job.seat
    rng = torch.Generator(device="cpu").manual_seed(sample_seed).get_state()
    trajectory = hashlib.sha256()
    timings: list[float] = []
    opponent_timings: list[float] = []
    accounting = GameAccounting(int(engine.configuration["turnsPerDay"]))
    started = time.perf_counter()
    for turn in range(int(job.environment["episodeSteps"]) - 1):
        observations = reference.observations([engine])
        session.update(observations[job.seat])
        session.observe_into(features)
        steps.fill_(turn)
        phase = time.perf_counter()
        with torch.random.fork_rng(devices=[]), torch.inference_mode():
            torch.set_rng_state(rng)
            program = actor(inputs, steps).numpy()
            rng = torch.get_rng_state()
        timings.append(time.perf_counter() - phase)
        session.set_program(program, 1, list(job.quantities))
        actions: list[dict[str, Any]] = [{}, {}]
        actions[job.seat] = dict(session.program_action())
        phase = time.perf_counter()
        actions[1 - job.seat] = runtime.act(observations[1 - job.seat])
        opponent_timings.append(time.perf_counter() - phase)
        trajectory.update(json.dumps(actions, sort_keys=True).encode())
        trace = engine.step_with_trace(*actions)
        accounting.record(observations, actions, trace, [engine.money(0), engine.money(1)])
        reference.games[0].step(actions)
    final_observations = reference.observations([engine])
    if not engine.done:
        raise ValueError("public arena game did not finish")
    cash, other = engine.money(job.seat), engine.money(1 - job.seat)
    return {
        "seed": job.seed,
        "seat": job.seat,
        "opponent": opponent.sha256,
        "cash": cash,
        "opponent_cash": other,
        "outcome": int(cash > other) - int(cash < other),
        "sampling_seed": sample_seed,
        "actor_sha256": job.actor_sha256,
        "trajectory_sha256": trajectory.hexdigest(),
        "official_reference": reference.report(),
        "accounting": accounting.finish(final_observations),
        "wall_seconds": time.perf_counter() - started,
        "actor_inference_seconds": {"mean": float(np.mean(timings)), "max": max(timings)},
        "opponent_action_seconds": {
            "mean": float(np.mean(opponent_timings)),
            "max": max(opponent_timings),
        },
    }
