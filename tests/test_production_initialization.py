import pytest
import torch

from kagg_revue.production.initialization import remove_optimizer_parameter


def test_removal_preserves_named_adam_moments_and_next_update() -> None:
    names = ["left", "table", "right"]
    parameters = [torch.nn.Parameter(torch.tensor([float(i)])) for i in range(3)]
    optimizer = torch.optim.AdamW(parameters, lr=0.02)
    for i, parameter in enumerate(parameters):
        parameter.grad = torch.full_like(parameter, i + 1.0)
    optimizer.step()
    original = optimizer.state_dict()
    migrated = remove_optimizer_parameter(original, names, "table")
    retained = [torch.nn.Parameter(parameters[i].detach().clone()) for i in (0, 2)]
    resumed = torch.optim.AdamW(retained)
    resumed.load_state_dict(migrated)
    assert len(original["param_groups"][0]["params"]) == len(parameters)
    assert len(migrated["state"]) == len(retained)
    for old, new in zip((parameters[0], parameters[2]), retained, strict=True):
        for key in ("exp_avg", "exp_avg_sq", "step"):
            torch.testing.assert_close(optimizer.state[old][key], resumed.state[new][key])
            # The two independent updates below must not share mutable moment tensors.
            resumed.state[new][key] = resumed.state[new][key].clone()
        old.grad = torch.ones_like(old)
        new.grad = torch.ones_like(new)
    optimizer.step()
    resumed.step()
    for old, new in zip((parameters[0], parameters[2]), retained, strict=True):
        torch.testing.assert_close(old, new)


def test_removal_rejects_an_optimizer_without_complete_parameter_identity() -> None:
    with pytest.raises(ValueError):
        remove_optimizer_parameter({"param_groups": [{"params": [0]}], "state": {}}, [], "x")
