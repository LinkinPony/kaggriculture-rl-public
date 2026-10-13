"""Run a predeclared paired panel using the submitted actor and a greedy control."""

import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.deployment.actor import freeze
from kagg_revue.evaluation.comparison import paired_cash, paired_scores
from kagg_revue.evaluation.temperature.actors import GreedyPolicy
from kagg_revue.evaluation.temperature.games import initialize, load_games, play, summary
from kagg_revue.opponents.portfolios.native import ASSET_SHA256
from kagg_revue.policy.checkpoints import load_policy


class Comparison(FrozenSettings):
    """Immutable checkpoint, submission package and seed panel for CPU evaluation."""

    checkpoint: Path
    package: Path
    output_dir: Path
    seed: int = Field(ge=0)
    seeds: int = Field(gt=0)
    opponents: tuple[str, ...]
    workers: int = Field(gt=0)


def run(config: Comparison) -> dict[str, Any]:
    """Authenticate artifacts, finish every declared game and report paired uncertainty."""
    torch.set_num_threads(1)
    profile = json.loads((config.package / "agent_profile.json").read_text())
    manifest = json.loads((config.package / "manifest.json").read_text())
    checkpoint_sha = digest(config.checkpoint)
    sampled = config.package / "actor.pt"
    if checkpoint_sha != manifest["checkpoint_sha256"]:
        raise ValueError("evaluation checkpoint differs from the submitted checkpoint")
    if digest(sampled) != profile["actor_sha256"]:
        raise ValueError("submitted actor hash differs")
    if len(set(config.opponents)) != len(config.opponents) or not config.opponents:
        raise ValueError("opponents must be nonempty and unique")
    identities = {name: ASSET_SHA256[name] for name in config.opponents}
    config.output_dir.mkdir(parents=True, exist_ok=True)
    resolved = config.model_dump(mode="json")
    configuration_path = config.output_dir / "configuration.json"
    if configuration_path.exists():
        previous = json.loads(configuration_path.read_text())
        previous.pop("workers")
        if previous != {k: v for k, v in resolved.items() if k != "workers"}:
            raise ValueError("existing evaluation has a different frozen configuration")
    write_json(configuration_path, resolved)
    policy, payload = load_policy(config.checkpoint, torch.device("cpu"))
    policy.eval()
    settings = payload["settings"]
    del payload
    greedy = config.output_dir / "greedy.pt"
    if not greedy.exists():
        freeze(GreedyPolicy(policy), greedy)
    del policy
    jobs = [
        (seed, seat, opponent, temperature)
        for seed in range(config.seed, config.seed + config.seeds)
        for opponent in config.opponents
        for seat in (0, 1)
        for temperature in (1, 0)
    ]
    records_path = config.output_dir / "games.jsonl"
    records = load_games(records_path)
    keys = ("seed", "seat", "opponent", "temperature")
    completed = {tuple(row[k] for k in keys) for row in records}
    if len(completed) != len(records) or not completed.issubset(set(jobs)):
        raise ValueError("existing records are duplicated or outside the declared panel")
    remaining = [job for job in jobs if job not in completed]
    print(json.dumps({"event": "start", "remaining": len(remaining)}), flush=True)
    with (
        ProcessPoolExecutor(
            max_workers=config.workers,
            mp_context=multiprocessing.get_context("spawn"),
            initializer=initialize,
            initargs=({0: str(greedy), 1: str(sampled)}, settings, profile),
        ) as pool,
        records_path.open("a") as stream,
    ):
        futures = [pool.submit(play, job) for job in remaining]
        for future in as_completed(futures):
            row = future.result()
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            records.append(row)
            if len(records) % 16 == 0 or len(records) == len(jobs):
                progress = {"completed": len(records), "total": len(jobs)}
                write_json(config.output_dir / "progress.json", progress)
                print(json.dumps(progress), flush=True)
    panels = {t: {"games": [r for r in records if r["temperature"] == t]} for t in (0, 1)}
    strata = {}
    for name in config.opponents:
        groups = {
            t: {"games": [r for r in panels[t]["games"] if r["opponent"] == name]} for t in (0, 1)
        }
        strata[name] = {
            "t0": summary(groups[0]["games"]),
            "t1": summary(groups[1]["games"]),
            "t0_minus_t1": paired_scores(groups[1], groups[0]),
        }
    result = {
        "configuration": resolved,
        "checkpoint_sha256": checkpoint_sha,
        "sampled_actor_sha256": digest(sampled),
        "greedy_actor_sha256": digest(greedy),
        "opponent_asset_sha256": identities,
        "torch_version": torch.__version__,
        "precision": "fp32_cpu_batch_one",
        "sampling": "submission fixed sampling_seed + seat, reset for every game",
        "t0": summary(panels[0]["games"]),
        "t1": summary(panels[1]["games"]),
        "t0_minus_t1": paired_scores(panels[1], panels[0]),
        "cash_t0_minus_t1": paired_cash(panels[1], panels[0]),
        "opponents": strata,
        "scope": "Fixed native script panel; seed-cluster intervals retain both seats and "
        "all opponents. Does not estimate Kaggle-wide win rate or independent sampling seeds.",
    }
    write_json(config.output_dir / "report.json", result)
    print(json.dumps({k: result[k] for k in ("t0", "t1", "t0_minus_t1")}), flush=True)
    return result


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="evaluation_temperature",
)
def main(configuration: DictConfig) -> None:
    """Resolve the local temperature comparison without touching training or deployment."""
    run(Comparison.model_validate(OmegaConf.to_container(configuration.comparison, resolve=True)))


if __name__ == "__main__":
    main()
