import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from kagg_revue.datasets.demonstrations.loading import Dataset
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.pretraining.config import Demonstrations, GroupedLoss
from kagg_revue.learning.pretraining.optimization import Optimizer
from kagg_revue.learning.pretraining.train import initialize
from kagg_revue.native import _revue_core as native
from kagg_revue.production.artifacts import digest, write_json
from kagg_revue.production.contracts import ContractLayout


def _dataset(config: Experiment, weighted: bool = False) -> Path:
    layout = ContractLayout.resolve(runtime_settings(config))
    directory = Path("data/external/pretraining-test")
    directory.mkdir(parents=True)
    shards = []
    for index, split in enumerate(("train", "train", "selection")):
        engine = native.Engine(11 + index, config.environment)
        session = native.ContractSession(config.environment, config.unit_limit)
        session.update(engine.observation(0))
        observations = np.empty((3, layout.observation.features), np.float16)
        session.observe_into(observations[:1])
        observations[1:] = observations[:1]
        arrays = {
            "observations": observations.astype(np.float16),
            "actions": np.zeros((3, layout.factors), np.int16),
            "origins": np.zeros((3, 2), np.int16),
            "quantity_coverage": np.ones(3, np.bool_),
        }
        if weighted:
            arrays["sampling_weights"] = np.array([0.5, 1.0, 2.0], np.float32)
            arrays["origins"][:, 0] = np.arange(3)
        record = {
            "split": split,
            "source_date": f"2026-09-0{3 + index}",
            "episodes": [{"seed": 11 + index}],
            "rows": 3,
            "hashes": {},
        }
        for key, values in arrays.items():
            path = directory / f"{index}-{key}.npy"
            np.save(path, values)
            record[key] = path.name
            record["hashes"][key] = digest(path)
        shards.append(record)
    manifest = directory / "manifest.json"
    write_json(
        manifest,
        {
            "schema": "grounded-daily-demonstrations-v1",
            "layout": asdict(layout),
            "configuration": {"environment": config.environment},
            "shards": shards,
            "coverage": {},
        },
    )
    return manifest


@pytest.mark.parametrize("weighted,grouped", [(False, False), (True, False), (False, True)])
def test_pretraining_resume_preserves_optimizer_and_separates_rl_zero_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    weighted: bool,
    grouped: bool,
) -> None:
    monkeypatch.chdir(tmp_path)
    torch.set_num_threads(1)
    monkeypatch.setattr(
        artifacts,
        "source_identity",
        lambda: {
            "files": {},
            "source_sha256": "test-source",
            "native_sha256": digest(Path(native.__file__)),
        },
    )
    base = Experiment(
        output_dir=Path("outputs/learning/continuous"),
        device="cpu",
        games=4,
        width=16,
        depth=1,
        critic_depth=1,
        critic_width=16,
        unit_limit=3,
        architecture="grounded-v2" if grouped else "grounded-v1",
        decision_interval=1,
        compile=False,
        precision="fp32",
        environment={
            "boardSize": 4,
            "episodeSteps": 13,
            "turnsPerDay": 6,
            "maxMarketOrdersPerTurn": 2,
        },
    )
    manifest = _dataset(base, weighted)
    config = base.model_copy(
        update={
            "demonstrations": Demonstrations(
                manifest=manifest,
                sha256=digest(manifest),
                epochs=2,
                batch_rows=4,
                checkpoint_shards=1,
                loss=GroupedLoss() if grouped else None,
            )
        }
    )
    settings = runtime_settings(config)
    continuous = artifacts.create(config, settings)
    initialize(config, settings, continuous, lambda: False)
    resumed_config = config.model_copy(update={"output_dir": Path("outputs/learning/resumed")})
    resumed = artifacts.create(resumed_config, settings)
    initialize(
        resumed_config,
        settings,
        resumed,
        lambda: resumed.get("pretraining", {}).get("cursor", 0) >= 1,
    )
    assert resumed["pretraining"]["cursor"] == 1
    assert "rl_initial" not in resumed
    if grouped:
        assert resumed["protocol"]["demonstrations"]["loss"] == GroupedLoss().model_dump()
        assert resumed["pretraining"]["loss"] == GroupedLoss().model_dump()
        assert resumed_config.demonstrations is not None
        changed = resumed_config.model_copy(
            update={
                "demonstrations": resumed_config.demonstrations.model_copy(update={"loss": None})
            }
        )
        with pytest.raises(ValueError, match="BC loss changed"):
            initialize(changed, settings, resumed, lambda: False)
    else:
        assert "loss" not in resumed["protocol"]["demonstrations"]
    restored = artifacts.restore(resumed_config.model_copy(update={"resume": True}))
    initialize(resumed_config, settings, restored, lambda: False)
    assert restored["completed_update"] == 0
    assert restored["pretraining"]["rows"] == 12
    assert restored["pretraining"]["optimizer_steps"] == 4
    assert artifacts.budget_member(restored, 0) == restored["rl_initial"] != "initial.pt"
    assert restored["pool"] == [restored["rl_initial"]]
    _, left = artifacts.load_member(config, continuous, continuous["latest"], torch.device("cpu"))
    _, right = artifacts.load_member(
        resumed_config, restored, restored["latest"], torch.device("cpu")
    )
    assert left["pretraining"] == right["pretraining"]
    assert torch.equal(left["rng"]["cpu"], right["rng"]["cpu"])
    for name in left["model"]:
        assert torch.equal(left["model"][name], right["model"][name])
    for key, values in left["optimizer"]["state"].items():
        for name, value in values.items():
            assert torch.equal(value, right["optimizer"]["state"][key][name])
    assert right["lineage"]["kind"] == "multi_source_demonstrations"
    assert right["lineage"]["root_sha256"] == restored["members"]["initial.pt"]
    assert restored["input_weights"] == []

    layout = ContractLayout.resolve(settings)
    if weighted:
        dataset = Dataset(manifest, digest(manifest), layout, config.environment, ())
        seed = (91, 7, 3)
        expected = np.random.default_rng(seed).choice(
            3, size=3, replace=True, p=np.array([0.5, 1, 2]) / 3.5
        )
        batch = next(dataset.batches(0, 4, torch.device("cpu"), seed))
        np.testing.assert_array_equal(batch[2].numpy(), np.resize(expected, 4))
        ranks = [
            next(dataset.batches(0, 4, torch.device("cpu"), seed, rank=r, world=2)) for r in (0, 1)
        ]
        torch.testing.assert_close(torch.cat([r[2] for r in ranks]), batch[2])
        validation = next(dataset.batches(2, 4, torch.device("cpu"), None))
        np.testing.assert_array_equal(validation[2].numpy(), [0, 1, 2, 0])
    with pytest.raises(ValueError, match="seed"):
        Dataset(manifest, digest(manifest), layout, config.environment, ((11, 12),))
    content = json.loads(manifest.read_text())
    path = manifest.parent / content["shards"][0]["actions"]
    path.write_bytes(path.read_bytes() + b"modified")
    with pytest.raises(ValueError, match="shard hash"):
        Dataset(manifest, digest(manifest), layout, config.environment, ())


