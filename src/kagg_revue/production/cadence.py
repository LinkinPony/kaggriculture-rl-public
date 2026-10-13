"""Controlled cadence transfer without changing the learned entity representation."""

import bisect
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import torch
from torch import Tensor

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native.features import Layout
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import Settings


def prior_indices(source: tuple[int, ...], target: tuple[int, ...]) -> list[int]:
    """Preserve the source policy's active calendar prior at every new decision time."""
    if not source or not target or source[0] != 0 or target[0] != 0:
        raise ValueError("decision calendars must begin at the initial observation")
    if list(source) != sorted(set(source)) or list(target) != sorted(set(target)):
        raise ValueError("decision calendars must be strictly increasing")
    return [bisect.bisect_right(source, turn) - 1 for turn in target]


def rehearsal_steps(
    manifest: dict[str, Any], layout: ContractLayout, device: torch.device
) -> Tensor:
    """Map unchanged BC observations to their exact times in the new action calendar."""
    stored = manifest["layout"]
    if (stored.get("network", {}).get("architecture") == "work-v1") != layout.work:
        raise ValueError("BC action language must match the current actor")
    if layout.work and (
        stored["interval"] != layout.interval
        or stored.get("late_interval", 0) != layout.late_interval
        or stored.get("late_start", 0) != layout.late_start
    ):
        raise ValueError("timed work programs require their original decision calendar")
    if replace(Layout(**stored["observation"]), width=0) != replace(layout.observation, width=0):
        raise ValueError("BC observation features must match the current actor")
    old = tuple(range(0, int(stored["observation"]["turns"]), int(stored["interval"])))
    if stored.get("late_interval", 0):
        old = (
            *range(0, stored["late_start"], stored["interval"]),
            *range(stored["late_start"], layout.observation.turns, stored["late_interval"]),
        )
    target = {turn: index for index, turn in enumerate(layout.starts)}
    if any(turn not in target for turn in old):
        raise ValueError("BC observations must fall on actual policy decision boundaries")
    return torch.tensor([target[turn] for turn in old], device=device, dtype=torch.long)


def _adapt(path: Path, layout: ContractLayout) -> tuple[Policy, dict[str, Any]]:
    source, payload = load_policy(path, torch.device("cpu"))
    if layout.work:
        raise ValueError("timed work programs require new proposals for a changed calendar")
    if source.layout.observation != layout.observation or source.layout.network != layout.network:
        raise ValueError("cadence transfer must preserve the entity architecture and features")
    policy = Policy.from_layout(layout)
    state = source.state_dict()
    state["prior"] = state["prior"][prior_indices(source.layout.starts, layout.starts)].clone()
    policy.load_state_dict(state)
    return policy, payload


def transfer(settings: Settings) -> None:
    """Initialize a controlled challenger from frozen actor/critic weights with fresh optimizers."""
    if settings.checkpoint is None:
        raise ValueError("cadence transfer requires a frozen source checkpoint")
    torch.set_num_threads(settings.cpu_threads)
    layout = ContractLayout.resolve(settings)
    policy, source = _adapt(settings.checkpoint, layout)
    initial = settings.output_dir / "initial.pt"
    baseline_path = settings.output_dir / "baseline-bc.pt"
    if initial.exists() or baseline_path.exists():
        raise FileExistsError("cadence initialization artifacts already exist")
    baseline_source = Path(source["baseline_checkpoint"])
    baseline, _ = _adapt(baseline_source, layout)
    identity = provenance(settings)
    save_policy(baseline_path, baseline, settings, provenance=identity)
    save_policy(
        initial,
        policy,
        settings,
        critic=source["critic"],
        baseline_checkpoint=str(baseline_path),
        provenance=identity,
    )
    write_json(
        settings.output_dir / "transfer.json",
        {
            "source_checkpoint": str(settings.checkpoint),
            "source_sha256": digest(settings.checkpoint),
            "source_update": source["update"],
            "initial_checkpoint_sha256": digest(initial),
            "baseline_source": str(baseline_source),
            "baseline_source_sha256": digest(baseline_source),
            "new_decision_turns": layout.starts,
            "actor_and_critic_weights_preserved": True,
            "calendar_prior": "copy the source prior active at each target official turn",
            "optimizers": "fresh for every challenger, including the fixed-cadence control",
            "bc_rehearsal": "unchanged observations and labels mapped to actual calendar times",
            "source": identity,
        },
    )
    print(json.dumps({"initial": str(initial), "decisions": layout.decisions}), flush=True)
