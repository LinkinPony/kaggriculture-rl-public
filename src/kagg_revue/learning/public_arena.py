"""Frozen external-script evaluation, isolated from the neural training population."""

import json
import multiprocessing
import tarfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Literal

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.deployment.actor import freeze
from kagg_revue.evaluation.comparison import paired_cash, paired_scores
from kagg_revue.evaluation.public import PublicGame, play
from kagg_revue.learning.state import budget_member, load_member, source_identity
from kagg_revue.learning.validation import validated_run
from kagg_revue.opponents.public import load_public_agent_manifest, resolve_public_agent_path


class PublicArena(FrozenSettings):
    """Registered new candidates and exact reviewed public source identities."""

    runs: tuple[Path, ...]
    updates: tuple[int, ...]
    manifest: Path
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_dir: Path
    reference_directory: Path
    seed: int = Field(ge=0)
    games_per_opponent: int = Field(default=64, gt=0, multiple_of=2)
    workers: int = Field(default=8, gt=0, le=32)
    role: Literal["selection", "confirmation"] = "selection"

    @model_validator(mode="after")
    def validate_panel(self) -> "PublicArena":
        """Require paired complete budgets and explicit artifact roles."""
        if not self.runs or len(set(self.runs)) != len(self.runs):
            raise ValueError("public arena requires unique candidate runs")
        if (
            not self.updates
            or self.updates[0] != 0
            or tuple(sorted(set(self.updates))) != self.updates
        ):
            raise ValueError("public arena requires an initial control and ordered unique budgets")
        for path, prefix in (
            (self.manifest, ("data", "external")),
            (self.reference_directory, ("data", "external")),
            (self.output_dir, ("outputs", "analysis")),
        ):
            if path.is_absolute() or ".." in path.parts or path.parts[:2] != prefix:
                raise ValueError("public arena path has the wrong artifact role")
        return self


def run(config: PublicArena) -> None:
    """Export authenticated members, then measure a frozen paired script panel."""
    if digest(config.manifest) != config.manifest_sha256:
        raise ValueError("public evaluation manifest identity differs")
    manifest = load_public_agent_manifest(config.manifest)
    if not manifest.agents or len({a.sha256 for a in manifest.agents}) != len(manifest.agents):
        raise ValueError("public panel requires unique nonempty reviewed scripts")
    for opponent in manifest.agents:
        resolve_public_agent_path(opponent, Path.cwd())
    runs = [
        validated_run(
            path, seed=config.seed, games_per_opponent=config.games_per_opponent, role=config.role
        )
        for path in config.runs
    ]
    for experiment, state in runs:
        if max(config.updates) > state["completed_update"] or (
            config.role == "confirmation" and state["completed_update"] != experiment.updates
        ):
            raise ValueError("requested public arena budget has not completed")
    occupied = (
        {path.name for path in config.output_dir.iterdir()} if config.output_dir.exists() else set()
    )
    if occupied - {"hydra"}:
        raise FileExistsError("public arena requires an unused report directory")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    source = source_identity()
    with tarfile.open(config.output_dir / "source.tar.gz", "w:gz") as archive:
        for name in source["files"]:
            archive.add(name, arcname=name, recursive=False)
    protocol = {
        "configuration": config.model_dump(mode="json"),
        "source": source,
        "source_archive_sha256": digest(config.output_dir / "source.tar.gz"),
        "opponents": [a.model_dump(mode="json") for a in manifest.agents],
        "candidates": [
            {
                "run": str(experiment.output_dir),
                "run_id": state["run_id"],
                "members": {
                    str(update): state["members"][budget_member(state, update)]
                    for update in config.updates
                },
            }
            for experiment, state in runs
        ],
        "sampling": "FP32 CPU TorchScript; private RNG = 2 * environment_seed + candidate_seat; "
        "paired across budgets, no per-turn reseeding or greedy conversion",
    }
    write_json(config.output_dir / "protocol.json", protocol)
    torch.set_num_threads(1)
    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(
        max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        for experiment, state in runs:
            initial = previous = None
            for update in config.updates:
                actor, _ = load_member(
                    experiment, state, budget_member(state, update), torch.device("cpu")
                )
                layout = actor.layout
                if (
                    layout.network.architecture not in {"grounded-v1", "grounded-v2"}
                    or layout.capacity != 1
                ):
                    raise ValueError("public arena requires grounded single-turn actors")
                directory = config.output_dir / experiment.output_dir.name
                directory.mkdir(exist_ok=True)
                path = directory / f"{update:06d}.pt"
                freeze(actor, path)
                sha = digest(path)
                environment = experiment.environment
                jobs = [
                    PublicGame(
                        path,
                        sha,
                        environment,
                        experiment.unit_limit,
                        layout.observation.features,
                        tuple(layout.observation.quantities),
                        opponent.model_dump(mode="json"),
                        config.reference_directory,
                        config.seed + index // 2,
                        index % 2,
                    )
                    for opponent in manifest.agents
                    for index in range(config.games_per_opponent)
                ]
                games = list(pool.map(play, jobs))
                record = {
                    "run": str(experiment.output_dir),
                    "run_id": state["run_id"],
                    "update": update,
                    "checkpoint_sha256": state["members"][budget_member(state, update)],
                    "actor_sha256": sha,
                    "mean_score": float(np.mean([(g["outcome"] + 1) / 2 for g in games])),
                    "mean_cash": float(np.mean([g["cash"] for g in games])),
                    "mean_opponent_cash": float(np.mean([g["opponent_cash"] for g in games])),
                    "games": games,
                }
                initial = record if initial is None else initial
                record["paired_initial_score"] = paired_scores(initial, record)
                record["paired_initial_cash"] = paired_cash(initial, record)
                if previous is not None:
                    record["paired_previous_score"] = paired_scores(previous, record)
                    record["paired_previous_cash"] = paired_cash(previous, record)
                previous = record
                results.append(record)
                write_json(directory / f"{update:06d}.json", record)
                print(json.dumps({k: v for k, v in record.items() if k != "games"}), flush=True)
    if source_identity() != source or digest(config.manifest) != config.manifest_sha256:
        raise ValueError("public arena source changed while measuring")
    write_json(
        config.output_dir / "comparison.json",
        {
            **protocol,
            "results": results,
            "scope": "Frozen public-script panel, official observations and complete state parity. "
            "FP32 CPU stochastic policies; not BF16 GPU trajectory identity, current leaderboard "
            "rating, unseen-policy-family coverage, or Kaggle deployment-budget certification.",
        },
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="learning_public_arena",
)
def main(configuration: DictConfig) -> None:
    """Resolve frozen external evidence before any model or public script executes."""
    run(PublicArena.model_validate(OmegaConf.to_container(configuration.arena, resolve=True)))


if __name__ == "__main__":
    main()
