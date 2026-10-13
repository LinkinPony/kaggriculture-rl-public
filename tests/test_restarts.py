import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
import torch

from kagg_revue.datasets.observations import ReplayObservations, difference
from kagg_revue.datasets.restarts import RestartBank, RestartSource
from kagg_revue.datasets.states import describe, partition
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.native import _revue_native as native
from kagg_revue.production.artifacts import digest
from kagg_revue.production.contracts import ContractLayout
from kagg_revue.production.population import TrainingBatch
from kagg_revue.production.runtime import ActorRuntime, collect


def _config() -> Experiment:
    return Experiment(
        output_dir=Path("outputs/learning/restart-test"),
        games=4,
        architecture="grounded-v1",
        decision_interval=1,
        unit_limit=3,
        width=16,
        depth=1,
        critic_width=16,
        critic_depth=1,
        device="cpu",
        cash_weight=1,
        cash_scale=1000,
        environment={
            "boardSize": 4,
            "episodeSteps": 25,
            "turnsPerDay": 4,
            "maxMarketOrdersPerTurn": 2,
        },
    )


def _actions() -> list[dict]:
    return [
        {"farmer": ["NORTH"], "market": [["BUY_SEED", "WHEAT", 1]]},
        {"farmer": ["WEST"], "market": [["BUY_PRODUCT", "WHEAT", 1]]},
    ]


def test_replay_inventory_order_uses_prefix_changes_instead_of_sorted_json() -> None:
    sequence = ReplayObservations()
    frames = [
        {},
        {"WHEAT": 2},
        {"SHEEP": 1, "WHEAT": 1},
        {"SHEEP": 1},
        {"SHEEP": 1, "WHEAT": 1},
        {},
    ]
    expected = [[], ["WHEAT"], ["WHEAT", "SHEEP"], ["SHEEP"], ["SHEEP", "WHEAT"], []]
    for step, (inventory, order) in enumerate(zip(frames, expected, strict=True)):
        raw = {"player": 0, "private": {"inventories": [inventory]}}
        normalized = sequence.update(raw, step)
        assert list(normalized["private"]["inventories"][0]) == order
        assert normalized["private"]["inventories"][0] == inventory
        assert raw["private"]["inventories"][0] is inventory
        assert "step" not in raw
    assert sequence.reordered_inventories == 1
    with pytest.raises(ValueError, match="cannot be recovered"):
        sequence.update({"player": 0, "private": {"inventories": [{"COW": 1, "SHEEP": 1}]}}, 6)
    with pytest.raises(ValueError, match="ordered single-seat"):
        sequence.update({"player": 0, "private": {"inventories": [{}]}}, 8)
    assert (
        difference(
            {"inventories": [{"COW": 1, "SHEEP": 1}]}, {"inventories": [{"SHEEP": 1, "COW": 1}]}
        )
        is not None
    )


def test_replay_is_atomic_and_preserves_both_seats_and_history() -> None:
    config = _config()
    layout = ContractLayout.resolve(runtime_settings(config))
    batch = native.ParallelBatch(
        config.environment,
        [3, 7],
        [0, 0],
        [],
        [],
        [],
        config.unit_limit,
        1,
        list(layout.observation.quantities),
    )
    reference = [native.Engine(seed, config.environment) for seed in (3, 7)]
    sessions = [
        [native.ContractSession(config.environment, config.unit_limit) for _ in range(2)]
        for _ in reference
    ]
    for engine, pair in zip(reference, sessions, strict=True):
        for step in range(9):
            if step:
                engine.step(*_actions())
            for seat, session in enumerate(pair):
                session.update(engine.observation(seat))
    before = batch.observation(0)
    with pytest.raises(ValueError, match="both official actions"):
        batch.replay_prefixes([[_actions()] * 8, [[{}]] * 8])
    assert batch.observation(0) == before
    assert batch.transitions == 0
    batch.replay_prefixes([[_actions()] * 8 for _ in range(2)])
    actual = np.empty((4, layout.observation.features), np.float16)
    expected = np.empty_like(actual)
    batch.observe_selfplay_into(actual)
    for lane, (engine, pair) in enumerate(zip(reference, sessions, strict=True)):
        for seat, session in enumerate(pair):
            assert batch.observation(lane, seat) == engine.observation(seat)
            row = 2 * lane + seat
            session.observe_into(expected[row : row + 1])
    np.testing.assert_array_equal(actual, expected)
    with pytest.raises(ValueError, match="fresh self-play"):
        batch.replay_prefixes([[], []])
    child = batch.fork(np.array([1, 0], dtype=np.int64))
    child.advance_programs(np.zeros((4, layout.factors), np.int64), 1, 1, True)
    assert batch.step_index == 8 and child.step_index == 9


