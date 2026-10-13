"""Host accumulation helpers for finite portfolio rollout panels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.policy.plans import PlanActions, PlanConditionalMasks, PlanInputs
from kagg_revue.policy.plans.model import (
    StructuredPlanBehaviorOutput,
    StructuredPlanPolicyOutput,
)
from kagg_revue.rl.plans.contract import PlanVersionContract
from kagg_revue.rl.plans.data import TensorPlanRolloutBatch

PlanBlocks: TypeAlias = dict[str, list[NDArray[Any]]]


@dataclass(frozen=True)
class FrozenPlanActions:
    """One-transfer host snapshot used by execution-only opponents."""

    mode: NDArray[np.int64]
    line_operations: NDArray[np.int64]
    line_values: NDArray[np.int64]
    global_operation: NDArray[np.int64]
    global_values: NDArray[np.int64]


@dataclass(frozen=True)
class FrozenPlanPolicyOutput:
    """Three-transfer host snapshot of one GPU portfolio batch."""

    mode: NDArray[np.int64]
    line_operations: NDArray[np.int64]
    line_values: NDArray[np.int64]
    global_operation: NDArray[np.int64]
    global_values: NDArray[np.int64]
    mode_mask: NDArray[np.bool_]
    line_operation_mask: NDArray[np.bool_]
    line_value_mask: NDArray[np.bool_]
    global_operation_mask: NDArray[np.bool_]
    global_value_mask: NDArray[np.bool_]
    factor_mask: NDArray[np.bool_]
    joint_log_probability: NDArray[np.float32]
    value: NDArray[np.float32]


def new_blocks() -> PlanBlocks:
    """Create aligned host columns for one finite rollout update."""
    return {
        name: []
        for name in (
            "board",
            "units",
            "global_features",
            "economic_state",
            "features",
            "journal",
            "events",
            "active_lines",
            "active_line_mask",
            "global_plan",
            "mode",
            "line_operations",
            "line_values",
            "global_operation",
            "global_values",
            "mode_mask",
            "line_operation_mask",
            "line_value_mask",
            "global_operation_mask",
            "global_value_mask",
            "factor_mask",
            "old_log_probability",
            "old_value",
            "episode_index",
            "start_step",
        )
    }


def freeze_plan_actions(actions: PlanActions) -> FrozenPlanActions:
    """Pack one action bundle without learner-only masks or statistics."""
    lines = actions.line_operations.shape[1]
    line_fields = actions.line_values.shape[2]
    global_fields = actions.global_values.shape[1]
    packed = (
        torch.cat(
            (
                actions.mode[:, None],
                actions.line_operations,
                actions.line_values.flatten(1),
                actions.global_operation[:, None],
                actions.global_values,
            ),
            dim=1,
        )
        .detach()
        .cpu()
        .numpy()
        .astype(np.int64, copy=False)
    )
    line_operation_end = 1 + lines
    line_value_end = line_operation_end + lines * line_fields
    global_operation_end = line_value_end + 1
    return FrozenPlanActions(
        mode=packed[:, 0],
        line_operations=packed[:, 1:line_operation_end],
        line_values=packed[:, line_operation_end:line_value_end].reshape(
            -1,
            lines,
            line_fields,
        ),
        global_operation=packed[:, line_value_end],
        global_values=packed[
            :,
            global_operation_end : global_operation_end + global_fields,
        ],
    )


def freeze_policy_output(
    output: StructuredPlanPolicyOutput | StructuredPlanBehaviorOutput,
) -> FrozenPlanPolicyOutput:
    """Pack heterogeneous policy tensors into three synchronized GPU copies."""
    actions = output.actions
    lines = actions.line_operations.shape[1]
    line_fields = actions.line_values.shape[2]
    global_fields = actions.global_values.shape[1]
    frozen_actions = freeze_plan_actions(actions)

    masks = output.masks
    mask_widths = (
        masks.mode.shape[1],
        masks.line_operations.shape[1] * masks.line_operations.shape[2],
        masks.line_values.shape[1] * masks.line_values.shape[2] * masks.line_values.shape[3],
        masks.global_operation.shape[1],
        masks.global_values.shape[1] * masks.global_values.shape[2],
        masks.factors.shape[1],
    )
    packed_masks = (
        torch.cat(
            (
                masks.mode,
                masks.line_operations.flatten(1),
                masks.line_values.flatten(1),
                masks.global_operation,
                masks.global_values.flatten(1),
                masks.factors,
            ),
            dim=1,
        )
        .detach()
        .cpu()
        .numpy()
        .astype(np.bool_, copy=False)
    )
    offsets = np.cumsum((0, *mask_widths), dtype=np.int64)
    mask_parts = tuple(
        packed_masks[:, offsets[index] : offsets[index + 1]] for index in range(len(mask_widths))
    )
    statistics = (
        torch.stack((output.joint_log_probability, output.value), dim=1)
        .detach()
        .cpu()
        .numpy()
        .astype(np.float32, copy=False)
    )
    return FrozenPlanPolicyOutput(
        mode=frozen_actions.mode,
        line_operations=frozen_actions.line_operations,
        line_values=frozen_actions.line_values,
        global_operation=frozen_actions.global_operation,
        global_values=frozen_actions.global_values,
        mode_mask=mask_parts[0],
        line_operation_mask=mask_parts[1].reshape(
            -1,
            lines,
            masks.line_operations.shape[2],
        ),
        line_value_mask=mask_parts[2].reshape(
            -1,
            lines,
            line_fields,
            masks.line_values.shape[3],
        ),
        global_operation_mask=mask_parts[3],
        global_value_mask=mask_parts[4].reshape(
            -1,
            global_fields,
            masks.global_values.shape[2],
        ),
        factor_mask=mask_parts[5],
        joint_log_probability=statistics[:, 0],
        value=statistics[:, 1],
    )


def record_policy(
    blocks: PlanBlocks,
    output: FrozenPlanPolicyOutput,
    indices: NDArray[np.int64],
) -> None:
    """Append sampled conditional masks, likelihood, and value."""
    blocks["mode_mask"].append(output.mode_mask[indices])
    blocks["line_operation_mask"].append(output.line_operation_mask[indices])
    blocks["line_value_mask"].append(output.line_value_mask[indices])
    blocks["global_operation_mask"].append(output.global_operation_mask[indices])
    blocks["global_value_mask"].append(output.global_value_mask[indices])
    blocks["factor_mask"].append(output.factor_mask[indices])
    blocks["old_log_probability"].append(output.joint_log_probability[indices])
    blocks["old_value"].append(output.value[indices])


def build_batch(
    blocks: PlanBlocks,
    episode_index: NDArray[np.int64],
    start_steps: NDArray[np.int64],
    durations: NDArray[np.int64],
    outcomes: NDArray[np.float32],
    episode_ids: list[str],
    contract: PlanVersionContract,
) -> TensorPlanRolloutBatch:
    """Freeze accumulated host columns into the validated SMDP batch."""
    concatenate = np.concatenate
    return TensorPlanRolloutBatch(
        inputs=PlanInputs(
            board=torch.from_numpy(concatenate(blocks["board"])),
            units=torch.from_numpy(concatenate(blocks["units"])),
            global_features=torch.from_numpy(concatenate(blocks["global_features"])),
            economic_state=torch.from_numpy(concatenate(blocks["economic_state"])),
            features=torch.from_numpy(concatenate(blocks["features"])),
            journal=torch.from_numpy(concatenate(blocks["journal"])),
            events=torch.from_numpy(concatenate(blocks["events"])),
            active_lines=torch.from_numpy(concatenate(blocks["active_lines"])),
            active_line_mask=torch.from_numpy(concatenate(blocks["active_line_mask"])),
            global_plan=torch.from_numpy(concatenate(blocks["global_plan"])),
        ),
        actions=PlanActions(
            mode=torch.from_numpy(concatenate(blocks["mode"])),
            line_operations=torch.from_numpy(concatenate(blocks["line_operations"])),
            line_values=torch.from_numpy(concatenate(blocks["line_values"])),
            global_operation=torch.from_numpy(concatenate(blocks["global_operation"])),
            global_values=torch.from_numpy(concatenate(blocks["global_values"])),
        ),
        masks=PlanConditionalMasks(
            mode=torch.from_numpy(concatenate(blocks["mode_mask"])),
            line_operations=torch.from_numpy(concatenate(blocks["line_operation_mask"])),
            line_values=torch.from_numpy(concatenate(blocks["line_value_mask"])),
            global_operation=torch.from_numpy(concatenate(blocks["global_operation_mask"])),
            global_values=torch.from_numpy(concatenate(blocks["global_value_mask"])),
            factors=torch.from_numpy(concatenate(blocks["factor_mask"])),
        ),
        old_joint_log_probability=torch.from_numpy(concatenate(blocks["old_log_probability"])),
        old_values=torch.from_numpy(concatenate(blocks["old_value"])),
        episode_index=torch.from_numpy(episode_index),
        start_steps=torch.from_numpy(start_steps),
        durations=torch.from_numpy(durations),
        outcomes=torch.from_numpy(outcomes),
        contract=contract,
        episode_ids=tuple(episode_ids),
    )


__all__ = [
    "FrozenPlanActions",
    "FrozenPlanPolicyOutput",
    "PlanBlocks",
    "build_batch",
    "freeze_plan_actions",
    "freeze_policy_output",
    "new_blocks",
    "record_policy",
]
