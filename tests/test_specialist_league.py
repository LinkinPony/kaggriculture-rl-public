from pathlib import Path
from types import SimpleNamespace

import numpy as np
import orjson
import pytest
import torch
from hydra import compose, initialize_config_dir

from kagg_revue.datasets.demonstrations.loading import Dataset
from kagg_revue.datasets.strata.loading import ResidentDataset
from kagg_revue.datasets.strata.selection import classify
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.league import collection
from kagg_revue.learning.league.config import League
from kagg_revue.learning.league.revision import changed_config
from kagg_revue.learning.league.storage import reconcile_metrics
from kagg_revue.learning.league.telemetry import member_outcomes
from kagg_revue.learning.pretraining.config import Demonstrations


def test_templates_exclude_both_seats_and_never_fit_heldout_actions() -> None:
    ids = ["a", "a", "b", "b", "c", "c", "heldout", "heldout"]
    rows = [{"episode_id": value} for value in ids]
    splits = {value: "selection" if value == "heldout" else "train" for value in ids}
    hashes = np.ones((len(rows), 24, 4), np.uint64)
    labels, _ = classify(rows, hashes, splits)
    assert not labels[:6].any()  # Three episodes cannot support themselves.
    assert labels[6:].all()
    hashes[6:, :, 3] = 2
    changed, _ = classify(rows, hashes, splits)
    np.testing.assert_array_equal(changed[:6], labels[:6])
    assert not changed[6:].any()
    rows.extend([{"episode_id": "d"}] * 2)
    splits["d"] = "train"
    labels, _ = classify(rows, np.ones((10, 24, 4), np.uint64), splits)
    assert labels.all()


def test_resident_loader_preserves_selected_rows_rank_shards_and_padding(tmp_path: Path) -> None:
    arrays = {
        "observations": np.arange(26, dtype=np.float16).reshape(13, 2),
        "actions": np.arange(13, dtype=np.int16).reshape(13, 1),
        "origins": np.column_stack((np.arange(13), np.zeros(13))).astype(np.int64),
        "quantity_coverage": np.array([True] * 12 + [False]),
        "row_selection": np.array([True, False] * 6 + [True]),
    }
    for name, values in arrays.items():
        np.save(tmp_path / f"{name}.npy", values)
    datasets = [object.__new__(Dataset), object.__new__(ResidentDataset)]
    for dataset in datasets:
        dataset.directory = tmp_path
        dataset.layout = SimpleNamespace(observation=SimpleNamespace(features=2), factors=1)
        dataset.shards = [{"rows": 13, **{key: f"{key}.npy" for key in arrays}}]
    for seed in (None, (123, 4)):
        observed = []
        for rank in (0, 1):
            batches = [
                list(dataset.batches(0, 4, torch.device("cpu"), seed, rank=rank, world=2))
                for dataset in datasets
            ]
            for left, right in zip(*batches, strict=True):
                assert left[3] == right[3]
                for old, new in zip(left[:3], right[:3], strict=True):
                    torch.testing.assert_close(old, new, rtol=0, atol=0)
                observed.extend(right[2][: max(0, right[3] - rank * 2)].tolist())
        assert sorted(observed) == [0, 2, 4, 6, 8, 10]


