"""Qualify an additive historical-pool repair against a stopped PPO checkpoint."""

import copy
import json
import os
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.archives import import_archive
from kagg_revue.learning.matchmaking.imports import registered, transition
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.matchmaking.verification import finite
from kagg_revue.learning.pretraining.weights import valid_root
from kagg_revue.learning.pretraining.weights import verify as verify_weights
from kagg_revue.learning.recovery.population import PopulationChange, changed_protocol
from kagg_revue.opponents.artifacts import identity as script_identity


def qualify(change: PopulationChange) -> dict[str, Any]:
    """Check all imported actors and preserved state before authorizing publication."""
    status = json.loads((change.run / "run-status.json").read_text())
    try:
        os.kill(status["pid"], 0)
    except ProcessLookupError:
        pass
    else:
        raise ValueError("history qualification requires a fully stopped checkpoint")
    ledger = change.run / "state.json"
    state_hash = digest(ledger)
    state = json.loads(ledger.read_text())
    old = Experiment.model_validate(state["protocol"])
    if (
        not valid_root(state)
        or change.historical_archive is None
        or change.batch is not None
        or change.execution is not None
        or old.execution is None
        or old.population.pfsp is None
        or not old.population.unified
        or old.script_population != change.script_population
    ):
        raise ValueError("history completion requires an unchanged authenticated PPO learner")
    verify_weights(change.run, state)
    config = changed_protocol(state, change.population, change.script_population)
    previous = old.population.model_dump()
    current = config.population.model_dump()
    if {key for key in current if current[key] != previous[key]} != {"sources", "capacity"}:
        raise ValueError("history completion may change only source selections and capacity")
    if any(source not in config.population.sources for source in old.population.sources):
        raise ValueError("history completion cannot remove or replace existing sources")
    identity = artifacts.source_identity()
    runtime = script_identity(change.script_population)
    if identity["native_sha256"] != state["native"] or any(
        state["script_runtime"].get(key) != value for key, value in runtime.items()
    ):
        raise ValueError("history completion cannot change native environment or scripts")
    payload = torch.load(
        artifacts.member_path(old, state, state["latest"]),
        map_location="cpu",
        weights_only=False,
        mmap=True,
    )
    if (
        payload.get("update") != state["completed_update"]
        or payload.get("pfsp") != state["pfsp"]
        or not finite(payload)
        or len(payload["rng"]["workers"]) != len(old.execution.devices)
    ):
        raise ValueError("checkpoint statistics, tensors or rank RNG are incomplete")
    simulated = copy.deepcopy(state)
    imported = import_archive(config, simulated, change.historical_archive, verify_only=True)
    if config.population.capacity - old.population.capacity != len(imported["added"]):
        raise ValueError("history capacity must preserve the existing own-snapshot allocation")
    transition(config, simulated, old)
    if (
        not registered(config, simulated)
        or simulated["pfsp"] != state["pfsp"]
        or set(simulated["pool"]) != set(state["pool"]) | set(imported["added"])
    ):
        raise ValueError("history completion changed incumbent evidence or pool membership")
    first = Matchmaker(config, simulated).select(
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
        "protocol": artifacts.protocol(config),
        "historical_archive": change.historical_archive.model_dump(mode="json"),
        "import_verification": imported,
        "finite_checkpoint_and_rank_rng": True,
        "incumbent_pool_and_pfsp_preserved": True,
        "foreign_pfsp_evidence_imported": False,
        "first_match": first.report,
        "qualification_scope": (
            "authenticated frozen actors, checkpoint and sampler; no GPU updates"
        ),
        "formal_post_resume_verification_required": True,
    }
    if digest(ledger) != state_hash or artifacts.source_identity() != identity:
        raise ValueError("training ledger or source changed during qualification")
    write_json(change.qualification, report)
    return report


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_population_change",
)
def main(configuration: DictConfig) -> None:
    """Bind the requested additive repair to its complete saved checkpoint."""
    change = PopulationChange.model_validate(
        OmegaConf.to_container(configuration.change, resolve=True)
    )
    report = qualify(change)
    print(json.dumps({"passed": report["passed"], "report": str(change.qualification)}), flush=True)


if __name__ == "__main__":
    main()
