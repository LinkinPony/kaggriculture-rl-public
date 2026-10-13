"""Recover frozen opponents from an authenticated downstream run's local archive."""

import copy
import json
from pathlib import Path
from typing import Any

import torch
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.imports import layout_from_payload, validate_layout
from kagg_revue.learning.matchmaking.observations import verify_native_identity
from kagg_revue.learning.storage.artifacts import import_member, resolve
from kagg_revue.policy.contracts import ContractLayout


class NativeQualification(FrozenSettings):
    """Pin replacement replay evidence without rewriting the donor's ledger."""

    path: Path
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class HistoricalArchive(FrozenSettings):
    """Pin the downstream ledger that preserves selected upstream opponent bytes."""

    run: Path
    state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    native_qualification: NativeQualification | None = None

    @model_validator(mode="after")
    def validate_path(self) -> "HistoricalArchive":
        """Restrict archives to repository-owned experiment directories."""
        if (
            self.run.is_absolute()
            or ".." in self.run.parts
            or self.run.parts[:2] != ("outputs", "learning")
        ):
            raise ValueError("historical archives require an outputs/learning run")
        return self


def import_archive(
    config: Experiment,
    state: dict[str, Any],
    archive: HistoricalArchive,
    *,
    verify_only: bool = False,
) -> dict[str, Any]:
    """Validate selected frozen actors without depending on mutable upstream ledgers.

    Only missing, explicitly selected opponents are imported. Their original
    provenance and identities remain intact; another learner's PFSP evidence is
    never copied. Verification mode changes only the supplied in-memory ledger.
    """
    ledger = archive.run / "state.json"
    if archive.run == config.output_dir or digest(ledger) != archive.state_sha256:
        raise ValueError("historical archive ledger differs from its pinned identity")
    donor = json.loads(ledger.read_text())
    if donor["protocol"]["output_dir"] != str(archive.run):
        raise ValueError("historical archive directory differs")
    expected = ContractLayout.resolve(runtime_settings(config))
    imported = copy.deepcopy(state.get("external_opponents", {}))
    added = []
    native_evidence = copy.deepcopy(donor.get("opponent_native_qualification"))
    if native_evidence is None:
        for revision in reversed(donor.get("population_history", [])):
            native_evidence = copy.deepcopy(
                revision.get("historical_archive", {}).get("native_evidence")
            )
            if native_evidence is not None:
                break
    if archive.native_qualification is not None:
        native_evidence = archive.native_qualification.model_dump(mode="json")
    if donor["native"] != state["native"]:
        verify_native_identity(
            {**state, "opponent_native_qualification": native_evidence}, donor["native"]
        )
    for source in config.population.sources:
        for checkpoint in source.checkpoints:
            name = f"historical/{source.run.name}/{Path(checkpoint).name}"
            if name in imported:
                metadata = imported[name]
            else:
                metadata = donor.get("external_opponents", {}).get(name, {})
            if (
                metadata.get("run") != str(source.run)
                or metadata.get("state_sha256") != source.state_sha256
                or metadata.get("checkpoint") != checkpoint
                or metadata.get("role") != "frozen_opponent_only"
                or not metadata.get("sha256")
            ):
                raise ValueError(f"archive does not authenticate the selected opponent: {name}")
            if name in imported:
                if state["members"].get(name) != metadata["sha256"]:
                    raise ValueError("existing opponent identity changed")
                continue
            if donor["members"].get(name) != metadata["sha256"]:
                raise ValueError("archived opponent identity differs from its source")
            if metadata["source_native_sha256"] != state["native"]:
                verify_native_identity(
                    {**state, "opponent_native_qualification": native_evidence},
                    metadata["source_native_sha256"],
                )
            path = resolve(archive.run, donor, name)
            payload = torch.load(path, map_location="cpu", weights_only=False, mmap=True)
            layout = layout_from_payload(payload)
            validate_layout(expected, layout)
            if checkpoint == "initial.pt":
                kind = metadata.get("root_kind")
                if kind not in {"random", "checkpoint"}:
                    raise ValueError("archived initial opponent lacks its authenticated root kind")
            else:
                kind = (
                    "multi_source_demonstrations"
                    if checkpoint.startswith("pretraining/")
                    else "reinforcement_learning"
                )
            if (
                payload.get("lineage", {}).get("run_id") != metadata["run_id"]
                or payload.get("lineage", {}).get("kind") != kind
                or (
                    kind == "reinforcement_learning" and payload.get("update") != metadata["update"]
                )
                or payload["settings"]["environment"] != config.environment
                or layout != layout_from_payload({"layout": metadata["layout"]})
                or not all(bool(torch.isfinite(t).all()) for t in payload["model"].values())
            ):
                raise ValueError("archived policy lineage, layout or tensors differ")
            if verify_only:
                state["members"][name] = metadata["sha256"]
            else:
                import_member(config.output_dir, state, name, path, metadata["sha256"])
            imported[name] = copy.deepcopy(metadata)
            added.append(name)
    if digest(ledger) != archive.state_sha256:
        raise ValueError("historical archive changed during import")
    state["external_opponents"] = imported
    if native_evidence is not None:
        state["opponent_native_qualification"] = native_evidence
    if not verify_only:
        write_json(config.output_dir / "historical/manifest.json", imported)
    return {**archive.model_dump(mode="json"), "added": added, "native_evidence": native_evidence}
