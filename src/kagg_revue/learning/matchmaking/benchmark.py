"""Full-size frozen-opponent sampling checks and serial/concurrent inference timing."""

import json
import statistics
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.archive import PopulationCache
from kagg_revue.learning.collection.sampling import collect
from kagg_revue.learning.config import Population
from kagg_revue.learning.distributed import seed_shard
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.optimization.settings import HistoricalPopulation
from kagg_revue.learning.recovery.population import changed_protocol
from kagg_revue.opponents.settings import PublicPopulation
from kagg_revue.policy.inference import ActorRuntime


def benchmark(change: dict[str, Any], report: Path) -> None:
    """Compare complete trajectories with paired RNG at production inference batch sizes."""
    source = Path(change["run"])
    state = json.loads((source / "state.json").read_text())
    config = changed_protocol(
        state,
        Population.model_validate(change["population"]),
        PublicPopulation.model_validate(change["script_population"]),
    )
    assert config.execution is not None
    device = torch.device(config.device)
    torch.cuda.set_device(device)
    torch.set_num_threads(config.execution.cpu_threads_per_rank)
    settings = runtime_settings(config)
    world = len(config.execution.devices)
    update = state["completed_update"] + 1
    match = Matchmaker(config, state).select(update, world)
    actor, payload = artifacts.load_member(config, state, state["latest"], device)
    del payload
    frozen, payload = artifacts.load_member(config, state, state["pool"][0], device)
    del payload
    frozen.requires_grad_(False)
    PopulationCache(config, state).load(match.history, frozen)
    games = config.games // world
    history = int(games * config.population.fraction)
    assert config.script_population is not None
    scripts = int(games * config.script_population.fraction)
    runtimes = [
        ActorRuntime(
            policy,
            count,
            sample=True,
            precision=config.precision,
            bf16_reduced_precision_reduction=False,
            compile_inference=config.execution.compile_inference,
        )
        for policy, count in ((actor, 2 * games - history - scripts), (frozen, history))
    ]
    timings = []
    for repetition in range(4):
        collected = []
        for concurrent in (False, True):
            active = settings.model_copy(
                update={
                    "ppo": settings.ppo.model_copy(
                        update={
                            "history": HistoricalPopulation(
                                checkpoint=source / match.history,
                                fraction=config.population.fraction,
                            ),
                            "script_allocation": match.scripts,
                            "concurrent_history_inference": concurrent,
                        }
                    )
                }
            )
            torch.manual_seed(config.seed + repetition)
            rollout = collect(
                active,
                actor,
                runtimes[0],
                seed_shard(config, update + repetition, 0, world),
                runtimes[1],
            )
            if not torch.isfinite(rollout.log_probabilities).all():
                raise ValueError("frozen opponent inference produced nonfinite likelihoods")
            collected.append(rollout)
            timings.append({"repetition": repetition, "concurrent": concurrent, **rollout.timing})
        left, right = collected
        for key in ("observations", "actions", "log_probabilities", "returns", "weights"):
            torch.testing.assert_close(getattr(left, key), getattr(right, key), rtol=0, atol=0)
        np.testing.assert_array_equal(left.cash, right.cash)
        print(
            json.dumps(
                {"repetition": repetition, "trajectory_equal": True, "timings": timings[-2:]}
            ),
            flush=True,
        )
        del left, right, rollout, collected
    serial, concurrent_seconds = (
        statistics.median(
            row["rollout_seconds"]
            for row in timings
            if row["repetition"] and row["concurrent"] == mode
        )
        for mode in (False, True)
    )
    write_json(
        report,
        {
            "passed": True,
            "paired_trajectories_exact": True,
            "physical_games": 8 * games,
            "games_per_rank": games,
            "learner_rows": 2 * games - history - scripts,
            "frozen_rows": history,
            "serial_seconds": serial,
            "concurrent_seconds": concurrent_seconds,
            "speedup": serial / concurrent_seconds,
            "records": timings,
            "checkpoint_sha256": state["members"][state["latest"]],
            "source_sha256": artifacts.source_identity()["source_sha256"],
        },
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_context_pfsp_change",
)
def main(configuration: DictConfig) -> None:
    """Resolve the intended production population before benchmarking its inference."""
    change = OmegaConf.to_container(configuration.change, resolve=True)
    assert isinstance(change, dict)
    benchmark(change, Path(str(configuration.change.qualification)).with_name("inference.json"))  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