def test_suffix_rollout_excludes_prefix_actions_and_subtracts_initial_cash() -> None:
    torch.set_num_threads(1)
    config = _config()
    settings = runtime_settings(config)
    layout = ContractLayout.resolve(settings)
    policy = random_policy(layout, 9, config.exploration)
    runtime = ActorRuntime(policy, 8, sample=True, precision="fp32")
    native_batch = native.ParallelBatch(
        config.environment,
        [3, 7, 9, 11],
        [0] * 4,
        [],
        [],
        [],
        config.unit_limit,
        1,
        list(layout.observation.quantities),
    )
    native_batch.replay_prefixes([[_actions()] * 8 for _ in range(4)])
    initial = native_batch.cash().copy()
    batch = TrainingBatch(native_batch, None, 4, ("self_play",) * 4, 1)
    with pytest.raises(ValueError, match="native state clock"):
        collect(
            settings,
            policy,
            runtime,
            [3, 7, 9, 11],
            prepared_batch=batch,
            start_decision=4,
            initial_cash=initial,
        )
    rollout = collect(
        settings,
        policy,
        runtime,
        [3, 7, 9, 11],
        prepared_batch=batch,
        start_decision=8,
        initial_cash=initial,
    )
    assert len(rollout.steps) == (24 - 8) * 8
    assert rollout.steps.min() == 8 and rollout.steps.max() == 23
    assert native_batch.completed_games == 4 and native_batch.transitions == 24 * 4
    rewards = np.sign(rollout.cash - rollout.cash[:, ::-1])
    rewards += (rollout.cash - initial) / config.cash_scale
    np.testing.assert_allclose(
        rollout.returns.numpy().reshape(16, 8), np.tile(rewards.reshape(1, 8), (16, 1)), atol=1e-6
    )


def test_restart_bank_authenticates_split_content_state_and_source_features(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = _config()
    layout = ContractLayout.resolve(runtime_settings(config))
    directory = Path("data/external/restarts")
    directory.mkdir(parents=True)
    seed = next(seed for seed in range(100) if partition(seed) == "train")
    engine = native.Engine(seed, config.environment)
    steps = []
    for step in range(25):
        if step:
            engine.step(*_actions())
        steps.append(
            [
                {
                    "observation": engine.observation(seat),
                    "action": _actions()[seat] if step else None,
                }
                for seat in range(2)
            ]
        )
    replay = {
        "info": {"seed": seed},
        "module_version": "test-version",
        "configuration": config.environment,
        "steps": steps,
    }
    del replay["steps"][0][1]["observation"]["step"]
    raw = json.dumps(replay).encode()
    archive = directory / "raw.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("episode.json", raw)
    row = {
        "member": "episode.json",
        "seed": seed,
        "split": "train",
        "step": 8,
        "seats": [describe(state["observation"], seat) for seat, state in enumerate(steps[8])],
    }
    index = directory / "candidates.jsonl"
    index.write_text(json.dumps(row) + "\n")
    manifest = directory / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "replay-restart-candidates-v1",
                "archive": str(archive),
                "archive_sha256": digest(archive),
                "index": index.name,
                "index_sha256": digest(index),
                "module_version": "test-version",
                "episodes": [
                    {
                        "member": "episode.json",
                        "seed": seed,
                        "split": "train",
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }
                ],
            }
        )
    )
    source = RestartSource(manifest=manifest, manifest_sha256=digest(manifest))
    kwargs = dict(
        environment=config.environment,
        units=config.unit_limit,
        quantities=layout.observation.quantities,
        workers=1,
        features=layout.observation.features,
        starts=(8,),
    )
    bank = RestartBank(source, split="train", **kwargs)
    sampled, metadata = bank.sample(8, 4, 11)
    assert sampled.step_index == 8
    assert metadata["official_prefix_actions_in_ppo"] == 0
    assert metadata["environment_seeds"] == [seed] * 4
    for seat in range(2):
        assert sampled.observation(0, seat) == steps[8][seat]["observation"]
    with pytest.raises(ValueError, match="no eligible states"):
        RestartBank(source, split="confirmation", **kwargs)
    index.write_text(index.read_text() + "\n")
    with pytest.raises(ValueError, match="source identity"):
        RestartBank(source, split="train", **kwargs)
