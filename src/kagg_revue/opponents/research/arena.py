"""Complete reacting-agent games and seed-clustered research comparisons."""

import hashlib
import multiprocessing
import shutil
import time
import traceback
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import orjson

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.accounting import GameAccounting
from kagg_revue.opponents.compilation.diagnostics import source_diagnostics
from kagg_revue.opponents.public import PublicAgentRecord, load_public_agent_manifest
from kagg_revue.opponents.research.runtime import ResearchRuntime
from kagg_revue.opponents.research.settings import Experiment, Variant


@dataclass(frozen=True)
class Game:
    """Bind one full game to exact source identities and declared interventions."""

    variant: Variant
    candidate: PublicAgentRecord
    opponent: PublicAgentRecord
    seed: int
    seat: int
    engine: str
    accounting: bool


def play(job: Game) -> dict[str, Any]:
    """Run fresh episode state; propagate exceptions instead of scoring broken agents."""
    from kagg_revue.native.engine import Engine

    configuration: dict[str, Any] = {"episodeSteps": 720, "maxMarketOrdersPerTurn": 10}
    engine = Engine(seed=job.seed, configuration=configuration)
    candidate = ResearchRuntime(job.candidate, dict(engine.configuration), job.variant)
    opponent = ResearchRuntime(
        job.opponent,
        dict(engine.configuration),
        Variant(name="control", base=job.opponent.agent_id),
    )
    runtimes = (candidate, opponent) if job.seat == 0 else (opponent, candidate)
    fingerprints = [hashlib.sha256(), hashlib.sha256()]
    timing: list[list[float]] = [[], []]
    accounting = GameAccounting(24) if job.accounting else None
    snapshots: list[dict[str, Any]] = []

    def act(seat: int, observation: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        action = runtimes[seat].act(observation)
        timing[seat].append(time.perf_counter() - started)
        fingerprints[seat].update(orjson.dumps(action, option=orjson.OPT_SORT_KEYS))
        fingerprints[seat].update(b"\0")
        return action

    started = time.perf_counter()
    if job.engine == "official":
        from importlib import import_module

        make = import_module("kaggle_environments").make
        official = make("kaggriculture", configuration={**configuration, "seed": job.seed})
        final = official.run([lambda obs, _: act(0, dict(obs)), lambda obs, _: act(1, dict(obs))])[
            -1
        ]
        if any(state.status != "DONE" for state in final):
            raise RuntimeError("official game did not finish successfully")
        money = [float(final[0].observation.farms[seat]["money"]) for seat in (0, 1)]
        steps = len(official.steps) - 1
    else:
        while not engine.done:
            observations = [dict(engine.observation(seat)) for seat in (0, 1)]
            if job.accounting and engine.step_index in (648, 672, 696, 712, 718):
                snapshots.append(observations[job.seat])
            actions = [act(seat, observations[seat]) for seat in (0, 1)]
            if accounting is not None:
                trace = engine.step_with_trace(*actions)
                accounting.record(
                    observations, actions, trace, [float(engine.money(seat)) for seat in (0, 1)]
                )
            else:
                engine.step(*actions)
        steps = int(engine.step_index)
        money = [float(engine.money(seat)) for seat in (0, 1)]
    if steps != 719 or any(len(samples) != 719 for samples in timing):
        raise RuntimeError("game did not execute all 719 actions")
    result: dict[str, Any] = {
        "variant": job.variant.name,
        "opponent": job.opponent.agent_id,
        "seed": job.seed,
        "seat": job.seat,
        "cash": money[job.seat],
        "opponent_cash": money[1 - job.seat],
        "margin": money[job.seat] - money[1 - job.seat],
        "outcome": int(money[job.seat] > money[1 - job.seat])
        - int(money[job.seat] < money[1 - job.seat]),
        "steps": steps,
        "action_sha256": [value.hexdigest() for value in fingerprints],
        "wall_seconds": time.perf_counter() - started,
        "candidate_timing_ms": {
            "p99": float(np.percentile(timing[job.seat], 99) * 1000),
            "max": max(timing[job.seat]) * 1000,
        },
        "counters": candidate.counters,
        "telemetry": source_diagnostics(candidate.base),
    }
    if accounting is not None:
        result["accounting"] = accounting.finish(
            [dict(engine.observation(seat)) for seat in (0, 1)]
        )
        result["snapshots"] = snapshots
    return result


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep paired seats within a seed when reporting intervals and outcomes."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["variant"], row["opponent"]].append(row)
        groups[row["variant"], "all"].append(row)
    result = []
    for (variant, opponent), games in sorted(groups.items()):
        seeds = sorted({row["seed"] for row in games})
        margins = np.array(
            [np.mean([row["margin"] for row in games if row["seed"] == seed]) for seed in seeds]
        )
        rng = np.random.default_rng(920001)
        samples = margins[rng.integers(0, len(seeds), (10000, len(seeds)))].mean(1)
        result.append(
            {
                "variant": variant,
                "opponent": opponent,
                "games": len(games),
                "seeds": len(seeds),
                "wins": sum(row["outcome"] > 0 for row in games),
                "ties": sum(row["outcome"] == 0 for row in games),
                "losses": sum(row["outcome"] < 0 for row in games),
                "mean_margin": float(margins.mean()),
                "margin_seed_bootstrap_95": np.quantile(samples, [0.025, 0.975]).tolist(),
                "paired_seed_wins": int(np.sum(margins > 0)),
                "paired_seed_ties": int(np.sum(margins == 0)),
                "paired_seed_losses": int(np.sum(margins < 0)),
            }
        )
    return result


def run(config: Experiment) -> dict[str, Any]:
    """Archive source before evaluation and save every completed physical game."""
    output = config.output.resolve()
    if not output.is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("research results must remain under repository outputs")
    output.mkdir(parents=True, exist_ok=False)
    records = load_public_agent_manifest(config.manifest).by_id()
    sources = list(Path(__file__).parent.glob("*.py"))
    files = {str(path): digest(path) for path in sources}
    for path in sources:
        target = output / "source" / path.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(path, target)
    from kagg_revue.native import _revue_native

    write_json(
        output / "protocol.json",
        {
            "declared_at": datetime.now(UTC).isoformat(),
            "configuration": config.model_dump(mode="json"),
            "source_sha256": files,
            "manifest_sha256": digest(config.manifest),
            "native_sha256": digest(Path(_revue_native.__file__)),
            "note": "Offline research; both agents react to actual observations.",
        },
    )
    jobs = [
        Game(
            variant,
            records[variant.base],
            records[opponent],
            seed,
            seat,
            config.engine,
            config.accounting,
        )
        for variant in config.variants
        for opponent in config.opponents
        for seed in config.seeds
        for seat in (0, 1)
    ]
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    with ProcessPoolExecutor(
        max_workers=config.workers,
        mp_context=multiprocessing.get_context("spawn"),
        max_tasks_per_child=1,
    ) as executor:
        futures = {executor.submit(play, job): index for index, job in enumerate(jobs)}
        for future in as_completed(futures):
            try:
                row = future.result()
            except Exception:
                job = jobs[futures[future]]
                failure = {
                    "variant": job.variant.name,
                    "opponent": job.opponent.agent_id,
                    "seed": job.seed,
                    "seat": job.seat,
                    "traceback": traceback.format_exc(),
                }
                failures.append(failure)
                write_json(output / "failures" / f"{futures[future]:06d}.json", failure)
                continue
            write_json(output / "games" / f"{futures[future]:06d}.json", row)
            rows.append(row)
            if len(rows) % max(1, len(jobs) // 20) == 0:
                print(f"completed {len(rows)}/{len(jobs)}", flush=True)
    if any(digest(Path(path)) != fingerprint for path, fingerprint in files.items()):
        raise RuntimeError("research source changed during evaluation")
    rows.sort(key=lambda row: (row["variant"], row["opponent"], row["seed"], row["seat"]))
    summary = summarize(rows)
    write_json(output / "summary.json", summary)
    write_json(output / "failures.json", failures)
    return {"games": len(rows), "failed_games": len(failures), "summary": summary}
