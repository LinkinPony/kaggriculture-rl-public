"""Measure complete native script seasons and repeated session ownership."""

import gc
import json
import os
import resource
import time
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.native import _revue_native as native
from kagg_revue.opponents.batches import create_batch
from kagg_revue.opponents.portfolios.catalog import ACTIVE_IDS
from kagg_revue.opponents.portfolios.native import create_native_session
from kagg_revue.policy.contracts import ContractLayout


class Benchmark(FrozenSettings):
    """Use a realistic per-rank script budget and retain exact timing evidence."""

    games: int = Field(default=16, ge=2)
    workers: int = Field(default=8, ge=1)
    repeats: int = Field(default=2, ge=2)
    seed: int = 1860914400
    output: Path = Path("outputs/opponents/public-20260914/throughput.json")
    opponents: tuple[str, ...] = ACTIVE_IDS


def rss() -> int:
    """Read resident bytes without imposing an additional runtime dependency."""
    return int(Path("/proc/self/statm").read_text().split()[1]) * os.sysconf("SC_PAGE_SIZE")


def benchmark(options: Benchmark) -> dict[str, Any]:
    """Time the GIL-free training boundary and check stable session destruction."""
    settings = runtime_settings(
        Experiment(
            output_dir=Path("outputs/learning/native-opponent-qualification"),
            architecture="grounded-v2",
            decision_interval=1,
            workers=options.workers,
        )
    )
    layout = ContractLayout.resolve(settings)
    plans = np.zeros((options.games, layout.factors), np.int64)
    rows = []
    if not options.opponents or not set(options.opponents) <= set(ACTIVE_IDS):
        raise ValueError("throughput requires active native opponents")
    for name in options.opponents:
        jobs = [(options.seed + i // 2, i % 2, name) for i in range(options.games)]
        samples, cpu, season_memory = [], [], []
        previous = None
        for _ in range(options.repeats):
            batch = create_batch(settings, jobs)
            usage = resource.getrusage(resource.RUSAGE_SELF)
            before_cpu = usage.ru_utime + usage.ru_stime
            started = time.perf_counter()
            for _ in range(719):
                batch.advance_programs(plans, 1, 1)
            samples.append(time.perf_counter() - started)
            usage = resource.getrusage(resource.RUSAGE_SELF)
            cpu.append(usage.ru_utime + usage.ru_stime - before_cpu)
            cash = batch.cash()
            if previous is not None:
                np.testing.assert_array_equal(previous, cash)
            previous = cash
            assert batch.completed_games == options.games
            del batch
            gc.collect()
            season_memory.append(rss())
        gc.collect()
        memory = [rss()]
        for _ in range(3):
            for _ in range(64):
                session = create_native_session(name)
                clone = session.clone()
                del session, clone
            gc.collect()
            memory.append(rss())
        row = {
            "opponent": name,
            "games": options.games,
            "workers": options.workers,
            "wall_seconds": samples,
            "cpu_seconds": cpu,
            "completed_season_rss_bytes": season_memory,
            "session_stress_rss_bytes": memory,
            "cash": previous.tolist() if previous is not None else [],
        }
        rows.append(row)
        print(json.dumps(row), flush=True)
        write_json(options.output, {"complete": False, "panels": rows})
    result = {
        "complete": True,
        "binary_sha256": digest(Path(native.__file__)),
        "panels": rows,
        "scope": "native advance_programs with PASS learner; excludes neural inference",
    }
    write_json(options.output, result)
    return result


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="native_public_benchmark",
)
def main(config: DictConfig) -> None:
    """Measure the frozen active population using an explicit Hydra recipe."""
    benchmark(Benchmark.model_validate(OmegaConf.to_container(config.benchmark, resolve=True)))


if __name__ == "__main__":
    main()
