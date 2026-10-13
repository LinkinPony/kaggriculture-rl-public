"""Prepare a new learner with a predecessor's full authenticated opponent archive."""

import fcntl
import json
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.archives import HistoricalArchive, import_archive
from kagg_revue.learning.matchmaking.config import HistoricalSource
from kagg_revue.learning.matchmaking.defaults import training_defaults
from kagg_revue.learning.matchmaking.imports import import_opponents, registered, transition
from kagg_revue.learning.matchmaking.inheritance import inherit


def _archived(source: HistoricalSource, donor: dict[str, Any]) -> bool:
    """Whether the predecessor already registered every selected member of this source."""
    registry = donor.get("external_opponents", {})
    hits = [
        registry.get(f"historical/{source.run.name}/{Path(member).name}", {}).get("state_sha256")
        == source.state_sha256
        for member in source.checkpoints
    ]
    if any(hits) and not all(hits):
        raise ValueError(f"source is only partially registered by the archive: {source.run}")
    return all(hits)


def prepare(config: Experiment, archive: HistoricalArchive) -> dict[str, Any]:
    """Freeze inherited opponents and initialize new PFSP evidence before any PPO step.

    Sources the predecessor never registered are imported directly from their own
    ledgers, like the predecessor's own checkpoints.
    """
    if config.resume or config.pretraining_only or config.demonstrations is not None:
        raise ValueError("opponent bootstrap requires a fresh PPO experiment")
    if config.population.pfsp is None or config.initial_weights is None:
        raise ValueError("opponent bootstrap requires PFSP and explicit initial weights")
    config = training_defaults(config)
    donor = json.loads((archive.run / "state.json").read_text())
    own = tuple(s for s in config.population.sources if s.run == archive.run)
    others = tuple(s for s in config.population.sources if s.run != archive.run)
    inherited = tuple(s for s in others if _archived(s, donor))
    fresh = tuple(s for s in others if s not in inherited)
    if len(own) != 1 or own[0].state_sha256 != archive.state_sha256 or not inherited:
        raise ValueError("declare the predecessor's own and inherited opponents explicitly")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    with (config.output_dir / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = artifacts.create(config, runtime_settings(config))
        inherited_config = config.model_copy(
            update={"population": config.population.model_copy(update={"sources": inherited})}
        )
        evidence = import_archive(inherited_config, state, archive)
        own_config = config.model_copy(
            update={"population": config.population.model_copy(update={"sources": own + fresh})}
        )
        import_opponents(own_config, state)
        if not registered(config, state):
            raise ValueError("new-run opponent registration is incomplete")
        transition(config, state, config)
        if state["pfsp"]["records"] or state["completed_update"]:
            raise ValueError("new learner cannot carry unregistered match outcomes")
        assert config.population.pfsp is not None
        seeded = (
            inherit(config, state, (archive,))
            if config.population.pfsp.inheritance is not None
            else None
        )
        result: dict[str, Any] = {
            "archive": evidence,
            "own_source": own[0].model_dump(mode="json"),
            "fresh_sources": [source.model_dump(mode="json") for source in fresh],
            "external_opponents": len(state["external_opponents"]),
            "policy_pool": len(state["pool"]),
            "statistics": (
                "discounted predecessor evidence for unmet opponents; own outcomes start empty"
                if seeded is not None
                else "fresh learner prior; predecessor evidence remains in its archive"
            ),
            **({"pfsp_inheritance": seeded} if seeded is not None else {}),
        }
        state["opponent_bootstrap"] = result
        artifacts.write_ledger(config.output_dir, state)
        write_json(config.output_dir / "opponent-bootstrap.json", result)
        return result


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_agronomy_watch2_ppo_20260922",
)
def main(configuration: DictConfig) -> None:
    """Prepare the pinned Hydra protocol, then launch it through normal resume handling."""
    config = Experiment.model_validate(
        OmegaConf.to_container(configuration.experiment, resolve=True)
    )
    archive = HistoricalArchive.model_validate(
        OmegaConf.to_container(configuration.historical_archive, resolve=True)
    )
    result = prepare(config, archive)
    print(
        {key: result[key] for key in ("external_opponents", "policy_pool", "statistics")},
        flush=True,
    )


if __name__ == "__main__":
    main()