@pytest.mark.parametrize("mutual,selfplay", [(64, 0), (32, 32)])
def test_native_collection_routes_each_seat_to_its_own_policy_and_reward(
    monkeypatch, mutual, selfplay
) -> None:
    with initialize_config_dir(version_base=None, config_dir=str(Path("configs").resolve())):
        cfg = compose(config_name="learning_league")
    league = League.model_validate(
        {
            **dict(cfg.league),
            "experiment": dict(cfg.experiment),
            "games_per_pair": mutual,
            "selfplay_games_per_member": selfplay,
        }
    )
    seeds, owners = collection.schedule(league, 1, 0, 2)
    other_seeds, other_owners = collection.schedule(league, 1, 1, 2)
    next_seeds, _ = collection.schedule(league, 2, 0, 2)
    assert len(set(seeds + other_seeds + next_seeds)) == 288
    for seats in (owners, other_owners):
        for member in range(3):
            assert (seats[:, 0] == member).sum() == (seats[:, 1] == member).sum() == 32
    layout = SimpleNamespace(
        decisions=3,
        spans=(1, 1, 1),
        observation=SimpleNamespace(features=2, turns=3),
        factors=1,
        capacity=1,
    )
    cash = np.arange(len(seeds) * 2, dtype=np.float64).reshape(-1, 2)

    class Batch:
        step = 0
        completed_games = len(seeds)
        transitions = len(seeds) * 3

        def observe_selfplay_into(self, host):
            host[:, 0] = np.arange(len(host))
            host[:, 1] = self.step

        def advance_programs(self, selected, span, capacity):
            np.testing.assert_array_equal(selected[:, 0], owners.ravel())
            self.step += 1

        def cash(self):
            return cash

    class Runtime:
        def __init__(self, member):
            self.member = member
            self.policy = SimpleNamespace(layout=layout)
            self.device = torch.device("cpu")
            self.host = torch.zeros((64, 2), dtype=torch.float16)
            self.observations = self.host
            self.selected = torch.full((64, 1), member, dtype=torch.long)
            self.temperature = 1.0

        def act(self, decision, synchronize):
            assert not synchronize
            assert (self.host[:, 1] == decision).all()
            return self.selected, torch.full((64, 1), -float(self.member + 1))

    monkeypatch.setattr(collection, "rank_world", lambda: (0, 2))
    monkeypatch.setattr(collection, "LeagueBatch", lambda *args: Batch())
    tapes, metrics = collection.collect(
        league, runtime_settings(league.experiment), [Runtime(i) for i in range(3)], 1
    )
    assert metrics["physical_games"] == 96
    for member, tape in enumerate(tapes):
        positions = np.flatnonzero(owners.ravel() == member)
        assert (tape.actions == member).all()
        assert (tape.log_probabilities == -(member + 1)).all()
        np.testing.assert_array_equal(tape.observations[:64, 0], positions)
        np.testing.assert_array_equal(tape.cash[:, 0], cash.ravel()[positions])
        np.testing.assert_array_equal(tape.cash[:, 1], cash.ravel()[positions ^ 1])
        assert (tape.returns[:64].sign() == torch.tensor(np.where(positions % 2, 1, -1))).all()
        same = owners.ravel()[positions ^ 1] == member
        np.testing.assert_array_equal(tape.weights[:64], np.where(same, 0.5, 1))
        panel = member_outcomes(metrics["pairs"], ("a", "bc", "spataro")[member])
        if selfplay:
            assert same.sum() == 32
            assert panel["self_play"]["games"] == 16
            assert panel["self_play"]["training_trajectories"] == 32
            assert panel["self_play"]["training_fraction"] == pytest.approx(1 / 3)
            assert (
                panel["self_play"]["wins"]
                + panel["self_play"]["ties"]
                + panel["self_play"]["losses"]
                == 16
            )
        else:
            assert "self_play" not in panel
    assert len(metrics["pairs"]) == (6 if selfplay else 3)


def test_selfplay_transition_preserves_the_budget_seed_stream_and_model_protocol() -> None:
    with initialize_config_dir(version_base=None, config_dir=str(Path("configs").resolve())):
        cfg = compose(config_name="learning_league")
    old = League.model_validate(
        {
            **dict(cfg.league),
            "experiment": dict(cfg.experiment),
            "games_per_pair": 64,
            "selfplay_games_per_member": 0,
        }
    )
    assert "selfplay_games_per_member" not in old.protocol()
    new = changed_config({"protocol": old.protocol()}, 32)
    assert old.experiment == new.experiment
    assert old.trajectories_per_member == new.trajectories_per_member == 128
    assert {key for key in new.protocol() if new.protocol()[key] != old.protocol().get(key)} == {
        "games_per_pair",
        "selfplay_games_per_member",
    }
    for rank in (0, 1):
        old_seeds, _ = collection.schedule(old, 41, rank, 2)
        new_seeds, _ = collection.schedule(new, 42, rank, 2)
        assert not set(old_seeds) & set(new_seeds)
    with pytest.raises(ValueError):
        changed_config({"protocol": old.protocol()}, 64)


def test_committed_bc_recipe_retains_role_and_controls_without_reading_example_shards(
    monkeypatch,
) -> None:
    with initialize_config_dir(version_base=None, config_dir=str(Path("configs").resolve())):
        cfg = compose(config_name="learning_league")
    league = League.model_validate({**dict(cfg.league), "experiment": dict(cfg.experiment)})
    committed = Demonstrations(
        manifest=league.strata.parent / "a/manifest.json",
        sha256="a" * 64,
        epochs=6,
        batch_rows=1024,
        learning_rate=0.0001,
        checkpoint_shards=8,
        distributed=True,
        behavior_games=0,
    )

    def unavailable(self):
        raise FileNotFoundError("original BC examples unavailable")

    monkeypatch.setattr(League, "sources", unavailable)
    assert league.member("a", committed=committed).demonstrations == committed
    with pytest.raises(FileNotFoundError):
        league.member("a")
    with pytest.raises(ValueError, match="role"):
        league.member("bc", committed=committed)
    with pytest.raises(ValueError, match="controls"):
        league.member("a", committed=committed.model_copy(update={"epochs": 5}))


def test_joint_recovery_reconciles_uncommitted_or_missing_metrics(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    path.write_bytes(b'{"update":1}\n{"update":2,"old":true}\n{"update":4}\n{"update":')
    reconcile_metrics(tmp_path, 3, [{"update": 2}, {"update": 3}])
    assert [orjson.loads(line) for line in path.read_bytes().splitlines()] == [
        {"update": 1},
        {"update": 2},
        {"update": 3},
    ]
