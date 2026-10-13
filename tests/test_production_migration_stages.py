from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import torch

from kagg_revue.production.migration import stages


class TinyPolicy(torch.nn.Module):
    def __init__(self, table=True):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.tensor([0.7, -0.4]))
        self.layout = SimpleNamespace(network=SimpleNamespace(time_prior=table))
        if table:
            self.prior = torch.nn.Parameter(torch.ones(2), requires_grad=False)

    def remove_prior(self):
        del self.prior
        self.layout.network.time_prior = False


def test_restored_moments_use_the_new_optimizer_step_size():
    initial = torch.nn.Parameter(torch.tensor([0.7, -0.4], dtype=torch.float64))
    old = torch.optim.AdamW([initial], lr=0.004, weight_decay=0)
    initial.square().sum().backward()
    old.step()
    saved = deepcopy(old.state_dict())
    before = initial.detach().clone()
    deltas = []
    for divisor in (1, 8):
        parameter = torch.nn.Parameter(before.clone())
        optimizer = torch.optim.AdamW([parameter], lr=old.param_groups[0]["lr"] / divisor)
        stages.restore_optimizer(optimizer, deepcopy(saved))
        parameter.square().sum().backward()
        optimizer.step()
        deltas.append((parameter.detach() - before) * divisor)
    torch.testing.assert_close(*deltas)


def test_objective_switch_preserves_weights_and_resumes_only_ppo_state(monkeypatch):
    def distiller(config, student, teacher):
        return SimpleNamespace(
            optimizer=torch.optim.AdamW([student.weight]), update=Mock(return_value="teacher")
        )

    def learner(settings, policy, critic, rehearsal):
        return SimpleNamespace(
            actor_optimizer=torch.optim.AdamW(policy.parameters()),
            critic_optimizer=torch.optim.AdamW(critic.parameters()),
            critic=critic,
            update=Mock(return_value="wdl"),
        )

    monkeypatch.setattr(stages, "Distiller", distiller)
    monkeypatch.setattr(stages, "Learner", learner)
    monkeypatch.setattr(stages, "Critic", lambda layout: torch.nn.Linear(2, 1))
    monkeypatch.setattr(stages, "at_scale", lambda settings, scale, table: settings)
    controls = SimpleNamespace(production=object())
    critic = torch.nn.Linear(2, 1)
    student = TinyPolicy()
    stage = stages.TrainingStage(controls, student, critic.state_dict(), object(), None)
    student.weight.square().sum().backward()
    stage.distiller.optimizer.step()
    assert stage.distiller.optimizer.state
    assert stage.update(None) == "teacher"
    neural = student.weight
    before = neural.detach().clone()
    stage.start_ppo()
    assert student.weight is neural
    torch.testing.assert_close(neural, before)
    assert not hasattr(student, "prior")
    assert stage.distiller is None
    assert not stage.ppo.actor_optimizer.state
    assert not stage.ppo.critic_optimizer.state
    for name, value in critic.state_dict().items():
        torch.testing.assert_close(stage.ppo.critic.state_dict()[name], value)
    assert stage.update(None) == "wdl"

    def step(active):
        for optimizer in (active.ppo.actor_optimizer, active.ppo.critic_optimizer):
            optimizer.zero_grad()
            for group in optimizer.param_groups:
                for parameter in group["params"]:
                    parameter.square().sum().backward()
            optimizer.step()

    step(stage)
    saved = deepcopy(stage.state_dict())
    assert "migration_optimizer" not in saved
    restored_student = TinyPolicy(table=False)
    restored_student.load_state_dict(student.state_dict())
    restored = stages.TrainingStage(controls, restored_student, saved["critic"], None, saved)
    assert restored.distiller is None
    assert restored.update(None) == "wdl"
    restored.start_ppo()  # Re-entering the stage must not reset restored Adam moments.
    step(stage)
    step(restored)
    torch.testing.assert_close(restored_student.weight, student.weight)
    for name, value in stage.ppo.critic.state_dict().items():
        torch.testing.assert_close(restored.ppo.critic.state_dict()[name], value)
