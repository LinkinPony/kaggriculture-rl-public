from dataclasses import replace

import numpy as np
import pytest
import torch

from kagg_revue.native import _revue_native as native
from kagg_revue.production.branching.proposals import ProposalPolicy
from kagg_revue.production.contracts import ContractLayout, NetworkShape
from kagg_revue.production.expert.proposals import SearchPolicy
from kagg_revue.production.model import Policy, imitation_loss, log_probabilities
from kagg_revue.production.native import Layout
from kagg_revue.production.networks.work import WorkPolicy
from kagg_revue.production.work import propose_programs


def _layout() -> ContractLayout:
    spec = native.parallel_spec()
    units, cells = 2, 4
    product, history = spec["product_features"], spec["history_features"]
    base = Layout(
        2 * cells * spec["board_channels"],
        spec["unit_features"],
        spec["global_features"],
        units,
        2,
        7,
        (1, 3),
        16,
        spec["entity_version"],
        units * spec["unit_features"] + 9 * product + history,
        product,
        history,
    )
    return ContractLayout(base, 2, 3, NetworkShape("work-v1", 1, 2, 2, 8, 1))


def test_forced_pivot_preserves_decoder_prefixes_and_replay_probabilities() -> None:
    layout = _layout()
    baseline = WorkPolicy(layout).eval()
    branch = ProposalPolicy(layout, 2).eval()
    branch.load_state_dict(baseline.state_dict())
    observations = torch.zeros(2, layout.observation.features)
    steps = torch.zeros(2, dtype=torch.long)
    with torch.no_grad():
        control, _ = baseline.act(observations, steps, sample=False)
        unchanged, _ = branch.act(observations, steps, sample=False)
        assert torch.equal(control, unchanged)
        alternate = (control[1, 0] + 1) % layout.cardinalities[0]
        branch.forced[1, 0] = alternate
        chosen, probabilities = branch.act(observations, steps, sample=False)
        assert torch.equal(chosen[0], control[0])
        assert chosen[1, 0] == alternate
        replay = baseline(observations, steps, chosen)
        torch.testing.assert_close(probabilities, log_probabilities(replay, chosen))
        assert torch.all(chosen < torch.tensor(layout.cardinalities))


def test_native_fork_reorders_roots_and_keeps_state_and_history_independent() -> None:
    environment = {
        "boardSize": 4,
        "episodeSteps": 17,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 2,
    }
    units, span, quantities = 3, 2, [1, 3]
    batch = native.ParallelBatch(
        environment, [3, 7], [0, 1], ["pass", "pass"], [None, None], [], units, 1, quantities
    )
    width = units * (span + 1) * 4 + span * environment["maxMarketOrdersPerTurn"] * 2
    actions = np.zeros((2, width), dtype=np.int64)
    batch.advance_programs(actions, span, span)
    parents = np.array([1, 0, 1], dtype=np.int64)
    child = batch.fork(parents)
    original = np.empty((2, batch.entity_features), dtype=np.float16)
    copied = np.empty((3, batch.entity_features), dtype=np.float16)
    batch.observe_into(original)
    child.observe_into(copied)
    np.testing.assert_array_equal(copied, original[parents])
    before = batch.step_index
    child.advance_programs(actions[parents], span, span)
    assert batch.step_index == before
    assert child.step_index == before + span
    batch.advance_programs(actions, span, span)
    batch.observe_into(original)
    child.observe_into(copied)
    np.testing.assert_array_equal(copied, original[parents])
    with pytest.raises(IndexError):
        batch.fork(np.array([len(actions)], dtype=np.int64))
    assert batch.step_index == before + span


