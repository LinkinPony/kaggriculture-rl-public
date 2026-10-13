"""Checkpoint identity and direct-outcome reports for the gradual transfer."""

from dataclasses import replace
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import save_policy
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.config import Settings
from kagg_revue.production.evaluation import panel
from kagg_revue.production.migration.config import MigrationSettings


def load_migration(path: Path, config: MigrationSettings, *, continuation: bool) -> dict[str, Any]:
    """Allow a fade or PPO actor-rate continuation while preserving other controls."""
    saved: dict[str, Any] = torch.load(path, map_location="cpu", weights_only=False)
    previous = dict(saved["migration_configuration"])
    if continuation:
        for key in (
            "minimum_stage_updates",
            "maximum_stage_updates",
            "confirmation_games",
            "initial_likelihood_tolerance",
        ):
            previous.pop(key, None)
        previous.update(
            resume_from=config.resume_from,
            scale_step=config.scale_step,
            scale_interval=config.scale_interval,
        )
        previous["production"] = {
            **previous["production"],
            "output_dir": config.production.output_dir,
        }
        if saved.get("training_phase") == "ppo":
            previous["production"]["ppo"] = {
                **previous["production"]["ppo"],
                "actor_learning_rate": config.production.ppo.actor_learning_rate,
            }
    if MigrationSettings.model_validate(previous) != config:
        raise ValueError("resume changed controls beyond the fade schedule or PPO actor rate")
    return saved


def at_scale(settings: Settings, scale: float, *, table: bool = True) -> Settings:
    """Describe the actual student function evaluated or saved at this stage."""
    return settings.model_copy(
        update={
            "model": settings.model.model_copy(update={"prior_scale": scale, "time_prior": table})
        }
    )


def save_student(
    path: Path, policy: WorkPolicy, settings: Settings, coefficient: float, **state: Any
) -> None:
    """Store the scale in the layout without invalidating compiled model guards."""
    original = policy.layout
    policy.layout = replace(original, network=replace(original.network, prior_scale=coefficient))
    try:
        save_policy(
            path,
            policy,
            at_scale(settings, coefficient, table=original.network.time_prior),
            **state,
        )
    finally:
        policy.layout = original


def evaluate_student(
    directory: Path,
    settings: Settings,
    policy: Policy,
    scale: float,
    seed: int,
    identity: dict[str, Any],
    checkpoint: Path,
) -> dict[str, dict[str, Any]]:
    """Keep greedy and sampled complete paired matches on the direct outcome surface."""
    resolved = at_scale(settings, scale, table=policy.layout.network.time_prior)
    results = {
        name: panel(resolved, policy, seed, sample=sample)
        for name, sample in (("greedy", False), ("sampled", True))
    }
    write_json(
        directory / "comparison.json",
        {
            "source": identity,
            "resolved_profile": resolved.model_dump(mode="json"),
            "checkpoint": {"path": str(checkpoint), "sha256": digest(checkpoint)},
            "prior_scale": scale,
            "results": results,
            "automatic_promotion": False,
        },
    )
    return results