@pytest.mark.parametrize("epochs,completed,reason", [(100, 14, "patience"), (3, 3, "epoch_limit")])
def test_validation_selection_and_patience_survive_restart(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    epochs: int,
    completed: int,
    reason: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    torch.set_num_threads(1)
    monkeypatch.setattr(
        artifacts,
        "source_identity",
        lambda: {
            "files": {},
            "source_sha256": "test",
            "native_sha256": digest(Path(native.__file__)),
        },
    )
    base = Experiment(
        output_dir=Path("outputs/learning/patience"),
        device="cpu",
        games=4,
        width=16,
        depth=1,
        critic_depth=1,
        critic_width=16,
        unit_limit=3,
        architecture="grounded-v1",
        decision_interval=1,
        compile=False,
        precision="fp32",
        checkpoint_keep_recent=2,
        environment={
            "boardSize": 4,
            "episodeSteps": 13,
            "turnsPerDay": 6,
            "maxMarketOrdersPerTurn": 2,
        },
    )
    manifest = _dataset(base)
    config = base.model_copy(
        update={
            "demonstrations": Demonstrations(
                manifest=manifest,
                sha256=digest(manifest),
                epochs=epochs,
                batch_rows=4,
                checkpoint_shards=1,
                early_stopping={"patience": 10, "min_delta": 0.001},
                epoch_checkpoint_interval=4,
            )
        }
    )
    original = Optimizer.shard
    losses = iter(
        [1.0, 0.9996, 0.9992, 0.9988, *([1.1] * 10)] if epochs == 100 else [1.0, 0.9996, 1.1]
    )

    def measured(
        self: Optimizer,
        dataset: Dataset,
        index: int,
        batch_rows: int,
        seed: tuple[int, ...] | None,
    ) -> dict[str, Any]:
        result = original(self, dataset, index, batch_rows, seed)
        if seed is None:
            result["loss_sum"] = next(losses) * result["rows"]
        return result

    monkeypatch.setattr(Optimizer, "shard", measured)
    settings = runtime_settings(config)
    state = artifacts.create(config, settings)
    stop_cursor = 12 if epochs == 100 else 5
    initialize(
        config,
        settings,
        state,
        lambda: state.get("pretraining", {}).get("cursor", 0) >= stop_cursor,
    )
    assert "rl_initial" not in state
    restored = artifacts.restore(config.model_copy(update={"resume": True}))
    initialize(config, settings, restored, lambda: False)
    progress = restored["pretraining"]
    best_epoch = 4 if epochs == 100 else 2
    assert len(progress["records"]) == completed
    assert progress["completion_reason"] == reason
    assert progress["early_stopping"]["bad_epochs"] == (10 if epochs == 100 else 2)
    assert progress["early_stopping"]["best_epoch"] == best_epoch
    selected = f"pretraining/shard-{2 * best_epoch:06d}.pt"
    assert restored["rl_initial"] == restored["latest"] == selected
    assert restored["pool"] == [selected]
    assert restored["bc_final"] == f"pretraining/shard-{2 * completed:06d}.pt"
    assert restored.get("pretraining_epoch_members", []) == [
        f"pretraining/shard-{2 * epoch:06d}.pt" for epoch in range(4, completed + 1, 4)
    ]
    for member in restored.get("pretraining_epoch_members", []):
        artifacts.load_member(config, restored, member, torch.device("cpu"))
    _, payload = artifacts.load_member(config, restored, selected, torch.device("cpu"))
    assert payload["pretraining"]["cursor"] == 2 * best_epoch
    initialize(config, settings, restored, lambda: False)
    assert restored["pretraining"] == progress