def test_search_samples_only_selected_lanes_with_actual_conditional_prefixes() -> None:
    layout = _layout()
    layout = replace(layout, network=replace(layout.network, time_prior=False))
    baseline = WorkPolicy(layout).eval()
    search = SearchPolicy(layout, 2).eval()
    search.load_state_dict(baseline.state_dict())
    search.ends[1] = 1
    observations = torch.zeros(2, layout.observation.features)
    steps = torch.zeros(2, dtype=torch.long)
    rng = torch.get_rng_state()
    with torch.no_grad():
        actions, _ = search.act(observations, steps, sample=False)
        torch.set_rng_state(rng)
        sampled, _ = baseline.act(observations, steps, sample=True)
        greedy, _ = baseline.act(observations, steps, sample=False)
        assert torch.equal(actions[0], greedy[0])
        assert torch.equal(actions[1], sampled[1])
        torch.testing.assert_close(
            search(observations, steps, actions), baseline(observations, steps, actions)
        )


def test_zero_table_scale_preserves_the_network_only_policy() -> None:
    layout = _layout()
    policy = Policy.from_layout(layout)
    with torch.no_grad():
        policy.prior.normal_()
    observations = torch.zeros(2, layout.observation.features)
    times = torch.zeros(2, dtype=torch.long)
    actions, _ = policy.act(observations, times, sample=False)
    full = policy(observations, times, actions)
    policy.prior_scale.fill_(0)
    zero = policy(observations, times, actions)
    valid = full > -1e8
    torch.testing.assert_close((full - zero)[valid], policy.prior[times][valid])
    stripped = Policy.from_layout(
        replace(layout, network=replace(layout.network, time_prior=False))
    )
    stripped.load_state_dict(
        {key: value for key, value in policy.state_dict().items() if key != "prior"}
    )
    torch.testing.assert_close(stripped(observations, times, actions), zero)
    assert "prior" not in dict(stripped.named_parameters())
    assert isinstance(policy, WorkPolicy)
    neural = {name: value for name, value in policy.named_parameters() if name != "prior"}
    policy.remove_prior()
    assert "prior" not in policy.state_dict()
    assert not hasattr(policy, "prior_scale")
    assert not policy.layout.network.time_prior
    assert all(dict(policy.named_parameters())[name] is value for name, value in neural.items())
    torch.testing.assert_close(policy(observations, times, actions), zero)


@pytest.mark.parametrize("temperature", [1.0, 0.4])
@pytest.mark.parametrize("time_prior", [False, True])
def test_conditional_program_replay_padding_and_gradients(
    temperature: float, time_prior: bool
) -> None:
    layout = _layout()
    layout = replace(layout, network=replace(layout.network, time_prior=time_prior))
    policy = Policy.from_layout(layout)
    for module in policy.modules():
        if isinstance(module, torch.nn.Linear):
            torch.nn.init.normal_(module.weight, std=0.04)
    observations = torch.randn(layout.decisions, layout.observation.features)
    units = observations[:, layout.observation.board_features :][
        :, : layout.observation.units * layout.observation.unit_features
    ].view(layout.decisions, layout.observation.units, -1)
    units[..., 0] = 0
    steps = torch.arange(layout.decisions)
    actions, behavior = policy.act(observations, steps, sample=True, temperature=temperature)
    replay = policy(observations, steps, actions)
    torch.testing.assert_close(behavior, log_probabilities(replay, actions, temperature))
    greedy, _ = policy.act(observations, steps, sample=False)
    tempered_greedy, _ = policy.act(observations, steps, sample=False, temperature=temperature)
    torch.testing.assert_close(greedy, tempered_greedy)
    assert torch.all(actions < torch.tensor(layout.cardinalities))
    padded = observations.clone()
    padded[
        :,
        layout.observation.board_features + 1 : layout.observation.board_features
        + layout.observation.unit_features,
    ] += 9
    torch.testing.assert_close(policy(padded, steps, actions), replay)
    market = actions[:, layout.work_factors :].view(
        -1, layout.capacity, layout.observation.markets, 2
    )
    assert not market[-1, layout.spans[-1] :].any()
    weights = policy.field_weights(actions, steps)
    assert torch.all(behavior[weights == 0] == 0)
    loss = imitation_loss(replay, actions, weights)
    loss.backward()
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in policy.encoder.parameters())
    assert all(torch.isfinite(p.grad).all() for p in policy.parameters() if p.grad is not None)
    if not time_prior:
        assert "prior" not in dict(policy.named_parameters())
        same_observations = observations[:1].expand(2, -1)
        same_actions = actions[:1].expand(2, -1)
        same_scores = policy(same_observations, torch.tensor([0, 1]), same_actions)
        torch.testing.assert_close(same_scores[0], same_scores[1])
    stopped = torch.zeros_like(actions)
    stopped_weights = policy.field_weights(stopped, steps)
    assert torch.all(
        stopped_weights.sum(-1) == layout.observation.units + torch.tensor(layout.spans)
    )


