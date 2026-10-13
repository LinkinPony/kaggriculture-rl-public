import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.bc.tasks.dataset import (
    collate_array_groups,
    collate_arrays,
)
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    FactorizedTaskMasks,
)


def _arrays(offset: int) -> dict[str, NDArray[np.generic]]:
    records = 2
    return {
        "context": np.arange(offset, offset + 6, dtype=np.float16).reshape(3, 2),
        "turn_index": np.asarray([0, 2], dtype=np.int16),
        "root_features": np.arange(offset, offset + 8, dtype=np.float16).reshape(
            records, 4
        ),
        "prefix_fields": np.arange(
            offset, offset + records * 2 * 9, dtype=np.int16
        ).reshape(records, 2, 9),
        "prefix_mask": np.asarray([[True, False], [True, True]]),
        "candidate_features": np.arange(
            offset, offset + records * 3 * 2, dtype=np.float16
        ).reshape(records, 3, 2),
        "candidate_mask": np.asarray(
            [[True, True, False], [True, False, True]]
        ),
        "candidate_arrivals": np.asarray([[0, 1, 2], [2, 1, 0]], dtype=np.int16),
        "mode_mask": np.ones((records, 2), dtype=np.bool_),
        "available_at": np.asarray([1, 2], dtype=np.int16),
        "day_end": np.asarray([3, 3], dtype=np.int16),
        "action": np.zeros((records, 5), dtype=np.int16),
        "quantity_mask": np.ones((records, 4), dtype=np.bool_),
        "earliest_mask": np.ones((records, 3), dtype=np.bool_),
        "deadline_mask": np.ones((records, 3), dtype=np.bool_),
        "factor_mask": np.ones((records, 5), dtype=np.bool_),
    }


def test_grouped_task_bc_collation_preserves_shard_slice_order() -> None:
    first = _arrays(0)
    second = _arrays(100)
    first_indices = np.asarray([1, 0], dtype=np.int64)
    second_indices = np.asarray([0], dtype=np.int64)
    individual = (
        collate_arrays(first, first_indices, torch.device("cpu")),
        collate_arrays(second, second_indices, torch.device("cpu")),
    )
    grouped = collate_array_groups(
        ((first, first_indices), (second, second_indices)),
        torch.device("cpu"),
    )

    for name in grouped.inputs.__dataclass_fields__:
        actual = getattr(grouped.inputs, name)
        if name == "prefix_length":
            assert actual == max(batch.inputs.prefix_length or 0 for batch in individual)
        else:
            torch.testing.assert_close(
                actual,
                torch.cat([getattr(batch.inputs, name) for batch in individual]),
            )
    for owner in ("actions", "masks"):
        actual_owner = getattr(grouped, owner)
        for name in actual_owner.__dataclass_fields__:
            torch.testing.assert_close(
                getattr(actual_owner, name),
                torch.cat(
                    [getattr(getattr(batch, owner), name) for batch in individual]
                ),
            )


def test_factorized_task_bc_collation_indexes_turn_state_once() -> None:
    records = 2
    arrays: dict[str, NDArray[np.generic]] = {
        "context": np.arange(6, dtype=np.float16).reshape(3, 2),
        "economic_state": np.arange(24, dtype=np.int32).reshape(3, 8),
        "stream_index": np.arange(records, dtype=np.int32),
        "turn_index": np.asarray([0, 2], dtype=np.int16),
        "root_features": np.zeros((records, 4), dtype=np.float16),
        "prefix_fields": np.zeros((records, 2, 9), dtype=np.int16),
        "prefix_mask": np.asarray([[True, False], [True, True]]),
        "current_unit": np.zeros(records, dtype=np.int16),
        "current_x": np.zeros(records, dtype=np.int16),
        "current_y": np.zeros(records, dtype=np.int16),
        "target_counts": np.zeros((records, 4), dtype=np.int16),
        "resource_counts": np.zeros((records, 8), dtype=np.int16),
        "mode_mask": np.ones((records, 2), dtype=np.bool_),
        "available_at": np.zeros(records, dtype=np.int16),
        "day_end": np.full(records, 2, dtype=np.int16),
        "action": np.zeros((records, 5), dtype=np.int16),
        "operation_mask": np.ones((records, 16), dtype=np.bool_),
        "argument_mask": np.ones((records, 13), dtype=np.bool_),
        "target_mask": np.ones((records, 5), dtype=np.bool_),
        "quantity_mask": np.ones((records, 4), dtype=np.bool_),
        "earliest_mask": np.ones((records, 3), dtype=np.bool_),
        "deadline_mask": np.ones((records, 3), dtype=np.bool_),
        "factor_mask": np.ones((records, 7), dtype=np.bool_),
    }

    batch = collate_arrays(
        arrays, np.asarray([1, 0], dtype=np.int64), torch.device("cpu")
    )

    assert isinstance(batch.inputs, FactorizedTaskDecisionInputs)
    assert isinstance(batch.masks, FactorizedTaskMasks)
    torch.testing.assert_close(
        batch.inputs.context,
        torch.as_tensor(arrays["context"][[2, 0]], dtype=torch.float32),
    )
    torch.testing.assert_close(
        batch.inputs.economic_state,
        torch.as_tensor(arrays["economic_state"][[2, 0]], dtype=torch.int32),
    )
    assert batch.inputs.prefix_length == 2
