import json
import random
from pathlib import Path

import numpy as np
import pytest
import torch

from kagg_revue.policy.state import load_causal_actor_state, migrate_optimizer_state
from kagg_revue.rl.checkpoint import (
    CheckpointStore,
    _actor_optimization_transition,
    _apply_actor_learning_rate_transition,
    _opening_exploration_transition,
    _terminal_reward_transition,
    _training_population_transition,
    capture_training_state,
    deserialize_training_state,
    restore_training_state,
    serialize_training_state,
)
from kagg_revue.rl.config import CheckpointSettings, ResumeTransitionSettings


def test_checkpoint_store_bounds_rolling_and_keeps_permanent(tmp_path: Path) -> None:
    store = CheckpointStore(
        tmp_path,
        CheckpointSettings(
            rolling_interval=2,
            rolling_keep=2,
            permanent_interval=4,
        ),
    )

    records = {
        update: store.publish(
            update,
            {"update": update, "weight": torch.tensor([float(update)])},
            final=False,
        )
        for update in range(1, 11)
    }

    assert records[1] is None
    assert records[2] is not None
    rolling = sorted((tmp_path / "checkpoints" / "rolling").glob("*.pt"))
    permanent = sorted((tmp_path / "checkpoints" / "permanent").glob("*.pt"))
    assert [torch.load(path, weights_only=True)["update"] for path in rolling] == [8, 10]
    assert [torch.load(path, weights_only=True)["update"] for path in permanent] == [4, 8]
    assert torch.load(tmp_path / "checkpoints" / "latest.pt", weights_only=True)["update"] == 10
    index = json.loads(
        (tmp_path / "checkpoints" / "checkpoint-index.json").read_text(encoding="utf-8")
    )
    assert index["latest"]["update"] == 10
    assert [record["update"] for record in index["rolling"]] == [8, 10]
    assert [record["update"] for record in index["permanent"]] == [4, 8]


def test_checkpoint_store_always_publishes_final_update(tmp_path: Path) -> None:
    store = CheckpointStore(
        tmp_path,
        CheckpointSettings(
            rolling_interval=4,
            rolling_keep=1,
            permanent_interval=8,
        ),
    )

    record = store.publish(3, {"update": 3}, final=True)

    assert record is not None
    assert record["rolling"] is True
    assert record["permanent"] is False
    assert torch.load(tmp_path / "checkpoints" / "latest.pt", weights_only=True)["update"] == 3


def test_training_random_state_round_trip_is_weights_only_safe(tmp_path: Path) -> None:
    random.seed(17)
    np.random.seed(19)
    torch.manual_seed(23)
    randomizer = random.Random(29)
    state = capture_training_state(randomizer, None, torch.device("cpu"))
    path = tmp_path / "state.pt"
    torch.save(state, path)
    loaded = torch.load(path, weights_only=True)

    expected = (
        random.random(),
        float(np.random.random()),
        float(torch.rand(()).item()),
        randomizer.random(),
    )
    random.seed(31)
    np.random.seed(37)
    torch.manual_seed(41)
    randomizer.seed(43)
    restore_training_state(loaded, randomizer, None, torch.device("cpu"))
    actual = (
        random.random(),
        float(np.random.random()),
        float(torch.rand(()).item()),
        randomizer.random(),
    )

    assert actual == expected


def test_training_random_state_collective_encoding_round_trip() -> None:
    randomizer = random.Random(47)
    state = capture_training_state(randomizer, None, torch.device("cpu"))

    restored = deserialize_training_state(serialize_training_state(state))

    assert restored["python_random_state"] == state["python_random_state"]
    assert torch.equal(
        restored["torch_cpu_random_state"],
        state["torch_cpu_random_state"],
    )


def test_actor_optimization_transition_is_exact_and_reapplies_rate() -> None:
    stored = {
        "critic_actor_gradient": True,
        "actor_learning_rate": 0.01,
        "unchanged": "contract",
    }
    current = {
        "critic_actor_gradient": False,
        "actor_learning_rate": 0.03,
        "unchanged": "contract",
    }
    authorization = ResumeTransitionSettings(
        detach_critic_from_actor=True,
        actor_learning_rate_multiplier=3.0,
    )

    transition = _actor_optimization_transition(
        stored,
        current,
        authorization,
    )

    assert transition is not None
    assert (
        _actor_optimization_transition(
            stored,
            {**current, "unchanged": "different"},
            authorization,
        )
        is None
    )
    actor = torch.nn.Parameter(torch.zeros(()))
    critic = torch.nn.Parameter(torch.zeros(()))
    optimizer = torch.optim.AdamW(
        [
            {"params": [actor], "lr": 0.01},
            {"params": [critic], "lr": 0.02},
        ]
    )
    _apply_actor_learning_rate_transition(optimizer, 0.03)

    assert optimizer.param_groups[0]["lr"] == 0.03
    assert optimizer.param_groups[1]["lr"] == 0.02


