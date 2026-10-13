"""Immutable policy roots and authenticated, same-run checkpoint membership."""

import hashlib
import json
import shutil
import subprocess
import tarfile
import time
import uuid
from pathlib import Path
from typing import Any

import orjson
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import rank_world, rng_snapshot
from kagg_revue.learning.initialization import random_policy
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.pretraining import critic as critic_weights
from kagg_revue.learning.pretraining import weights
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.storage.artifacts import resolve
from kagg_revue.learning.storage.publication import publish as publish_storage
from kagg_revue.learning.storage.roles import checkpoint_due, required_members
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import Policy


def source_identity() -> dict[str, Any]:
    """Hash tracked and untracked implementation files, including dirty edits."""
    names = subprocess.check_output(
        ["rg", "--files", "src", "configs", "pyproject.toml"], text=True
    ).splitlines()
    files = {
        name: digest(Path(name))
        for name in sorted(names)
        if Path(name).suffix
        in {".py", ".pyi", ".c", ".cpp", ".hpp", ".h", ".inc", ".cu", ".cuh", ".yaml", ".toml"}
        or Path(name).name == "CMakeLists.txt"
    }
    return {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "files": files,
        "source_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        "native_sha256": digest(Path(native.__file__)),
        "torch_version": torch.__version__,
    }


def protocol(config: Experiment) -> dict[str, Any]:
    """Normalize the continuation switch, leaving every experimental control bound."""
    result = config.model_copy(update={"resume": False}).model_dump(mode="json")
    if config.initial_weights is None:
        result.pop("initial_weights")  # Preserve existing random-root protocols.
    if config.initial_critic is None:
        result.pop("initial_critic")  # Preserve existing random-critic protocols.
    for key, default in (("gamma", 1.0), ("gae_lambda", 1.0), ("learning_rate_warmup_updates", 0)):
        if result[key] == default:
            result.pop(key)  # Preserve identities of archived direct-return runs.
    if not config.pretraining_only:
        result.pop("pretraining_only")  # Preserve existing continuation identities.
    if config.cash_margin is None:
        result.pop("cash_margin")  # Preserve archived reward protocol identities.
    if config.demonstrations is not None and config.demonstrations.early_stopping is None:
        result["demonstrations"].pop("early_stopping")
    if config.demonstrations is not None and not config.demonstrations.control_games:
        result["demonstrations"].pop("control_games")
    if config.demonstrations is not None and config.demonstrations.loss is None:
        result["demonstrations"].pop("loss")  # Preserve archived equal-row BC protocols.
    for key in ("schedule", "joint_learning_rate"):
        if config.demonstrations is not None and getattr(config.demonstrations, key) is None:
            result["demonstrations"].pop(key)
    if config.demonstrations is not None and config.demonstrations.epoch_checkpoint_interval == 1:
        result["demonstrations"].pop("epoch_checkpoint_interval")
    if config.kl_control == "rollback":
        result.pop("kl_control")
    if not config.gated and not config.memory_turns:
        for key in (
            "gated",
            "memory_turns",
            "memory_width",
            "memory_layers",
            "memory_tokens",
            "sequence_chunk_turns",
            "sequence_games_per_rank",
        ):
            result.pop(key)
    if not config.market_budget:
        result.pop("market_budget")  # Preserve archived policy protocol identities.
    if not config.joint_units:
        result.pop("joint_units")
    if not config.derived:
        result.pop("derived")  # Preserve v4 and earlier protocol identities.
    if config.execution is None:
        result.pop("execution")  # Preserve archived single-device protocol identities.
    elif config.execution.pipeline_groups == 1:
        result["execution"].pop("pipeline_groups")  # Preserve serial collection identities.
    if config.execution is not None and not config.execution.async_checkpoint:
        result["execution"].pop("async_checkpoint")  # Preserve synchronous save identities.
    if config.script_population is None:
        result.pop("script_population")  # Preserve pure-neural run protocol identities.
    if config.population.pfsp is None:
        result["population"].pop("pfsp")  # Preserve archived uniform population protocols.
    elif config.population.pfsp.script_sampling == "pfsp":
        result["population"]["pfsp"].pop("script_sampling")
    if config.population.pfsp is not None and config.population.pfsp.mastery is None:
        result["population"]["pfsp"].pop("mastery")  # Preserve archived PFSP identities.
    if config.population.pfsp is not None and config.population.pfsp.inheritance is None:
        result["population"]["pfsp"].pop("inheritance")
    if not config.population.sources:
        result["population"].pop("sources")
    if not config.population.unified:
        result["population"].pop("unified")
    return result


