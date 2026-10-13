from __future__ import annotations

import pytest
import torch

from kagg_revue.policy.capability import (
    CapabilityCandidates,
    CapabilitySelector,
    CapabilitySelectorArchitecture,
)
from kagg_revue.rl.capabilities.search import FrozenTargetSearch


def _selector() -> CapabilitySelector:
    architecture = CapabilitySelectorArchitecture(
        state_width=8,
        model_width=8,
        feedforward_width=16,
        mode_tokens=4,
        integer_vocab_sizes=(7, 7, 7, 7, 7, 7),
        edit_value_features=4,
        candidate_features=5,
        search_features=3,
    )
    return CapabilitySelector(architecture)


def _candidates(batch: int, count: int, edits: int, mask: torch.Tensor) -> CapabilityCandidates:
    return CapabilityCandidates(
        mode=torch.randint(0, 4, (batch, count)),
        int_fields=torch.randint(0, 7, (batch, count, edits, 6)),
        edit_values=torch.randn(batch, count, edits, 4),
        edit_counts=torch.randint(0, edits + 1, (batch, count)),
        candidate_features=torch.randn(batch, count, 5),
        mask=mask,
    )


def test_capability_policy_replays_masked_behavior_without_search_gradients() -> None:
    torch.manual_seed(10)
    selector = _selector()
    mask = torch.tensor(
        [
            [True, True, False, True],
            [True, False, True, False],
            [True, True, True, True],
        ]
    )
    candidates = _candidates(3, 4, 2, mask)
    state = torch.randn(3, 8)
    search_logits = torch.randn(3, 4, requires_grad=True)
    search_features = torch.randn(3, 4, 3, requires_grad=True)

    rollout = selector.rollout(
        state,
        candidates,
        search_logits,
        search_features,
        sample=True,
        exploration_epsilon=0.2,
        uniform=torch.rand(3, 4),
    )
    replay = selector.evaluate_actions(
        state,
        candidates,
        search_logits,
        rollout.ids,
        search_features,
        exploration_epsilon=0.2,
        validate_ids=True,
    )

    assert torch.equal(rollout.ids, replay.ids)
    assert torch.allclose(rollout.log_probability, replay.log_probability)
    assert torch.allclose(replay.policy.probabilities.sum(dim=-1), torch.ones(3))
    assert torch.count_nonzero(replay.policy.probabilities[~mask]) == 0
    assert replay.policy.value_logits.shape == (3, 3)
    assert replay.policy.candidate_value_logits.shape == (3, 4, 3)

    loss = -replay.log_probability.mean() + replay.policy.value_logits.square().mean()
    loss.backward()
    assert selector.policy_query.weight.grad is not None
    assert selector.search_gate_head.weight.grad is not None
    assert search_logits.grad is None
    assert search_features.grad is None


def test_capability_policy_supports_buckets_and_safe_fallback() -> None:
    selector = _selector().eval()
    for candidate_count, edits in ((2, 1), (5, 3)):
        mask = torch.zeros(2, candidate_count, dtype=torch.uint8)
        candidates = _candidates(2, candidate_count, edits, mask)
        output = selector.rollout(
            torch.randn(2, 8),
            candidates,
            torch.randn(2, candidate_count),
            torch.randn(2, candidate_count, 3),
            sample=False,
        )

        assert torch.equal(output.ids, torch.zeros(2, dtype=torch.long))
        assert torch.equal(output.policy.candidate_mask[:, 0], torch.ones(2, dtype=torch.bool))
        assert torch.count_nonzero(output.policy.candidate_mask[:, 1:]) == 0
        assert torch.equal(output.policy.probabilities[:, 0], torch.ones(2))


def test_fixed_proposal_prior_skips_unvalidated_candidate_values() -> None:
    selector = _selector().eval()
    search = FrozenTargetSearch(
        selector,
        candidate_value_scale=0.0,
        replay_prior_logit=3.0,
    )
    calls: list[torch.nn.Module] = []
    handle = search.target.register_forward_hook(
        lambda module, _inputs, _output: calls.append(module)
    )
    try:
        candidates = _candidates(
            2,
            4,
            2,
            torch.tensor(
                [
                    [True, True, False, True],
                    [True, False, True, True],
                ]
            ),
        )
        candidates.mode[:, 0] = 0
        result = search.score(torch.randn(2, 8), candidates)
    finally:
        handle.remove()

    assert not calls
    assert torch.count_nonzero(result.target_values) == 0
    torch.testing.assert_close(result.logits[:, 0], torch.full((2,), 3.0))


def test_capability_exploration_is_an_exact_masked_behavior_mixture() -> None:
    torch.manual_seed(20)
    selector = _selector().eval()
    mask = torch.tensor(
        [
            [True, False, True, True],
            [True, True, False, False],
        ]
    )
    candidates = _candidates(2, 4, 2, mask)
    state = torch.randn(2, 8)
    search_logits = torch.randn(2, 4)
    search_features = torch.randn(2, 4, 3)
    learned = selector(state, candidates, search_logits, search_features)
    epsilon = 0.3

    rollout = selector.rollout(
        state,
        candidates,
        search_logits,
        search_features,
        sample=True,
        exploration_epsilon=epsilon,
        uniform=torch.rand(2, 4),
    )
    valid = mask.to(learned.probabilities.dtype)
    uniform = valid / valid.sum(dim=-1, keepdim=True)
    expected = (1.0 - epsilon) * learned.probabilities + epsilon * uniform
    expected = expected.masked_fill(~mask, 0.0)

    assert torch.allclose(rollout.policy.probabilities, expected)
    assert torch.allclose(torch.softmax(rollout.policy.logits, dim=-1), expected)
    assert torch.allclose(
        rollout.policy.log_probabilities[mask],
        expected[mask].log(),
    )
    assert torch.count_nonzero(rollout.policy.probabilities[~mask]) == 0
    expected_log = expected.clamp_min(torch.finfo(expected.dtype).tiny).log()
    expected_entropy = -(expected * expected_log.masked_fill(~mask, 0.0)).sum(dim=-1)
    assert torch.allclose(rollout.entropy, expected_entropy)

    replay = selector.evaluate_actions(
        state,
        candidates,
        search_logits,
        rollout.ids,
        search_features,
        exploration_epsilon=epsilon,
        validate_ids=True,
    )
    assert torch.allclose(replay.log_probability, rollout.log_probability)
    assert torch.allclose(replay.entropy, rollout.entropy)


@pytest.mark.parametrize("epsilon", [-0.1, 1.0, float("inf"), float("nan"), True])
def test_capability_exploration_rejects_invalid_epsilon(epsilon: float) -> None:
    selector = _selector().eval()
    candidates = _candidates(1, 2, 1, torch.ones(1, 2, dtype=torch.bool))

    with pytest.raises(ValueError, match="epsilon"):
        selector.rollout(
            torch.randn(1, 8),
            candidates,
            torch.randn(1, 2),
            torch.randn(1, 2, 3),
            sample=True,
            exploration_epsilon=epsilon,
        )