def test_actor_learning_rate_transition_preserves_gradient_semantics() -> None:
    stored = {
        "critic_actor_gradient": False,
        "actor_learning_rate": 0.03,
        "unchanged": "contract",
    }
    current = {
        "critic_actor_gradient": False,
        "actor_learning_rate": 0.05,
        "unchanged": "contract",
    }
    authorization = ResumeTransitionSettings(
        actor_learning_rate_multiplier=5.0 / 3.0,
    )

    transition = _actor_optimization_transition(
        stored,
        current,
        authorization,
    )

    assert transition is not None
    assert transition["critic_actor_gradient"] == {
        "checkpoint": False,
        "resolved": False,
        "detach_authorized": False,
    }
    assert (
        _actor_optimization_transition(
            stored,
            {**current, "critic_actor_gradient": True},
            authorization,
        )
        is None
    )


def test_opening_exploration_transition_is_explicit() -> None:
    stored = {"unchanged": "contract"}
    current = {
        "unchanged": "contract",
        "opening_exploration": {"enabled": True, "synthetic_setting": 3},
    }
    authorization = ResumeTransitionSettings(enable_opening_exploration=True)

    assert _opening_exploration_transition(stored, current, authorization) is True
    assert _opening_exploration_transition(stored, current, None) is False
    assert (
        _opening_exploration_transition(
            {**stored, "opening_exploration": {"enabled": True}},
            current,
            authorization,
        )
        is False
    )
    replacement = ResumeTransitionSettings(replace_opening_exploration=True)
    assert (
        _opening_exploration_transition(
            {**stored, "opening_exploration": {"enabled": True, "mode": "legacy"}},
            {**stored, "opening_exploration": {"enabled": True, "mode": "continuous"}},
            replacement,
        )
        is True
    )
    assert (
        _opening_exploration_transition(
            current,
            current,
            replacement,
        )
        is False
    )
    assert (
        _opening_exploration_transition(
            stored,
            {**current, "unchanged": "different"},
            authorization,
        )
        is False
    )


def test_training_population_transition_accepts_one_frozen_actor_branch() -> None:
    stored = {
        "opponents": ["self_play"],
        "opponent_sampling": None,
        "unchanged": "contract",
    }
    current = {
        "opponents": ["self_play", "snapshot"],
        "opponent_sampling": {
            "mode": "weighted_per_seed",
            "weights": {"self_play": 0.5, "snapshot": 0.5},
        },
        "frozen_actor_opponents": {"snapshot": {"checkpoint": "synthetic.pt", "sha256": "0" * 64}},
        "unchanged": "contract",
    }

    assert _training_population_transition(stored, current) is True
    assert (
        _training_population_transition(
            stored,
            {**current, "unchanged": "different"},
        )
        is False
    )


def test_terminal_reward_transition_requires_explicit_authorization() -> None:
    stored = {"unchanged": "contract"}
    current = {
        "unchanged": "contract",
        "terminal_reward": {
            "mode": "margin_augmented_wdl",
            "margin_beta": 0.75,
            "margin_cash_scale": 12.0,
        },
    }
    authorization = ResumeTransitionSettings(enable_margin_augmented_wdl=True)

    transition = _terminal_reward_transition(stored, current, authorization)

    assert transition is not None
    assert transition["resolved"] == current["terminal_reward"]
    assert _terminal_reward_transition(stored, current, None) is None
    assert (
        _terminal_reward_transition(
            stored,
            {**current, "unchanged": "different"},
            authorization,
        )
        is None
    )


def test_enabled_legacy_parameter_noise_state_is_rejected() -> None:
    randomizer = random.Random(53)
    state = capture_training_state(randomizer, None, torch.device("cpu"))
    state["parameter_noise_state"] = {"enabled": True}

    with pytest.raises(
        ValueError,
        match="failed whole-episode parameter-noise checkpoints cannot resume",
    ):
        restore_training_state(state, randomizer, None, torch.device("cpu"))


def test_legacy_auxiliary_actor_and_optimizer_slots_are_removed_by_name() -> None:
    class CausalActor(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.base = torch.nn.Linear(2, 2)
            self.skills = torch.nn.Module()
            self.skills.prior = torch.nn.Linear(2, 2)
            self.skills.codebook = torch.nn.Embedding(2, 2)

    actor = CausalActor()
    target_names = tuple(name for name, _ in actor.named_parameters())
    legacy_names = list(target_names)
    legacy_names.insert(2, "skills.effect.weight")
    legacy_state = dict(actor.state_dict())
    legacy_state["skills.effect.weight"] = torch.ones(2, 2)

    removed = load_causal_actor_state(actor, legacy_state)

    optimizer = torch.optim.SGD(actor.parameters(), lr=0.1)
    source_optimizer = optimizer.state_dict()
    source_ids = list(range(100, 100 + len(legacy_names)))
    source_optimizer["param_groups"][0]["params"] = source_ids
    source_optimizer["state"] = {
        identifier: {"marker": torch.tensor(float(index))}
        for index, identifier in enumerate(source_ids)
    }
    migrated, removed_slots = migrate_optimizer_state(
        source_optimizer,
        (tuple(legacy_names),),
        optimizer,
        (target_names,),
    )
    optimizer.load_state_dict(migrated)

    assert removed == ("skills.effect.weight",)
    assert removed_slots == removed
    for name, parameter in actor.named_parameters():
        assert optimizer.state[parameter]["marker"] == legacy_names.index(name)
