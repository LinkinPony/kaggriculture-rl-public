"""Authenticate and preserve an independently selected pretrained PPO critic."""

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.matchmaking.imports import layout_from_payload
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.policy.contracts import ContractLayout

if TYPE_CHECKING:
    from kagg_revue.learning.config import Experiment


def archive(
    config: "Experiment", state: dict[str, Any], layout: ContractLayout
) -> dict[str, torch.Tensor]:
    """Copy a full registered donor checkpoint and validate every critic tensor."""
    source = config.initial_critic
    assert source is not None
    ledger = source.run / "state.json"
    parent = json.loads(ledger.read_text())
    checkpoint = source.run / source.checkpoint
    if (
        parent["members"].get(source.checkpoint) != source.sha256
        or digest(checkpoint) != source.sha256
    ):
        raise ValueError("initial critic differs from its registered parent checkpoint")
    target = config.output_dir / "critic-transfer" / "parent.pt"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(checkpoint, target)
    if digest(target) != source.sha256:
        raise ValueError("initial critic changed while copying")
    payload = torch.load(target, map_location="cpu", weights_only=False)
    if (
        "layout" not in payload
        or layout_from_payload(payload) != layout
        or payload.get("lineage", {}).get("run_id") != parent["run_id"]
        or not payload.get("critic")
        or any(not bool(torch.isfinite(value).all()) for value in payload["critic"].values())
    ):
        raise ValueError("initial critic has incompatible geometry, lineage or nonfinite tensors")
    with torch.random.fork_rng(devices=[]):
        model = MemoryCritic(layout) if config.memory_turns else PrefixCritic(layout)
        model.load_state_dict(payload["critic"], strict=True)
    event = {
        **source.model_dump(mode="json"),
        "parent_run_id": parent["run_id"],
        "parent_state_sha256": digest(ledger),
        "checkpoint_update": payload.get("update"),
        "artifact": str(target.relative_to(config.output_dir)),
        "tensor_count": len(payload["critic"]),
        "optimizer": "fresh PPO Adam; critic weights inherited, donor optimizer not resumed",
    }
    state["critic_transfer"] = event
    write_json(target.parent / "provenance.json", event)
    return dict(payload["critic"])


def verify(directory: Path, state: dict[str, Any]) -> None:
    """Recover using the authenticated local copy without needing the donor run."""
    source = state["protocol"].get("initial_critic")
    if source is None:
        return
    transfer = state.get("critic_transfer", {})
    artifact = directory / transfer.get("artifact", "missing")
    if (
        any(transfer.get(key) != value for key, value in source.items())
        or not artifact.resolve().is_relative_to(directory.resolve())
        or not artifact.is_file()
        or digest(artifact) != source["sha256"]
    ):
        raise ValueError("preserved initial critic differs from its registered identity")
