"""Checkpoint-bound membership changes with immutable pre-transition recovery state."""

import copy
import fcntl
import os
import shutil
import time
from pathlib import Path
from typing import Any, Literal

import hydra
import orjson
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.collection.public import records
from kagg_revue.learning.league.config import League
from kagg_revue.learning.league.revision import stopped_state
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining.config import Demonstrations
from kagg_revue.learning.recovery.cli import Recovery
from kagg_revue.opponents.artifacts import archive as archive_scripts
from kagg_revue.opponents.artifacts import identity as script_identity
from kagg_revue.opponents.portfolios.catalog import ACTIVE_IDS


class PopulationChange(Recovery):
    """Explicit two-member/five-script composition and separate qualification artifacts."""

    mode: Literal["qualify", "apply"] = "qualify"
    manifest: Path
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    games_per_pair: int = Field(default=32, gt=0)
    selfplay_games_per_member: int = Field(default=40, gt=0)
    games_per_script_per_member: int = Field(default=8, gt=0)
    destination: Path
    report: Path
    report_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


def proposed(state: dict[str, Any], change: PopulationChange) -> League:
    """Retain the training budget, data origins, seeds and optimization settings."""
    games = state["protocol"]["experiment"]["games"]
    protocol = copy.deepcopy(state["protocol"])
    protocol.update(
        members=["bc", "spataro"],
        games_per_pair=change.games_per_pair,
        selfplay_games_per_member=change.selfplay_games_per_member,
        games_per_script_per_member=change.games_per_script_per_member,
    )
    protocol["experiment"]["script_population"] = {
        "manifest": str(change.manifest),
        "sha256": change.manifest_sha256,
        "agents": ACTIVE_IDS,
        "backend": "native-cpp",
        "fraction": 2 * len(ACTIVE_IDS) * change.games_per_script_per_member / games,
    }
    config = League.model_validate(protocol)
    assert config.experiment.script_population is not None
    records(config.experiment.script_population)
    return config


def filtered_checkpoint(source: Path, state: dict[str, Any], config: League, target: Path) -> str:
    """Remove retired model tensors while preserving retained weights, optimizers and RNG."""
    payload = torch.load(source / state["latest"], map_location="cpu", weights_only=False)
    if (
        payload["members"] != state["members"]
        or payload["update"] != state["completed_update"]
        or payload["run_id"] != state["run_id"]
    ):
        raise ValueError("source checkpoint membership, update or lineage differs")
    payload["members"] = {name: payload["members"][name] for name in config.members}
    payload["models"] = {name: payload["models"][name] for name in config.members}
    payload["parent_sha256"] = state["checkpoints"][state["latest"]]
    target.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, target.with_suffix(".partial"))
    target.with_suffix(".partial").replace(target)
    return digest(target)


def child_state(
    source: Path,
    name: str,
    config: League,
    identity: dict[str, Any],
    target: Path,
    source_directory: str = ".",
) -> dict[str, Any]:
    """Authenticate the original BC artifacts and archive the new native script runtime."""
    child = orjson.loads((source / name / "state.json").read_bytes())
    if child["native"] != identity["native_sha256"]:
        raise ValueError("membership changes must retain the qualified rules core")
    recipe = config.member(
        name, committed=Demonstrations.model_validate(child["protocol"]["demonstrations"])
    )
    assert config.experiment.script_population is not None
    return {
        **child,
        "protocol": artifacts.protocol(recipe),
        "source": identity["source_sha256"],
        "source_directory": source_directory,
        "script_runtime": {
            **archive_scripts(target, config.experiment.script_population),
            "directory": str(Path(source_directory) / "script-runtime"),
        },
    }


def qualification_copy(change: PopulationChange) -> League:
    """Create an isolated continuation branch; qualification seeds never enter formal training."""
    state = stopped_state(change.run)
    config = proposed(state, change)
    Recovery(run=change.destination)
    identity = artifacts.source_identity()
    protocol = config.protocol()
    protocol["experiment"].update(output_dir=str(change.destination), train_seed=3792000000)
    config = League.model_validate(protocol)
    destination = change.destination
    destination.mkdir(parents=True, exist_ok=False)
    for name in config.members:
        original = orjson.loads((change.run / name / "state.json").read_bytes())
        target = destination / name
        target.mkdir()
        for relative in (*original["members"], original["native_artifact"]):
            old = change.run / name / relative
            expected = original["members"].get(relative, original["native"])
            if digest(old) != expected:
                raise ValueError("original BC or rules core artifact changed")
            new = target / relative
            new.parent.mkdir(parents=True, exist_ok=True)
            os.link(old, new)
        child = child_state(change.run, name, config, identity, target)
        archive_source(target, identity)
        write_json(target / "state.json", child)
        write_json(target / "resolved-config.json", child["protocol"])
        shutil.copy2(
            change.run / name / "learning-progress.json", target / "learning-progress.json"
        )
    checkpoint_sha = filtered_checkpoint(change.run, state, config, destination / state["latest"])
    state.update(
        protocol=config.protocol(),
        source=identity["source_sha256"],
        members={name: state["members"][name] for name in config.members},
        checkpoints={state["latest"]: checkpoint_sha},
        qualification_parent={"run": str(change.run), "checkpoint": state["latest"]},
        population_history=[
            *state.get("population_history", []),
            {
                "effective_from_update": state["completed_update"] + 1,
                "qualification_only": True,
            },
        ],
    )
    write_json(destination / "league.json", state)
    write_json(destination / "resolved-config.json", state["protocol"])
    for filename in ("metrics.jsonl", "run-status.json", "league-progress.json"):
        shutil.copy2(change.run / filename, destination / filename)
    return config


