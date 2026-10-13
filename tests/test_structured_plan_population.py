from __future__ import annotations

import copy

import pytest
import torch

from kagg_revue.policy.plans import (
    GLOBAL_FIELDS,
    LINE_FIELDS,
    PRODUCTION_LINES,
    StructuredPlanArchitecture,
    StructuredPlanPolicy,
)
from kagg_revue.rl.plans.population import PlanSelfPlayPopulation


def _policy() -> StructuredPlanPolicy:
    architecture = StructuredPlanArchitecture(
        6,
        3,
        4,
        PRODUCTION_LINES,
        LINE_FIELDS,
        GLOBAL_FIELDS,
        16,
        24,
    )
    return StructuredPlanPolicy(architecture)


def _population(policy: StructuredPlanPolicy) -> PlanSelfPlayPopulation:
    return PlanSelfPlayPopulation(
        policy.architecture,
        capacity=3,
        snapshot_interval=2,
        selection_seed=41,
        device=torch.device("cpu"),
    )


def test_plan_population_retains_bounded_immutable_lineage() -> None:
    policy = _policy()
    population = _population(policy)
    assert population.snapshot(0, policy, force=True)
    initial_identity = population.identities[0]

    with torch.no_grad():
        next(policy.parameters()).add_(1.0)
    assert not population.snapshot(1, policy)
    assert population.snapshot(2, policy)
    with torch.no_grad():
        next(policy.parameters()).add_(1.0)
    assert population.snapshot(4, policy)

    assert population.size == 3
    assert population.identities[0] == initial_identity
    with torch.no_grad():
        next(policy.parameters()).add_(1.0)
    assert population.snapshot(6, policy)
    assert population.size == 3
    assert initial_identity not in population.identities
    state = population.state_dict()
    snapshots = state["snapshots"]
    assert isinstance(snapshots, list)
    assert [snapshot["update"] for snapshot in snapshots] == [2, 4, 6]
    selected = population.select(7)
    resident = population.policy(selected)
    for name, value in resident.state_dict().items():
        torch.testing.assert_close(value.cpu(), selected.model_state[name])
    assert not any(parameter.requires_grad for parameter in resident.parameters())


def test_plan_population_restore_authenticates_snapshot_identity() -> None:
    policy = _policy()
    population = _population(policy)
    population.snapshot(0, policy, force=True)
    state = population.state_dict()

    restored = _population(policy)
    restored.load_state_dict(state, completed_update=0)
    assert restored.identities == population.identities
    assert restored.select(7).identity == population.select(7).identity

    tampered = copy.deepcopy(state)
    snapshots = tampered["snapshots"]
    assert isinstance(snapshots, list)
    model_state = snapshots[0]["model_state"]
    first_tensor = next(iter(model_state.values()))
    first_tensor.view(-1)[0] += 1
    with pytest.raises(ValueError, match="identity differs"):
        restored.load_state_dict(tampered, completed_update=0)


def test_plan_population_rotates_by_direct_match_recency() -> None:
    policy = _policy()
    population = _population(policy)
    population.snapshot(0, policy, force=True)
    with torch.no_grad():
        next(policy.parameters()).add_(1.0)
    population.snapshot(2, policy)
    with torch.no_grad():
        next(policy.parameters()).add_(1.0)
    population.snapshot(4, policy)

    first = population.select(5)
    assert first.update == 0
    population.record_outcomes(first.identity, 5, (1, 0, -1))
    second = population.select(6)
    assert second.update == 2
    population.record_outcomes(second.identity, 6, (1, 1, -1))
    third = population.select(7)
    assert third.update == 4
    population.record_outcomes(third.identity, 7, (0, 0, 1))

    assert population.select(8).identity == first.identity
    state = population.state_dict()
    restored = _population(policy)
    restored.load_state_dict(state, completed_update=7)
    assert restored.select(8).identity == first.identity