def test_proposals_keep_release_order_market_quantity_and_unfinished_travel() -> None:
    layout = _layout()
    base = layout.observation
    observations = np.zeros((base.turns, 1, base.features), dtype=np.float16)
    units = observations[
        ..., base.board_features : base.board_features + base.units * base.unit_features
    ].reshape(base.turns, 1, base.units, -1)
    units[:, :, 0, 0] = 1
    actions = np.zeros((base.turns, 1, base.units + base.markets, 2), dtype=np.int16)
    actions[0, 0, 0, 0] = 35
    actions[1, 0, 0, 0] = 36
    actions[2, 0, 0, 0] = 3
    actions[1, 0, base.units] = [11, 1]
    plan = propose_programs(observations, actions, layout)
    jobs = plan[0, 0, : layout.work_factors].reshape(base.units, layout.capacity + 1, 4)
    assert jobs[0, :2, 1].tolist() == actions[:2, 0, 0, 0].tolist()
    assert jobs[0, :2, 3].tolist() == [0, 1]
    assert jobs[0, 2, 0] != jobs[0, 1, 0]
    assert not jobs[1].any()
    market = plan[0, 0, layout.work_factors :].reshape(layout.capacity, base.markets, 2)
    np.testing.assert_array_equal(market[1, 0], actions[1, 0, base.units])


@pytest.mark.parametrize("selfplay", [False, True])
def test_persistent_program_matches_batched_execution_and_rejects_before_mutation(
    selfplay: bool,
) -> None:
    environment = {
        "boardSize": 4,
        "episodeSteps": 17,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 2,
    }
    units, span, quantities = 3, 8, [1, 3]
    seats = [0, 1] if selfplay else [1]
    reference = native.Engine(5, environment)
    batch = native.ParallelBatch(
        environment,
        [5],
        [seats[0]],
        [] if selfplay else ["pass"],
        [] if selfplay else [None],
        [],
        units,
        1,
        quantities,
    )
    sessions = [native.ContractSession(environment, units) for _ in seats]
    work = units * (span + 1) * 4
    plans = np.zeros(
        (len(seats), work + span * environment["maxMarketOrdersPerTurn"] * 2), dtype=np.int64
    )
    for index, seat in enumerate(seats):
        observation = reference.observation(seat)
        x, y = observation["farms"][seat]["farmer"]
        target = 1 + x + environment["boardSize"] * y
        jobs = plans[index, :work].reshape(units, span + 1, 4)
        jobs[0, :3] = [[target, 35, 0, 0], [target, 30, 0, 1], [target, 35, 0, 2]]
        markets = plans[index, work:].reshape(span, environment["maxMarketOrdersPerTurn"], 2)
        markets[0, 0] = [11, 1]
    invalid = plans.copy()
    invalid[-1, 1] = 1
    with pytest.raises(ValueError):
        batch.advance_programs(invalid, span, span, selfplay)
    assert batch.step_index == 0
    for _ in range(0, environment["episodeSteps"] - 1, span):
        for offset in range(span):
            actions = [{}, {}]
            for index, seat in enumerate(seats):
                session = sessions[index]
                session.update(reference.observation(seat))
                if offset == 0:
                    session.set_program(plans[index : index + 1], span, quantities)
                actions[seat] = session.program_action()
                assert session.program_action() == actions[seat]
            reference.step(*actions)
        batch.advance_programs(plans, span, span, selfplay)
        assert batch.observation(0) == reference.observation(seats[0])
    assert batch.completed_games == 1
