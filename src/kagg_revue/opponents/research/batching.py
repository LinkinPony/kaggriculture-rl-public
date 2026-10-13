"""Qualify a research portfolio in the native training batch boundary."""

import json
import time
import zlib
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.opponents.compilation.sources import CANDIDATES
from kagg_revue.opponents.public import (
    PublicAgentRuntime,
    load_public_agent_manifest,
)
from kagg_revue.opponents.research.qualification import Qualification, _agent, library


def verify(config: Qualification) -> dict[str, Any]:
    """Check mixed sessions against original sources, including cloned batch owners."""
    if not config.output.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("research batch artifacts must remain under outputs")
    native = library(config.library)
    if digest(config.source) != config.source_sha256 or digest(config.asset) != config.asset_sha256:
        raise ValueError("research batch source or asset changed")
    records = load_public_agent_manifest(config.manifest).by_id()
    public_dir = Path("src/kagg_revue/opponents/portfolios")
    assets = [public_dir / f"{candidate.agent_id}.json.zlib" for candidate in CANDIDATES]
    assets.append(config.asset)
    payloads = [json.loads(zlib.decompress(path.read_bytes())) for path in assets]
    names = [payload["agent_id"] for payload in payloads]
    environment = {"episodeSteps": 720, "maxMarketOrdersPerTurn": 10}
    seeds = [1860916601 + index // 2 for index in range(len(names) * 2)]
    seats = [index % 2 for index in range(len(seeds))]
    ids = [name for name in names for _ in (0, 1)]
    portfolios = [native.NativeOpponentPortfolio(payload) for payload in payloads]
    sessions = [native.NativeOpponentSession(p, 10) for p in portfolios for _ in (0, 1)]
    units, span = 9, 1
    width = units * (span + 1) * 4 + span * environment["maxMarketOrdersPerTurn"] * 2
    plans = np.zeros((len(seeds), width), dtype=np.int64)
    batch = native.ParallelBatch(
        environment, seeds, seats, ids, sessions, [], units, config.workers, [1]
    )
    engines = [native.Engine(seed, environment) for seed in seeds]
    actors = []
    for name in ids:
        if name == payloads[-1]["agent_id"]:
            actors.append(_agent(config.source, "none"))
        else:
            actor = PublicAgentRuntime(records[name], Path.cwd(), dict(engines[0].configuration))
            actors.append(actor.act)
    before = time.perf_counter()
    fork = None
    indices = np.array([0, 9, 10, 11, 10], dtype=np.int64)
    native_seconds = 0.0
    for turn in range(719):
        if turn == 216:
            fork = batch.fork(indices)
        started = time.perf_counter()
        batch.advance_programs(plans, 1, 1)
        if fork is not None:
            fork.advance_programs(plans[indices], 1, 1)
            np.testing.assert_array_equal(fork.cash(), batch.cash()[indices])
        native_seconds += time.perf_counter() - started
        for index, (engine, actor) in enumerate(zip(engines, actors, strict=True)):
            opponent = 1 - seats[index]
            action = actor(dict(engine.observation(opponent)))
            engine.step(*([action, {}] if opponent == 0 else [{}, action]))
        np.testing.assert_array_equal(
            batch.cash(),
            [
                [engine.money(seat) for seat in (seats[i], 1 - seats[i])]
                for i, engine in enumerate(engines)
            ],
        )
    if batch.completed_games != len(seeds) or fork is None or fork.completed_games != len(indices):
        raise AssertionError("mixed native batch did not complete")
    result = {
        "games": len(seeds),
        "fork_games": len(indices),
        "all_turn_cash_matched": True,
        "fork_turns_matched": 503,
        "opponents": ids,
        "library_sha256": digest(config.library),
        "assets_sha256": {str(path): digest(path) for path in assets},
        "native_seconds_including_fork": native_seconds,
        "wall_seconds": time.perf_counter() - before,
        "cash": batch.cash().tolist(),
        "scope": "ParallelBatch.advance_programs; PASS learner; original script references",
    }
    write_json(config.output / "batch-verification.json", result)
    return result


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="script_qualification"
)
def main(configuration: DictConfig) -> None:
    """Run the explicit research library separately from the installed training library."""
    config = Qualification.model_validate(OmegaConf.to_container(configuration.panel, resolve=True))
    print(json.dumps(verify(config)), flush=True)


if __name__ == "__main__":
    main()