def apply(change: PopulationChange) -> dict[str, Any]:
    """Install the exact qualified population, retaining an authenticated rollback boundary."""
    root = change.run
    with (root / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = stopped_state(root)
        config = proposed(state, change)
        identity = artifacts.source_identity()
        scripts = config.experiment.script_population
        assert scripts is not None
        expected = {
            "passed": True,
            "run_id": state["run_id"],
            "completed_update": state["completed_update"],
            "checkpoint_sha256": state["checkpoints"][state["latest"]],
            "source_state_sha256": digest(root / "league.json"),
            "source_sha256": identity["source_sha256"],
            "native_sha256": identity["native_sha256"],
            "script_runtime": script_identity(scripts),
            "protocol": config.protocol(),
        }
        if not change.report_sha256 or digest(change.report) != change.report_sha256:
            raise ValueError("qualification report must retain its reviewed fingerprint")
        report = orjson.loads(change.report.read_bytes())
        if any(report.get(key) != value for key, value in expected.items()):
            raise ValueError(
                "qualification must bind this checkpoint, source and script population"
            )
        index = f"{len(state.get('population_history', [])) + 1:04d}"
        relative = f"population-revisions/{index}"
        revision = root / relative
        revision.mkdir(parents=True, exist_ok=False)
        archive_source(revision, identity)
        write_json(revision / "previous-league.json", state)
        write_json(revision / "qualification.json", report)
        os.link(root / state["latest"], revision / "previous-checkpoint.pt")
        fingerprint = filtered_checkpoint(root, state, config, revision / "checkpoint.pt")
        children, updated = {}, {}
        for name in config.members:
            children[name] = orjson.loads((root / name / "state.json").read_bytes())
            target = root / name / relative
            target.mkdir(parents=True, exist_ok=False)
            write_json(target / "previous-state.json", children[name])
            for filename in ("source.json", "source.tar.gz"):
                os.link(revision / filename, target / filename)
            updated[name] = child_state(root, name, config, identity, target, relative)
        transition = {
            **expected,
            "time": time.time(),
            "effective_from_update": state["completed_update"] + 1,
            "previous_source": state["source"],
            "previous_protocol": state["protocol"],
            "revision": relative,
            "retired_members": ["a"],
            "optimizer_rng_and_bc_preserved": True,
            "migrated_checkpoint_sha256": fingerprint,
        }
        latest = f"{relative}/checkpoint.pt"
        migrated = {
            **state,
            "protocol": config.protocol(),
            "source": identity["source_sha256"],
            "members": {name: state["members"][name] for name in config.members},
            "latest": latest,
            "checkpoints": {latest: fingerprint},
            "population_history": [*state.get("population_history", []), transition],
        }
        try:
            for name, child in updated.items():
                write_json(root / name / "state.json", child)
                write_json(root / name / "resolved-config.json", child["protocol"])
            write_json(root / "resolved-config.json", config.protocol())
            write_json(root / "league.json", migrated)
        except BaseException:
            for name, child in children.items():
                write_json(root / name / "state.json", child)
                write_json(root / name / "resolved-config.json", child["protocol"])
            write_json(root / "resolved-config.json", state["protocol"])
            write_json(root / "league.json", state)
            raise
        write_json(revision / "transition.json", transition)
        return transition


@hydra.main(version_base=None, config_path="../../../../configs", config_name="league_population")
def main(configuration: DictConfig) -> None:
    """Qualify or publish a requested member and native script change."""
    change = PopulationChange.model_validate(
        OmegaConf.to_container(configuration.change, resolve=True)
    )
    if change.mode == "qualify":
        from kagg_revue.learning.league.population_qualification import qualify

        result = qualify(change)
    else:
        result = apply(change)
    print(orjson.dumps(result).decode(), flush=True)


if __name__ == "__main__":
    main()