def write_ledger(directory: Path, state: dict[str, Any]) -> None:
    """Publish a compact ledger without Python's growing pretty-print serialization cost."""
    path = directory / "state.json"
    temporary = path.with_suffix(".json.partial")
    temporary.write_bytes(orjson.dumps(state, option=orjson.OPT_APPEND_NEWLINE))
    temporary.replace(path)


def create(config: Experiment, settings: RuntimeSettings) -> dict[str, Any]:
    """Archive a new run and construct its declared random or checkpoint actor root."""
    directory = config.output_dir
    occupied = {path.name for path in directory.iterdir()} if directory.exists() else set()
    if occupied - {"hydra", "train.log", "launch.json", "run.lock"}:
        raise FileExistsError("fresh initialization requires a new experiment directory")
    directory.mkdir(parents=True, exist_ok=True)
    identity = source_identity()
    with tarfile.open(directory / "source.tar.gz", "w:gz") as archive:
        for name in identity["files"]:
            archive.add(name, arcname=name, recursive=False)
    write_json(directory / "source.json", identity)
    native_path = Path(native.__file__)
    native_artifact = directory / "native" / native_path.name
    native_artifact.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(native_path, native_artifact)
    if digest(native_artifact) != identity["native_sha256"]:
        raise ValueError("native binary changed while archiving the random-root experiment")
    state: dict[str, Any] = {
        "schema": "random-root-league-v1",
        "run_id": uuid.uuid4().hex,
        "created_at": time.time(),
        "initialization": "random",
        "input_weights": [],
        "protocol": protocol(config),
        "source": identity["source_sha256"],
        "native": identity["native_sha256"],
        "native_artifact": str(native_artifact.relative_to(directory)),
        "members": {},
        "pool": ["initial.pt"],
        "completed_update": 0,
        "latest": "initial.pt",
        "records": [],
    }
    if config.script_population is not None:
        from kagg_revue.opponents.artifacts import archive as archive_scripts

        state["script_runtime"] = archive_scripts(directory, config.script_population)
    layout = ContractLayout.resolve(settings)
    inherited_critic = (
        critic_weights.archive(config, state, layout) if config.initial_critic is not None else None
    )
    for name, seed in [
        ("initial.pt", config.seed),
        *((f"anchors/seed-{seed}.pt", seed) for seed in config.evaluation.anchor_seeds),
    ]:
        transferred = name == "initial.pt" and config.initial_weights is not None
        actor = (
            weights.load(config, settings, state)
            if transferred
            else random_policy(layout, seed, config.exploration)
        )
        save_policy(
            directory / name,
            actor,
            settings,
            **({"critic": inherited_critic} if name == "initial.pt" and inherited_critic else {}),
            lineage={
                "run_id": state["run_id"],
                "kind": "checkpoint" if transferred else "random",
                "seed": seed,
                **(
                    {"parent_sha256": config.initial_weights.sha256}
                    if transferred and config.initial_weights is not None
                    else {}
                ),
            },
        )
        state["members"][name] = digest(directory / name)
    write_json(directory / "state.json", state)
    write_json(directory / "resolved-config.json", protocol(config))
    return state


def restore(config: Experiment) -> dict[str, Any]:
    """Require exact protocol/source identity and authenticate live dependencies only."""
    state: dict[str, Any] = json.loads((config.output_dir / "state.json").read_text())
    identity = source_identity()
    if (
        not weights.valid_root(state)
        or state["protocol"] != protocol(config)
        or state["source"] != identity["source_sha256"]
        or state["native"] != identity["native_sha256"]
    ):
        raise ValueError("resume must preserve the policy root, protocol, source, and native ABI")
    weights.verify(config.output_dir, state)
    critic_weights.verify(config.output_dir, state)
    if config.script_population is not None:
        from kagg_revue.learning.collection.public import records
        from kagg_revue.opponents.artifacts import identity as script_identity

        records(config.script_population)
        current_scripts = script_identity(config.script_population)
        registered = state.get("script_runtime", {})
        if any(registered.get(key) != value for key, value in current_scripts.items()):
            raise ValueError("resume must preserve the native script binary and route assets")
        for name, expected in registered["files"].items():
            path = (config.output_dir / registered["directory"] / name).resolve()
            if not path.is_relative_to(config.output_dir.resolve()) or digest(path) != expected:
                raise ValueError("archived script runtime differs from the experiment identity")
    if state["latest"] in state.get("inference_artifacts", {}):
        raise ValueError("latest recovery checkpoint must retain optimizer and RNG state")
    for name in required_members(config, state):
        member_path(config, state, name)
    if "native_artifact" in state:
        binary = (config.output_dir / state["native_artifact"]).resolve()
        if (
            not binary.is_relative_to(config.output_dir.resolve())
            or digest(binary) != state["native"]
        ):
            raise ValueError("archived native binary differs from the experiment identity")
    return state


