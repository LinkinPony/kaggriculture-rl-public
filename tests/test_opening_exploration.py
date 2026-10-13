import numpy as np
import torch

from kagg_revue.rl.opening.noise import (
    OpeningProbe,
    OpeningResidual,
    build_opening_noise_plan,
    materialize_opening_residuals,
    normalized_action_head_direction,
)
from kagg_revue.rl.rollout.batch import _ActorInputBuffers
from kagg_revue.rl.rollout.scheduler import BatchedRolloutRunner


def test_opening_residual_is_deterministic_and_action_row_exchangeable() -> None:
    actions = 7
    width = 128
    first = normalized_action_head_direction(17, actions, width)
    second = normalized_action_head_direction(17, actions, width)

    np.testing.assert_array_equal(first, second)
    assert first.shape == (actions, width)
    assert first.dtype == np.float32
    assert np.all(np.linalg.norm(first, axis=1) > 0.0)

    bank = np.stack([normalized_action_head_direction(seed, actions, width) for seed in range(64)])
    np.testing.assert_allclose(bank.mean(axis=(0, 2)), 0.0, atol=0.003)
    np.testing.assert_allclose(
        bank.var(axis=(0, 2)),
        np.full(actions, 1.0 / width),
        rtol=0.05,
    )

    residual = materialize_opening_residuals(
        [OpeningResidual(direction_id=3, seed=17, scale=2.5, prefix_turns=4), None],
        actions,
        width,
        force=True,
    )
    assert residual is not None
    np.testing.assert_array_equal(residual[0], first * np.float32(2.5))
    np.testing.assert_array_equal(residual[1], np.zeros((actions, width), dtype=np.float32))


def test_opening_noise_plan_samples_training_perspectives_without_action_bias() -> None:
    probe = OpeningProbe(
        hidden=torch.tensor(
            [
                [1.0, 0.0, 0.5, -0.5],
                [0.0, 1.0, -0.5, 0.5],
            ]
        ),
        logits=torch.tensor([[8.0, 0.0, 0.0], [8.0, 0.0, 0.0]]),
        legal_mask=torch.ones((2, 3), dtype=torch.bool),
    )
    jobs = (
        (11, 0, "self_play"),
        (12, 0, "frozen"),
        (12, 1, "frozen"),
    )

    plan = build_opening_noise_plan(
        probe,
        jobs,
        noisy_fraction=0.5,
        selection_seed=19,
        direction_seed=23,
        prefix_turns=2,
        target_escape=0.2,
        maximum_scale=64.0,
        bisection_steps=12,
    )

    assert plan.total_perspectives == 4
    assert plan.sampled_perspectives == 2
    assert len(plan.assignments) == 2
    assert len({residual.seed for residual in plan.assignments.values()}) == 2
    assert all(residual.prefix_turns == 2 for residual in plan.assignments.values())
    assert plan.calibration.mean_escape > 0.0


def _actor_inputs(
    host_residual: np.ndarray,
    device_residual: torch.Tensor | None = None,
) -> _ActorInputBuffers:
    return _ActorInputBuffers(
        engines=[],
        players=[],
        previous_tokens=np.zeros((1, 1), dtype=np.int64),
        previous_quantities=np.zeros((1, 1), dtype=np.int64),
        previous_mask=np.zeros((1, 1), dtype=np.bool_),
        opening_residual=host_residual,
        residual_turns=3,
        device_opening_residual=device_residual,
    )


def test_opening_residual_is_zeroed_in_place_after_prefix() -> None:
    host = np.ones((1, 3, 4), dtype=np.float32)
    host_pointer = int(host.__array_interface__["data"][0])
    host_inputs = _actor_inputs(host)

    BatchedRolloutRunner._disable_completed_residual(host_inputs, turn_index=2)
    np.testing.assert_array_equal(host, np.ones_like(host))
    BatchedRolloutRunner._disable_completed_residual(host_inputs, turn_index=3)

    assert host_inputs.opening_residual is host
    assert int(host.__array_interface__["data"][0]) == host_pointer
    np.testing.assert_array_equal(host, np.zeros_like(host))
    assert host_inputs.residual_disabled is True

    device = torch.ones((1, 3, 4))
    device_pointer = device.data_ptr()
    device_inputs = _actor_inputs(np.ones((1, 3, 4), dtype=np.float32), device)

    BatchedRolloutRunner._disable_completed_residual(device_inputs, turn_index=3)
    BatchedRolloutRunner._disable_completed_residual(device_inputs, turn_index=4)

    assert device_inputs.device_opening_residual is device
    assert device.data_ptr() == device_pointer
    assert torch.count_nonzero(device).item() == 0
    assert device_inputs.residual_disabled is True
