"""Rank8 labels on exact factor states visited by a frozen effect policy."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.teacher.effects import EffectTeacherPlan, Rank8EffectTeacher
from kagg_revue.teacher.submission import SubmissionTeacherArtifact

_FNV_OFFSET = 1_469_598_103_934_665_603
_FNV_PRIME = 1_099_511_628_211
_UINT64_MASK = 2**64 - 1
_EFFECT_SPEC_VERSION = 2
_WORK_PHASE = 0
_MARKET_PHASE = 1


def _hash_word(word: int, value: int) -> int:
    result = value
    unsigned = word & _UINT64_MASK
    for byte in range(8):
        result ^= (unsigned >> (byte * 8)) & 0xFF
        result = (result * _FNV_PRIME) & _UINT64_MASK
    return result


def effect_candidate_canonical_id(
    candidate_fields: NDArray[np.int64],
    *,
    phase: int,
    turn: int,
    market_prefix: NDArray[np.int64],
) -> int:
    """Reproduce the native atomic-effect candidate identity."""
    value = _hash_word(_EFFECT_SPEC_VERSION, _FNV_OFFSET)
    value = _hash_word(phase, value)
    if phase == _WORK_PHASE:
        value = _hash_word(turn, value)
    elif phase == _MARKET_PHASE:
        for field in market_prefix.reshape(-1):
            value = _hash_word(int(field), value)
    else:
        raise ValueError(f"effect correction cannot label phase {phase}")
    for field in candidate_fields:
        value = _hash_word(int(field), value)
    return 1 if value == 0 else value


def prefix_consistent_policy_mask(
    episode_index: NDArray[np.int64],
    turn_index: NDArray[np.int64],
    transaction_step: NDArray[np.int64],
    student_agreement: NDArray[np.bool_],
    policy_mask: NDArray[np.bool_],
) -> NDArray[np.bool_]:
    """Retain supervision through the first student divergence per turn."""
    arrays = (
        episode_index,
        turn_index,
        transaction_step,
        student_agreement,
        policy_mask,
    )
    if any(value.ndim != 1 for value in arrays) or len(
        {value.shape for value in arrays}
    ) != 1:
        raise ValueError("effect correction prefix fields must be aligned vectors")
    if np.any(episode_index < 0) or np.any(turn_index < 0):
        raise ValueError("effect correction prefix keys must be nonnegative")
    result = policy_mask.copy()
    order = np.lexsort((transaction_step, turn_index, episode_index))
    previous_key: tuple[int, int] | None = None
    expected_step = 0
    diverged = False
    for raw_row in order:
        row = int(raw_row)
        key = (
            int(episode_index[row]),
            int(turn_index[row]),
        )
        if key != previous_key:
            previous_key = key
            expected_step = 0
            diverged = False
        step = int(transaction_step[row])
        if step != expected_step:
            raise ValueError(
                "effect correction turn steps must be contiguous from zero"
            )
        expected_step += 1
        if diverged:
            result[row] = False
        elif not bool(student_agreement[row]):
            diverged = True
    return result


@dataclass(frozen=True, slots=True)
class EffectCorrectionLabels:
    """One relabeled rollout plus provenance-relevant diagnostics."""

    keys: tuple[tuple[int, int], ...]
    buckets: tuple[Mapping[str, Any], ...]
    route_ids: tuple[str, ...]
    first_event_days: tuple[int, ...]
    statistics: Mapping[str, int]


class Rank8EffectCorrectionObserver:
    """Query Rank8 once per official state and relabel student prefixes."""

    def __init__(
        self,
        artifact: SubmissionTeacherArtifact,
        effect_spec: Mapping[str, object],
        item_names: Sequence[object],
    ) -> None:
        """Retain immutable teacher inputs across fixed-size rollout groups."""
        self._artifact = artifact
        self._effect_spec = effect_spec
        self._item_names = item_names
        self._keys: tuple[tuple[int, int], ...] | None = None
        self._controllers: list[Rank8EffectTeacher] = []
        self._plans: list[list[EffectTeacherPlan]] = []
        self._turns = 0
        self._pending: EffectCorrectionLabels | None = None

    def start_group(
        self,
        keys: Sequence[tuple[int, int]],
        engines: Sequence[Any],
        players: NDArray[np.int64],
        turns: int,
    ) -> None:
        """Create one stateful Rank8 runtime per student perspective."""
        if self._keys is not None or self._pending is not None:
            raise RuntimeError("effect correction observer has an unfinished group")
        if (
            not keys
            or len(keys) != len(engines)
            or players.shape != (len(keys),)
            or turns < 1
        ):
            raise ValueError("effect correction group inputs are misaligned")
        self._keys = tuple(keys)
        self._controllers = [
            Rank8EffectTeacher(
                cast(Mapping[str, object], dict(engine.configuration)),
                self._artifact,
                self._effect_spec,
                self._item_names,
            )
            for engine in engines
        ]
        self._plans = [[] for _ in keys]
        self._turns = turns

    def begin_turn(
        self,
        engines: Sequence[Any],
        players: NDArray[np.int64],
        turn: int,
    ) -> None:
        """Freeze Rank8 intent before the student changes this turn's prefix."""
        if self._keys is None or len(engines) != len(self._controllers):
            raise RuntimeError("effect correction turn has no active group")
        if players.shape != (len(engines),) or not 0 <= turn < self._turns:
            raise ValueError("effect correction turn inputs are misaligned")
        if any(len(plans) != turn for plans in self._plans):
            raise RuntimeError("effect correction turns are not sequential")
        for row, (controller, engine, player) in enumerate(
            zip(self._controllers, engines, players.tolist(), strict=True)
        ):
            observation = cast(Mapping[str, object], engine.observation(int(player)))
            controller.prepare(observation)
            self._plans[row].append(controller.snapshot())

    def relabel_buckets(
        self,
        buckets: Sequence[Mapping[str, Any]],
    ) -> list[Mapping[str, Any]]:
        """Replace recorded student choices with expert labels in-place copies."""
        keys = self._keys
        if keys is None or any(len(plans) != self._turns for plans in self._plans):
            raise RuntimeError("effect correction labels lack complete teacher plans")
        relabeled: list[Mapping[str, Any]] = []
        statistics: Counter[str] = Counter()
        row_counts: list[int] = []
        episode_parts: list[NDArray[np.int64]] = []
        turn_parts: list[NDArray[np.int64]] = []
        step_parts: list[NDArray[np.int64]] = []
        agreement_parts: list[NDArray[np.bool_]] = []
        policy_parts: list[NDArray[np.bool_]] = []
        for raw in buckets:
            payload = dict(raw)
            fields = np.asarray(payload["candidate_fields"], dtype=np.int64)
            masks = np.asarray(payload["candidate_mask"], dtype=np.bool_)
            counts = np.asarray(payload["candidate_counts"], dtype=np.int64)
            phases = np.asarray(payload["phase"], dtype=np.int64)
            episodes = np.asarray(payload["episode_index"], dtype=np.int64)
            turns = np.asarray(payload["turn_index"], dtype=np.int64)
            market = np.asarray(payload["market_prefix"], dtype=np.int64)
            market_counts = np.asarray(payload["market_counts"], dtype=np.int64)
            native_steps = np.asarray(payload["transaction_step"], dtype=np.int64)
            behavior = np.asarray(payload["selected"], dtype=np.int64)
            policy = np.asarray(payload["policy_mask"], dtype=np.bool_)
            selected = behavior.copy()
            canonical_ids = np.asarray(
                payload["selected_canonical_id"], dtype=np.uint64
            ).copy()
            for row in range(selected.shape[0]):
                episode = int(episodes[row])
                turn = int(turns[row])
                count = int(counts[row])
                phase = int(phases[row])
                if not 0 <= episode < len(keys) or not 0 <= turn < self._turns:
                    raise ValueError("effect correction factor escaped its rollout group")
                plan = self._plans[episode][turn]
                local_fields = fields[row, :count]
                local_mask = masks[row, :count]
                if phase == _WORK_PHASE:
                    label = self._controllers[episode].label_work(
                        plan,
                        local_fields,
                        local_mask,
                    )
                    prefix = np.empty((0, fields.shape[-1]), dtype=np.int64)
                    statistics["work_labels"] += 1
                elif phase == _MARKET_PHASE:
                    prefix_count = int(market_counts[row])
                    prefix = market[row, :prefix_count]
                    label = self._controllers[episode].label_market(
                        plan,
                        prefix_count,
                        local_fields,
                        local_mask,
                    )
                    statistics["market_labels"] += 1
                else:
                    raise ValueError(f"effect correction cannot label phase {phase}")
                if not 0 <= label < count or not bool(local_mask[label]):
                    raise RuntimeError("effect correction teacher selected an invalid candidate")
                selected[row] = label
                canonical_ids[row] = effect_candidate_canonical_id(
                    local_fields[label],
                    phase=phase,
                    turn=turn,
                    market_prefix=prefix,
                )
                statistics["student_agreements"] += int(label == int(behavior[row]))
                statistics[
                    "work_student_agreements"
                    if phase == _WORK_PHASE
                    else "market_student_agreements"
                ] += int(label == int(behavior[row]))
                statistics["labels"] += 1
            payload["selected"] = selected
            payload["selected_canonical_id"] = canonical_ids
            relabeled.append(payload)
            row_counts.append(selected.shape[0])
            episode_parts.append(episodes)
            turn_parts.append(turns)
            step_parts.append(native_steps)
            agreement_parts.append(selected == behavior)
            policy_parts.append(policy)
        retained_policy = prefix_consistent_policy_mask(
            np.concatenate(episode_parts),
            np.concatenate(turn_parts),
            np.concatenate(step_parts),
            np.concatenate(agreement_parts),
            np.concatenate(policy_parts),
        )
        original_policy_labels = sum(
            int(np.count_nonzero(policy)) for policy in policy_parts
        )
        retained_policy_labels = int(np.count_nonzero(retained_policy))
        statistics["policy_labels_before_prefix_mask"] = original_policy_labels
        statistics["policy_labels"] = retained_policy_labels
        statistics["post_divergence_policy_labels_masked"] = (
            original_policy_labels - retained_policy_labels
        )
        offset = 0
        for labeled_payload, count in zip(relabeled, row_counts, strict=True):
            mutable = cast(dict[str, Any], labeled_payload)
            mutable["policy_mask"] = retained_policy[offset : offset + count].copy()
            offset += count
        route_ids: list[str] = []
        event_days: list[int] = []
        for plans in self._plans:
            metadata = plans[-1]
            if not isinstance(metadata.route_id, str):
                raise TypeError("effect correction teacher route id is absent")
            event_day = metadata.first_event_day
            if event_day is not None and (
                not isinstance(event_day, int) or isinstance(event_day, bool)
            ):
                raise TypeError("effect correction event day is invalid")
            route_ids.append(metadata.route_id)
            event_days.append(-1 if event_day is None else event_day)
        self._pending = EffectCorrectionLabels(
            keys=keys,
            buckets=tuple(relabeled),
            route_ids=tuple(route_ids),
            first_event_days=tuple(event_days),
            statistics=dict(statistics),
        )
        return relabeled

    def finish_group(self) -> None:
        """Release stateful teachers after labels have been attached."""
        if self._keys is None or self._pending is None:
            raise RuntimeError("effect correction group finished before relabeling")
        self._keys = None
        self._controllers = []
        self._plans = []
        self._turns = 0

    def take_labels(self) -> EffectCorrectionLabels:
        """Consume the one completed relabeled group."""
        if self._keys is not None or self._pending is None:
            raise RuntimeError("effect correction labels are not complete")
        result = self._pending
        self._pending = None
        return result


__all__ = [
    "EffectCorrectionLabels",
    "Rank8EffectCorrectionObserver",
    "effect_candidate_canonical_id",
    "prefix_consistent_policy_mask",
]
