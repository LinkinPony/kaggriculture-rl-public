"""Compare standalone Python, normalized Python and C++ on complete live games."""

import hashlib
import importlib.util
import json
import multiprocessing
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, ConfigDict, Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.opponents.compilation.normalization import Normalization, normalize
from kagg_revue.opponents.public import (
    PublicAgentRecord,
    PublicAgentRuntime,
    load_public_agent_manifest,
)


class Qualification(BaseModel):
    """Identify all artifacts explicitly without replacing an installed native library."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: Path
    source_sha256: str
    asset: Path
    asset_sha256: str
    library: Path
    manifest: Path
    output: Path
    normalization: Normalization = "none"
    opponents: tuple[str, ...]
    seeds: tuple[int, ...]
    perturbations: tuple[bool, ...] = (False, True)
    workers: int = Field(default=8, ge=1, le=32)


@dataclass(frozen=True)
class Trial:
    """A source-equivalence trial with one reacting public opponent."""

    config: Qualification
    opponent: PublicAgentRecord
    seed: int
    seat: int
    perturb: bool


def library(path: Path) -> ModuleType:
    """Load an explicitly selected extension without changing files on disk."""
    spec = importlib.util.spec_from_file_location("_revue_native", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load the declared native library")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _agent(path: Path, normalization: Normalization) -> Any:
    import ast

    namespace: dict[str, Any] = {"__name__": "research_qualified_agent", "__file__": str(path)}
    tree = normalize(ast.parse(path.read_text()), normalization)
    exec(compile(tree, str(path), "exec"), namespace)  # noqa: S102
    return namespace["agent"]


def play(trial: Trial) -> dict[str, Any]:
    """Check every action, session cloning, and episode reset in real observations."""
    config = trial.config
    if digest(config.source) != config.source_sha256 or digest(config.asset) != config.asset_sha256:
        raise ValueError("qualification source or asset changed")
    native = library(config.library)
    payload = json.loads(zlib.decompress(config.asset.read_bytes()))
    if payload["source_sha256"] != config.source_sha256:
        raise ValueError("asset was generated from another source")
    portfolio = native.NativeOpponentPortfolio(payload)
    session = native.NativeOpponentSession(portfolio, 10)
    engine = native.Engine(trial.seed, {"episodeSteps": 720, "maxMarketOrdersPerTurn": 10})
    settings = dict(engine.configuration)
    original = _agent(config.source, "none")
    normalized = _agent(config.source, config.normalization)
    opponent = PublicAgentRuntime(trial.opponent, Path.cwd(), settings)
    fingerprints = [hashlib.sha256(), hashlib.sha256()]
    native_seconds = 0.0
    python_seconds = 0.0
    started = time.perf_counter()
    for turn in range(719):
        observation = dict(engine.observation(trial.seat))
        before = time.perf_counter()
        expected = original(observation, settings)
        python_seconds += time.perf_counter() - before
        adapted = normalized(observation, settings)
        before = time.perf_counter()
        fork = session.clone() if turn in (0, 144, 216, 648, 718) else None
        actual = native.native_opponent_action(engine, trial.seat, session)
        native_seconds += time.perf_counter() - before
        canonical = native.canonical_opponent_action(expected, 10)
        if expected != adapted or canonical != actual:
            raise AssertionError(
                {"turn": turn, "expected": expected, "normalized": adapted, "native": actual}
            )
        if fork is not None:
            if native.native_opponent_action(engine, trial.seat, fork) != actual:
                raise AssertionError(f"cloned session differs at {turn}")
            session = fork
        other = opponent.act(dict(engine.observation(1 - trial.seat)))
        actions = [expected, other] if trial.seat == 0 else [other, expected]
        if trial.perturb and turn in (145, 217, 433, 650):
            actions[trial.seat] = {"farmer": ["PASS"], "hands": [], "market": []}
        for fingerprint, action in zip(fingerprints, actions, strict=True):
            fingerprint.update(orjson.dumps(action, option=orjson.OPT_SORT_KEYS))
            fingerprint.update(b"\0")
        engine.step(*actions)
    if not engine.done:
        raise AssertionError("qualification game did not finish")
    # Reuse the final native session on step zero, as batch owners do at reset.
    reset = native.Engine(trial.seed + 1000, settings)
    fresh = _agent(config.source, "none")
    first = native.canonical_opponent_action(
        fresh(dict(reset.observation(trial.seat)), settings), 10
    )
    if native.native_opponent_action(reset, trial.seat, session) != first:
        raise AssertionError("native episode reset differs from a fresh Python namespace")
    return {
        "opponent": trial.opponent.agent_id,
        "seed": trial.seed,
        "seat": trial.seat,
        "perturbed": trial.perturb,
        "actions_matched": 719,
        "clones_matched": 5,
        "reset_matched": True,
        "cash": float(engine.money(trial.seat)),
        "opponent_cash": float(engine.money(1 - trial.seat)),
        "action_sha256": [value.hexdigest() for value in fingerprints],
        "python_seconds": python_seconds,
        "native_seconds": native_seconds,
        "wall_seconds": time.perf_counter() - started,
    }


def run(config: Qualification) -> dict[str, Any]:
    """Retain artifacts and stop qualification if any complete-game comparison fails."""
    if not config.output.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("qualification artifacts must remain under outputs")
    config.output.mkdir(parents=True, exist_ok=False)
    records = load_public_agent_manifest(config.manifest).by_id()
    write_json(
        config.output / "protocol.json",
        {
            "configuration": config.model_dump(mode="json"),
            "library_sha256": digest(config.library),
            "runner_sha256": digest(Path(__file__)),
        },
    )
    jobs = [
        Trial(config, records[opponent], seed, seat, perturb)
        for opponent in config.opponents
        for seed in config.seeds
        for seat in (0, 1)
        for perturb in config.perturbations
    ]
    rows = []
    with ProcessPoolExecutor(
        max_workers=config.workers,
        mp_context=multiprocessing.get_context("spawn"),
        max_tasks_per_child=1,
    ) as pool:
        futures = {pool.submit(play, job): index for index, job in enumerate(jobs)}
        for future in as_completed(futures):
            row = future.result()
            write_json(config.output / "games" / f"{futures[future]:04d}.json", row)
            rows.append(row)
            if len(rows) % 8 == 0:
                print(f"qualified {len(rows)}/{len(jobs)}", flush=True)
    result = {
        "games": len(rows),
        "actions_matched": sum(row["actions_matched"] for row in rows),
        "clones_matched": sum(row["clones_matched"] for row in rows),
        "resets_matched": len(rows),
        "aggregate_python_seconds": sum(row["python_seconds"] for row in rows),
        "aggregate_native_seconds": sum(row["native_seconds"] for row in rows),
    }
    write_json(config.output / "summary.json", result)
    return result


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="script_qualification"
)
def main(configuration: DictConfig) -> None:
    """Resolve an explicit isolated-library conformance panel."""
    config = Qualification.model_validate(OmegaConf.to_container(configuration.panel, resolve=True))
    print(json.dumps(run(config)), flush=True)


if __name__ == "__main__":
    main()
