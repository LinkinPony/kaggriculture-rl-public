from types import SimpleNamespace

import torch

from kagg_revue.production.evaluation.matches import PairedPolicy


def test_each_policy_receives_its_own_observation_on_both_seats() -> None:
    class Actor(torch.nn.Module):
        def __init__(self, bias: float) -> None:
            super().__init__()
            self.bias = torch.nn.Parameter(torch.tensor(bias))
            self.layout = SimpleNamespace(
                factors=1, same_interface=lambda other: other.factors == 1
            )

        def act(self, observations, steps, *, sample, temperature):
            actions = (observations + self.bias).long()
            return actions, actions.float()

    learner, opponent = Actor(10.0), Actor(20.0)
    joint = PairedPolicy(learner, opponent, 2)
    observations = torch.arange(4).float()[:, None]
    actions, probabilities = joint.act(observations, torch.zeros(4), sample=False)
    torch.testing.assert_close(actions[:, 0], torch.tensor([10, 21, 22, 13]))
    torch.testing.assert_close(probabilities, actions.float())
