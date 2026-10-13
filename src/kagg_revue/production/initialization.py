"""Explicit checkpoint ablations that preserve the remaining learned state."""

from dataclasses import replace
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import Settings


def extract_actor(source: Path, settings: Settings) -> Path:
    """Freeze exact actor weights for a new optimizer and independent critics."""
    destination = settings.checkpoint
    if (
        destination is None
        or destination.is_absolute()
        or ".." in destination.parts
        or destination.parts[:1] != ("outputs",)
    ):
        raise ValueError("the extracted checkpoint must be an explicit outputs artifact")
    if destination.exists():
        raise FileExistsError(destination)
    policy, payload = load_policy(source, torch.device("cpu"))
    if policy.layout != ContractLayout.resolve(settings):
        raise ValueError("actor extraction must preserve the complete policy semantics")
    parent = {
        "path": str(source),
        "sha256": digest(source),
        "generation": payload.get("generation"),
        "update": payload.get("update"),
    }
    save_policy(destination, policy, settings, parent=parent)
    restored, saved = load_policy(destination, torch.device("cpu"))
    if any(
        not torch.equal(value, restored.state_dict()[name])
        for name, value in policy.state_dict().items()
    ) or set(saved) != {"layout", "model", "settings", "parent"}:
        raise ValueError("extraction changed the actor or retained optimizer state")
    write_json(
        destination.parent / "release.json",
        {
            "source": parent,
            "checkpoint": str(destination),
            "sha256": digest(destination),
            "retained_state": "exact actor weights and layout; new optimizers and critics",
            "actor_verified_equal": True,
            "provenance": provenance(settings),
            "metadata_device": "CPU for checkpoint extraction; no inference or training",
        },
    )
    return destination


def remove_optimizer_parameter(
    optimizer: dict[str, Any], names: list[str], removed: str
) -> dict[str, Any]:
    """Remove one named parameter from the learner's single ordered Adam group."""
    groups = optimizer["param_groups"]
    if len(groups) != 1 or len(groups[0]["params"]) != len(names):
        raise ValueError("optimizer must contain the complete ordered actor parameter group")
    identifiers = groups[0]["params"]
    if len(set(names)) != len(names) or len(set(identifiers)) != len(identifiers):
        raise ValueError("parameter names and optimizer identifiers must be unique")
    removed_id = identifiers[names.index(removed)]
    return {
        **optimizer,
        "param_groups": [
            {**groups[0], "params": [key for key in identifiers if key != removed_id]}
        ],
        "state": {key: value for key, value in optimizer["state"].items() if key != removed_id},
    }


def remove_time_prior(source: Path, settings: Settings) -> Path:
    """Fork a resumed PPO actor without its time table or its Adam moments."""
    destination = settings.checkpoint
    if (
        destination is None
        or destination.is_absolute()
        or not destination.parts
        or ".." in destination.parts
        or destination.parts[0] != "outputs"
    ):
        raise ValueError("the stripped checkpoint must be an explicit outputs artifact")
    if destination.exists() or source.resolve() == destination.resolve():
        raise FileExistsError("preserve the frozen source and use a new checkpoint destination")
    torch.set_num_threads(settings.cpu_threads)
    original, payload = load_policy(source, torch.device("cpu"))
    if not original.layout.work or not original.layout.network.time_prior:
        raise ValueError("source must be a work actor with an enabled time prior")
    layout = replace(original.layout, network=replace(original.layout.network, time_prior=False))
    if layout != ContractLayout.resolve(settings):
        raise ValueError("removing the time prior must not change other model semantics")
    policy = Policy.from_layout(layout)
    state = {key: value for key, value in original.state_dict().items() if key != "prior"}
    policy.load_state_dict(state)
    optimizer = remove_optimizer_parameter(
        payload["actor_optimizer"], [name for name, _ in original.named_parameters()], "prior"
    )
    # Exercise the same ordered-parameter restoration used by the resumed learner.
    restored = torch.optim.AdamW(policy.parameters())
    restored.load_state_dict(optimizer)
    for parameter in policy.parameters():
        moments = restored.state.get(parameter, {})
        if any(
            moments[key].shape != parameter.shape
            for key in ("exp_avg", "exp_avg_sq")
            if key in moments
        ):
            raise ValueError("remaining optimizer moments do not match their actor parameters")
    identity = provenance(settings)
    parent = {"path": str(source), "sha256": digest(source), "update": payload["update"]}
    save_policy(
        destination,
        policy,
        settings,
        update=payload["update"],
        critic=payload["critic"],
        actor_optimizer=optimizer,
        critic_optimizer=payload["critic_optimizer"],
        rank_rng=payload["rank_rng"],
        baseline_checkpoint=str(destination),
        parent=parent,
        provenance=identity,
    )
    write_json(
        destination.parent / "release.json",
        {
            "source": parent,
            "checkpoint": str(destination),
            "sha256": digest(destination),
            "update": payload["update"],
            "first_training_update": int(payload["update"]) + 1,
            "time_prior": False,
            "removed_parameter": "prior",
            "retained_state": "all other actor weights/moments, critic, critic optimizer, rank RNG",
            "baseline": "this stripped initializer; the intact parent remains an external control",
            "provenance": identity,
            "metadata_device": "CPU for checkpoint migration; no inference or training",
        },
    )
    return destination
