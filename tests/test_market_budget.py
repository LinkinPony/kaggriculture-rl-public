from pathlib import Path

import numpy as np
import pytest
import torch

from kagg_revue.deployment.actor import freeze
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.typed import TypedGroundedPolicy
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import log_probabilities


def _inputs() -> tuple[Experiment, TypedGroundedPolicy, torch.Tensor]:
    torch.set_num_threads(1)
    config = Experiment(
        output_dir=Path("outputs/learning/budget-check"),
        architecture="grounded-v2",
        market_budget=True,
        decision_interval=1,
        width=16,
        depth=1,
        critic_width=16,
        critic_depth=1,
        unit_limit=4,
        quantity_max=4,
        quantity_extra=(1000000,),
        environment={
            "boardSize": 4,
            "episodeSteps": 25,
            "turnsPerDay": 4,
            "maxMarketOrdersPerTurn": 3,
        },
    )
    layout = ContractLayout.resolve(runtime_settings(config))
    policy = random_policy(layout, 3, config.exploration)
    assert isinstance(policy, TypedGroundedPolicy)
    inputs = np.empty((2, layout.observation.features), np.float16)
    for index, cash in enumerate((988, 1054)):
        observation = native.Engine(9, config.environment).observation(0)
        observation["farms"][0]["money"] = cash
        observation["private"]["shed"]["WHEAT"] = 7
        session = native.ContractSession(config.environment, config.unit_limit)
        session.update(observation)
        session.observe_into(inputs[index : index + 1])
    return config, policy, torch.from_numpy(inputs)


def test_quote_ledger_respects_funding_boundary_and_caps_estimated_oversells() -> None:
    _, policy, inputs = _inputs()
    budget = policy.budget
    assert budget is not None
    ledger, costs = budget.start(inputs)
    torch.testing.assert_close(ledger[:, 1], torch.tensor([988.0, 1054.0]), atol=0.5, rtol=0)
    torch.testing.assert_close(costs[:, 20], torch.full((2,), 500.0))
    active = torch.ones(2, dtype=torch.bool)
    after, _ = budget.advance(ledger, costs, torch.full((2,), 20), torch.ones(2).long(), active)
    torch.testing.assert_close(after[:, 14], ledger[:, 14] + torch.tensor([1.0, 2.0]))
    torch.testing.assert_close(after[:, 1], torch.tensor([488.0, 54.0]), atol=0.5, rtol=0)
    sold, _ = budget.advance(ledger, costs, torch.full((2,), 2), torch.full((2,), 4), active)
    torch.testing.assert_close(sold[:, 3], torch.zeros(2))
    torch.testing.assert_close(sold[:, 1], ledger[:, 1] - 7 * costs[:, 2])
    stopped, stopped_costs = budget.advance(
        ledger, costs, torch.full((2,), 20), torch.ones(2).long(), ~active
    )
    torch.testing.assert_close(stopped, ledger)
    torch.testing.assert_close(stopped_costs, costs)


def test_budget_sampling_is_causal_and_survives_checkpoint_and_cpu_export(tmp_path: Path) -> None:
    config, policy, inputs = _inputs()
    steps = torch.zeros(2, dtype=torch.long)
    actions, behavior = policy.act(inputs, steps, sample=True)
    logits = policy(inputs, steps, actions)
    torch.testing.assert_close(log_probabilities(logits, actions), behavior)
    changed = actions.clone()
    changed[:, -2:] = torch.tensor([20, 1])
    torch.testing.assert_close(policy(inputs, steps, changed)[:, :-1], logits[:, :-1])
    weights = policy.field_weights(actions, steps, inputs)
    loss = -(log_probabilities(logits, actions) * weights).sum(-1).mean()
    loss.backward()
    assert policy.budget is not None
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in policy.budget.parameters())
    assert all(torch.isfinite(p.grad).all() for p in policy.parameters() if p.grad is not None)
    checkpoint = tmp_path / "policy.pt"
    save_policy(checkpoint, policy, runtime_settings(config))
    restored, _ = load_policy(checkpoint, torch.device("cpu"))
    torch.testing.assert_close(restored(inputs, steps, actions), logits)
    frozen = tmp_path / "actor.pt"
    freeze(restored, frozen)
    exported = torch.jit.load(str(frozen))
    with torch.inference_mode():
        torch.manual_seed(910)
        expected = restored.act(inputs[:1], steps[:1], sample=True)[0]
        torch.manual_seed(910)
        actual = exported(inputs[:1], steps[:1])
    torch.testing.assert_close(actual, expected)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA graph regression requires a GPU")
def test_budget_features_support_bf16_cuda_graph_capture() -> None:
    _, policy, inputs = _inputs()
    policy = policy.to("cuda:0")
    runtime = ActorRuntime(policy, 2, sample=False, precision="bf16")
    runtime.host.copy_(inputs)
    actual, probabilities = runtime.act(0)
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16, cache_enabled=False):
        expected, expected_probabilities = policy.act(
            inputs.to("cuda:0"), torch.zeros(2, device="cuda:0", dtype=torch.long), sample=False
        )
    torch.testing.assert_close(actual, expected)
    torch.testing.assert_close(probabilities, expected_probabilities)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA RNG regression requires a GPU")
@pytest.mark.parametrize("compiled", [False, True])
def test_captured_sampling_advances_rng_and_resumes_at_the_next_draw(compiled: bool) -> None:
    _, policy, inputs = _inputs()
    policy = policy.to("cuda:0")
    torch.manual_seed(66001)
    runtime = ActorRuntime(policy, 2, sample=True, compile_inference=compiled)
    runtime.host.copy_(inputs)
    draws, states = [], [torch.cuda.get_rng_state(0)]
    for _ in range(8):
        draws.append(runtime.act(0)[0].cpu().clone())
        states.append(torch.cuda.get_rng_state(0))
    assert all(not torch.equal(a, b) for a, b in zip(states, states[1:], strict=False))
    assert len({draw.numpy().tobytes() for draw in draws}) > 1
    # A new inference graph must continue after the saved draw, including the
    # RNG-preserving warmup/capture performed during process recovery.
    torch.cuda.set_rng_state(states[3], 0)
    restored = ActorRuntime(policy, 2, sample=True, compile_inference=compiled)
    restored.host.copy_(inputs)
    torch.testing.assert_close(torch.cuda.get_rng_state(0), states[3])
    for expected, state in zip(draws[3:], states[4:], strict=True):
        torch.testing.assert_close(restored.act(0)[0].cpu(), expected)
        torch.testing.assert_close(torch.cuda.get_rng_state(0), state)
