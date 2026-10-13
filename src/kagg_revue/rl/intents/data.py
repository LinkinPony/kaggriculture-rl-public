"""Compact rollout records for intent-ledger PPO."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, TypeAlias

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.intents.data import IntentTensorState


@dataclass(frozen=True)
class IntentDecisionBlock:
    """Native observations and behavior values from one active lane set."""

    candidate_fields: NDArray[np.int64]
    candidate_features: NDArray[np.float32]
    candidate_mask: NDArray[np.bool_]
    ledger: NDArray[np.int64]
    status: NDArray[np.int64]
    work_priorities: NDArray[np.int64]
    work_orders: NDArray[np.int64]
    work_mask: NDArray[np.bool_]
    positions: NDArray[np.int64]
    market_prefix: NDArray[np.int64]
    market_mask: NDArray[np.bool_]
    phase: NDArray[np.int64]
    candidate_counts: NDArray[np.int64]
    work_counts: NDArray[np.int64]
    market_counts: NDArray[np.int64]
    selected: NDArray[np.int64]
    selected_canonical_id: NDArray[np.uint64]
    old_log_probability: NDArray[np.float32]
    old_value: NDArray[np.float32]
    policy_mask: NDArray[np.bool_]
    episode_index: NDArray[np.int64]
    turn_index: NDArray[np.int64]

    @classmethod
    def from_native(
        cls,
        payload: Mapping[str, Any],
        *,
        candidate_mask: NDArray[np.bool_],
        selected: NDArray[np.int64],
        old_log_probability: NDArray[np.float32],
        old_value: NDArray[np.float32],
        episode_index: NDArray[np.int64],
        turn_index: int,
    ) -> IntentDecisionBlock:
        """Freeze one batched native boundary after runtime mask changes."""
        rows = len(selected)
        counts = np.asarray(payload["market_counts"], dtype=np.int64)
        market = np.asarray(payload["market_prefix"], dtype=np.int64)
        market_mask = np.arange(market.shape[1])[None] < counts[:, None]
        canonical = np.asarray(payload["canonical_id"], dtype=np.uint64)
        chosen_ids = canonical[np.arange(rows), selected]
        return cls(
            candidate_fields=np.asarray(payload["candidate_fields"], dtype=np.int64),
            candidate_features=np.asarray(payload["candidate_features"], dtype=np.float32),
            candidate_mask=np.asarray(candidate_mask, dtype=np.bool_),
            ledger=np.asarray(payload["ledger"], dtype=np.int64),
            status=np.asarray(payload["status"], dtype=np.int64),
            work_priorities=np.asarray(payload["work_priorities"], dtype=np.int64),
            work_orders=np.asarray(payload["work_orders"], dtype=np.int64),
            work_mask=np.asarray(payload["work_mask"], dtype=np.bool_),
            positions=np.asarray(payload["positions"], dtype=np.int64),
            market_prefix=market,
            market_mask=np.asarray(market_mask, dtype=np.bool_),
            phase=np.asarray(payload["phase"], dtype=np.int64),
            candidate_counts=np.asarray(payload["candidate_counts"], dtype=np.int64),
            work_counts=np.asarray(payload["work_counts"], dtype=np.int64),
            market_counts=counts,
            selected=np.asarray(selected, dtype=np.int64),
            selected_canonical_id=chosen_ids,
            old_log_probability=np.asarray(old_log_probability, dtype=np.float32),
            old_value=np.asarray(old_value, dtype=np.float32),
            policy_mask=np.asarray(candidate_mask.sum(axis=1) > 1, dtype=np.bool_),
            episode_index=np.asarray(episode_index, dtype=np.int64),
            turn_index=np.full(rows, turn_index, dtype=np.int64),
        )


def tensor_state_from_native(
    payload: Mapping[str, Any],
    candidate_mask: NDArray[np.bool_],
    device: torch.device,
) -> IntentTensorState:
    """Upload one active native observation batch for inference."""
    market = np.asarray(payload["market_prefix"], dtype=np.int64)
    counts = np.asarray(payload["market_counts"], dtype=np.int64)
    market_mask = np.arange(market.shape[1])[None] < counts[:, None]
    return IntentTensorState(
        candidate_fields=torch.as_tensor(payload["candidate_fields"], device=device),
        candidate_features=torch.as_tensor(payload["candidate_features"], device=device),
        candidate_mask=torch.as_tensor(candidate_mask, device=device),
        ledger=torch.as_tensor(payload["ledger"], device=device),
        status=torch.as_tensor(payload["status"], device=device),
        work_priorities=torch.as_tensor(payload["work_priorities"], device=device),
        work_orders=torch.as_tensor(payload["work_orders"], device=device),
        work_mask=torch.as_tensor(payload["work_mask"], device=device, dtype=torch.bool),
        positions=torch.as_tensor(payload["positions"], device=device),
        market_prefix=torch.as_tensor(market, device=device),
        market_mask=torch.as_tensor(market_mask, device=device),
        phase=torch.as_tensor(payload["phase"], device=device),
    )


def _padded_concat(
    blocks: Sequence[IntentDecisionBlock],
    field: str,
    *,
    width_axis: int = 1,
) -> NDArray[Any]:
    values = [np.asarray(getattr(block, field)) for block in blocks]
    width = max(value.shape[width_axis] for value in values)
    padded: list[NDArray[Any]] = []
    for value in values:
        shape = list(value.shape)
        shape[width_axis] = width
        result = np.zeros(shape, dtype=value.dtype)
        slices = [slice(None)] * value.ndim
        slices[width_axis] = slice(0, value.shape[width_axis])
        result[tuple(slices)] = value
        padded.append(result)
    return np.concatenate(padded, axis=0)


def _padded_tensor_concat(values: Sequence[Tensor], width: int) -> Tensor:
    """Concatenate CPU shard rows while padding only the selected minibatch."""
    padded: list[Tensor] = []
    for value in values:
        if value.shape[1] == width:
            padded.append(value)
            continue
        shape = list(value.shape)
        shape[1] = width
        result = torch.zeros(shape, dtype=value.dtype)
        result[:, : value.shape[1]] = value
        padded.append(result)
    return torch.cat(padded)


def _payload_tensor(payload: Mapping[str, Any], name: str) -> Tensor:
    """Wrap one native ndarray without copying its owned storage."""
    return torch.from_numpy(np.asarray(payload[name]))


EpisodeRows: TypeAlias = Tensor | slice


def _episode_row_groups(indices: Tensor, episode_count: int) -> tuple[EpisodeRows, ...]:
    """Build one reusable row lookup without scanning the tape per minibatch."""
    if indices.device.type != "cpu" or indices.ndim != 1:
        raise ValueError("intent row lookup requires one CPU index vector")
    counts = torch.bincount(indices, minlength=episode_count)
    if indices.numel() < 2 or bool((indices[1:] >= indices[:-1]).all()):
        offsets = torch.cat((counts.new_zeros(1), counts.cumsum(0))).tolist()
        return tuple(
            slice(int(offsets[index]), int(offsets[index + 1])) for index in range(episode_count)
        )
    order = torch.argsort(indices)
    return tuple(torch.split(order, counts.tolist()))


def _row_count(rows: EpisodeRows) -> int:
    """Return the number of rows represented by one episode selector."""
    if isinstance(rows, slice):
        if rows.start is None or rows.stop is None:
            raise ValueError("intent episode slice must be bounded")
        return int(rows.stop) - int(rows.start)
    return int(rows.numel())


def _row_indices(rows: EpisodeRows) -> Tensor:
    """Materialize indices only for compact decision metadata."""
    if isinstance(rows, slice):
        if rows.start is None or rows.stop is None:
            raise ValueError("intent episode slice must be bounded")
        return torch.arange(int(rows.start), int(rows.stop))
    return rows


@dataclass(frozen=True)
class IntentDecisionShard:
    """One native width bucket retained without rollout-wide padding."""

    state: IntentTensorState
    candidate_counts: Tensor
    work_counts: Tensor
    market_counts: Tensor
    episode_index: Tensor

    @property
    def row_count(self) -> int:
        """Return the pseudo-step count in this native bucket."""
        return int(self.episode_index.shape[0])

    def validate(self) -> None:
        """Validate one independently padded native bucket."""
        self.state.validate()
        rows = self.row_count
        for value in (
            self.candidate_counts,
            self.work_counts,
            self.market_counts,
            self.episode_index,
        ):
            if value.shape != (rows,):
                raise ValueError("intent decision shard vectors do not align")
        limits = (
            (self.state.candidate_fields.shape[1], self.candidate_counts, 1),
            (self.state.work_orders.shape[1], self.work_counts, 0),
            (self.state.market_prefix.shape[1], self.market_counts, 0),
        )
        for width, counts, minimum in limits:
            if bool(((counts < minimum) | (counts > width)).any()):
                raise ValueError("intent decision shard count exceeds its width")

    def offset_episodes(self, offset: int) -> IntentDecisionShard:
        """Shift local episode identities when joining device collectors."""
        return IntentDecisionShard(
            state=self.state,
            candidate_counts=self.candidate_counts,
            work_counts=self.work_counts,
            market_counts=self.market_counts,
            episode_index=self.episode_index + offset,
        )


@dataclass(frozen=True)
class IntentRolloutBatch:
    """Complete self-play episodes and independent pseudo-step behavior."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    economic_state: Tensor
    actions: Tensor
    quantities: Tensor
    turn_mask: Tensor
    decision_mask: Tensor
    state: IntentTensorState | None
    candidate_counts: Tensor
    work_counts: Tensor
    market_counts: Tensor
    selected: Tensor
    selected_canonical_id: Tensor
    old_log_probability: Tensor
    old_value: Tensor
    policy_mask: Tensor
    episode_index: Tensor
    turn_index: Tensor
    outcomes: Tensor
    decision_shards: tuple[IntentDecisionShard, ...] = ()
    episode_rows: tuple[EpisodeRows, ...] = ()
    shard_episode_rows: tuple[tuple[EpisodeRows, ...], ...] = ()

    def _with_row_index(self) -> IntentRolloutBatch:
        """Attach linear-size episode lookups once at the coarse boundary."""
        if self.decision_shards:
            return replace(
                self,
                shard_episode_rows=tuple(
                    _episode_row_groups(shard.episode_index, self.episode_count)
                    for shard in self.decision_shards
                ),
            )
        return replace(
            self,
            episode_rows=_episode_row_groups(self.episode_index, self.episode_count),
        )

    @classmethod
    def from_collated(
        cls,
        *,
        board: NDArray[np.float16],
        units: NDArray[np.float16],
        global_features: NDArray[np.float32],
        economic_state: NDArray[np.int32],
        actions: NDArray[np.int64],
        quantities: NDArray[np.int64],
        decision_counts: NDArray[np.int64],
        decisions: Mapping[str, Any],
        outcomes: NDArray[np.float32],
    ) -> IntentRolloutBatch:
        """Build a rollout from one native-preallocated decision surface."""
        turns = board.shape[1]
        turn_mask = np.ones(board.shape[:2], dtype=np.bool_)
        action_positions = np.arange(actions.shape[2])[None, None]
        decision_mask = action_positions < decision_counts[:, :, None]

        def tensor(name: str) -> Tensor:
            return torch.from_numpy(np.asarray(decisions[name]))

        market_prefix = tensor("market_prefix")
        market_counts = tensor("market_counts")
        market_mask = torch.arange(market_prefix.shape[1])[None] < market_counts[:, None]
        state = IntentTensorState(
            candidate_fields=tensor("candidate_fields"),
            candidate_features=tensor("candidate_features"),
            candidate_mask=tensor("candidate_mask").bool(),
            ledger=tensor("ledger"),
            status=tensor("status"),
            work_priorities=tensor("work_priorities"),
            work_orders=tensor("work_orders"),
            work_mask=tensor("work_mask").bool(),
            positions=tensor("positions"),
            market_prefix=market_prefix,
            market_mask=market_mask,
            phase=tensor("phase"),
        )
        result = cls(
            board=torch.from_numpy(board),
            units=torch.from_numpy(units),
            global_features=torch.from_numpy(global_features),
            economic_state=torch.from_numpy(economic_state),
            actions=torch.from_numpy(actions),
            quantities=torch.from_numpy(quantities),
            turn_mask=torch.from_numpy(turn_mask),
            decision_mask=torch.from_numpy(decision_mask),
            state=state,
            candidate_counts=tensor("candidate_counts"),
            work_counts=tensor("work_counts"),
            market_counts=market_counts,
            selected=tensor("selected"),
            selected_canonical_id=tensor("selected_canonical_id"),
            old_log_probability=tensor("old_log_probability"),
            old_value=tensor("old_value"),
            policy_mask=tensor("policy_mask").bool(),
            episode_index=tensor("episode_index"),
            turn_index=tensor("turn_index"),
            outcomes=torch.from_numpy(outcomes),
        )
        if turns < 1:
            raise ValueError("intent rollout needs at least one official turn")
        result.validate()
        return result._with_row_index()

    @classmethod
    def from_native_buckets(
        cls,
        *,
        board: NDArray[np.float16],
        units: NDArray[np.float16],
        global_features: NDArray[np.float32],
        economic_state: NDArray[np.int32],
        actions: NDArray[np.int64],
        quantities: NDArray[np.int64],
        decision_counts: NDArray[np.int64],
        decisions: Sequence[Mapping[str, Any]],
        outcomes: NDArray[np.float32],
        device_behavior: NDArray[np.float32] | None = None,
    ) -> IntentRolloutBatch:
        """Retain native width buckets and attach one bulk behavior export."""
        if not decisions:
            raise ValueError("intent rollout contains no native decision bucket")
        turns = board.shape[1]
        turn_mask = np.ones(board.shape[:2], dtype=np.bool_)
        action_positions = np.arange(actions.shape[2])[None, None]
        decision_mask = action_positions < decision_counts[:, :, None]
        behavior = None if device_behavior is None else np.asarray(device_behavior)
        if behavior is not None and (behavior.ndim != 2 or behavior.shape[1] != 2):
            raise ValueError("intent device behavior tape must have shape [N, 2]")

        shards: list[IntentDecisionShard] = []
        vectors: dict[str, list[Tensor]] = {
            name: []
            for name in (
                "candidate_counts",
                "work_counts",
                "market_counts",
                "selected",
                "selected_canonical_id",
                "old_log_probability",
                "old_value",
                "policy_mask",
                "episode_index",
                "turn_index",
            )
        }
        for payload in decisions:
            market_prefix = _payload_tensor(payload, "market_prefix")
            market_counts = _payload_tensor(payload, "market_counts")
            market_mask = torch.arange(market_prefix.shape[1])[None] < market_counts[:, None]
            state = IntentTensorState(
                candidate_fields=_payload_tensor(payload, "candidate_fields"),
                candidate_features=_payload_tensor(payload, "candidate_features"),
                candidate_mask=_payload_tensor(payload, "candidate_mask").bool(),
                ledger=_payload_tensor(payload, "ledger"),
                status=_payload_tensor(payload, "status"),
                work_priorities=_payload_tensor(payload, "work_priorities"),
                work_orders=_payload_tensor(payload, "work_orders"),
                work_mask=_payload_tensor(payload, "work_mask").bool(),
                positions=_payload_tensor(payload, "positions"),
                market_prefix=market_prefix,
                market_mask=market_mask,
                phase=_payload_tensor(payload, "phase"),
            )
            candidate_counts = _payload_tensor(payload, "candidate_counts")
            work_counts = _payload_tensor(payload, "work_counts")
            episode_index = _payload_tensor(payload, "episode_index")
            shard = IntentDecisionShard(
                state=state,
                candidate_counts=candidate_counts,
                work_counts=work_counts,
                market_counts=market_counts,
                episode_index=episode_index,
            )
            shard.validate()
            shards.append(shard)
            for name in vectors:
                if name in {"old_log_probability", "old_value"} and behavior is not None:
                    continue
                vectors[name].append(_payload_tensor(payload, name))
            if behavior is not None:
                indices = np.asarray(payload["behavior_index"], dtype=np.int64)
                if (
                    indices.shape != (shard.row_count,)
                    or np.any(indices < 0)
                    or np.any(indices >= behavior.shape[0])
                ):
                    raise ValueError("intent native behavior index escaped the device tape")
                vectors["old_log_probability"].append(torch.from_numpy(behavior[indices, 0]))
                vectors["old_value"].append(torch.from_numpy(behavior[indices, 1]))

        def concatenate(name: str) -> Tensor:
            return torch.cat(vectors[name])

        result = cls(
            board=torch.from_numpy(board),
            units=torch.from_numpy(units),
            global_features=torch.from_numpy(global_features),
            economic_state=torch.from_numpy(economic_state),
            actions=torch.from_numpy(actions),
            quantities=torch.from_numpy(quantities),
            turn_mask=torch.from_numpy(turn_mask),
            decision_mask=torch.from_numpy(decision_mask),
            state=None,
            candidate_counts=concatenate("candidate_counts"),
            work_counts=concatenate("work_counts"),
            market_counts=concatenate("market_counts"),
            selected=concatenate("selected"),
            selected_canonical_id=concatenate("selected_canonical_id"),
            old_log_probability=concatenate("old_log_probability"),
            old_value=concatenate("old_value"),
            policy_mask=concatenate("policy_mask").bool(),
            episode_index=concatenate("episode_index"),
            turn_index=concatenate("turn_index"),
            outcomes=torch.from_numpy(outcomes),
            decision_shards=tuple(shards),
        )
        if turns < 1:
            raise ValueError("intent rollout needs at least one official turn")
        result.validate()
        return result._with_row_index()

    @classmethod
    def concatenate(cls, batches: Sequence[IntentRolloutBatch]) -> IntentRolloutBatch:
        """Join disjoint device rollout shards without padding decision tensors."""
        if not batches:
            raise ValueError("intent rollout concatenation requires at least one batch")
        if any(batch.state is not None or not batch.decision_shards for batch in batches):
            raise ValueError("intent rollout concatenation requires native bucket batches")
        turns = {int(batch.board.shape[1]) for batch in batches}
        if len(turns) != 1:
            raise ValueError("intent rollout device shards completed different turn counts")

        episode_offset = 0
        shards: list[IntentDecisionShard] = []
        episode_indices: list[Tensor] = []
        for batch in batches:
            shards.extend(shard.offset_episodes(episode_offset) for shard in batch.decision_shards)
            episode_indices.append(batch.episode_index + episode_offset)
            episode_offset += batch.episode_count

        def join(name: str) -> Tensor:
            return torch.cat([getattr(batch, name) for batch in batches])

        result = cls(
            board=join("board"),
            units=join("units"),
            global_features=join("global_features"),
            economic_state=join("economic_state"),
            actions=join("actions"),
            quantities=join("quantities"),
            turn_mask=join("turn_mask"),
            decision_mask=join("decision_mask"),
            state=None,
            candidate_counts=join("candidate_counts"),
            work_counts=join("work_counts"),
            market_counts=join("market_counts"),
            selected=join("selected"),
            selected_canonical_id=join("selected_canonical_id"),
            old_log_probability=join("old_log_probability"),
            old_value=join("old_value"),
            policy_mask=join("policy_mask"),
            episode_index=torch.cat(episode_indices),
            turn_index=join("turn_index"),
            outcomes=join("outcomes"),
            decision_shards=tuple(shards),
        )
        result.validate()
        return result._with_row_index()

    @classmethod
    def from_blocks(
        cls,
        *,
        board: NDArray[np.float16],
        units: NDArray[np.float16],
        global_features: NDArray[np.float32],
        economic_state: NDArray[np.int32],
        actions: NDArray[np.int64],
        quantities: NDArray[np.int64],
        decision_counts: NDArray[np.int64],
        blocks: Sequence[IntentDecisionBlock],
        outcomes: NDArray[np.float32],
    ) -> IntentRolloutBatch:
        """Pad only dynamic entity axes and retain complete episode sequences."""
        if not blocks:
            raise ValueError("intent rollout contains no pseudo-step")
        turns = board.shape[1]
        turn_mask = np.ones(board.shape[:2], dtype=np.bool_)
        action_positions = np.arange(actions.shape[2])[None, None]
        decision_mask = action_positions < decision_counts[:, :, None]

        def concat(name: str) -> NDArray[Any]:
            return np.concatenate([np.asarray(getattr(block, name)) for block in blocks], axis=0)

        state = IntentTensorState(
            candidate_fields=torch.from_numpy(_padded_concat(blocks, "candidate_fields")),
            candidate_features=torch.from_numpy(_padded_concat(blocks, "candidate_features")),
            candidate_mask=torch.from_numpy(_padded_concat(blocks, "candidate_mask")),
            ledger=torch.from_numpy(concat("ledger")),
            status=torch.from_numpy(concat("status")),
            work_priorities=torch.from_numpy(concat("work_priorities")),
            work_orders=torch.from_numpy(_padded_concat(blocks, "work_orders")),
            work_mask=torch.from_numpy(_padded_concat(blocks, "work_mask")),
            positions=torch.from_numpy(concat("positions")),
            market_prefix=torch.from_numpy(_padded_concat(blocks, "market_prefix")),
            market_mask=torch.from_numpy(_padded_concat(blocks, "market_mask")),
            phase=torch.from_numpy(concat("phase")),
        )
        result = cls(
            board=torch.from_numpy(board),
            units=torch.from_numpy(units),
            global_features=torch.from_numpy(global_features),
            economic_state=torch.from_numpy(economic_state),
            actions=torch.from_numpy(actions),
            quantities=torch.from_numpy(quantities),
            turn_mask=torch.from_numpy(turn_mask),
            decision_mask=torch.from_numpy(decision_mask),
            state=state,
            candidate_counts=torch.from_numpy(concat("candidate_counts")),
            work_counts=torch.from_numpy(concat("work_counts")),
            market_counts=torch.from_numpy(concat("market_counts")),
            selected=torch.from_numpy(concat("selected")),
            selected_canonical_id=torch.from_numpy(concat("selected_canonical_id")),
            old_log_probability=torch.from_numpy(concat("old_log_probability")),
            old_value=torch.from_numpy(concat("old_value")),
            policy_mask=torch.from_numpy(concat("policy_mask")),
            episode_index=torch.from_numpy(concat("episode_index")),
            turn_index=torch.from_numpy(concat("turn_index")),
            outcomes=torch.from_numpy(outcomes),
        )
        if turns < 1:
            raise ValueError("intent rollout needs at least one official turn")
        result.validate()
        return result._with_row_index()

    @property
    def episode_count(self) -> int:
        """Return the number of actor perspectives."""
        return int(self.outcomes.shape[0])

    @property
    def decision_count(self) -> int:
        """Return the number of real pseudo-steps."""
        return int(self.selected.shape[0])

    def record_stream(self, stream: torch.cuda.Stream) -> None:
        """Keep a prefetched learner batch alive on its consumer stream."""
        if self.state is None:
            raise ValueError("intent stream recording requires a materialized batch")
        tensors = (
            self.board,
            self.units,
            self.global_features,
            self.economic_state,
            self.actions,
            self.quantities,
            self.turn_mask,
            self.decision_mask,
            self.selected,
            self.selected_canonical_id,
            self.old_log_probability,
            self.old_value,
            self.policy_mask,
            self.episode_index,
            self.turn_index,
            self.outcomes,
            *(getattr(self.state, name) for name in IntentTensorState.__dataclass_fields__),
        )
        for tensor in tensors:
            if tensor.device.type == "cuda":
                tensor.record_stream(stream)

    def validate(self) -> None:
        """Check episode and decision alignment before optimization."""
        decisions = self.decision_count
        for value in (
            self.candidate_counts,
            self.work_counts,
            self.market_counts,
            self.selected,
            self.selected_canonical_id,
            self.old_log_probability,
            self.old_value,
            self.policy_mask,
            self.episode_index,
            self.turn_index,
        ):
            if value.shape != (decisions,):
                raise ValueError("intent rollout decision vectors do not align")
        if self.board.shape[:2] != self.turn_mask.shape:
            raise ValueError("intent rollout turn mask does not align")
        if self.actions.shape != self.quantities.shape or self.actions.shape[:2] != (
            self.episode_count,
            self.board.shape[1],
        ):
            raise ValueError("intent rollout action history does not align")
        if self.decision_mask.shape != self.actions.shape:
            raise ValueError("intent rollout primitive decision mask does not align")
        if bool(((self.episode_index < 0) | (self.episode_index >= self.episode_count)).any()):
            raise ValueError("intent rollout decision has an invalid episode")
        if bool(((self.turn_index < 0) | (self.turn_index >= self.board.shape[1])).any()):
            raise ValueError("intent rollout decision has an invalid turn")
        if self.decision_shards:
            if self.state is not None:
                raise ValueError("intent native buckets cannot also hold a dense state")
            for shard in self.decision_shards:
                shard.validate()
            if sum(shard.row_count for shard in self.decision_shards) != decisions:
                raise ValueError("intent native bucket rows do not align")
        else:
            if self.state is None:
                raise ValueError("intent rollout lacks both dense and bucketed state")
            self.state.validate()
            widths_and_counts = (
                (self.state.candidate_fields.shape[1], self.candidate_counts, False),
                (self.state.work_orders.shape[1], self.work_counts, True),
                (self.state.market_prefix.shape[1], self.market_counts, True),
            )
            for width, counts, empty_allowed in widths_and_counts:
                minimum = 0 if empty_allowed else 1
                if bool(((counts < minimum) | (counts > width)).any()):
                    raise ValueError("intent rollout entity count exceeds its padded width")
        selected_counts = self.candidate_counts.to(device=self.selected.device)
        if bool(((self.selected < 0) | (self.selected >= selected_counts)).any()):
            raise ValueError("intent rollout selected candidate is outside its observation")

    def subset(
        self,
        episodes: Sequence[int],
        device: torch.device,
        *,
        critic_only: bool = False,
    ) -> IntentRolloutBatch:
        """Select episodes, optionally omitting candidate data unused by the critic."""
        chosen = torch.as_tensor(episodes, dtype=torch.long)
        if chosen.ndim != 1 or chosen.numel() < 1 or torch.unique(chosen).numel() != chosen.numel():
            raise ValueError("intent minibatch episodes must be nonempty and unique")
        if bool(((chosen < 0) | (chosen >= self.episode_count)).any()):
            raise ValueError("intent minibatch episode is outside the rollout")
        remap = torch.full((self.episode_count,), -1, dtype=torch.long)
        remap[chosen] = torch.arange(chosen.numel())

        def move(value: Tensor, rows: Tensor | None = None) -> Tensor:
            selected = value if rows is None else value[rows]
            return selected.to(device=device, non_blocking=device.type == "cuda")

        source = self.state
        selected_states: dict[str, list[Tensor]] | None = None
        if source is None:
            if len(self.shard_episode_rows) != len(self.decision_shards):
                raise RuntimeError("intent native tape lacks its episode row lookup")
            selected_states = {name: [] for name in IntentTensorState.__dataclass_fields__}
            decision_parts: list[Tensor] = []
            shard_offset = 0
            chosen_episodes = [int(episode) for episode in chosen]
            for shard, groups in zip(self.decision_shards, self.shard_episode_rows, strict=True):
                for episode in chosen_episodes:
                    shard_rows = groups[episode]
                    if _row_count(shard_rows) == 0:
                        continue
                    decision_parts.append(_row_indices(shard_rows) + shard_offset)
                    for name in selected_states:
                        selected_states[name].append(getattr(shard.state, name)[shard_rows])
                shard_offset += shard.row_count
            if not selected_states["phase"]:
                raise ValueError("intent minibatch selected no decision rows")
            decision_rows = torch.cat(decision_parts)
        else:
            if len(self.episode_rows) != self.episode_count:
                raise RuntimeError("intent dense tape lacks its episode row lookup")
            decision_rows = torch.cat(
                [_row_indices(self.episode_rows[int(episode)]) for episode in chosen]
            )

        candidate_counts = self.candidate_counts[decision_rows]
        work_counts = self.work_counts[decision_rows]
        market_counts = self.market_counts[decision_rows]
        candidate_width = 1 if critic_only else int(candidate_counts.max())
        work_width = int(work_counts.max())
        market_width = int(market_counts.max())
        if source is None:
            if selected_states is None:
                raise RuntimeError("intent native tape selection was not materialized")

            def dynamic(name: str, width: int) -> Tensor:
                values = [value[:, :width] for value in selected_states[name]]
                return _padded_tensor_concat(values, width)

            source = IntentTensorState(
                candidate_fields=dynamic("candidate_fields", candidate_width),
                candidate_features=dynamic("candidate_features", candidate_width),
                candidate_mask=dynamic("candidate_mask", candidate_width),
                ledger=torch.cat(selected_states["ledger"]),
                status=torch.cat(selected_states["status"]),
                work_priorities=torch.cat(selected_states["work_priorities"]),
                work_orders=dynamic("work_orders", work_width),
                work_mask=dynamic("work_mask", work_width),
                positions=torch.cat(selected_states["positions"]),
                market_prefix=dynamic("market_prefix", market_width),
                market_mask=dynamic("market_mask", market_width),
                phase=torch.cat(selected_states["phase"]),
            )
            state_rows: Tensor | None = None
        else:
            state_rows = decision_rows
        candidate_mask = move(source.candidate_mask[:, :candidate_width], state_rows)
        if critic_only:
            candidate_mask.fill_(True)
            candidate_counts = torch.ones_like(candidate_counts)
        state = IntentTensorState(
            candidate_fields=move(source.candidate_fields[:, :candidate_width], state_rows),
            candidate_features=move(source.candidate_features[:, :candidate_width], state_rows),
            candidate_mask=candidate_mask,
            ledger=move(source.ledger, state_rows),
            status=move(source.status, state_rows),
            work_priorities=move(source.work_priorities, state_rows),
            work_orders=move(source.work_orders[:, :work_width], state_rows),
            work_mask=move(source.work_mask[:, :work_width], state_rows),
            positions=move(source.positions, state_rows),
            market_prefix=move(source.market_prefix[:, :market_width], state_rows),
            market_mask=move(source.market_mask[:, :market_width], state_rows),
            phase=move(source.phase, state_rows),
        )
        return IntentRolloutBatch(
            board=move(self.board[chosen]),
            units=move(self.units[chosen]),
            global_features=move(self.global_features[chosen]),
            economic_state=move(self.economic_state[chosen]),
            actions=move(self.actions[chosen]),
            quantities=move(self.quantities[chosen]),
            turn_mask=move(self.turn_mask[chosen]),
            decision_mask=move(self.decision_mask[chosen]),
            state=state,
            # These are CPU shape metadata used to plan coarse learner buckets.
            candidate_counts=candidate_counts,
            work_counts=work_counts,
            market_counts=market_counts,
            selected=(
                torch.zeros(decision_rows.numel(), dtype=torch.long, device=device)
                if critic_only
                else move(self.selected, decision_rows)
            ),
            selected_canonical_id=move(self.selected_canonical_id, decision_rows),
            old_log_probability=move(self.old_log_probability, decision_rows),
            old_value=move(self.old_value, decision_rows),
            policy_mask=(
                torch.zeros(decision_rows.numel(), dtype=torch.bool, device=device)
                if critic_only
                else move(self.policy_mask, decision_rows)
            ),
            episode_index=move(remap[self.episode_index[decision_rows]]),
            turn_index=move(self.turn_index, decision_rows),
            outcomes=move(self.outcomes[chosen]),
        )


__all__ = [
    "IntentDecisionBlock",
    "IntentDecisionShard",
    "IntentRolloutBatch",
    "tensor_state_from_native",
]
