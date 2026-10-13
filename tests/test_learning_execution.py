import copy
from pathlib import Path

import numpy as np
import pytest
import torch
from pydantic import ValidationError

from kagg_revue.learning import distributed
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.initialization import random_policy
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.learning.state import protocol
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.policy.contracts import ContractLayout


def test_seed_shards_preserve_population_and_original_seed_budget():
    config = Experiment(output_dir=Path("outputs/learning/test"), games=128)
    full = distributed.seed_shard(config, 93, 0, 1)
    first, second = [distributed.seed_shard(config, 93, rank, 2) for rank in range(2)]
    assert first[:32] + second[:32] == full[:64]
    assert first[32:] + second[32:] == full[64:]
    assert set(first).isdisjoint(second)
    assert sorted(first + second) == full
    for shard in (first, second):
        assert [seed % 2 for seed in shard[32:]] == [0, 1] * 16
    following = distributed.seed_shard(config, 94, 0, 1)
    assert set(full).isdisjoint(following)
    assert following == [seed + config.games for seed in full]


def test_execution_preserves_optimizer_budget_and_legacy_protocol():
    config = Experiment(output_dir=Path("outputs/learning/test"), games=128)
    assert "execution" not in protocol(config)
    parallel = Experiment.model_validate({**protocol(config), "execution": Execution()})
    before, after = runtime_settings(config), runtime_settings(parallel)
    assert after.devices == ("cuda:0", "cuda:1")
    assert after.ppo.games_per_update == before.ppo.games_per_update
    assert after.ppo.batch_rows == before.ppo.batch_rows
    assert after.ppo.epochs == before.ppo.epochs
    with pytest.raises(ValidationError, match="historical"):
        Experiment.model_validate({**protocol(config), "games": 12, "execution": Execution()})
    with pytest.raises(ValidationError, match="unique CUDA"):
        Execution(devices=("cuda:0", "cuda:0"))


def test_recovery_restores_each_rank_rng_and_rejects_world_size_change(monkeypatch):
    config = Experiment(output_dir=Path("outputs/learning/test"))
    saved = [
        {
            "cpu": torch.Generator().manual_seed(i).get_state(),
            "cuda": torch.Generator().manual_seed(i + 10).get_state(),
        }
        for i in range(2)
    ]
    observed = {}
    monkeypatch.setattr(distributed, "rank_world", lambda: (1, 2))
    monkeypatch.setattr(torch, "set_rng_state", lambda value: observed.update(cpu=value))
    monkeypatch.setattr(
        torch.cuda, "set_rng_state", lambda value, device: observed.update(cuda=value)
    )
    distributed.restore_rng({"rng": {"workers": saved}}, torch.device("cuda:1"), config)
    assert torch.equal(observed["cpu"], saved[1]["cpu"])
    assert torch.equal(observed["cuda"], saved[1]["cuda"])
    monkeypatch.setattr(distributed, "rank_world", lambda: (0, 1))
    with pytest.raises(ValueError, match="worker count"):
        distributed.restore_rng({"rng": {"workers": saved}}, torch.device("cuda:0"), config)


def test_fused_prefix_objectives_preserve_full_optimizer_update():
    torch.set_num_threads(1)
    torch.manual_seed(99)
    config = Experiment(
        output_dir=Path("outputs/learning/test"),
        architecture="grounded-v1",
        decision_interval=1,
        width=16,
        depth=1,
        critic_width=16,
        critic_depth=1,
        unit_limit=2,
        games=8,
        batch_rows=16,
        microbatch_rows=8,
        compile=False,
        precision="fp32",
        environment={
            "boardSize": 4,
            "episodeSteps": 9,
            "turnsPerDay": 3,
            "maxMarketOrdersPerTurn": 2,
        },
    )
    settings = runtime_settings(config)
    policy = random_policy(ContractLayout.resolve(settings), 99, config.exploration)
    critic = PrefixCritic(policy.layout)
    packed = np.empty((16, policy.layout.observation.features), np.float16)
    create_selfplay_batch(settings, list(range(8))).observe_selfplay_into(packed)
    observations = torch.from_numpy(packed)
    steps = torch.zeros(16, dtype=torch.long)
    with torch.no_grad():
        actions, behavior = policy.act(observations, steps, sample=True)
    rollout = Rollout(
        observations,
        actions,
        behavior,
        steps,
        torch.linspace(-1, 3, 16),
        np.zeros((8, 2)),
        {},
        torch.tensor([0.5, 1.0] * 8),
        ("self_play",) * 8,
    )
    reference = Learner(settings, copy.deepcopy(policy), copy.deepcopy(critic), None)
    fused = Learner(settings.model_copy(update={"fused_loss": True}), policy, critic, None)
    torch.manual_seed(17)
    expected = reference.update(rollout)
    torch.manual_seed(17)
    actual = fused.update(rollout)
    assert actual["actor_steps"] == expected["actor_steps"] == 1
    assert actual["value_loss"] == pytest.approx(expected["value_loss"], abs=1e-6)
    for old, new in ((reference.policy, fused.policy), (reference.critic, fused.critic)):
        for key, value in old.state_dict().items():
            torch.testing.assert_close(value, new.state_dict()[key], atol=5e-6, rtol=1e-5)
        for left, right in zip(old.parameters(), new.parameters(), strict=True):
            if left.grad is not None:
                torch.testing.assert_close(left.grad, right.grad, atol=1e-7, rtol=1e-5)


@pytest.mark.parametrize("constant", [True, False])
def test_optimizer_resume_restores_constant_rates_without_resetting_moments(constant):
    torch.set_num_threads(1)
    config = Experiment(
        output_dir=Path("outputs/learning/test"),
        architecture="grounded-v1",
        decision_interval=1,
        width=16,
        depth=1,
        critic_width=16,
        critic_depth=1,
        unit_limit=2,
        compile=False,
        precision="fp32",
    )
    settings = runtime_settings(config)
    assert settings.ppo.protection.learning_rate_decay == 1
    if not constant:
        settings = settings.model_copy(
            update={
                "ppo": settings.ppo.model_copy(
                    update={
                        "protection": settings.ppo.protection.model_copy(
                            update={"learning_rate_decay": 0.5, "backtrack_attempts": 3}
                        )
                    }
                )
            }
        )
    policy = random_policy(ContractLayout.resolve(settings), 99, config.exploration)
    learner = Learner(settings, policy, PrefixCritic(policy.layout), None)
    snapshots = []
    for optimizer in (learner.actor_optimizer, learner.critic_optimizer):
        for group in optimizer.param_groups:
            for parameter in group["params"]:
                parameter.grad = torch.ones_like(parameter)
        optimizer.step()
        snapshot = copy.deepcopy(optimizer.state_dict())
        snapshot["param_groups"][0]["lr"] /= 8
        snapshot["param_groups"][0]["guard_lr_scale"] = 0.125
        snapshots.append(snapshot)
    learner.restore_optimizers(*snapshots)
    for optimizer, saved, rate in zip(
        (learner.actor_optimizer, learner.critic_optimizer),
        snapshots,
        (config.actor_learning_rate, config.critic_learning_rate),
        strict=True,
    ):
        actual = optimizer.state_dict()
        assert actual["param_groups"][0]["lr"] == (rate if constant else rate / 8)
        assert ("guard_lr_scale" not in actual["param_groups"][0]) == constant
        assert saved["param_groups"][0]["lr"] == rate / 8
        for index, state in saved["state"].items():
            for name, value in state.items():
                torch.testing.assert_close(actual["state"][index][name], value)
