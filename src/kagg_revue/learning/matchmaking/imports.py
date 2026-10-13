"""Authenticated cross-run opponents, isolated from learner initialization and ancestry."""

import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.migration import preserve_script_evidence
from kagg_revue.learning.matchmaking.pool import initialize, retain
from kagg_revue.learning.storage.artifacts import import_member
from kagg_revue.native.features import Layout
from kagg_revue.policy.contracts import ContractLayout, NetworkShape


def registered(config: Experiment, state: dict[str, Any]) -> bool:
    """Reuse complete imports only after restore() authenticated all local member bytes."""
    imported = state.get("external_opponents", {})
    for source in config.population.sources:
        for checkpoint in source.checkpoints:
            name = f"historical/{source.run.name}/{Path(checkpoint).name}"
            metadata = imported.get(name, {})
            if (
                metadata.get("run") != str(source.run)
                or metadata.get("state_sha256") != source.state_sha256
                or metadata.get("checkpoint") != checkpoint
                or metadata.get("role") != "frozen_opponent_only"
                or not metadata.get("sha256")
                or metadata["sha256"] != state["members"].get(name)
            ):
                return False
    return True


def ensure_imported(config: Experiment, state: dict[str, Any]) -> None:
    """Reuse authenticated local opponents when only the sampling protocol changes."""
    if not registered(config, state):
        import_opponents(config, state)
        return
    from kagg_revue.learning.state import member_path

    for source in config.population.sources:
        for checkpoint in source.checkpoints:
            name = f"historical/{source.run.name}/{Path(checkpoint).name}"
            member_path(config, state, name)


def layout_from_payload(payload: dict[str, Any]) -> ContractLayout:
    """Reconstruct checkpoint semantics without loading optimizer tensors onto a GPU."""
    stored = payload["layout"]
    return ContractLayout(
        Layout(**stored["observation"]),
        stored["board_size"],
        stored["interval"],
        NetworkShape(**stored.get("network", {})),
        stored.get("late_start", 0),
        stored.get("late_interval", 0),
    )


def validate_layout(expected: ContractLayout, actual: ContractLayout) -> None:
    """Permit exact v2/v4 projections of an additive v5b learner observation."""
    if expected.observation.version == "grounded-derived-context-v5b" and (
        actual.observation.version != expected.observation.version
    ):
        from kagg_revue.policy.grounded.migration import legacy_contract

        expected = legacy_contract(expected)
    if (
        expected.observation.version == "grounded-production-context-v4"
        and actual.observation.version == "grounded-production-context-v2"
    ):
        from kagg_revue.learning.matchmaking.observations import legacy_layout

        expected = legacy_layout(expected)
    adjusted = replace(
        actual,
        observation=replace(actual.observation, quantities=expected.observation.quantities),
    )
    if not expected.same_interface(adjusted) or not actual.work:
        raise ValueError("external history has incompatible observations or action semantics")


