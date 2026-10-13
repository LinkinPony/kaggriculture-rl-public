"""Complete immutable records for dynamic capability candidate sets."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.rl.capabilities.contract import (
    CapabilityVersionContract,
    FrozenSearchContext,
)

IntArray = NDArray[np.int64]
UIntArray = NDArray[np.uint64]
FloatArray = NDArray[np.float32]
BoolArray = NDArray[np.bool_]


def _freeze(value: NDArray[Any], dtype: np.dtype[Any]) -> NDArray[Any]:
    result = np.array(value, dtype=dtype, order="C", copy=True)
    result.flags.writeable = False
    return result


def _array_fingerprint(arrays: Sequence[NDArray[Any]]) -> str:
    digest = hashlib.sha256()
    for value in arrays:
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(json.dumps(value.shape, separators=(",", ":")).encode("ascii"))
        digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True)
class CapabilityCandidateSetRecord:
    """Every candidate and model-visible field at one macro decision.

    Candidate count and edit count are dynamic in the durable record. Padding
    exists only after collation. Masked edit slots are canonicalized to zero so
    their bytes cannot carry accidental or privileged state.
    """

    mode: IntArray
    int_fields: IntArray
    edit_values: FloatArray
    edit_mask: BoolArray
    candidate_features: FloatArray
    search_logits: FloatArray
    search_features: FloatArray
    canonical_ids: UIntArray

    def __post_init__(self) -> None:
        """Copy, canonicalize, validate, and freeze the complete candidate set."""
        mode = cast(IntArray, _freeze(self.mode, np.dtype(np.int64)))
        int_fields = cast(IntArray, _freeze(self.int_fields, np.dtype(np.int64)))
        edit_values = cast(FloatArray, _freeze(self.edit_values, np.dtype(np.float32)))
        edit_mask = cast(BoolArray, _freeze(self.edit_mask, np.dtype(np.bool_)))
        candidate_features = cast(
            FloatArray,
            _freeze(self.candidate_features, np.dtype(np.float32)),
        )
        search_logits = cast(
            FloatArray,
            _freeze(self.search_logits, np.dtype(np.float32)),
        )
        search_features = cast(
            FloatArray,
            _freeze(self.search_features, np.dtype(np.float32)),
        )
        canonical_ids = cast(UIntArray, _freeze(self.canonical_ids, np.dtype(np.uint64)))

        if mode.ndim != 1 or mode.shape[0] < 1:
            raise ValueError("capability record needs at least one dynamic candidate")
        candidates = mode.shape[0]
        if int_fields.ndim != 3 or int_fields.shape[0] != candidates or int_fields.shape[2] != 6:
            raise ValueError("capability integer edits must have shape [candidates, edits, 6]")
        edits = int_fields.shape[1]
        if edits < 1 or edit_values.shape != (candidates, edits, 4):
            raise ValueError("capability edit values must have shape [candidates, edits, 4]")
        if edit_mask.shape != (candidates, edits):
            raise ValueError("capability edit mask must align with candidate edits")
        if candidate_features.ndim != 2 or candidate_features.shape[0] != candidates:
            raise ValueError("capability candidate features must align with candidates")
        if candidate_features.shape[1] < 1:
            raise ValueError("capability candidates need at least one proposal feature")
        if search_logits.shape != (candidates,):
            raise ValueError("capability search logits must align with candidates")
        if search_features.ndim != 2 or search_features.shape[0] != candidates:
            raise ValueError("capability search features must align with candidates")
        if canonical_ids.shape != (candidates,):
            raise ValueError("capability canonical ids must align with candidates")
        if np.any(mode < 0):
            raise ValueError("capability modes must be non-negative")
        if np.unique(canonical_ids).size != candidates:
            raise ValueError("capability canonical ids must be unique within a candidate set")
        if (
            not np.isfinite(candidate_features).all()
            or not np.isfinite(search_logits).all()
            or not np.isfinite(search_features).all()
        ):
            raise ValueError("capability model features must be finite")
        if not np.isfinite(edit_values[edit_mask]).all():
            raise ValueError("capability active edit values must be finite")
        edit_counts = edit_mask.sum(axis=1)
        prefix_mask = np.arange(edits)[None, :] < edit_counts[:, None]
        if not np.array_equal(edit_mask, prefix_mask):
            raise ValueError("capability active edits must form a contiguous prefix")

        retained_edits = max(1, int(edit_counts.max()))
        canonical_edit_mask = cast(
            BoolArray,
            _freeze(edit_mask[:, :retained_edits], np.dtype(np.bool_)),
        )
        canonical_int_fields = np.array(
            int_fields[:, :retained_edits],
            dtype=np.int64,
            order="C",
            copy=True,
        )
        canonical_edit_values = np.array(
            edit_values[:, :retained_edits],
            dtype=np.float32,
            order="C",
            copy=True,
        )
        canonical_int_fields[~canonical_edit_mask] = 0
        canonical_edit_values[~canonical_edit_mask] = 0.0
        canonical_int_fields.flags.writeable = False
        canonical_edit_values.flags.writeable = False

        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "int_fields", canonical_int_fields)
        object.__setattr__(self, "edit_values", canonical_edit_values)
        object.__setattr__(self, "edit_mask", canonical_edit_mask)
        object.__setattr__(self, "candidate_features", candidate_features)
        object.__setattr__(self, "search_logits", search_logits)
        object.__setattr__(self, "search_features", search_features)
        object.__setattr__(self, "canonical_ids", canonical_ids)

    @classmethod
    def from_padded(
        cls,
        *,
        mode: IntArray,
        int_fields: IntArray,
        edit_values: FloatArray,
        edit_counts: IntArray,
        candidate_features: FloatArray,
        candidate_mask: BoolArray,
        canonical_ids: UIntArray,
        search_logits: FloatArray,
        search_features: FloatArray | None = None,
    ) -> CapabilityCandidateSetRecord:
        """Strip one native padded row into a durable dynamic candidate set."""
        raw_mask = np.asarray(candidate_mask, dtype=np.bool_)
        raw_mode = np.asarray(mode)
        if raw_mask.ndim != 1 or raw_mode.ndim != 1 or raw_mask.shape != raw_mode.shape:
            raise ValueError("native capability mask and modes must have shape [candidates]")
        raw_fields = np.asarray(int_fields)
        if raw_fields.ndim != 3 or raw_fields.shape[0] != raw_mask.shape[0]:
            raise ValueError("native capability integer fields do not align with candidates")
        raw_counts = np.asarray(edit_counts, dtype=np.int64)
        if raw_counts.shape != raw_mask.shape:
            raise ValueError("native capability edit counts do not align with candidates")
        if np.any((raw_counts < 0) | (raw_counts > raw_fields.shape[1])):
            raise ValueError("native capability edit count lies outside the edit capacity")
        selected = np.flatnonzero(raw_mask)
        if selected.size < 1:
            raise ValueError("native capability row contains no valid candidates")
        counts = raw_counts[selected]
        selected_search = (
            np.zeros((selected.size, 0), dtype=np.float32)
            if search_features is None
            else np.asarray(search_features)[selected]
        )
        return cls(
            mode=np.asarray(mode)[selected],
            int_fields=raw_fields[selected],
            edit_values=np.asarray(edit_values)[selected],
            edit_mask=np.arange(raw_fields.shape[1])[None, :] < counts[:, None],
            candidate_features=np.asarray(candidate_features)[selected],
            search_logits=np.asarray(search_logits)[selected],
            search_features=selected_search,
            canonical_ids=np.asarray(canonical_ids)[selected],
        )

    @property
    def candidates(self) -> int:
        """Return the number of real, unpadded candidates."""
        return int(self.mode.shape[0])

    @property
    def edits(self) -> int:
        """Return the local edit capacity retained in this record."""
        return int(self.int_fields.shape[1])

    @property
    def edit_counts(self) -> IntArray:
        """Return the prefix length consumed by the neural candidate encoder."""
        counts = np.asarray(self.edit_mask.sum(axis=1), dtype=np.int64)
        counts.flags.writeable = False
        return counts

    @property
    def fingerprint(self) -> str:
        """Bind the exact stored candidates and every model-visible feature."""
        return _array_fingerprint(
            (
                self.mode,
                self.int_fields,
                self.edit_values,
                self.edit_mask,
                self.candidate_features,
                self.search_logits,
                self.search_features,
                self.canonical_ids,
            )
        )


@dataclass(frozen=True)
class MacroDecisionRecord:
    """One executed SMDP choice with one frozen joint behavior probability."""

    episode_id: str
    decision_index: int
    start_step: int
    end_step: int
    context: FrozenSearchContext
    candidates: CapabilityCandidateSetRecord
    root_features: FloatArray
    selected_index: int
    old_joint_log_probability: float
    old_value: float
    behavior_factor_count: int
    executor_trace_id: str

    def __post_init__(self) -> None:
        """Require a complete executable transition and finite behavior statistics."""
        if not self.episode_id or self.episode_id != self.episode_id.strip():
            raise ValueError("macro decision needs a canonical episode identity")
        if self.decision_index < 0:
            raise ValueError("macro decision index must be non-negative")
        if self.start_step < 0 or self.end_step <= self.start_step:
            raise ValueError("macro decision needs a positive SMDP duration")
        if not 0 <= self.selected_index < self.candidates.candidates:
            raise ValueError("selected capability index lies outside the frozen candidate set")
        root_features = cast(
            FloatArray,
            _freeze(self.root_features, np.dtype(np.float32)),
        )
        if root_features.ndim != 1 or root_features.shape[0] < 1:
            raise ValueError("macro decision root features must be a nonempty vector")
        if not np.isfinite(root_features).all():
            raise ValueError("macro decision root features must be finite")
        if not math.isfinite(self.old_joint_log_probability):
            raise ValueError("macro behavior joint log probability must be finite")
        if not math.isfinite(self.old_value) or not -1.0 <= self.old_value <= 1.0:
            raise ValueError("macro behavior WDL value must lie in [-1, 1]")
        if self.behavior_factor_count < 1:
            raise ValueError("macro joint probability needs at least one stochastic factor")
        if not self.executor_trace_id or self.executor_trace_id != self.executor_trace_id.strip():
            raise ValueError("macro decision needs an authenticated executor trace identity")
        object.__setattr__(self, "root_features", root_features)

    @property
    def duration(self) -> int:
        """Return primitive official turns controlled by this macro choice."""
        return self.end_step - self.start_step

    @property
    def selected_canonical_id(self) -> int:
        """Return the native canonical identity of the executed candidate."""
        return int(self.candidates.canonical_ids[self.selected_index])

    @property
    def fingerprint(self) -> str:
        """Return a stable identity for replay and optimizer provenance."""
        payload = {
            "episode_id": self.episode_id,
            "decision_index": self.decision_index,
            "start_step": self.start_step,
            "end_step": self.end_step,
            "context": self.context.fingerprint,
            "candidates": self.candidates.fingerprint,
            "root_features": _array_fingerprint((self.root_features,)),
            "selected_index": self.selected_index,
            "selected_canonical_id": self.selected_canonical_id,
            "old_joint_log_probability": self.old_joint_log_probability,
            "old_value": self.old_value,
            "behavior_factor_count": self.behavior_factor_count,
            "executor_trace_id": self.executor_trace_id,
        }
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CapabilityEpisodeRecord:
    """One complete official match represented at its macro decision boundaries."""

    episode_id: str
    opponent_id: str
    seed: int
    seat: int
    terminal_step: int
    outcome: int
    decisions: tuple[MacroDecisionRecord, ...]

    def __post_init__(self) -> None:
        """Validate chronological SMDP transitions and a single frozen batch contract."""
        if not self.episode_id or self.episode_id != self.episode_id.strip():
            raise ValueError("capability episode needs a canonical identity")
        if not self.opponent_id or self.opponent_id != self.opponent_id.strip():
            raise ValueError("capability episode needs a canonical opponent identity")
        if self.seed < 0 or self.seat not in (0, 1):
            raise ValueError("capability episode seed or seat is invalid")
        if self.terminal_step < 1:
            raise ValueError("capability episode terminal step must be positive")
        if self.outcome not in (-1, 0, 1):
            raise ValueError("capability episode outcome must be loss, tie, or win")
        decisions = tuple(self.decisions)
        if not decisions:
            raise ValueError("capability episode needs at least one macro decision")
        previous_end = -1
        reference = decisions[0].context
        for index, decision in enumerate(decisions):
            if decision.episode_id != self.episode_id or decision.decision_index != index:
                raise ValueError("capability macro decisions do not match episode order")
            if decision.start_step < previous_end:
                raise ValueError("capability macro decisions overlap")
            if decision.end_step > self.terminal_step:
                raise ValueError("capability macro decision extends past the terminal step")
            reference.require_batch_compatible(decision.context)
            previous_end = decision.end_step
        object.__setattr__(self, "decisions", decisions)

    @property
    def contract(self) -> CapabilityVersionContract:
        """Return the exact proposal/search/executor version contract."""
        return self.decisions[0].context.contract


@dataclass(frozen=True)
class TensorCapabilityRolloutBatch:
    """Padded candidate inputs plus flat macro-decision PPO statistics."""

    root_features: Tensor
    mode: Tensor
    int_fields: Tensor
    edit_values: Tensor
    edit_counts: Tensor
    edit_mask: Tensor
    candidate_features: Tensor
    candidate_mask: Tensor
    search_logits: Tensor
    search_features: Tensor
    selected_indices: Tensor
    old_joint_log_probability: Tensor
    old_values: Tensor
    behavior_factor_counts: Tensor
    episode_index: Tensor
    start_steps: Tensor
    durations: Tensor
    outcomes: Tensor
    direct_outcomes: Tensor | None
    contract: CapabilityVersionContract
    episode_ids: tuple[str, ...]
    context_fingerprints: tuple[str, ...]
    record_fingerprints: tuple[str, ...]
    selected_canonical_ids: tuple[int, ...]

    def to(self, device: torch.device) -> TensorCapabilityRolloutBatch:
        """Transfer tensor fields while retaining immutable provenance identities."""
        return TensorCapabilityRolloutBatch(
            root_features=self.root_features.to(device),
            mode=self.mode.to(device),
            int_fields=self.int_fields.to(device),
            edit_values=self.edit_values.to(device),
            edit_counts=self.edit_counts.to(device),
            edit_mask=self.edit_mask.to(device),
            candidate_features=self.candidate_features.to(device),
            candidate_mask=self.candidate_mask.to(device),
            search_logits=self.search_logits.to(device),
            search_features=self.search_features.to(device),
            selected_indices=self.selected_indices.to(device),
            old_joint_log_probability=self.old_joint_log_probability.to(device),
            old_values=self.old_values.to(device),
            behavior_factor_counts=self.behavior_factor_counts.to(device),
            episode_index=self.episode_index.to(device),
            start_steps=self.start_steps.to(device),
            durations=self.durations.to(device),
            outcomes=self.outcomes.to(device),
            direct_outcomes=(
                None if self.direct_outcomes is None else self.direct_outcomes.to(device)
            ),
            contract=self.contract,
            episode_ids=self.episode_ids,
            context_fingerprints=self.context_fingerprints,
            record_fingerprints=self.record_fingerprints,
            selected_canonical_ids=self.selected_canonical_ids,
        )

    @property
    def decisions(self) -> int:
        """Return the number of real macro selections in the batch."""
        return int(self.selected_indices.shape[0])

    @property
    def episodes(self) -> int:
        """Return the number of equally weighted complete episodes."""
        return int(self.outcomes.shape[0])

    @property
    def optional_search_features(self) -> Tensor | None:
        """Match the selector API when the frozen search-feature ABI is empty."""
        return self.search_features if self.search_features.shape[-1] else None


def collate_capability_episodes(
    episodes: Sequence[CapabilityEpisodeRecord],
    device: torch.device | None = None,
) -> TensorCapabilityRolloutBatch:
    """Pad dynamic candidates while retaining one row per macro decision."""
    if not episodes:
        raise ValueError("capability collation needs at least one complete episode")
    reference = episodes[0].decisions[0].context
    for episode in episodes:
        reference.contract.require_compatible(episode.contract)
        reference.require_batch_compatible(episode.decisions[0].context)

    decisions = [decision for episode in episodes for decision in episode.decisions]
    candidate_widths = {decision.candidates.candidate_features.shape[1] for decision in decisions}
    search_widths = {decision.candidates.search_features.shape[1] for decision in decisions}
    root_widths = {decision.root_features.shape[0] for decision in decisions}
    if len(candidate_widths) != 1 or len(search_widths) != 1 or len(root_widths) != 1:
        raise ValueError("capability feature ABI differs across rollout records")
    candidate_width = candidate_widths.pop()
    search_width = search_widths.pop()
    root_width = root_widths.pop()
    rows = len(decisions)
    maximum_candidates = max(decision.candidates.candidates for decision in decisions)
    maximum_edits = max(decision.candidates.edits for decision in decisions)

    root_features = np.empty((rows, root_width), dtype=np.float32)
    mode = np.zeros((rows, maximum_candidates), dtype=np.int64)
    int_fields = np.zeros((rows, maximum_candidates, maximum_edits, 6), dtype=np.int64)
    edit_values = np.zeros(
        (rows, maximum_candidates, maximum_edits, 4),
        dtype=np.float32,
    )
    edit_counts = np.zeros((rows, maximum_candidates), dtype=np.int64)
    edit_mask = np.zeros(
        (rows, maximum_candidates, maximum_edits),
        dtype=np.bool_,
    )
    candidate_features = np.zeros(
        (rows, maximum_candidates, candidate_width),
        dtype=np.float32,
    )
    candidate_mask = np.zeros((rows, maximum_candidates), dtype=np.bool_)
    search_logits = np.zeros((rows, maximum_candidates), dtype=np.float32)
    search_features = np.zeros(
        (rows, maximum_candidates, search_width),
        dtype=np.float32,
    )

    selected_indices = np.empty(rows, dtype=np.int64)
    old_joint_log_probability = np.empty(rows, dtype=np.float32)
    old_values = np.empty(rows, dtype=np.float32)
    behavior_factor_counts = np.empty(rows, dtype=np.int64)
    episode_index = np.empty(rows, dtype=np.int64)
    start_steps = np.empty(rows, dtype=np.int64)
    durations = np.empty(rows, dtype=np.int64)
    context_fingerprints: list[str] = []
    record_fingerprints: list[str] = []
    selected_canonical_ids: list[int] = []

    row = 0
    for episode_row, episode in enumerate(episodes):
        for decision in episode.decisions:
            candidates = decision.candidates.candidates
            edits = decision.candidates.edits
            root_features[row] = decision.root_features
            mode[row, :candidates] = decision.candidates.mode
            int_fields[row, :candidates, :edits] = decision.candidates.int_fields
            edit_values[row, :candidates, :edits] = decision.candidates.edit_values
            edit_counts[row, :candidates] = decision.candidates.edit_counts
            edit_mask[row, :candidates, :edits] = decision.candidates.edit_mask
            candidate_features[row, :candidates] = decision.candidates.candidate_features
            candidate_mask[row, :candidates] = True
            search_logits[row, :candidates] = decision.candidates.search_logits
            search_features[row, :candidates] = decision.candidates.search_features
            selected_indices[row] = decision.selected_index
            old_joint_log_probability[row] = decision.old_joint_log_probability
            old_values[row] = decision.old_value
            behavior_factor_counts[row] = decision.behavior_factor_count
            episode_index[row] = episode_row
            start_steps[row] = decision.start_step
            durations[row] = decision.duration
            context_fingerprints.append(decision.context.fingerprint)
            record_fingerprints.append(decision.fingerprint)
            selected_canonical_ids.append(decision.selected_canonical_id)
            row += 1

    batch = TensorCapabilityRolloutBatch(
        root_features=torch.from_numpy(root_features),
        mode=torch.from_numpy(mode),
        int_fields=torch.from_numpy(int_fields),
        edit_values=torch.from_numpy(edit_values),
        edit_counts=torch.from_numpy(edit_counts),
        edit_mask=torch.from_numpy(edit_mask),
        candidate_features=torch.from_numpy(candidate_features),
        candidate_mask=torch.from_numpy(candidate_mask),
        search_logits=torch.from_numpy(search_logits),
        search_features=torch.from_numpy(search_features),
        selected_indices=torch.from_numpy(selected_indices),
        old_joint_log_probability=torch.from_numpy(old_joint_log_probability),
        old_values=torch.from_numpy(old_values),
        behavior_factor_counts=torch.from_numpy(behavior_factor_counts),
        episode_index=torch.from_numpy(episode_index),
        start_steps=torch.from_numpy(start_steps),
        durations=torch.from_numpy(durations),
        outcomes=torch.tensor([episode.outcome for episode in episodes], dtype=torch.float32),
        direct_outcomes=None,
        contract=reference.contract,
        episode_ids=tuple(episode.episode_id for episode in episodes),
        context_fingerprints=tuple(context_fingerprints),
        record_fingerprints=tuple(record_fingerprints),
        selected_canonical_ids=tuple(selected_canonical_ids),
    )
    return batch if device is None else batch.to(device)


__all__ = [
    "CapabilityCandidateSetRecord",
    "CapabilityEpisodeRecord",
    "MacroDecisionRecord",
    "TensorCapabilityRolloutBatch",
    "collate_capability_episodes",
]
