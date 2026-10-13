import torch

from kagg_revue.production.expert.mutations import ParameterSearch


def test_mutations_are_antithetic_and_recenter_without_accumulating_noise() -> None:
    parameter = torch.nn.Parameter(torch.tensor([[0.2, -0.5], [0.7, 0.1]]))
    center = parameter.detach().clone()
    search = ParameterSearch({"projection": parameter})
    search.propose(19, 0.4)
    positive = parameter.detach().clone()
    search.propose(19, -0.4)
    torch.testing.assert_close(positive + parameter, 2 * center)
    search.propose(19, 0.0)
    torch.testing.assert_close(parameter, center)
    search.propose(19, 0.4)
    search.recenter()
    search.propose(71, 0.0)
    torch.testing.assert_close(parameter, positive)
