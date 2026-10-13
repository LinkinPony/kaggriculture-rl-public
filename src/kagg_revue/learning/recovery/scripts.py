"""Bind offline native-script qualification to an unchanged stopped PPO continuation."""

import copy
import json
import os
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.league.verification import _finite
from kagg_revue.learning.matchmaking.imports import transition
from kagg_revue.learning.matchmaking.migration import restored_statistics
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.recovery.population import PopulationChange, changed_protocol
from kagg_revue.opponents.artifacts import identity as script_identity


class Evidence(FrozenSettings):
    """Completed original-source comparisons and the real neural batch boundary."""

    conformance: Path
    official: Path
    throughput: Path


def qualify(change: PopulationChange, evidence: Evidence) -> dict[str, Any]:
    """Require unchanged PPO controls and bind only actually completed offline checks."""
    status = json.loads((change.run / "run-status.json").read_text())
    try:
        os.kill(status["pid"], 0)
    except ProcessLookupError:
        pass
    else:
        raise ValueError("checkpoint binding requires a fully saved, stopped training process")
    state_path = change.run / "state.json"
    state_hash = digest(state_path)
    state = json.loads(state_path.read_text())
    old = Experiment.model_validate(state["protocol"])
    if (
        old.script_population is None
        or old.population != change.population
        or old.population.pfsp is None
        or old.execution is None
        or not old.population.unified
        or change.batch is not None
        or change.execution is not None
    ):
        raise ValueError("offline refresh requires an existing unchanged unified PFSP protocol")
    config = changed_protocol(state, change.population, change.script_population)
    protocol = artifacts.protocol(config)
    if {key for key in protocol if protocol[key] != state["protocol"].get(key)} != {
        "script_population"
    }:
        raise ValueError("native script refresh must preserve every learner and sampling control")
    added = set(change.script_population.agents) - set(old.script_population.agents)
    if not added or not set(old.script_population.agents) <= set(change.script_population.agents):
        raise ValueError("this refresh must extend the current script pool")
    identity = artifacts.source_identity()
    runtime = script_identity(change.script_population)
    if identity["native_sha256"] != state["native"]:
        raise ValueError("native refresh cannot change the authenticated rule engine")
    binary = next(value for name, value in runtime["files"].items() if name.endswith(".so"))
    for name, fingerprint in state["script_runtime"]["files"].items():
        if not name.endswith(".so") and runtime["files"].get(name) != fingerprint:
            raise ValueError("an incumbent script asset changed")
    paths = evidence.model_dump()
    reports = {name: json.loads(path.read_text()) for name, path in paths.items()}
    for report in reports.values():
        if report.get("binary_sha256") != binary:
            raise ValueError("offline evidence belongs to a different native binary")
    parity, official, throughput = (reports[name] for name in paths)
    games = json.loads(evidence.conformance.with_name("games.json").read_text())
    covered = {(name, seat) for game in games for seat, name in enumerate(game["agents"])}
    if (
        not parity["passed"]
        or not games
        or not all(game["passed"] and game["actions"] == 1438 for game in games)
        or not {(name, seat) for name in added for seat in (0, 1)} <= covered
        or parity["manifest_sha256"] != change.script_population.sha256
        or not official["passed"]
        or not added <= set(official["opponents"])
        or official["matched_script_actions"] != 719 * official["games"]
        or not official["official_reference"]["matched"]
        or not official["script_prefetch"]
        or not throughput["complete"]
        or not added <= {row["opponent"] for row in throughput["panels"]}
    ):
        raise ValueError(
            "native conformance, both-seat neural integration or throughput is incomplete"
        )
    checkpoint = artifacts.member_path(old, state, state["latest"])
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if (
        payload.get("update") != state["completed_update"]
        or not _finite(payload)
        or len(payload["rng"]["workers"]) != len(old.execution.devices)
    ):
        raise ValueError("checkpoint tensors or per-rank RNG are incomplete")
    migrated = copy.deepcopy(state)
    transition(config, migrated, old)
    if restored_statistics(payload.get("pfsp"), migrated) != migrated["pfsp"]:
        raise ValueError("checkpoint PFSP cannot replay the registered manifest migration")
    if state["pool"] != migrated["pool"] or state["members"] != migrated["members"]:
        raise ValueError("script refresh changed historical checkpoint membership")
    moved = {
        row["source"]: row["target"] for row in migrated["script_identity_history"][-1]["moved"]
    }
    for key, value in state["pfsp"]["records"].items():
        if migrated["pfsp"]["records"].get(moved.get(key, key)) != value:
            raise ValueError("script refresh changed incumbent PFSP evidence")
    first = Matchmaker(config, migrated).select(
        state["completed_update"] + 1, len(old.execution.devices)
    )
    report = {
        "passed": True,
        "run_id": state["run_id"],
        "completed_update": state["completed_update"],
        "checkpoint_sha256": state["members"][state["latest"]],
        "source_state_sha256": state_hash,
        "source_sha256": identity["source_sha256"],
        "native_sha256": state["native"],
        "script_runtime": runtime,
        "protocol": protocol,
        "qualification_scope": (
            "offline full-game native parity and real-checkpoint neural rollout; "
            "unchanged PPO controls"
        ),
        "separate_gpu_qualification_updates": 0,
        "formal_post_resume_verification_required": True,
        "evidence": {
            name: {"path": str(path), "sha256": digest(path)} for name, path in paths.items()
        },
        "finite_checkpoint_and_rank_rng": True,
        "old_script_assets_unchanged": True,
        "script_identity_migration": migrated["script_identity_history"][-1],
        "first_match": first.report,
    }
    if digest(state_path) != state_hash or artifacts.source_identity() != identity:
        raise ValueError("checkpoint ledger or implementation changed during qualification")
    write_json(change.qualification, report)
    return report


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="learning_compact_scripts_refresh_20260921",
)
def main(configuration: DictConfig) -> None:
    """Freeze reviewed native evidence immediately before an authorized pool extension."""
    change = PopulationChange.model_validate(
        OmegaConf.to_container(configuration.change, resolve=True)
    )
    evidence = Evidence.model_validate(OmegaConf.to_container(configuration.evidence, resolve=True))
    print(json.dumps(qualify(change, evidence)), flush=True)


if __name__ == "__main__":
    main()
