"""Authenticate actor weight transfers without inheriting parent training state."""

import hashlib
import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.pretraining.config import InitialWeights
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.storage.artifacts import resolve
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.migration import expand_units, migrate_policy
from kagg_revue.policy.spatial.model import Policy

if TYPE_CHECKING:
    from kagg_revue.learning.config import Experiment


def valid_root(state: dict[str, Any]) -> bool:
    """Recognize the declared root kind without mislabelling transferred weights."""
    source = state["protocol"].get("initial_weights")
    if source is None:
        return bool(
            state["schema"] == "random-root-league-v1"
            and state["initialization"] == "random"
            and not state["input_weights"]
        )
    declared = InitialWeights.model_validate(source).model_dump(mode="json")
    return bool(
        state["schema"] == "checkpoint-root-league-v1"
        and state["initialization"] == "checkpoint"
        and state["input_weights"] == [declared]
        and (
            state["protocol"].get("pretraining_only")
            or state["protocol"].get("demonstrations") is None
        )
        and state.get("weight_transfer", {}).get("sha256") == declared["sha256"]
    )


def load(config: "Experiment", settings: RuntimeSettings, state: dict[str, Any]) -> Policy:
    """Copy a hash-pinned checkpoint and load only its compatible actor parameters."""
    source = config.initial_weights
    assert source is not None
    ledger = source.run / "state.json"
    parent_bytes = ledger.read_bytes()
    parent = json.loads(parent_bytes)
    if parent["members"].get(source.checkpoint) != source.sha256:
        raise ValueError("initial weights differ from the pinned parent checkpoint")
    checkpoint = resolve(source.run, parent, source.checkpoint)
    storage = parent.get("inference_artifacts", {}).get(source.checkpoint)
    artifact_sha256 = storage["sha256"] if storage else source.sha256
    target = config.output_dir / "weight-transfer" / "parent.pt"
    target.parent.mkdir(parents=True)
    shutil.copy2(checkpoint, target)
    if digest(target) != artifact_sha256:
        raise ValueError("initial weights changed while copying")
    actor, payload = load_policy(target, torch.device("cpu"))
    expected = ContractLayout.resolve(settings)
    migration = expansion = None
    if expected.network.joint_units and not actor.layout.network.joint_units:
        actor, expansion = expand_units(actor, expected)
    if config.derived and actor.layout != expected:
        actor, migration = migrate_policy(actor, expected)
    if (
        actor.layout != expected
        or payload.get("lineage", {}).get("run_id") != parent["run_id"]
        or any(not bool(torch.isfinite(value).all()) for value in actor.state_dict().values())
    ):
        raise ValueError("initial weights have incompatible geometry, lineage or nonfinite tensors")
    event = {
        **source.model_dump(mode="json"),
        "parent_run_id": parent["run_id"],
        "parent_source": parent["source"],
        "parent_state_sha256": hashlib.sha256(parent_bytes).hexdigest(),
        "parent_latest": parent["latest"],
        "parent_completed_update": parent["completed_update"],
        "checkpoint_update": payload.get("update"),
        "checkpoint_bc_cursor": payload.get("pretraining", {}).get("cursor"),
        "checkpoint_bc_rows": payload.get("pretraining", {}).get("rows"),
        "artifact": "weight-transfer/parent.pt",
        "artifact_sha256": artifact_sha256,
        "parent_checkpoint_storage": storage,
        "optimizer": "fresh BC Adam; parent optimizers are not resumed"
        if config.pretraining_only
        else (
            "fresh PPO actor/critic Adam; critic transferred separately; no parent optimizer"
            if config.initial_critic is not None
            else "fresh PPO actor/critic Adam and random critic; parent optimizers are not resumed"
        ),
        "rng": "new run seed; no parent RNG continuation",
    }
    if migration is not None:
        event["feature_migration"] = {
            "source": payload["layout"]["observation"]["version"],
            "target": expected.observation.version,
            "new_projection_initialization": "zero",
            **migration,
        }
    if expansion is not None:
        event["joint_unit_expansion"] = {"new_output_initialization": "zero", **expansion}
    state.update(
        schema="checkpoint-root-league-v1",
        initialization="checkpoint",
        input_weights=[source.model_dump(mode="json")],
        weight_transfer=event,
    )
    write_json(target.parent / "provenance.json", event)
    write_json(target.parent / "parent-protocol.json", parent["protocol"])
    return actor


def verify(directory: Path, state: dict[str, Any]) -> None:
    """Recover entirely from the preserved local parent copy, even if the old run moves."""
    if state["initialization"] == "checkpoint":
        source = state["weight_transfer"]
        path = (directory / source["artifact"]).resolve()
        if not path.is_relative_to(directory.resolve()) or digest(path) != source.get(
            "artifact_sha256", source["sha256"]
        ):
            raise ValueError("preserved initial checkpoint differs from its registered identity")
