"""Qualification and throughput of the actual native training batch boundary."""

import json
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.native.comparison import MirrorReference
from kagg_revue.opponents.batches import create_batch
from kagg_revue.opponents.native_batch import create_native_opponent_session
from kagg_revue.opponents.portfolios.catalog import ACTIVE_IDS
from kagg_revue.opponents.public import PublicAgentRuntime, load_public_agent_manifest
from kagg_revue.policy.contracts import ContractLayout


def training_parity(manifest: Path, output: Path) -> dict[str, Any]:
    """Check both seats, numeric stepping, native forks and the official interpreter."""
    from kagg_revue.native import _revue_native as native

    config = Experiment(
        output_dir=Path("outputs/learning/native-opponent-qualification"),
        architecture="grounded-v2",
        decision_interval=1,
        workers=4,
    )
    settings = runtime_settings(config)
    layout = ContractLayout.resolve(settings)
    sources = load_public_agent_manifest(manifest).by_id()
    selected = tuple(name for name in ACTIVE_IDS if name in sources)
    jobs: list[tuple[int, int, str]] = [
        (1860908200 + i, seat, name) for i, name in enumerate(selected) for seat in (0, 1)
    ]
    batch = create_batch(settings, jobs)
    plans = np.zeros((len(jobs), layout.factors), np.int64)
    engines = [native.Engine(seed, config.environment) for seed, _, _ in jobs]
    numeric = [engine.clone() for engine in engines]
    originals = [
        PublicAgentRuntime(sources[name], Path.cwd(), engine.configuration)
        for engine, (_, _, name) in zip(engines, jobs, strict=True)
    ]
    sessions = [create_native_opponent_session(name, 10) for _, _, name in jobs]
    reference = MirrorReference(
        Path("data/external/kaggriculture-reference-1.32.7"),
        config.environment,
        [job[0] for job in jobs],
    )
    seats = np.array([seat for _, seat, _ in jobs], np.int64)
    tokens = np.tile([0, 44], (len(jobs), 2, 1)).astype(np.int64)
    quantities = np.zeros_like(tokens)
    counts = np.full((len(jobs), 2), 2, np.int64)
    units = np.ones_like(counts)
    fork = None
    parents = np.repeat(np.arange(len(jobs), dtype=np.int64), 2)
    for turn in range(719):
        observations = reference.observations(engines)
        for i in range(len(jobs)):
            for seat in (0, 1):
                if batch.observation(i, seat) != engines[i].observation(seat):
                    raise AssertionError(f"training batch differs at turn {turn}, lane {i}")
            if fork is not None:
                for child in (2 * i, 2 * i + 1):
                    for seat in (0, 1):
                        if fork.observation(child, seat) != batch.observation(i, seat):
                            raise AssertionError("forked opponent state is not independent")
        if turn == 360:
            fork = batch.fork(parents)
        actions = []
        for i, (_, seat, _) in enumerate(jobs):
            action: list[dict[str, Any]] = [{}, {}]
            action[1 - seat] = originals[i].act(observations[2 * i + 1 - seat])
            actions.append(action)
        batch.advance_programs(plans, 1, 1)
        if fork is not None:
            fork.advance_programs(plans[parents], 1, 1)
        native.engine_step_native_opponent_batch(
            numeric, seats, sessions, tokens, quantities, counts, units, 4
        )
        for i, (engine, game, action) in enumerate(
            zip(engines, reference.games, actions, strict=True)
        ):
            engine.step(*action)
            game.step(action)
            for seat in (0, 1):
                if numeric[i].observation(seat) != engine.observation(seat):
                    raise AssertionError(f"numeric opponent batch differs at turn {turn}")
    reference.observations(engines)
    for i, engine in enumerate(engines):
        for seat in (0, 1):
            if batch.observation(i, seat) != engine.observation(seat):
                raise AssertionError("training final state differs")
    if batch.completed_games != len(jobs) or batch.transitions != 719 * len(jobs):
        raise AssertionError("training physical-game accounting differs")
    report = {
        "passed": True,
        "games": len(jobs),
        "script_actions": len(jobs) * 719,
        "forked_games": len(parents),
        "fork_step": 360,
        "official": reference.report(),
        "cash": batch.cash().tolist(),
        "binary_sha256": digest(Path(native.__file__)),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "training-parity.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def throughput(output: Path, games: int = 128) -> dict[str, Any]:
    """Time full seasons through advance_programs; exclude setup and model inference."""
    from kagg_revue.native import _revue_native as native

    rows = []
    for names, workers in [((name,), 4) for name in ACTIVE_IDS] + [
        (ACTIVE_IDS, workers) for workers in (1, 4, 8)
    ]:
        config = Experiment(
            output_dir=Path("outputs/learning/native-opponent-qualification"),
            architecture="grounded-v2",
            decision_interval=1,
            workers=workers,
        )
        settings = runtime_settings(config)
        layout = ContractLayout.resolve(settings)
        jobs: list[tuple[int, int, str]] = [
            (1860908300 + i // 2, i % 2, names[(i // 2) % len(names)]) for i in range(games)
        ]
        plans = np.zeros((games, layout.factors), np.int64)
        samples = []
        final_cash = None
        for repeat in range(4):
            batch = create_batch(settings, jobs)
            started = time.perf_counter()
            for _ in range(719):
                batch.advance_programs(plans, 1, 1)
            seconds = time.perf_counter() - started
            cash = batch.cash()
            if batch.completed_games != games:
                raise AssertionError("throughput panel did not finish")
            if final_cash is not None:
                np.testing.assert_array_equal(cash, final_cash)
            final_cash = cash
            if repeat:
                samples.append(seconds)
        median = statistics.median(samples)
        row = {
            "opponents": names,
            "games": games,
            "workers": workers,
            "seconds": samples,
            "median_seconds": median,
            "transitions_per_second": games * 719 / median,
            "games_per_second": games / median,
        }
        rows.append(row)
        print(json.dumps(row), flush=True)
    report = {
        "binary_sha256": digest(Path(native.__file__)),
        "panels": rows,
        "scope": (
            "CPU engine + native opponent + PASS learner via advance_programs; "
            "excludes model inference and observations"
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "throughput.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
