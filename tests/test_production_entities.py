from dataclasses import asdict, replace

import numpy as np
import pytest
import torch

from kagg_revue.native import _revue_native as native
from kagg_revue.production.cadence import prior_indices, rehearsal_steps
from kagg_revue.production.contracts import ContractLayout, NetworkShape
from kagg_revue.production.model import Critic, Policy, log_probabilities
from kagg_revue.production.native import Layout
from kagg_revue.production.runtime import ActorRuntime


def _layout() -> ContractLayout:
    spec = native.parallel_spec()
    cells, units = 4, 2
    product, history = spec["product_features"], spec["history_features"]
    base = Layout(
        2 * cells * spec["board_channels"],
        spec["unit_features"],
        spec["global_features"],
        units,
        2,
        7,
        (1,),
        16,
        spec["entity_version"],
        units * spec["unit_features"] + 9 * product + history,
        product,
        history,
    )
    return ContractLayout(base, 2, 3, NetworkShape("entities-v2", 2, 2, 2, 8, 1))


def test_conditional_sampling_replays_and_respects_predecessors_and_padding() -> None:
    layout = _layout()
    policy = Policy.from_layout(layout)
    # Exercise actual state-dependent heads, rather than the zero residual initializer.
    for module in policy.modules():
        if isinstance(module, torch.nn.Linear):
            torch.nn.init.normal_(module.weight, std=0.04)
    base = layout.observation
    observations = torch.randn(3, base.features)
    unit_start = base.board_features
    units = observations[:, unit_start : unit_start + base.units * base.unit_features].view(
        3, base.units, base.unit_features
    )
    units[:, 0, 0] = 1
    units[:, 1, 0] = 0
    steps = torch.arange(3)
    actions, behavior = policy.act(observations, steps, sample=True)
    replay = policy(observations, steps, actions)
    torch.testing.assert_close(behavior, log_probabilities(replay, actions))
    assert torch.all(actions < torch.tensor(layout.cardinalities))
    changed = actions.clone()
    changed[:, 0] = (changed[:, 0] + 1) % layout.cardinalities[0]
    alternate = policy(observations, steps, changed)
    torch.testing.assert_close(replay[:, 0], alternate[:, 0])
    assert not torch.allclose(replay[:, 1], alternate[:, 1])
    padded = observations.clone()
    start = unit_start + base.unit_features
    padded[:, start + 1 : start + base.unit_features] += 20
    torch.testing.assert_close(policy(padded, steps, actions), replay)
    critic = Critic(layout)
    torch.testing.assert_close(critic(padded), critic(observations))
    loss = -log_probabilities(replay, actions).mean()
    loss.backward()
    assert any(
        parameter.grad is not None and parameter.grad.abs().sum() > 0
        for parameter in policy.encoder.parameters()
    )
    assert all(
        torch.isfinite(parameter.grad).all()
        for parameter in policy.parameters()
        if parameter.grad is not None
    )


def test_public_history_and_entity_encoding_match_bulk_and_single_turn_execution() -> None:
    environment = {
        "boardSize": 4,
        "episodeSteps": 19,
        "turnsPerDay": 3,
        "maxMarketOrdersPerTurn": 3,
    }
    units = 3
    first = native.ParallelBatch(environment, [11], [0], [], [], [], units, 1, [1])
    second = native.ParallelBatch(environment, [11], [0], [], [], [], units, 1, [1])
    cells = environment["boardSize"] ** 2
    plans = np.zeros((2, cells * 4 + 23), dtype=np.int64)
    plans[:, : cells * 4] = np.tile([1, 1, 1, 2], cells)
    plans[:, cells * 4 : cells * 4 + 5] = [2, 1, 0, 4, 2]
    encoded = np.empty((2, first.entity_features), dtype=np.float16)
    expected = np.empty_like(encoded)
    for _ in range(3):
        first.advance_selfplay(plans, 1)
    second.advance_selfplay(plans, 3)
    first.observe_selfplay_into(encoded)
    second.observe_selfplay_into(expected)
    np.testing.assert_array_equal(encoded, expected)
    # Observation encoding is pure: repeated reads must not consume history.
    first.observe_selfplay_into(expected)
    np.testing.assert_array_equal(encoded, expected)
    legacy = np.empty((2, first.features), dtype=np.float16)
    first.observe_selfplay_into(legacy)
    np.testing.assert_array_equal(encoded[:, : first.features], legacy)
    assert np.isfinite(encoded).all()
    spec = native.parallel_spec()
    opponent = encoded[:, first.features : first.features + units * spec["unit_features"]]
    opponent = opponent.reshape(2, units, spec["unit_features"])
    # Public opposing unit tokens must never expose carried quantities or insertion order.
    assert not opponent[..., 6:19].any()
    assert not opponent[..., -12:].any()


