"""Isolated qualification copies and source archives for explicit hardware transitions."""

import copy
import json
import os
import shutil
import tarfile
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.optimization.settings import CashMargin
from kagg_revue.learning.pretraining import weights


def archive_source(directory: Path, identity: dict[str, Any]) -> None:
    """Archive an exact implementation using the existing source identity format."""
    with tarfile.open(directory / "source.tar.gz", "w:gz") as archive:
        for name in identity["files"]:
            archive.add(name, arcname=name, recursive=False)
    write_json(directory / "source.json", identity)


def qualification_copy(
    source: Path,
    destination: Path,
    execution: Execution,
    updates: int,
    *,
    population_changes: dict[str, Any] | None = None,
    batch_changes: dict[str, Any] | None = None,
    protocol_changes: dict[str, Any] | None = None,
    wdl: bool = False,
    cash_margin: CashMargin | None = None,
    evaluation_games: int | None = None,
) -> Experiment:
    """Clone only authenticated immutable own-run artifacts into a labeled test branch."""
    if destination.exists():
        raise FileExistsError(destination)
    state = json.loads((source / "state.json").read_text())
    original = Experiment.model_validate(state["protocol"], context={"archived_population": True})
    if original.output_dir != source:
        raise ValueError("qualification source directory differs from its protocol")
    if not weights.valid_root(state):
        raise ValueError("qualification requires an authenticated policy root")
    weights.verify(source, state)
    if population_changes and set(population_changes) != {"population", "script_population"}:
        raise ValueError("population qualification may change only declared opponent controls")
    if batch_changes and (set(batch_changes) != {"games", "train_seed"} or population_changes):
        raise ValueError("batch qualification may change only game count and training seeds")
    if protocol_changes and (
        population_changes
        or batch_changes
        or not set(protocol_changes)
        <= {
            "pretraining_only",
            "games",
            "train_seed",
            "population",
            "script_population",
            "batch_rows",
            "sequence_games_per_rank",
            "actor_learning_rate",
            "target_kl",
            "kl_control",
        }
    ):
        raise ValueError("sampling qualification may change only opponent and batch controls")
    if wdl and (population_changes or batch_changes or protocol_changes):
        raise ValueError("WDL qualification must preserve sampling and batch controls")
    if cash_margin is not None and (wdl or population_changes or batch_changes or protocol_changes):
        raise ValueError("cash-margin qualification must preserve sampling and batch controls")
    config = Experiment.model_validate(
        {
            **state["protocol"],
            **(population_changes or {}),
            **(batch_changes or {}),
            **(protocol_changes or {}),
            **({"cash_weight": 0.0, "cash_margin": None} if wdl else {}),
            **(
                {"cash_weight": 0.0, "cash_margin": cash_margin.model_dump()}
                if cash_margin is not None
                else {}
            ),
            "output_dir": str(destination),
            "execution": execution.model_dump(),
            "updates": state["completed_update"] + updates,
            # Keep the starting optimizer and every qualification checkpoint for
            # ancestry and optimizer-step verification after stop/resume.
            "checkpoint_keep_recent": None
            if original.checkpoint_keep_recent is None
            else max(original.checkpoint_keep_recent, updates + 1),
            "evaluation": {
                **state["protocol"]["evaluation"],
                "selection_seed": 3050000000,
                "confirmation_seed": 3060000000,
                **({"games": evaluation_games} if evaluation_games is not None else {}),
            },
        }
    )
    for name in state["members"]:
        artifacts.member_path(original, state, name)
    destination.mkdir(parents=True)
    if state["initialization"] == "checkpoint":
        # A qualified continuation retains its authenticated local parent copy.
        shutil.copytree(source / "weight-transfer", destination / "weight-transfer")
    for name in state["members"]:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        physical = artifacts.member_path(original, state, name)
        record = state.get("inference_artifacts", {}).get(name)
        if record:
            target = destination / record["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            os.link(physical, target)
    native = Path(state["native_artifact"])
    (destination / native).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / native, destination / native)
    identity = artifacts.source_identity()
    archive_source(destination, identity)
    state = copy.deepcopy(state)
    state["qualification_parent"] = {
        "directory": str(source),
        "checkpoint_sha256": state["members"][state["latest"]],
        "completed_update": state["completed_update"],
        "purpose": "hardware execution qualification",
    }
    if execution != original.execution:
        state["execution_history"] = [
            *state.get("execution_history", []),
            {
                "completed_update": state["completed_update"],
                "checkpoint_sha256": state["members"][state["latest"]],
                "previous_protocol": state["protocol"],
                "execution": execution.model_dump(mode="json"),
                "purpose": "isolated hardware execution qualification",
            },
        ]
    state["protocol"] = artifacts.protocol(config)
    state["source"] = identity["source_sha256"]
    state["source_directory"] = "."
    if population_changes:
        state["qualification_parent"]["purpose"] = "public opponent integration qualification"
    if batch_changes:
        state["qualification_parent"]["purpose"] = "rollout size continuation qualification"
    if protocol_changes:
        state["qualification_parent"]["purpose"] = "requested sampling and minibatch qualification"
    if wdl:
        state["qualification_parent"]["purpose"] = "pure WDL reward continuation qualification"
    if cash_margin is not None:
        state["qualification_parent"]["purpose"] = "bounded cash-margin continuation qualification"
    if config.script_population is not None:
        from kagg_revue.opponents.artifacts import archive

        state["script_runtime"] = archive(destination, config.script_population)
    else:
        state.pop("script_runtime", None)
    if config.population.pfsp is not None:
        from kagg_revue.learning.matchmaking.imports import ensure_imported, transition

        if population_changes:
            ensure_imported(config, state)
            transition(config, state, original)
        else:
            from kagg_revue.learning.matchmaking.pool import initialize

            initialize(config, state)
    write_json(destination / "state.json", state)
    write_json(destination / "resolved-config.json", state["protocol"])
    return config
