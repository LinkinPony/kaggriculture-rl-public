"""Direct paired-seat games between greedy and sampled copies of the same checkpoint."""

import json
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.temperature import games
from kagg_revue.evaluation.temperature.cli import Comparison
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.policy.checkpoints import load_policy


def play(job: tuple[int, int]) -> dict[str, Any]:
    """Give each temperature only its own observation and complete one reactive game."""
    seed, greedy_seat = job
    settings = games._SETTINGS
    assert settings is not None
    profile = games._PROFILE
    batch = create_selfplay_batch(settings, [seed])
    features = np.empty((2, profile["observation_features"]), dtype=np.float16)
    inputs = torch.from_numpy(features)
    step = torch.zeros(1, dtype=torch.long)
    sample_seat = 1 - greedy_seat
    sampling_seed = int(profile["sampling_seed"]) + sample_seat
    torch.manual_seed(sampling_seed)
    started = time.perf_counter()
    with torch.inference_mode():
        for turn in range(settings.turns):
            batch.observe_selfplay_into(features)
            step.fill_(turn)
            programs = [
                games._ACTORS[int(seat == sample_seat)](inputs[seat : seat + 1], step)
                for seat in (0, 1)
            ]
            batch.advance_programs(torch.cat(programs).numpy(), 1, 1, True)
    if batch.completed_games != 1 or batch.transitions != settings.turns:
        raise RuntimeError("direct temperature duel did not complete")
    values = batch.cash()[0]
    cash, other = float(values[greedy_seat]), float(values[sample_seat])
    return {
        "seed": seed,
        "seat": greedy_seat,
        "opponent": "same_checkpoint_t1",
        "cash": cash,
        "opponent_cash": other,
        "outcome": int(cash > other) - int(cash < other),
        "sampling_seed": sampling_seed,
        "wall_seconds": time.perf_counter() - started,
    }


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="evaluation_temperature",
)
def main(configuration: DictConfig) -> None:
    """Run a fresh-seed direct comparison after specifying both seats in advance."""
    config = Comparison.model_validate(
        OmegaConf.to_container(configuration.comparison, resolve=True)
    )
    specification = configuration.duels
    torch.set_num_threads(1)
    profile = json.loads((config.package / "agent_profile.json").read_text())
    policy, payload = load_policy(config.checkpoint, torch.device("cpu"))
    settings = payload["settings"]
    del policy, payload
    path = config.output_dir / "duels.jsonl"
    records = games.load_games(path)
    jobs = [
        (seed, seat)
        for seed in range(
            int(specification.seed), int(specification.seed) + int(specification.seeds)
        )
        for seat in (0, 1)
    ]
    completed = {(row["seed"], row["seat"]) for row in records}
    if len(completed) != len(records) or not completed.issubset(set(jobs)):
        raise ValueError("direct duel records do not match the declared unique seed/seat pairs")
    with (
        ProcessPoolExecutor(
            max_workers=int(specification.workers),
            mp_context=multiprocessing.get_context("spawn"),
            initializer=games.initialize,
            initargs=(
                {0: str(config.output_dir / "greedy.pt"), 1: str(config.package / "actor.pt")},
                settings,
                profile,
            ),
        ) as pool,
        path.open("a") as stream,
    ):
        futures = [pool.submit(play, job) for job in jobs if job not in completed]
        for future in as_completed(futures):
            row = future.result()
            records.append(row)
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            print(json.dumps({"duels_completed": len(records)}), flush=True)
    by_seed = {}
    for seed in {r["seed"] for r in records}:
        by_seed[seed] = np.mean([(r["outcome"] + 1) / 2 for r in records if r["seed"] == seed])
    means = np.asarray(list(by_seed.values()))
    indices = np.random.default_rng(0).integers(len(means), size=(4096, len(means)))
    write_json(
        config.output_dir / "duels-report.json",
        {
            "configuration": OmegaConf.to_container(specification, resolve=True),
            "t0": games.summary(records),
            "t0_score_seed_cluster_95_interval": np.quantile(
                means[indices].mean(1), [0.025, 0.975]
            ).tolist(),
            "scope": "Exploratory direct same-checkpoint comparison on fresh paired seeds; "
            "not Kaggle-wide win rate. Both actors use CPU FP32 batch-one inference.",
        },
    )


if __name__ == "__main__":
    main()
