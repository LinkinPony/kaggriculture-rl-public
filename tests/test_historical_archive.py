import copy
import json
from dataclasses import asdict
from pathlib import Path

import pytest
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.matchmaking.archives import HistoricalArchive, import_archive
from kagg_revue.learning.matchmaking.config import HistoricalSource, Pfsp
from kagg_revue.learning.matchmaking.imports import registered, transition
from kagg_revue.learning.storage.artifacts import resolve
from kagg_revue.policy.contracts import ContractLayout


def _archive(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = HistoricalSource(
        run=Path("outputs/learning/upstream"),
        state_sha256="a" * 64,
        checkpoints=("checkpoints/update-000064.pt",),
    )
    config = Experiment(
        output_dir=Path("outputs/learning/learner"),
        architecture="grounded-v2",
        decision_interval=1,
        population=Population(capacity=9, pfsp=Pfsp(), sources=(source,)),
    )
    layout = asdict(ContractLayout.resolve(runtime_settings(config)))
    donor = Path("outputs/learning/donor")
    name = "historical/upstream/update-000064.pt"
    path = donor / name
    path.parent.mkdir(parents=True)
    torch.save(
        {
            "layout": layout,
            "model": {"weight": torch.ones(2)},
            "settings": {"environment": config.environment},
            "lineage": {"run_id": "upstream", "kind": "reinforcement_learning"},
            "update": 64,
        },
        path,
    )
    metadata = {
        "run": str(source.run),
        "state_sha256": source.state_sha256,
        "checkpoint": source.checkpoints[0],
        "role": "frozen_opponent_only",
        "sha256": digest(path),
        "source_native_sha256": "native",
        "run_id": "upstream",
        "update": 64,
        "layout": layout,
    }
    write_json(
        donor / "state.json",
        {
            "protocol": {"output_dir": str(donor)},
            "native": "native",
            "members": {name: metadata["sha256"]},
            "external_opponents": {name: metadata},
            "pfsp": {"foreign_evidence": 999},
        },
    )
    archive = HistoricalArchive(run=donor, state_sha256=digest(donor / "state.json"))
    state = {
        "native": "native",
        "members": {"initial.pt": "initial", "checkpoints/update-000004.pt": "old"},
        "pool": ["initial.pt"],
        "pfsp": {"records": {"incumbent": {"wins": 3}}},
        "completed_update": 8,
        "retired_members": ["checkpoints/update-000004.pt"],
    }
    return config, state, archive, name, path


def test_import_uses_frozen_archive_and_preserves_pool_evidence(tmp_path, monkeypatch):
    config, state, archive, name, _ = _archive(tmp_path, monkeypatch)
    before = copy.deepcopy(state)
    report = import_archive(config, state, archive)
    previous = config.model_copy(update={"population": Population(capacity=8, pfsp=Pfsp())})
    transition(config, state, previous)
    assert report["added"] == [name]
    assert registered(config, state)
    assert resolve(config.output_dir, state, name).is_file()
    assert not config.population.sources[0].run.exists()
    assert state["pool"] == ["initial.pt", name]
    assert state["pfsp"] == before["pfsp"]
    assert state["members"]["checkpoints/update-000004.pt"] == "old"


@pytest.mark.parametrize("tamper", ["ledger", "actor", "selection"])
def test_archive_rejects_changed_bytes_or_selection(tmp_path, monkeypatch, tamper):
    config, state, archive, _, path = _archive(tmp_path, monkeypatch)
    if tamper == "ledger":
        (archive.run / "state.json").write_text("{}")
    elif tamper == "actor":
        path.write_bytes(b"tampered")
    else:
        source = config.population.sources[0].model_copy(update={"state_sha256": "b" * 64})
        config = config.model_copy(
            update={
                "population": config.population.model_copy(update={"sources": (source,)}),
            }
        )
    with pytest.raises(ValueError):
        import_archive(config, state, archive)


def test_verification_does_not_publish_files_or_copy_donor_statistics(tmp_path, monkeypatch):
    config, state, archive, name, _ = _archive(tmp_path, monkeypatch)
    before = json.dumps(state["pfsp"], sort_keys=True)
    report = import_archive(config, state, archive, verify_only=True)
    assert report["added"] == [name]
    assert registered(config, state)
    assert not config.output_dir.exists()
    assert json.dumps(state["pfsp"], sort_keys=True) == before
