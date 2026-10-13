"""Strict v4 to v5b weight transfer with an initially identical policy function."""

from dataclasses import replace

import torch
from torch import nn

from kagg_revue.native.derived import legacy_layout
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import Policy


def legacy_contract(layout: ContractLayout) -> ContractLayout:
    """Remove the supplement while requiring the remaining network to match exactly."""
    if not layout.network.derived:
        raise ValueError("v5b transfer requires the explicit derived network setting")
    return replace(
        layout,
        observation=legacy_layout(layout.observation),
        network=replace(layout.network, derived=False),
    )


def copy_parameters(source: nn.Module, target: nn.Module, encoder: str) -> dict[str, int]:
    """Retain every old tensor and allow exactly four zero residual weight matrices."""
    previous = source.state_dict()
    current = target.state_dict()
    expected = {f"{encoder}.supplement.projections.{index}.weight" for index in range(4)}
    if set(previous) - set(current) or set(current) - set(previous) != expected:
        raise ValueError("weight migration changed keys beyond the four residual projections")
    for name, tensor in previous.items():
        if tensor.shape != current[name].shape or tensor.dtype != current[name].dtype:
            raise ValueError(f"incompatible pretrained parameter: {name}")
        current[name] = tensor
    if any(torch.count_nonzero(current[name]).item() for name in expected):
        raise ValueError("new residual projections must start at zero")
    target.load_state_dict(current, strict=True)
    if any(not torch.equal(tensor, target.state_dict()[name]) for name, tensor in previous.items()):
        raise ValueError("pretrained tensors changed while migrating")
    return {
        "retained_tensors": len(previous),
        "retained_parameters": sum(t.numel() for t in previous.values()),
        "added_tensors": len(expected),
        "added_parameters": sum(current[name].numel() for name in expected),
    }


def expand_units(actor: Policy, layout: ContractLayout) -> tuple[Policy, dict[str, int]]:
    """Add a zero-output joint unit context to an otherwise identical parallel decoder."""
    if not layout.network.joint_units or actor.layout != replace(
        layout, network=replace(layout.network, joint_units=False)
    ):
        raise ValueError("joint expansion requires the target contract without joint units")
    with torch.random.fork_rng(devices=[]):
        expanded = Policy.from_layout(layout)
    previous, current = actor.state_dict(), expanded.state_dict()
    added = set(current) - set(previous)
    if set(previous) - set(current) or any(not name.startswith("joint.") for name in added):
        raise ValueError("joint expansion changed keys outside the unit context")
    for name, tensor in previous.items():
        if tensor.shape != current[name].shape or tensor.dtype != current[name].dtype:
            raise ValueError(f"incompatible pretrained parameter: {name}")
        current[name] = tensor
    output = (current["joint.output.weight"], current["joint.output.bias"])
    if any(torch.count_nonzero(tensor).item() for tensor in output):
        raise ValueError("the joint unit context must start with a zero output")
    expanded.load_state_dict(current, strict=True)
    return expanded, {
        "retained_tensors": len(previous),
        "retained_parameters": sum(t.numel() for t in previous.values()),
        "added_tensors": len(added),
        "added_parameters": sum(current[name].numel() for name in added),
    }


def migrate_policy(actor: Policy, layout: ContractLayout) -> tuple[Policy, dict[str, int]]:
    """Expand only a complete v4 checkpoint with exactly matching architecture."""
    if actor.layout != legacy_contract(layout):
        raise ValueError("source actor differs from the target's exact v4 contract")
    with torch.random.fork_rng(devices=[]):
        expanded = Policy.from_layout(layout)
    report = copy_parameters(actor, expanded, "encoder")
    return expanded, report
