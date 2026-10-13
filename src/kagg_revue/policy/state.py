"""Compatibility helpers for causal-only actor state."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import torch
from torch import Tensor, nn

LEGACY_SKILL_AUXILIARY_PREFIXES = (
    "skills.observation.",
    "skills.hindsight.",
    "skills.effect.",
)


def is_legacy_skill_auxiliary(name: str) -> bool:
    """Return whether a parameter belonged only to the removed future auxiliary."""
    return name.startswith(LEGACY_SKILL_AUXILIARY_PREFIXES)


def causal_actor_state(
    state: Mapping[str, object],
) -> tuple[dict[str, Tensor], tuple[str, ...]]:
    """Drop only obsolete auxiliary tensors from a legacy actor state."""
    normalized: dict[str, Tensor] = {}
    removed: list[str] = []
    for name, value in state.items():
        if not isinstance(name, str):
            raise ValueError("actor state keys must be strings")
        if is_legacy_skill_auxiliary(name):
            removed.append(name)
            continue
        if not isinstance(value, Tensor):
            raise ValueError(f"actor state tensor is invalid: {name}")
        normalized[name] = value
    return normalized, tuple(removed)


def load_causal_actor_state(
    model: nn.Module,
    state: Mapping[str, object],
) -> tuple[str, ...]:
    """Strictly load retained actor tensors and report discarded legacy tensors."""
    normalized, removed = causal_actor_state(state)
    model.load_state_dict(normalized, strict=True)
    return removed


def migrate_optimizer_state(
    source: Mapping[str, object],
    source_parameter_names: Sequence[Sequence[str]],
    optimizer: torch.optim.Optimizer,
    target_parameter_names: Sequence[Sequence[str]],
    *,
    allowed_missing_parameter_names: Sequence[Sequence[str]] | None = None,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Remap optimizer slots after deleting or explicitly adding parameters."""
    source_groups = source.get("param_groups")
    source_slots = source.get("state")
    target = optimizer.state_dict()
    target_groups = target.get("param_groups")
    if not isinstance(source_groups, list) or not isinstance(source_slots, Mapping):
        raise ValueError("optimizer state is invalid")
    if not isinstance(target_groups, list):
        raise RuntimeError("new optimizer state is invalid")
    group_count = len(source_groups)
    if not (
        group_count
        == len(target_groups)
        == len(source_parameter_names)
        == len(target_parameter_names)
    ):
        raise ValueError("optimizer parameter-group layout differs")
    allowed_missing = (
        tuple(() for _ in range(group_count))
        if allowed_missing_parameter_names is None
        else tuple(tuple(group) for group in allowed_missing_parameter_names)
    )
    if len(allowed_missing) != group_count:
        raise ValueError("optimizer allowed-missing groups differ")

    migrated_slots: dict[int, object] = {}
    migrated_groups: list[dict[str, object]] = []
    removed: list[str] = []
    for source_group, target_group, source_names, target_names, allowed in zip(
        source_groups,
        target_groups,
        source_parameter_names,
        target_parameter_names,
        allowed_missing,
        strict=True,
    ):
        if not isinstance(source_group, Mapping) or not isinstance(target_group, Mapping):
            raise ValueError("optimizer parameter group is invalid")
        source_ids = source_group.get("params")
        target_ids = target_group.get("params")
        if not isinstance(source_ids, list) or not isinstance(target_ids, list):
            raise ValueError("optimizer parameter identifiers are invalid")
        if len(source_ids) != len(source_names) or len(target_ids) != len(target_names):
            raise ValueError("optimizer parameter names do not match stored identifiers")
        if len(set(target_names)) != len(target_names):
            raise ValueError("new optimizer parameter names are not unique")
        target_by_name = dict(zip(target_names, target_ids, strict=True))
        source_name_set = set(source_names)
        missing = [name for name in target_names if name not in source_name_set]
        unexpected_missing = set(missing) - set(allowed)
        if unexpected_missing:
            name = sorted(unexpected_missing)[0]
            raise ValueError(f"optimizer state lacks retained parameter: {name}")
        unexpected_allowed = set(allowed) - set(missing)
        if unexpected_allowed:
            name = sorted(unexpected_allowed)[0]
            raise ValueError(f"optimizer unexpectedly contains added parameter: {name}")

        for source_id, name in zip(source_ids, source_names, strict=True):
            target_id = target_by_name.get(name)
            if target_id is None:
                if not is_legacy_skill_auxiliary(name):
                    raise ValueError(f"optimizer state has unexpected deleted parameter: {name}")
                removed.append(name)
                continue
            if not isinstance(source_id, int) or not isinstance(target_id, int):
                raise ValueError("optimizer parameter identifier is not an integer")
            if source_id in source_slots:
                migrated_slots[target_id] = source_slots[source_id]

        migrated_group = dict(source_group)
        migrated_group["params"] = list(target_ids)
        migrated_groups.append(migrated_group)

    return {
        "state": migrated_slots,
        "param_groups": migrated_groups,
    }, tuple(removed)


__all__ = [
    "LEGACY_SKILL_AUXILIARY_PREFIXES",
    "causal_actor_state",
    "is_legacy_skill_auxiliary",
    "load_causal_actor_state",
    "migrate_optimizer_state",
]