def import_opponents(config: Experiment, state: dict[str, Any]) -> None:
    """Copy only explicitly selected, hashed source members and preserve their provenance."""
    from kagg_revue.learning.state import member_path

    expected_layout = ContractLayout.resolve(runtime_settings(config))
    imported = dict(state.get("external_opponents", {}))
    for source in config.population.sources:
        if source.run == config.output_dir:
            raise ValueError("external history must refer to a different run")
        source_path = source.run / "state.json"
        if digest(source_path) != source.state_sha256:
            raise ValueError("historical source ledger hash differs from the declared selection")
        original = json.loads(source_path.read_text())
        old = Experiment.model_validate(original["protocol"], context={"archived_population": True})
        if old.output_dir != source.run:
            raise ValueError("historical source directory differs")
        if original["native"] != state["native"]:
            from kagg_revue.learning.matchmaking.observations import verify_native_identity

            verify_native_identity(state, original["native"])
        if "initial.pt" in source.checkpoints:
            from kagg_revue.learning.pretraining.weights import valid_root, verify

            if not valid_root(original):
                raise ValueError("historical initial policy lacks authenticated root provenance")
            verify(source.run, original)
        for member in source.checkpoints:
            path = member_path(old, original, member)
            payload = torch.load(path, map_location="cpu", weights_only=False)
            is_bc = member == original.get("rl_initial") and member.startswith("pretraining/")
            is_initial = member == "initial.pt"
            if member.startswith("pretraining/") and not is_bc:
                raise ValueError("historical BC imports must be the source run's final RL initial")
            update = 0 if is_bc or is_initial else int(Path(member).stem.removeprefix("update-"))
            if (
                payload.get("lineage", {}).get("run_id") != original["run_id"]
                or (
                    is_bc
                    and payload.get("lineage", {}).get("kind") != "multi_source_demonstrations"
                )
                or (
                    not is_bc
                    and not is_initial
                    and payload.get("lineage", {}).get("kind") != "reinforcement_learning"
                )
                or (not is_bc and not is_initial and payload.get("update") != update)
                or (
                    is_initial
                    and (
                        payload.get("lineage", {}).get("kind") != original["initialization"]
                        or payload.get("lineage", {}).get("seed") != old.seed
                        or (
                            old.initial_weights is not None
                            and payload.get("lineage", {}).get("parent_sha256")
                            != old.initial_weights.sha256
                        )
                    )
                )
                or update > original["completed_update"]
                or payload["settings"]["environment"] != config.environment
            ):
                raise ValueError("historical checkpoint lineage or game environment differs")
            layout = layout_from_payload(payload)
            validate_layout(expected_layout, layout)
            if not all(torch.isfinite(t).all() for t in payload["model"].values()):
                raise ValueError("external historical actor contains nonfinite tensors")
            name = f"historical/{source.run.name}/{Path(member).name}"
            metadata = {
                "run": str(source.run),
                "run_id": original["run_id"],
                "state_sha256": source.state_sha256,
                "checkpoint": member,
                "sha256": original["members"][member],
                "update": update,
                "layout": asdict(layout),
                "role": "frozen_opponent_only",
                "source_native_sha256": original["native"],
                **({"root_kind": original["initialization"]} if is_initial else {}),
            }
            import_member(config.output_dir, state, name, path, metadata["sha256"])
            imported[name] = metadata
            del payload
        if digest(source_path) != source.state_sha256:
            raise ValueError("historical source changed during import")
    if imported:
        state["external_opponents"] = imported
        write_json(config.output_dir / "historical/manifest.json", imported)


def transition(config: Experiment, state: dict[str, Any], previous: Experiment) -> None:
    """Explicitly reactivate paused statistics and reserve slots for imported opponents."""
    options = config.population.pfsp
    if options is None:
        return
    initialize(config, state)
    preserve_script_evidence(state, previous.script_population, config.script_population)
    if previous.population.pfsp is None or (
        config.population.separate_scripts != previous.population.separate_scripts
    ):
        if state["pfsp"]["last_update"] > state["completed_update"]:
            raise ValueError("paused PFSP contains future evidence")
        state["pfsp"] = {
            **state["pfsp"],
            "started_update": state["completed_update"] + 1,
            "last_update": state["completed_update"],
        }
    external = list(state.get("external_opponents", {}))
    own_pool = [name for name in state["pool"] if name not in external]
    if (
        previous.population.pfsp is not None
        and config.population.sources != previous.population.sources
        and config.population.snapshot_interval == previous.population.snapshot_interval
        and len(own_pool) <= config.population.capacity - len(external)
    ):
        # Extending foreign history must not resurrect retired own-run files or
        # promote unscheduled recovery checkpoints into sampling snapshots.
        state["pool"] = [own_pool[0], *external, *own_pool[1:]]
        return
    if (
        previous.population.pfsp is not None
        and config.population.capacity == previous.population.capacity
        and config.population.sources == previous.population.sources
        and config.population.snapshot_interval == previous.population.snapshot_interval
        and set(external).issubset(state["pool"])
    ):
        # Script or quota changes retain the exact historical pool and checkpoint
        # statistics. Identical scripts carry their evidence across manifest
        # versions; new strategies start at the prior.
        return
    own = retain(
        [
            str(state.get("rl_initial", "initial.pt")),
            *(name for name in state["members"] if name.startswith("checkpoints/update-")),
        ],
        config.population.capacity - len(external),
        options.recent_snapshots,
    )
    state["pool"] = [own[0], *external, *own[1:]]
