"""Pin authenticated checkpoint bytes while training independently retires old files."""

import json
import os
import shutil
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.pretraining import weights
from kagg_revue.learning.storage.artifacts import resolve
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.spatial.model import Policy


def capture(run: Path, state: dict[str, Any], destination: Path) -> str:
    """Pin the ledger's selected member without locking or modifying the trainer."""
    member = str(state["latest"])
    source = resolve(run, state, member)
    destination.mkdir(parents=True, exist_ok=False)
    target = destination / "checkpoint.pt"
    try:
        try:
            os.link(source, target)
        except OSError:
            shutil.copyfile(source, target)
        expected = (
            state.get("inference_artifacts", {})
            .get(member, {})
            .get("sha256", state["members"][member])
        )
        if digest(target) != expected:
            raise ValueError("checkpoint changed while pinning its deployment snapshot")
        write_json(destination / "state.json", state)
    except BaseException:
        shutil.rmtree(destination)
        raise
    return member


def load(
    run: Path, member: str, snapshot: Path
) -> tuple[Experiment, dict[str, Any], Policy, dict[str, Any]]:
    """Authenticate a saved ledger and its pinned physical checkpoint representation."""
    state = json.loads((snapshot / "state.json").read_text())
    if not weights.valid_root(state) or state["protocol"]["output_dir"] != str(run):
        raise ValueError("snapshot does not belong to the declared policy root")
    weights.verify(run, state)
    expected = (
        state.get("inference_artifacts", {}).get(member, {}).get("sha256", state["members"][member])
    )
    checkpoint = snapshot / "checkpoint.pt"
    if member != state["latest"] or digest(checkpoint) != expected:
        raise ValueError("snapshot checkpoint differs from its ledger")
    policy, payload = load_policy(checkpoint, torch.device("cpu"))
    if payload.get("lineage", {}).get("run_id") != state["run_id"]:
        raise ValueError("snapshot checkpoint has a different lineage")
    return Experiment.model_validate(state["protocol"]), state, policy, payload