def member_path(config: Experiment, state: dict[str, Any], name: str) -> Path:
    """Reject external or modified weights before checkpoint deserialization."""
    return resolve(config.output_dir, state, name)


def load_member(
    config: Experiment,
    state: dict[str, Any],
    name: str,
    device: torch.device,
) -> tuple[Policy, dict[str, Any]]:
    """Load only a registered descendant or independent random evaluation anchor."""
    actor, payload = load_policy(member_path(config, state, name), device)
    if payload.get("lineage", {}).get("run_id") != state["run_id"]:
        raise ValueError("checkpoint lineage differs from this experiment")
    return actor, payload


def budget_member(state: dict[str, Any], update: int) -> str:
    """Resolve zero online budget to the fixed initialization-stage control."""
    return (
        str(state.get("rl_initial", "initial.pt"))
        if update == 0
        else f"checkpoints/update-{update:06d}.pt"
    )


def checkpoint(
    config: Experiment,
    settings: RuntimeSettings,
    state: dict[str, Any],
    learner: Learner,
    update: int,
    metrics: dict[str, Any],
) -> None:
    """Collect every update, committing at the declared recovery boundaries."""
    state["records"].append(metrics)
    if checkpoint_due(config, update):
        commit_pending(config, settings, state, learner)


def commit_pending(
    config: Experiment,
    settings: RuntimeSettings,
    state: dict[str, Any],
    learner: Learner,
) -> None:
    """Save pending updates atomically, including on a graceful stop."""
    previous = state["completed_update"]
    if not state["records"] or state["records"][-1]["update"] <= previous:
        return
    update = state["records"][-1]["update"]
    name = f"checkpoints/update-{update:06d}.pt"
    rank, world = rank_world()
    rng = rng_snapshot(learner.device)
    if rank == 0:
        save_policy(
            config.output_dir / name,
            learner.policy,
            settings,
            update=update,
            critic=learner.critic.state_dict(),
            actor_optimizer=learner.actor_optimizer.state_dict(),
            critic_optimizer=learner.critic_optimizer.state_dict(),
            rng=rng,
            **({"pfsp": state["pfsp"]} if "pfsp" in state else {}),
            lineage={
                "run_id": state["run_id"],
                "kind": "reinforcement_learning",
                "root_sha256": state["members"]["initial.pt"],
                "parent_sha256": state["members"][state["latest"]],
            },
        )
    hashes = [digest(config.output_dir / name) if rank == 0 else None]
    if world > 1:
        torch.distributed.broadcast_object_list(hashes, src=0)
    state["members"][name] = hashes[0]
    state.update(completed_update=update, latest=name)
    if update % config.population.snapshot_interval == 0:
        from kagg_revue.learning.matchmaking.pool import snapshot

        snapshot(config, state, name)
    publish_storage(config, state)
    if rank != 0:
        return
    # The atomic ledger is authoritative. Resume rebuilds this display log if an
    # interruption happened between the ledger commit and these append writes.
    with (config.output_dir / "metrics.jsonl").open("a") as stream:
        for row in state["records"][previous:update]:
            stream.write(json.dumps(row) + "\n")


def publish_metrics(config: Experiment, state: dict[str, Any]) -> None:
    """Rebuild the display log from the authoritative atomic checkpoint ledger."""
    path = config.output_dir / "metrics.jsonl"
    temporary = path.with_suffix(".partial")
    temporary.write_text("".join(json.dumps(row) + "\n" for row in state["records"]))
    temporary.replace(path)
