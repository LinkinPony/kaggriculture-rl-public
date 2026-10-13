"""Adam migration must follow names even when inserted tensors have the same shape."""

import copy

import torch
from torch import nn

from kagg_revue.learning.optimization.migration import expand_adam


def test_inserted_parameter_preserves_old_adam_updates_and_starts_fresh() -> None:
    """Distinct old moments cannot be assigned to a new tensor by positional loading."""
    before = nn.ModuleDict(
        {"first": nn.Linear(2, 2, bias=False), "last": nn.Linear(2, 2, bias=False)}
    )
    optimizer = torch.optim.AdamW(before.parameters(), lr=7.5e-6, weight_decay=0)
    for _ in range(3):
        for i, parameter in enumerate(before.parameters()):
            parameter.grad = torch.full_like(parameter, (i + 1) * 0.1)
        optimizer.step()
    after = nn.ModuleDict(
        {
            "first": copy.deepcopy(before["first"]),
            "added": nn.Linear(2, 2, bias=False),
            "last": copy.deepcopy(before["last"]),
        }
    )
    added = dict(after.named_parameters())["added.weight"]
    last = dict(after.named_parameters())["last.weight"]
    nn.init.zeros_(added)
    saved = copy.deepcopy(optimizer.state_dict())
    migrated, report = expand_adam(saved, before, after)
    restored = torch.optim.AdamW(after.parameters(), lr=7.5e-6, weight_decay=0)
    restored.load_state_dict(migrated)
    assert report["retained_steps"] == [3]
    assert report["added_parameters"] == ["added.weight"]
    assert added not in restored.state
    for i, (name, parameter) in enumerate(before.named_parameters()):
        target = dict(after.named_parameters())[name]
        assert all(
            torch.equal(value, restored.state[target][key])
            for key, value in optimizer.state[parameter].items()
        )
        parameter.grad = torch.full_like(parameter, (i + 1) * -0.2)
        target.grad = parameter.grad.clone()
    added.grad = torch.ones_like(added)
    optimizer.step()
    restored.step()
    for name, parameter in before.named_parameters():
        assert torch.equal(parameter, dict(after.named_parameters())[name])
    assert bool(torch.count_nonzero(added))
    assert int(restored.state[added]["step"]) == 1
    assert int(restored.state[last]["step"]) == 4
