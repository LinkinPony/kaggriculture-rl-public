"""Validated Python boundary for the native unit-task tensor ABI."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.tasks.contract import TASK_TAPE_ABI_VERSION
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    TaskCatalog,
    TaskDecisionInputs,
)
from kagg_revue.policy.tasks.schema import TaskTapeArchitecture


def _integer_array(value: object, shape: tuple[int, ...], name: str) -> NDArray[np.int64]:
    array = np.asarray(value)
    if array.shape != shape or array.dtype.kind not in "iu":
        raise ValueError(f"native unit-task {name} differs from its declared shape")
    return np.ascontiguousarray(array, dtype=np.int64)


def _flag_array(value: object, shape: tuple[int, ...], name: str) -> NDArray[np.bool_]:
    array = np.asarray(value)
    if array.shape != shape or array.dtype.kind not in "biu":
        raise ValueError(f"native unit-task {name} differs from its declared shape")
    return np.ascontiguousarray(array, dtype=np.bool_)


@dataclass(frozen=True)
class NativeTaskContract:
    """Authenticated static dimensions and catalog exported by native C++."""

    version: str
    candidate_count: int
    candidate_feature_count: int
    root_feature_count: int
    task_field_count: int
    prefix_capacity: int
    time_token_count: int
    maximum_quantity: int
    unit_limit: int
    board_size: int
    catalog: TaskCatalog
    catalog_fingerprint: str
    candidate_feature_names: tuple[str, ...]
    root_feature_names: tuple[str, ...]
    task_field_names: tuple[str, ...]

    @classmethod
    def from_spec(cls, raw: Mapping[str, object]) -> NativeTaskContract:
        """Validate a native spec before it can define a model artifact."""
        version = str(raw.get("version"))
        if version != TASK_TAPE_ABI_VERSION:
            raise ValueError("native unit-task ABI version is unsupported")

        def positive(name: str) -> int:
            value = raw.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"native unit-task {name} must be positive")
            return value

        candidates = positive("candidate_count")
        catalog_arrays = (
            _integer_array(raw.get("candidate_operations"), (candidates,), "operations"),
            _integer_array(raw.get("candidate_arguments"), (candidates,), "arguments"),
            _integer_array(raw.get("candidate_targets"), (candidates, 2), "targets"),
            _flag_array(
                raw.get("candidate_requires_quantity"),
                (candidates,),
                "quantity flags",
            ),
            _integer_array(
                raw.get("candidate_operation_turns"),
                (candidates,),
                "operation turns",
            ),
        )
        digest = hashlib.sha256()
        for array in catalog_arrays:
            digest.update(np.ascontiguousarray(array).tobytes(order="C"))
        catalog = TaskCatalog(
            operations=torch.from_numpy(catalog_arrays[0]),
            arguments=torch.from_numpy(catalog_arrays[1]),
            targets=torch.from_numpy(catalog_arrays[2]),
            requires_quantity=torch.from_numpy(catalog_arrays[3]),
            operation_turns=torch.from_numpy(catalog_arrays[4]),
        )
        catalog.validate()

        def names(key: str, count: int) -> tuple[str, ...]:
            values = raw.get(key)
            if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
                raise ValueError(f"native unit-task {key} must be a name sequence")
            result = tuple(str(value) for value in values)
            if len(result) != count or len(set(result)) != count:
                raise ValueError(f"native unit-task {key} must be unique and complete")
            return result

        candidate_features = positive("candidate_feature_count")
        root_features = positive("root_feature_count")
        task_fields = positive("task_field_count")
        return cls(
            version=version,
            candidate_count=candidates,
            candidate_feature_count=candidate_features,
            root_feature_count=root_features,
            task_field_count=task_fields,
            prefix_capacity=positive("prefix_capacity"),
            time_token_count=positive("time_token_count"),
            maximum_quantity=positive("maximum_quantity"),
            unit_limit=positive("unit_limit"),
            board_size=positive("board_size"),
            catalog=catalog,
            catalog_fingerprint=digest.hexdigest(),
            candidate_feature_names=names("candidate_features", candidate_features),
            root_feature_names=names("root_features", root_features),
            task_field_names=names("task_fields", task_fields),
        )

    def architecture(
        self,
        *,
        architecture_version: Literal[
            "attention-v1", "pooled-v2", "factorized-v3"
        ] = "attention-v1",
        context_width: int,
        model_width: int,
        feedforward_width: int,
        attention_heads: int,
        prefix_layers: int,
        history_window: int | None = None,
    ) -> TaskTapeArchitecture:
        """Build a checkpoint shape from measured native capacities."""
        resolved_history_window = (
            self.prefix_capacity
            if architecture_version == "factorized-v3" and history_window is None
            else 64
            if history_window is None
            else history_window
        )
        return TaskTapeArchitecture(
            architecture_version=architecture_version,
            context_width=context_width,
            model_width=model_width,
            feedforward_width=feedforward_width,
            attention_heads=attention_heads,
            prefix_layers=prefix_layers,
            candidate_count=self.candidate_count,
            candidate_features=self.candidate_feature_count,
            root_features=self.root_feature_count,
            prefix_capacity=self.prefix_capacity,
            history_window=resolved_history_window,
            task_fields=self.task_field_count,
            operation_tokens=16,
            item_tokens=12,
            status_tokens=9,
            time_tokens=self.time_token_count,
            maximum_quantity=self.maximum_quantity,
            unit_limit=self.unit_limit,
            board_size=self.board_size,
            native_abi_version=self.version,
            catalog_fingerprint=self.catalog_fingerprint,
        )


def decision_inputs(
    raw: Mapping[str, Any],
    context: Tensor,
    contract: NativeTaskContract,
    *,
    device: torch.device | str,
) -> TaskDecisionInputs:
    """Move one native decision batch into the task policy tensor contract."""
    batch = context.shape[0]

    def tensor(key: str, dtype: torch.dtype) -> Tensor:
        value = np.asarray(raw[key])
        return torch.as_tensor(value, dtype=dtype, device=device)

    prefix_mask = np.asarray(raw["prefix_mask"])
    result = TaskDecisionInputs(
        context=context.to(device),
        root_features=tensor("root_features", torch.float32),
        prefix_fields=tensor("prefix_fields", torch.int32),
        prefix_mask=tensor("prefix_mask", torch.bool),
        candidate_features=tensor("candidate_features", torch.float16),
        candidate_mask=tensor("candidate_mask", torch.bool),
        candidate_arrivals=tensor("candidate_arrivals", torch.int16),
        mode_mask=tensor("mode_mask", torch.bool),
        available_at=tensor("available_at", torch.int16),
        day_end=tensor("day_end", torch.int16),
        prefix_length=int(np.count_nonzero(prefix_mask, axis=1).max()),
    )
    if result.batch_size != batch:
        raise ValueError("native unit-task decisions and actor contexts differ")
    return result


def factorized_decision_inputs(
    raw: Mapping[str, Any],
    context: Tensor,
    economic_state: Tensor,
    contract: NativeTaskContract,
    *,
    device: torch.device | str,
    history_window: int | None = None,
) -> FactorizedTaskDecisionInputs:
    """Move one compact native planning decision into the typed contract."""
    batch = context.shape[0]
    layout = EconomicStateLayout.create(contract.board_size, contract.unit_limit)

    def tensor(key: str, dtype: torch.dtype) -> Tensor:
        return torch.as_tensor(np.asarray(raw[key]), dtype=dtype, device=device)

    state = economic_state.to(device=device)
    if state.shape != (batch, layout.width):
        raise ValueError("factorized native task state differs from its economic ABI")
    source_prefix = np.asarray(raw["prefix_fields"])
    source_mask = np.asarray(raw["prefix_mask"], dtype=np.bool_)
    resolved_history_window = (
        contract.prefix_capacity if history_window is None else history_window
    )
    if (
        resolved_history_window < 1
        or resolved_history_window > contract.prefix_capacity
    ):
        raise ValueError("factorized task history window is outside the native ABI")
    prefix = np.zeros(
        (batch, resolved_history_window, contract.task_field_count),
        dtype=np.int32,
    )
    prefix_mask = np.zeros((batch, resolved_history_window), dtype=np.bool_)
    for row in range(batch):
        count = int(np.count_nonzero(source_mask[row]))
        active = min(count, resolved_history_window)
        if active:
            prefix[row, :active] = source_prefix[
                row, count - active : count
            ]
            prefix_mask[row, :active] = True
    result = FactorizedTaskDecisionInputs(
        context=context.to(device),
        root_features=tensor("root_features", torch.float32),
        prefix_fields=torch.as_tensor(prefix, dtype=torch.int32, device=device),
        prefix_mask=torch.as_tensor(prefix_mask, dtype=torch.bool, device=device),
        economic_state=state.to(torch.int32),
        current_unit=tensor("unit_indices", torch.long),
        current_x=tensor("current_x", torch.long),
        current_y=tensor("current_y", torch.long),
        target_counts=tensor("target_conflicts", torch.int32),
        resource_counts=tensor("resource_conflicts", torch.int32),
        mode_mask=tensor("mode_mask", torch.bool),
        available_at=tensor("available_at", torch.int16),
        day_end=tensor("day_end", torch.int16),
        prefix_length=int(np.count_nonzero(prefix_mask, axis=1).max()),
    )
    if result.batch_size != batch:
        raise ValueError("factorized native decisions and actor contexts differ")
    return result


__all__ = [
    "NativeTaskContract",
    "decision_inputs",
    "factorized_decision_inputs",
]
