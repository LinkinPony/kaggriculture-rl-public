"""Preserve Adam state by parameter name when zero residual features are inserted."""

import copy
from typing import Any

import torch
from torch import nn


def expand_adam(
    state: dict[str, Any], source: nn.Module, target: nn.Module
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Remap existing moments and steps; leave added parameters to Adam's lazy zero init.

    The training learner uses one group over ``model.parameters()``. Inserting
    encoder modules changes integer parameter IDs, so positional appending would
    attach old moments to unrelated tensors with potentially identical shapes.
    """
    old = dict(source.named_parameters())
    new = dict(target.named_parameters())
    groups = state["param_groups"]
    if len(groups) != 1 or len(groups[0]["params"]) != len(old) or not old.keys() <= new.keys():
        raise ValueError("Adam expansion requires one complete, unchanged named parameter group")
    indices = dict(zip(old, groups[0]["params"], strict=True))
    if len(set(indices.values())) != len(old) or not state["state"].keys() <= set(indices.values()):
        raise ValueError("Adam parameter ownership differs from the source model")
    migrated: dict[int, Any] = {}
    for index, (name, parameter) in enumerate(new.items()):
        if name not in old:
            if bool(torch.count_nonzero(parameter)):
                raise ValueError("added feature parameters must start at zero")
            continue
        if parameter.shape != old[name].shape or parameter.dtype != old[name].dtype:
            raise ValueError(f"Adam expansion changed parameter geometry: {name}")
        values = state["state"].get(indices[name])
        if values is None:
            continue
        if any(
            value.shape != parameter.shape
            for key, value in values.items()
            if key != "step" and isinstance(value, torch.Tensor)
        ):
            raise ValueError(f"Adam moments do not match their named parameter: {name}")
        migrated[index] = copy.deepcopy(values)
    result = {
        "state": migrated,
        "param_groups": [{**copy.deepcopy(groups[0]), "params": list(range(len(new)))}],
    }
    return result, {
        "retained_parameters": len(old),
        "retained_states": len(migrated),
        "added_parameters": sorted(new.keys() - old.keys()),
        "new_parameter_state": "lazy zero initialization on first gradient",
        "retained_steps": sorted({int(v["step"]) for v in migrated.values()}),
        "hyperparameters_preserved": True,
    }
