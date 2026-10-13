from __future__ import annotations

import numpy as np
import torch

from kagg_revue.policy.plans import (
    BOARD_SHAPE,
    ECONOMIC_STATE_FEATURES,
    GLOBAL_FEATURES,
    GLOBAL_FIELDS,
    LINE_FIELDS,
    PRODUCTION_LINES,
    UNIT_SHAPE,
    PlanInputs,
    StructuredPlanArchitecture,
    StructuredPlanPolicy,
)
from kagg_revue.rl.plans import PlanVersionContract, TensorPlanRolloutBatch
from kagg_revue.rl.plans.rollout import _training_perspectives
from kagg_revue.rl.plans.storage import freeze_policy_output


def test_structured_plan_self_play_uses_both_training_perspectives() -> None:
    jobs = (
        (11, 0, "self_play"),
        (13, 0, "history:u00000000:synthetic"),
        (13, 1, "history:u00000000:synthetic"),
    )
    assert _training_perspectives(jobs) == (
        *jobs,
        (11, 1, "self_play"),
    )


def test_structured_plan_rollout_batch_preserves_complete_behavior_contract() -> None:
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
    policy = StructuredPlanPolicy(architecture)
    inputs = PlanInputs(
        board=torch.randn(3, *BOARD_SHAPE),
        units=torch.randn(3, *UNIT_SHAPE),
        global_features=torch.randn(3, GLOBAL_FEATURES),
        economic_state=torch.zeros(
            3,
            ECONOMIC_STATE_FEATURES,
            dtype=torch.int32,
        ),
        features=torch.randn(3, 6),
        journal=torch.randn(3, 3),
        events=torch.zeros(3, 4),
        active_lines=torch.zeros(
            3,
            PRODUCTION_LINES,
            LINE_FIELDS,
            dtype=torch.long,
        ),
        active_line_mask=torch.zeros(3, PRODUCTION_LINES, dtype=torch.bool),
        global_plan=torch.zeros(3, GLOBAL_FIELDS, dtype=torch.long),
    )
    output = policy.rollout(
        inputs,
        sample=True,
        generator=torch.Generator().manual_seed(42),
    )
    frozen = freeze_policy_output(output)
    np.testing.assert_array_equal(frozen.mode, output.actions.mode.numpy())
    np.testing.assert_array_equal(
        frozen.line_operations,
        output.actions.line_operations.numpy(),
    )
    np.testing.assert_array_equal(
        frozen.line_values,
        output.actions.line_values.numpy(),
    )
    np.testing.assert_array_equal(
        frozen.global_values,
        output.actions.global_values.numpy(),
    )
    np.testing.assert_array_equal(
        frozen.line_value_mask,
        output.masks.line_values.numpy(),
    )
    np.testing.assert_allclose(
        frozen.joint_log_probability,
        output.joint_log_probability.detach().numpy(),
    )
    contract = PlanVersionContract(
        language_version="synthetic-language",
        observation_version="synthetic-observation",
        grammar_version="synthetic-grammar",
        executor_version="synthetic-executor",
    )
    batch = TensorPlanRolloutBatch(
        inputs=inputs,
        actions=output.actions,
        masks=output.masks,
        old_joint_log_probability=output.joint_log_probability.detach(),
        old_values=output.value.detach(),
        episode_index=torch.tensor([0, 1, 1]),
        start_steps=torch.tensor([0, 0, 12]),
        durations=torch.tensor([20, 12, 8]),
        outcomes=torch.tensor([-1.0, 1.0]),
        contract=contract,
        episode_ids=("episode-a", "episode-b"),
    )
    copied = batch.to("cpu")
    assert copied.contract.fingerprint == contract.fingerprint
    assert copied.decisions == 3
    assert copied.episodes == 2
    assert copied.tensor_bytes() > 0
