"""Compact native rollout storage for atomic-effect PPO."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, TypeAlias

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.effects.data import EffectTensorState


def _payload_tensor(payload: Mapping[str, Any], name: str) -> Tensor:
    """Wrap one native-owned ndarray without a second host copy."""
    return torch.from_numpy(np.asarray(payload[name]))


def _mask(values: Tensor, counts: Tensor) -> Tensor:
    """Derive an exact prefix mask, including legal zero-width axes."""
    return torch.arange(values.shape[1])[None] < counts[:, None]


def _padded_tensor_concat(
    values: Sequence[Tensor],
    width: int,
    *,
    fill_value: float | int | bool = 0,
) -> Tensor:
    """Join selected native shards while padding only one minibatch."""
    padded: list[Tensor] = []
    for value in values:
        value = value[:, :width]
        if value.shape[1] == width:
            padded.append(value)
            continue
        shape = list(value.shape)
        shape[1] = width
        result = value.new_zeros(shape)
        if fill_value != 0:
            result.fill_(fill_value)
        result[:, : value.shape[1]] = value
        padded.append(result)
    return torch.cat(padded)


EpisodeRows: TypeAlias = Tensor | slice


def _episode_row_groups(indices: Tensor, episode_count: int) -> tuple[EpisodeRows, ...]:
    """Build one reusable episode-to-row lookup at tape sealing time."""
    if indices.device.type != "cpu" or indices.ndim != 1:
        raise ValueError("effect row lookup requires one CPU index vector")
    counts = torch.bincount(indices, minlength=episode_count)
    if indices.numel() < 2 or bool((indices[1:] >= indices[:-1]).all()):
        offsets = torch.cat((counts.new_zeros(1), counts.cumsum(0))).tolist()
        return tuple(
            slice(int(offsets[index]), int(offsets[index + 1])) for index in range(episode_count)
        )
    order = torch.argsort(indices)
    return tuple(torch.split(order, counts.tolist()))


def _row_count(rows: EpisodeRows) -> int:
    if isinstance(rows, slice):
        if rows.start is None or rows.stop is None:
            raise ValueError("effect episode slice must be bounded")
        return int(rows.stop) - int(rows.start)
    return int(rows.numel())


def _row_indices(rows: EpisodeRows) -> Tensor:
    if isinstance(rows, slice):
        if rows.start is None or rows.stop is None:
            raise ValueError("effect episode slice must be bounded")
        return torch.arange(int(rows.start), int(rows.stop))
    return rows


@dataclass(frozen=True)
class EffectDecisionShard:
    """One candidate-width native bucket retained without global padding."""

    state: EffectTensorState
    candidate_counts: Tensor
    job_counts: Tensor
    work_counts: Tensor
    market_counts: Tensor
    previous_counts: Tensor
    episode_index: Tensor
    reference_candidate_log_probabilities: Tensor | None = None

    @property
    def row_count(self) -> int:
        """Return the number of policy factors in this bucket."""
        return int(self.episode_index.shape[0])

    def validate(self) -> None:
        """Validate counts against this independently padded state."""
        self.state.validate()
        rows = self.row_count
        counts_and_widths = (
            (self.candidate_counts, self.state.candidate_fields.shape[1], 1),
            (self.job_counts, self.state.jobs.shape[1], 0),
            (self.work_counts, self.state.work_prefix.shape[1], 0),
            (self.market_counts, self.state.market_prefix.shape[1], 0),
            (self.previous_counts, self.state.previous_action.shape[1], 0),
        )
        for counts, width, minimum in counts_and_widths:
            if counts.shape != (rows,):
                raise ValueError("effect shard count vectors do not align")
            if bool(((counts < minimum) | (counts > width)).any()):
                raise ValueError("effect shard count exceeds its padded width")
        reference = self.reference_candidate_log_probabilities
        if reference is not None:
            if reference.shape != self.state.candidate_mask.shape:
                raise ValueError("effect behavior distribution does not align with candidates")
            if bool(torch.isnan(reference).any()) or bool(torch.isposinf(reference).any()):
                raise ValueError("effect behavior distribution contains invalid values")

    def offset_episodes(self, offset: int) -> EffectDecisionShard:
        """Shift local episode identities when joining rollout devices."""
        return replace(self, episode_index=self.episode_index + offset)


def _selected_shard_vector(
    parts: Sequence[tuple[EffectDecisionShard, Tensor, Tensor]],
    name: str,
) -> Tensor:
    """Concatenate one vector from selected rows of same-width shards."""
    return torch.cat(
        [getattr(shard, name)[rows] for shard, rows, _global_rows in parts]
    )


@dataclass(frozen=True)
class EffectRolloutBatch:
    """Complete games and their factorized official-turn actions."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    economic_state: Tensor
    actions: Tensor
    quantities: Tensor
    turn_mask: Tensor
    decision_mask: Tensor
    state: EffectTensorState | None
    candidate_counts: Tensor
    job_counts: Tensor
    work_counts: Tensor
    market_counts: Tensor
    previous_counts: Tensor
    selected: Tensor
    selected_canonical_id: Tensor
    old_log_probability: Tensor
    old_value: Tensor
    policy_mask: Tensor
    value_mask: Tensor
    episode_index: Tensor
    turn_index: Tensor
    factor_index: Tensor
    outcomes: Tensor
    decision_shards: tuple[EffectDecisionShard, ...] = ()
    episode_rows: tuple[EpisodeRows, ...] = ()
    shard_episode_rows: tuple[tuple[EpisodeRows, ...], ...] = ()
    reference_candidate_log_probabilities: Tensor | None = None

    @property
    def episode_count(self) -> int:
        """Return the number of actor perspectives."""
        return int(self.outcomes.shape[0])

    @property
    def factor_count(self) -> int:
        """Return the number of complete effect/order choices."""
        return int(self.selected.shape[0])

    @property
    def official_turn_count(self) -> int:
        """Return the number of value-bearing MDP states."""
        return int(self.value_mask.sum())

    @property
    def candidate_width(self) -> int:
        """Return the widest candidate shard represented by this batch."""
        if self.decision_shards:
            return max(
                int(shard.state.candidate_fields.shape[1])
                for shard in self.decision_shards
            )
        if self.state is None:
            raise ValueError("effect rollout lacks candidate state")
        return int(self.state.candidate_fields.shape[1])

    def _with_row_index(self) -> EffectRolloutBatch:
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
        device_behavior: NDArray[np.float32] | Mapping[str, Any] | None = None,
    ) -> EffectRolloutBatch:
        """Attach native buckets to contiguous official-state sequences."""
        if not decisions:
            raise ValueError("effect rollout contains no native decision bucket")
        turn_mask = np.ones(board.shape[:2], dtype=np.bool_)
        positions = np.arange(actions.shape[2])[None, None]
        decision_mask = positions < decision_counts[:, :, None]
        shards: list[EffectDecisionShard] = []
        vector_names = (
            "candidate_counts",
            "job_counts",
            "work_counts",
            "market_counts",
            "previous_counts",
            "selected",
            "selected_canonical_id",
            "old_log_probability",
            "old_value",
            "policy_mask",
            "value_mask",
            "episode_index",
            "turn_index",
        )
        vectors: dict[str, list[Tensor]] = {name: [] for name in vector_names}
        behavior_payload = device_behavior if isinstance(device_behavior, Mapping) else None
        behavior = (
            None
            if device_behavior is None
            else np.asarray(
                behavior_payload["statistics"]
                if behavior_payload is not None
                else device_behavior
            )
        )
        if behavior is not None and (behavior.ndim != 2 or behavior.shape[1] != 2):
            raise ValueError("effect device behavior tape must have shape [N, 2]")
        behavior_width: NDArray[np.int32] | None = None
        behavior_row: NDArray[np.int64] | None = None
        behavior_distributions: dict[int, NDArray[np.float32]] = {}
        if behavior_payload is not None:
            behavior_width = np.asarray(
                behavior_payload["distribution_width"],
                dtype=np.int32,
            )
            behavior_row = np.asarray(
                behavior_payload["distribution_row"],
                dtype=np.int64,
            )
            raw_distributions = behavior_payload["candidate_log_probabilities"]
            if not isinstance(raw_distributions, Mapping):
                raise ValueError("effect device behavior distributions must be width-mapped")
            behavior_distributions = {
                int(width): np.asarray(values, dtype=np.float32)
                for width, values in raw_distributions.items()
            }
            if behavior is None or behavior_width.shape != behavior.shape[:1] or (
                behavior_row.shape != behavior.shape[:1]
            ):
                raise ValueError("effect behavior distribution index does not align")
        for payload in decisions:
            candidate_counts = _payload_tensor(payload, "candidate_counts")
            job_counts = _payload_tensor(payload, "job_counts")
            work_counts = _payload_tensor(payload, "work_counts")
            market_counts = _payload_tensor(payload, "market_counts")
            previous_counts = _payload_tensor(payload, "previous_counts")
            jobs = _payload_tensor(payload, "jobs")
            work = _payload_tensor(payload, "work_prefix")
            market = _payload_tensor(payload, "market_prefix")
            previous = _payload_tensor(payload, "previous_action")
            state = EffectTensorState(
                candidate_fields=_payload_tensor(payload, "candidate_fields"),
                candidate_features=_payload_tensor(payload, "candidate_features"),
                candidate_mask=_payload_tensor(payload, "candidate_mask").bool(),
                jobs=jobs,
                job_mask=_mask(jobs, job_counts),
                work_prefix=work,
                work_mask=_mask(work, work_counts),
                market_prefix=market,
                market_mask=_mask(market, market_counts),
                previous_action=previous,
                previous_mask=_mask(previous, previous_counts),
                phase=_payload_tensor(payload, "phase"),
                work_limit=_payload_tensor(payload, "work_limit"),
            )
            behavior_indices: NDArray[np.int64] | None = None
            reference_log_probabilities: Tensor | None = None
            if behavior is not None:
                behavior_indices = np.asarray(payload["behavior_index"], dtype=np.int64)
                if (
                    behavior_indices.shape != (state.batch_size,)
                    or np.any(behavior_indices < 0)
                    or np.any(behavior_indices >= behavior.shape[0])
                ):
                    raise ValueError("effect behavior index escaped the device tape")
                if behavior_width is not None and behavior_row is not None:
                    target_width = int(state.candidate_fields.shape[1])
                    reference = np.full(
                        (state.batch_size, target_width),
                        -np.inf,
                        dtype=np.float32,
                    )
                    recorded_widths = behavior_width[behavior_indices]
                    recorded_rows = behavior_row[behavior_indices]
                    for recorded_width in np.unique(recorded_widths):
                        width = int(recorded_width)
                        source = behavior_distributions.get(width)
                        selected_rows = recorded_widths == width
                        source_rows = recorded_rows[selected_rows]
                        if (
                            source is None
                            or source.ndim != 2
                            or source.shape[1] != width
                            or width < target_width
                            or np.any(source_rows < 0)
                            or np.any(source_rows >= source.shape[0])
                        ):
                            raise ValueError("effect behavior distribution escaped its width tape")
                        reference[selected_rows] = source[source_rows, :target_width]
                    reference_log_probabilities = torch.from_numpy(reference)
            shard = EffectDecisionShard(
                state=state,
                candidate_counts=candidate_counts,
                job_counts=job_counts,
                work_counts=work_counts,
                market_counts=market_counts,
                previous_counts=previous_counts,
                episode_index=_payload_tensor(payload, "episode_index"),
                reference_candidate_log_probabilities=reference_log_probabilities,
            )
            shards.append(shard)
            for name in vector_names:
                if name in {"old_log_probability", "old_value"} and behavior is not None:
                    continue
                vectors[name].append(_payload_tensor(payload, name))
            if behavior is not None:
                if behavior_indices is None:
                    raise RuntimeError("effect behavior indices were not initialized")
                vectors["old_log_probability"].append(
                    torch.from_numpy(behavior[behavior_indices, 0])
                )
                vectors["old_value"].append(torch.from_numpy(behavior[behavior_indices, 1]))

        def concatenate(name: str) -> Tensor:
            return torch.cat(vectors[name])

        selected = concatenate("selected")
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
            job_counts=concatenate("job_counts"),
            work_counts=concatenate("work_counts"),
            market_counts=concatenate("market_counts"),
            previous_counts=concatenate("previous_counts"),
            selected=selected,
            selected_canonical_id=concatenate("selected_canonical_id"),
            old_log_probability=concatenate("old_log_probability"),
            old_value=concatenate("old_value"),
            policy_mask=concatenate("policy_mask").bool(),
            value_mask=concatenate("value_mask").bool(),
            episode_index=concatenate("episode_index"),
            turn_index=concatenate("turn_index"),
            factor_index=torch.arange(selected.shape[0]),
            outcomes=torch.from_numpy(outcomes),
            decision_shards=tuple(shards),
        )
        result.validate()
        return result._with_row_index()

    @classmethod
    def concatenate(
        cls,
        batches: Sequence[EffectRolloutBatch],
        *,
        validate: bool = True,
    ) -> EffectRolloutBatch:
        """Join complete-game device shards without padding factor tensors."""
        if not batches:
            raise ValueError("effect rollout concatenation needs at least one batch")
        if any(batch.state is not None or not batch.decision_shards for batch in batches):
            raise ValueError("effect rollout concatenation requires native buckets")
        if len({int(batch.board.shape[1]) for batch in batches}) != 1:
            raise ValueError("effect device shards completed different turn counts")
        offset = 0
        shards: list[EffectDecisionShard] = []
        episodes: list[Tensor] = []
        for batch in batches:
            shards.extend(shard.offset_episodes(offset) for shard in batch.decision_shards)
            episodes.append(batch.episode_index + offset)
            offset += batch.episode_count

        def join(name: str) -> Tensor:
            return torch.cat([getattr(batch, name) for batch in batches])

        factor_count = sum(batch.factor_count for batch in batches)
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
            job_counts=join("job_counts"),
            work_counts=join("work_counts"),
            market_counts=join("market_counts"),
            previous_counts=join("previous_counts"),
            selected=join("selected"),
            selected_canonical_id=join("selected_canonical_id"),
            old_log_probability=join("old_log_probability"),
            old_value=join("old_value"),
            policy_mask=join("policy_mask"),
            value_mask=join("value_mask"),
            episode_index=torch.cat(episodes),
            turn_index=join("turn_index"),
            factor_index=torch.arange(factor_count),
            outcomes=join("outcomes"),
            decision_shards=tuple(shards),
        )
        # Native batches were validated before joining. Offsetting episode IDs
        # and concatenating complete games does not change their candidate ABI.
        if validate:
            result.validate()
        return result._with_row_index()

    def validate(self) -> None:
        """Check factor, episode, and unique official-turn value alignment."""
        factors = self.factor_count
        vectors = (
            self.candidate_counts,
            self.job_counts,
            self.work_counts,
            self.market_counts,
            self.previous_counts,
            self.selected,
            self.selected_canonical_id,
            self.old_log_probability,
            self.old_value,
            self.policy_mask,
            self.value_mask,
            self.episode_index,
            self.turn_index,
            self.factor_index,
        )
        if any(value.shape != (factors,) for value in vectors):
            raise ValueError("effect rollout factor vectors do not align")
        if self.board.shape[:2] != self.turn_mask.shape:
            raise ValueError("effect rollout turn mask does not align")
        if self.actions.shape != self.quantities.shape or self.actions.shape[:2] != (
            self.episode_count,
            self.board.shape[1],
        ):
            raise ValueError("effect rollout action history does not align")
        if self.decision_mask.shape != self.actions.shape:
            raise ValueError("effect primitive-action mask does not align")
        if self.policy_mask.dtype != torch.bool or self.value_mask.dtype != torch.bool:
            raise ValueError("effect policy and value masks must be boolean")
        if bool(((self.episode_index < 0) | (self.episode_index >= self.episode_count)).any()):
            raise ValueError("effect factor has an invalid episode")
        turn_count = self.board.shape[1]
        if bool(((self.turn_index < 0) | (self.turn_index >= turn_count)).any()):
            raise ValueError("effect factor has an invalid official turn")
        if not bool(torch.isfinite(self.old_log_probability).all()) or not bool(
            torch.isfinite(self.old_value).all()
        ):
            raise ValueError("effect behavior statistics must be finite")
        if bool((self.old_value.abs() > 1.0).any()):
            raise ValueError("effect behavior values must lie in [-1, 1]")
        keys = self.episode_index.long() * turn_count + self.turn_index.long()
        represented = torch.bincount(keys, minlength=self.episode_count * turn_count)
        valued = torch.bincount(keys[self.value_mask], minlength=self.episode_count * turn_count)
        if bool((represented != 0).logical_xor(valued == 1).any()):
            raise ValueError("effect rollout needs exactly one value per represented turn")
        if bool((represented == 0).any()):
            raise ValueError("effect rollout omitted an official turn")
        if self.decision_shards:
            for shard in self.decision_shards:
                shard.validate()
            if sum(shard.row_count for shard in self.decision_shards) != factors:
                raise ValueError("effect native bucket rows do not align")
            if self.state is not None:
                self.state.validate()
                if self.state.batch_size != factors:
                    raise ValueError("effect shared factor state rows do not align")
        else:
            if self.state is None:
                raise ValueError("effect rollout lacks factor state")
            self.state.validate()
            widths = (
                (self.candidate_counts, self.state.candidate_fields.shape[1], 1),
                (self.job_counts, self.state.jobs.shape[1], 0),
                (self.work_counts, self.state.work_prefix.shape[1], 0),
                (self.market_counts, self.state.market_prefix.shape[1], 0),
                (self.previous_counts, self.state.previous_action.shape[1], 0),
            )
            for counts, width, minimum in widths:
                if bool(((counts < minimum) | (counts > width)).any()):
                    raise ValueError("effect entity count exceeds its padded width")
            chosen = self.state.candidate_mask.gather(1, self.selected[:, None])
            if not bool(chosen.all()):
                raise ValueError("effect rollout selected a masked candidate")
        reference = self.reference_candidate_log_probabilities
        if reference is not None:
            if reference.shape != (factors, self.candidate_width):
                raise ValueError("effect learner behavior distribution does not align")
            if bool(torch.isnan(reference).any()) or bool(torch.isposinf(reference).any()):
                raise ValueError("effect learner behavior distribution contains invalid values")
        if not bool(torch.isfinite(self.outcomes).all()) or bool(
            ((self.outcomes < -1) | (self.outcomes > 1)).any()
        ):
            raise ValueError("effect outcomes must be terminal W/D/L")

    def record_stream(self, stream: torch.cuda.Stream) -> None:
        """Keep a prefetched minibatch alive on its consumer stream."""
        tensors: tuple[Tensor, ...] = (
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
            self.value_mask,
            self.episode_index,
            self.turn_index,
            self.factor_index,
            self.outcomes,
        )
        if self.reference_candidate_log_probabilities is not None:
            tensors += (self.reference_candidate_log_probabilities,)
        if self.state is not None:
            tensors += tuple(
                getattr(self.state, name) for name in EffectTensorState.__dataclass_fields__
            )
        if self.decision_shards:
            tensors += tuple(
                tensor
                for shard in self.decision_shards
                for tensor in (
                    *(
                        getattr(shard.state, name)
                        for name in EffectTensorState.__dataclass_fields__
                    ),
                    shard.candidate_counts,
                    shard.job_counts,
                    shard.work_counts,
                    shard.market_counts,
                    shard.previous_counts,
                    shard.episode_index,
                    *(
                        ()
                        if shard.reference_candidate_log_probabilities is None
                        else (shard.reference_candidate_log_probabilities,)
                    ),
                )
            )
        if self.state is None and not self.decision_shards:
            raise ValueError("effect stream recording requires factor state")
        for tensor in tensors:
            if tensor.device.type == "cuda":
                tensor.record_stream(stream)

    def subset(
        self,
        episodes: Sequence[int],
        device: torch.device,
        *,
        critic_only: bool = False,
    ) -> EffectRolloutBatch:
        """Gather episode rows while preserving compact candidate-width shards."""
        chosen = torch.as_tensor(episodes, dtype=torch.long)
        if chosen.ndim != 1 or chosen.numel() < 1 or torch.unique(chosen).numel() != chosen.numel():
            raise ValueError("effect minibatch episodes must be nonempty and unique")
        if bool(((chosen < 0) | (chosen >= self.episode_count)).any()):
            raise ValueError("effect minibatch episode is outside the rollout")
        remap = torch.full((self.episode_count,), -1, dtype=torch.long)
        remap[chosen] = torch.arange(chosen.numel())

        def move(value: Tensor, rows: Tensor | None = None) -> Tensor:
            selected = value if rows is None else value[rows]
            return selected.to(device=device, non_blocking=device.type == "cuda")

        source = self.state
        selected_shards: list[EffectDecisionShard] = []
        if source is None:
            if len(self.shard_episode_rows) != len(self.decision_shards):
                raise RuntimeError("effect native tape lacks its episode row lookup")
            grouped: dict[
                int,
                list[tuple[EffectDecisionShard, Tensor, Tensor]],
            ] = {}
            shard_offset = 0
            chosen_episodes = [int(episode) for episode in chosen]
            for shard, groups in zip(
                self.decision_shards,
                self.shard_episode_rows,
                strict=True,
            ):
                local_parts: list[Tensor] = []
                for episode in chosen_episodes:
                    shard_rows = groups[episode]
                    if _row_count(shard_rows) == 0:
                        continue
                    local_parts.append(_row_indices(shard_rows))
                if local_parts:
                    local_rows = torch.cat(local_parts)
                    capacity = int(shard.state.candidate_fields.shape[1])
                    grouped.setdefault(capacity, []).append(
                        (shard, local_rows, local_rows + shard_offset)
                    )
                shard_offset += shard.row_count
            if not grouped:
                raise ValueError("effect minibatch selected no factor rows")

            decision_parts: list[Tensor] = []
            for _capacity, parts in sorted(grouped.items()):
                decision_parts.append(torch.cat([part[2] for part in parts]))
                local_candidate_counts = _selected_shard_vector(
                    parts, "candidate_counts"
                )
                local_job_counts = _selected_shard_vector(parts, "job_counts")
                local_work_counts = _selected_shard_vector(parts, "work_counts")
                local_market_counts = _selected_shard_vector(parts, "market_counts")
                local_previous_counts = _selected_shard_vector(
                    parts, "previous_counts"
                )
                candidate_width = 1 if critic_only else int(local_candidate_counts.max())
                state_widths = {
                    "candidate_fields": candidate_width,
                    "candidate_features": candidate_width,
                    "candidate_mask": candidate_width,
                    "jobs": int(local_job_counts.max()),
                    "job_mask": int(local_job_counts.max()),
                    "work_prefix": int(local_work_counts.max()),
                    "work_mask": int(local_work_counts.max()),
                    "market_prefix": int(local_market_counts.max()),
                    "market_mask": int(local_market_counts.max()),
                    "previous_action": int(local_previous_counts.max()),
                    "previous_mask": int(local_previous_counts.max()),
                }

                shard_values: dict[str, Tensor] = {}
                for name in EffectTensorState.__dataclass_fields__:
                    values = [
                        getattr(shard.state, name)[rows]
                        for shard, rows, _global in parts
                    ]
                    if name in state_widths:
                        packed = _padded_tensor_concat(values, state_widths[name])
                    else:
                        packed = torch.cat(values)
                    shard_values[name] = move(packed)
                if critic_only:
                    shard_values["candidate_mask"].fill_(True)
                shard_state = EffectTensorState(**shard_values)
                local_rows_count = local_candidate_counts.numel()
                references = [
                    shard.reference_candidate_log_probabilities
                    for shard, _rows, _global in parts
                ]
                if any(reference is None for reference in references) and not all(
                    reference is None for reference in references
                ):
                    raise RuntimeError("effect behavior distribution shards are incomplete")
                local_reference = (
                    None
                    if critic_only or references[0] is None
                    else move(
                        _padded_tensor_concat(
                            [
                                reference[rows]
                                for reference, (_shard, rows, _global) in zip(
                                    references,
                                    parts,
                                    strict=True,
                                )
                                if reference is not None
                            ],
                            candidate_width,
                        )
                    )
                )
                selected_shards.append(
                    EffectDecisionShard(
                        state=shard_state,
                        candidate_counts=(
                            torch.ones(
                                local_rows_count,
                                dtype=torch.long,
                                device=device,
                            )
                            if critic_only
                            else move(local_candidate_counts)
                        ),
                        job_counts=move(local_job_counts),
                        work_counts=move(local_work_counts),
                        market_counts=move(local_market_counts),
                        previous_counts=move(local_previous_counts),
                        episode_index=move(
                            torch.cat(
                                [
                                    remap[shard.episode_index[rows]]
                                    for shard, rows, _global in parts
                                ]
                            )
                        ),
                        reference_candidate_log_probabilities=local_reference,
                    )
                )
            decision_rows = torch.cat(decision_parts)
        else:
            if len(self.episode_rows) != self.episode_count:
                raise RuntimeError("effect dense tape lacks its episode row lookup")
            decision_rows = torch.cat(
                [_row_indices(self.episode_rows[int(episode)]) for episode in chosen]
            )

        candidate_counts = self.candidate_counts[decision_rows]
        job_counts = self.job_counts[decision_rows]
        work_counts = self.work_counts[decision_rows]
        market_counts = self.market_counts[decision_rows]
        previous_counts = self.previous_counts[decision_rows]
        widths = {
            "candidate": 1 if critic_only else int(candidate_counts.max()),
            "job": int(job_counts.max()),
            "work": int(work_counts.max()),
            "market": int(market_counts.max()),
            "previous": int(previous_counts.max()),
        }
        state: EffectTensorState | None
        if source is None:
            if critic_only:
                candidate_counts = torch.ones_like(candidate_counts)
            factor_rows = sum(shard.row_count for shard in selected_shards)

            def shared(name: str, width: int) -> Tensor:
                return _padded_tensor_concat(
                    [getattr(shard.state, name) for shard in selected_shards],
                    width,
                )

            exemplar = selected_shards[0].state
            candidate_fields = exemplar.candidate_fields.new_zeros(
                (factor_rows, 1, exemplar.candidate_fields.shape[-1])
            )
            candidate_features = exemplar.candidate_features.new_zeros(
                (factor_rows, 1, exemplar.candidate_features.shape[-1])
            )
            state = EffectTensorState(
                candidate_fields=candidate_fields,
                candidate_features=candidate_features,
                candidate_mask=torch.ones(
                    (factor_rows, 1),
                    dtype=torch.bool,
                    device=device,
                ),
                jobs=shared("jobs", widths["job"]),
                job_mask=shared("job_mask", widths["job"]),
                work_prefix=shared("work_prefix", widths["work"]),
                work_mask=shared("work_mask", widths["work"]),
                market_prefix=shared("market_prefix", widths["market"]),
                market_mask=shared("market_mask", widths["market"]),
                previous_action=shared("previous_action", widths["previous"]),
                previous_mask=shared("previous_mask", widths["previous"]),
                phase=torch.cat([shard.state.phase for shard in selected_shards]),
                work_limit=torch.cat(
                    [shard.state.work_limit for shard in selected_shards]
                ),
            )
        else:
            state_rows = decision_rows
            candidate_mask = move(source.candidate_mask[:, : widths["candidate"]], state_rows)
            if critic_only:
                candidate_mask.fill_(True)
                candidate_counts = torch.ones_like(candidate_counts)
            state = EffectTensorState(
                candidate_fields=move(
                    source.candidate_fields[:, : widths["candidate"]], state_rows
                ),
                candidate_features=move(
                    source.candidate_features[:, : widths["candidate"]], state_rows
                ),
                candidate_mask=candidate_mask,
                jobs=move(source.jobs[:, : widths["job"]], state_rows),
                job_mask=move(source.job_mask[:, : widths["job"]], state_rows),
                work_prefix=move(source.work_prefix[:, : widths["work"]], state_rows),
                work_mask=move(source.work_mask[:, : widths["work"]], state_rows),
                market_prefix=move(source.market_prefix[:, : widths["market"]], state_rows),
                market_mask=move(source.market_mask[:, : widths["market"]], state_rows),
                previous_action=move(
                    source.previous_action[:, : widths["previous"]], state_rows
                ),
                previous_mask=move(source.previous_mask[:, : widths["previous"]], state_rows),
                phase=move(source.phase, state_rows),
                work_limit=move(source.work_limit, state_rows),
            )
        reference_candidate_log_probabilities: Tensor | None = None
        if not critic_only:
            if selected_shards and all(
                shard.reference_candidate_log_probabilities is not None
                for shard in selected_shards
            ):
                reference_candidate_log_probabilities = _padded_tensor_concat(
                    [
                        shard.reference_candidate_log_probabilities
                        for shard in selected_shards
                        if shard.reference_candidate_log_probabilities is not None
                    ],
                    widths["candidate"],
                    fill_value=-torch.inf,
                )
            elif self.reference_candidate_log_probabilities is not None:
                reference_candidate_log_probabilities = move(
                    self.reference_candidate_log_probabilities[:, : widths["candidate"]],
                    decision_rows,
                )
        return EffectRolloutBatch(
            board=move(self.board[chosen]),
            units=move(self.units[chosen]),
            global_features=move(self.global_features[chosen]),
            economic_state=move(self.economic_state[chosen]),
            actions=move(self.actions[chosen]),
            quantities=move(self.quantities[chosen]),
            turn_mask=move(self.turn_mask[chosen]),
            decision_mask=move(self.decision_mask[chosen]),
            state=state,
            candidate_counts=candidate_counts,
            job_counts=job_counts,
            work_counts=work_counts,
            market_counts=market_counts,
            previous_counts=previous_counts,
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
            value_mask=move(self.value_mask, decision_rows),
            episode_index=move(remap[self.episode_index[decision_rows]]),
            turn_index=move(self.turn_index, decision_rows),
            factor_index=move(self.factor_index, decision_rows),
            outcomes=move(self.outcomes[chosen]),
            decision_shards=tuple(selected_shards),
            reference_candidate_log_probabilities=(
                reference_candidate_log_probabilities
            ),
        )


__all__ = ["EffectDecisionShard", "EffectRolloutBatch"]