@pytest.mark.parametrize("seat", [0, 1])
def test_official_observation_adapter_preserves_history_and_compiled_actions(seat: int) -> None:
    environment = {
        "boardSize": 4,
        "episodeSteps": 17,
        "turnsPerDay": 3,
        "maxMarketOrdersPerTurn": 3,
    }
    units = 3
    batch = native.ParallelBatch(environment, [7], [seat], ["pass"], [None], [], units, 1, [1])
    session = native.ContractSession(environment, units)
    cells = environment["boardSize"] ** 2
    plan = np.zeros((1, cells * 4 + 23), dtype=np.int64)
    plan[:, : cells * 4] = np.tile([1, 2, 1, 2], cells)
    plan[:, cells * 4 : cells * 4 + 5] = [2, 1, 0, 4, 2]
    expected = np.empty((1, batch.entity_features), dtype=np.float16)
    actual = np.empty_like(expected)
    for _ in range(environment["episodeSteps"] - 1):
        observation = batch.observation(0)
        session.update(observation)
        session.update(observation)
        batch.observe_into(expected)
        session.observe_into(actual)
        np.testing.assert_array_equal(actual, expected)
        assert session.action(plan) == batch.contract_action(0, plan)
        batch.advance(plan, 1)


def test_traced_greedy_policy_preserves_state_and_time_conditioning() -> None:
    from kagg_revue.production.deployment.bundle import GreedyActor

    policy = Policy.from_layout(_layout()).eval()
    for parameter in policy.parameters():
        torch.nn.init.normal_(parameter, std=0.05)
    example = torch.zeros((1, policy.layout.observation.features))
    actor = GreedyActor(policy).eval()
    traced = torch.jit.freeze(torch.jit.trace(actor, (example, torch.zeros(1, dtype=torch.long))))
    with torch.no_grad():
        for step in range(policy.layout.decisions):
            observation = torch.randn_like(example)
            time = torch.tensor([step])
            torch.testing.assert_close(traced(observation, time), actor(observation, time))


def test_finer_terminal_calendar_covers_every_turn_and_preserves_causal_prior() -> None:
    source = _layout()
    target = replace(source, late_start=4, late_interval=1)
    visited = [
        turn
        for start, span in zip(target.starts, target.spans, strict=True)
        for turn in range(start, start + span)
    ]
    assert visited == list(range(source.observation.turns))
    assert target.spans[-1] == 1
    for turn, index in zip(target.starts, prior_indices(source.starts, target.starts), strict=True):
        assert source.starts[index] <= turn
        assert index + 1 == source.decisions or turn < source.starts[index + 1]


def test_rehearsal_keeps_original_observation_times_under_more_frequent_decisions() -> None:
    source = _layout()
    target = replace(source, interval=1)
    mapping = rehearsal_steps({"layout": asdict(source)}, target, torch.device("cpu"))
    assert [target.starts[index] for index in mapping.tolist()] == list(source.starts)
    with pytest.raises(ValueError, match="actual policy decision"):
        rehearsal_steps(
            {"layout": asdict(source)}, replace(source, interval=2), torch.device("cpu")
        )


@pytest.mark.skipif(
    not torch.cuda.is_available(), reason="CUDA Graph weight lifetime requires CUDA"
)
@pytest.mark.parametrize(("sample", "temperature"), [(False, 1.0), (True, 0.4)])
def test_actor_graph_uses_current_weights_after_updates_and_another_capture(
    sample: bool, temperature: float
) -> None:
    policy = Policy.from_layout(_layout()).cuda()
    for module in policy.modules():
        if isinstance(module, torch.nn.Linear):
            torch.nn.init.normal_(module.weight, std=0.03)
    runtime = ActorRuntime(policy, 3, sample=sample, temperature=temperature)
    runtime.host.copy_(torch.randn_like(runtime.host))
    with torch.no_grad():
        for module in policy.modules():
            if isinstance(module, torch.nn.Linear):
                module.weight.add_(torch.randn_like(module.weight) * 0.04)
        other = ActorRuntime(policy, 2, sample=False)
        other.host.zero_()
        other.act(0)
        del other
        chosen, actual = runtime.act(0)
        with torch.autocast("cuda", dtype=torch.bfloat16, cache_enabled=False):
            expected = log_probabilities(
                policy(runtime.observations, runtime.steps, chosen), chosen, temperature
            )
    torch.testing.assert_close(actual, expected, atol=2e-4, rtol=2e-4)
