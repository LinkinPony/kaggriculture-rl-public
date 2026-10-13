"""Batched native complete-match rollout for capability-space PPO."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.kaito.native import create_native_session as kaito_session
from kagg_revue.policy.capability import CapabilityCandidates, CapabilitySelector
from kagg_revue.rl.capabilities.contract import CapabilityVersionContract
from kagg_revue.rl.capabilities.data import TensorCapabilityRolloutBatch
from kagg_revue.rl.capabilities.direct_control import (
    collect_paired_direct_control,
    create_opponent_session,
)
from kagg_revue.rl.capabilities.search import FrozenTargetSearch
from kagg_revue.rl.rollout.population import weighted_rollout_jobs


@dataclass(frozen=True)
class CapabilityGameResult:
    """Direct official-rule outcome for one candidate seat."""

    episode_id: str
    opponent_id: str
    seed: int
    seat: int
    outcome: int
    terminal_cash: float
    opponent_cash: float


@dataclass(frozen=True)
class CapabilityRolloutResult:
    """One complete PPO panel and its outcome/throughput diagnostics."""

    batch: TensorCapabilityRolloutBatch
    games: tuple[CapabilityGameResult, ...]
    diagnostics: dict[str, float | int]


def _tensor_candidates(
    panel: Mapping[str, Any],
    device: torch.device,
) -> tuple[torch.Tensor, CapabilityCandidates]:
    """Upload one native candidate panel without Python candidate loops."""
    state = torch.as_tensor(panel["root_features"], device=device)
    candidates = CapabilityCandidates(
        mode=torch.as_tensor(panel["mode"], device=device),
        int_fields=torch.as_tensor(panel["int_fields"], device=device),
        edit_values=torch.as_tensor(panel["float_fields"], device=device),
        edit_counts=torch.as_tensor(panel["edit_counts"], device=device),
        candidate_features=torch.as_tensor(panel["candidate_features"], device=device),
        mask=torch.as_tensor(panel["candidate_mask"], device=device, dtype=torch.bool),
    )
    return state, candidates


def _fingerprint(*values: object) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(str(value).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


class CapabilityRolloutCollector:
    """Keep native rollout lanes resident while policy updates on the GPU."""

    def __init__(
        self,
        backend: BackendApi,
        selector: CapabilitySelector,
        search: FrozenTargetSearch,
        environment: Mapping[str, object],
        opponent_weights: Mapping[str, float],
        contract: CapabilityVersionContract,
        *,
        max_candidates: int,
        max_edits: int,
        cpu_workers: int,
        device: torch.device,
        sampling_seed: int,
        action_generator: torch.Generator,
        behavior_exploration_epsilon: float,
        sample_actions: bool = True,
        collect_direct_control: bool = False,
    ) -> None:
        """Bind the fixed compiler/search/executor implementation."""
        self._backend = backend
        self._selector = selector
        self._search = search
        self._environment = dict(environment)
        self._opponent_weights = dict(opponent_weights)
        self._contract = contract
        self._max_candidates = max_candidates
        self._max_edits = max_edits
        self._cpu_workers = cpu_workers
        self._device = device
        self._sampling_seed = sampling_seed
        self._action_generator = action_generator
        self._behavior_exploration_epsilon = behavior_exploration_epsilon
        self._sample_actions = sample_actions
        self._collect_direct_control = collect_direct_control
        raw_market_orders = self._environment.get("maxMarketOrdersPerTurn", 10)
        if not isinstance(raw_market_orders, int) or isinstance(raw_market_orders, bool):
            raise TypeError("capability market order capacity must be an integer")
        self._maximum_market_orders = raw_market_orders

    def _jobs(self, seeds: Sequence[int], update: int) -> tuple[tuple[int, int, str], ...]:
        return weighted_rollout_jobs(
            seeds,
            self._opponent_weights,
            rank=0,
            world_size=1,
            sampling_seed=self._sampling_seed + update * 1_000_003,
        )

    def _step(
        self,
        engines: list[Any],
        seats: NDArray[np.int64],
        opponent_ids: Sequence[str],
        opponent_sessions: list[Any],
        candidate_tokens: NDArray[np.int64],
        candidate_quantities: NDArray[np.int64],
        candidate_counts: NDArray[np.int64],
        candidate_units: NDArray[np.int64],
    ) -> NDArray[np.bool_]:
        """Advance grouped native opponents without an observation boundary."""
        batch = len(engines)
        width = candidate_tokens.shape[1]
        tokens = np.zeros((batch, 2, width), dtype=np.int64)
        quantities = np.zeros_like(tokens)
        decision_counts = np.zeros((batch, 2), dtype=np.int64)
        unit_counts = np.zeros((batch, 2), dtype=np.int64)
        rows = np.arange(batch)
        tokens[rows, seats] = candidate_tokens
        quantities[rows, seats] = candidate_quantities
        decision_counts[rows, seats] = candidate_counts
        unit_counts[rows, seats] = candidate_units
        done = np.zeros(batch, dtype=np.bool_)
        for opponent_id in self._opponent_weights:
            indices = np.asarray(
                [index for index, value in enumerate(opponent_ids) if value == opponent_id],
                dtype=np.int64,
            )
            if indices.size == 0:
                continue
            result = self._backend.native_opponent_batch_steps[opponent_id](
                [engines[int(index)] for index in indices],
                seats[indices],
                [opponent_sessions[int(index)] for index in indices],
                tokens[indices],
                quantities[indices],
                decision_counts[indices],
                unit_counts[indices],
                min(self._cpu_workers, int(indices.size)),
            )
            done[indices] = np.asarray(result, dtype=np.bool_)
        return done

    def collect(self, seeds: Sequence[int], *, update: int) -> CapabilityRolloutResult:
        """Collect paired complete matches and freeze every behavior tensor."""
        if not seeds:
            raise ValueError("capability rollout needs at least one seed")
        jobs = self._jobs(seeds, update)
        engines = [
            self._backend.engine(seed=int(seed), configuration=self._environment)
            for seed, _seat, _opponent in jobs
        ]
        seats = np.asarray([seat for _seed, seat, _opponent in jobs], dtype=np.int64)
        opponent_ids = tuple(opponent for _seed, _seat, opponent in jobs)
        capability_sessions = [
            self._backend.capability_session(
                self._environment,
                self._max_candidates,
                self._max_edits,
            )
            for _ in jobs
        ]
        direct_sessions = [kaito_session(self._maximum_market_orders) for _ in jobs]
        opponent_sessions = [
            create_opponent_session(opponent_id, self._maximum_market_orders)
            for opponent_id in opponent_ids
        ]

        root_blocks: list[NDArray[np.float32]] = []
        mode_blocks: list[NDArray[np.int64]] = []
        integer_blocks: list[NDArray[np.int64]] = []
        value_blocks: list[NDArray[np.float32]] = []
        count_blocks: list[NDArray[np.int64]] = []
        edit_mask_blocks: list[NDArray[np.bool_]] = []
        feature_blocks: list[NDArray[np.float32]] = []
        candidate_mask_blocks: list[NDArray[np.bool_]] = []
        search_blocks: list[NDArray[np.float32]] = []
        selected_blocks: list[NDArray[np.int64]] = []
        log_probability_blocks: list[NDArray[np.float32]] = []
        old_value_blocks: list[NDArray[np.float32]] = []
        canonical_id_blocks: list[NDArray[np.uint64]] = []
        start_steps: list[int] = []
        direct_turns = 0
        primitive_turns = 0
        decision_seconds = 0.0
        executor_seconds = 0.0
        started = time.perf_counter()
        done = np.zeros(len(jobs), dtype=np.bool_)
        self._selector.eval()

        while not bool(done.all()):
            step = int(engines[0].step_index)
            if any(int(engine.step_index) != step for engine in engines):
                raise RuntimeError("capability native rollout lanes lost lockstep")
            required = np.asarray(
                self._backend.capability_decision_required_batch(
                    capability_sessions,
                    engines,
                    seats,
                    self._cpu_workers,
                ),
                dtype=np.bool_,
            )
            if bool(required.any()):
                if not bool(required.all()):
                    raise RuntimeError("capability macro boundaries differ across paired lanes")
                decision_started = time.perf_counter()
                panel = cast(
                    Mapping[str, Any],
                    self._backend.capability_candidates_batch(
                        capability_sessions,
                        engines,
                        seats,
                        self._cpu_workers,
                    ),
                )
                state, candidates = _tensor_candidates(panel, self._device)
                with torch.inference_mode():
                    search = self._search.score(state, candidates)
                    action = self._selector.rollout(
                        state,
                        candidates,
                        search.logits,
                        sample=self._sample_actions,
                        generator=self._action_generator,
                        exploration_epsilon=self._behavior_exploration_epsilon,
                    )
                selected = action.ids.cpu().numpy().astype(np.int64, copy=False)
                selection = cast(
                    Mapping[str, Any],
                    self._backend.capability_select_batch(
                        capability_sessions,
                        selected,
                        self._cpu_workers,
                    ),
                )
                root_blocks.append(np.asarray(panel["root_features"], dtype=np.float32))
                mode_blocks.append(np.asarray(panel["mode"], dtype=np.int64))
                integer_blocks.append(np.asarray(panel["int_fields"], dtype=np.int64))
                value_blocks.append(np.asarray(panel["float_fields"], dtype=np.float32))
                count_blocks.append(np.asarray(panel["edit_counts"], dtype=np.int64))
                edit_mask_blocks.append(np.asarray(panel["edit_mask"], dtype=np.bool_))
                feature_blocks.append(np.asarray(panel["candidate_features"], dtype=np.float32))
                candidate_mask_blocks.append(np.asarray(panel["candidate_mask"], dtype=np.bool_))
                search_blocks.append(search.logits.cpu().numpy().astype(np.float32, copy=False))
                selected_blocks.append(selected)
                log_probability_blocks.append(
                    action.log_probability.cpu().numpy().astype(np.float32, copy=False)
                )
                old_value_blocks.append(action.value.cpu().numpy().astype(np.float32, copy=False))
                canonical_id_blocks.append(np.asarray(selection["canonical_id"], dtype=np.uint64))
                start_steps.append(step)
                decision_seconds += time.perf_counter() - decision_started

            executor_started = time.perf_counter()
            compiled = cast(
                Mapping[str, Any],
                self._backend.capability_actions_batch(
                    capability_sessions,
                    engines,
                    seats,
                    self._cpu_workers,
                ),
            )
            requires_direct = np.asarray(compiled["requires_direct"], dtype=np.bool_)
            candidate_tokens = np.asarray(compiled["tokens"], dtype=np.int64)
            candidate_quantities = np.asarray(compiled["quantities"], dtype=np.int64)
            candidate_counts = np.asarray(compiled["decision_counts"], dtype=np.int64)
            candidate_units = np.asarray(compiled["unit_counts"], dtype=np.int64)
            if bool(requires_direct.any()):
                direct_width = self._maximum_market_orders + 65
                direct_tokens = np.zeros((len(jobs), direct_width), dtype=np.int64)
                direct_quantities = np.zeros_like(direct_tokens)
                direct_counts = np.zeros(len(jobs), dtype=np.int64)
                direct_units = np.zeros(len(jobs), dtype=np.int64)
                self._backend.kaito_v48_action_numeric_batch(
                    engines,
                    seats,
                    direct_sessions,
                    direct_tokens,
                    direct_quantities,
                    direct_counts,
                    direct_units,
                    self._cpu_workers,
                )
                width = max(candidate_tokens.shape[1], direct_tokens.shape[1])
                merged_tokens = np.zeros((len(jobs), width), dtype=np.int64)
                merged_quantities = np.zeros_like(merged_tokens)
                merged_tokens[:, : candidate_tokens.shape[1]] = candidate_tokens
                merged_quantities[:, : candidate_quantities.shape[1]] = candidate_quantities
                rows = np.flatnonzero(requires_direct)
                merged_tokens[rows] = 0
                merged_quantities[rows] = 0
                merged_tokens[rows, : direct_tokens.shape[1]] = direct_tokens[rows]
                merged_quantities[rows, : direct_quantities.shape[1]] = direct_quantities[rows]
                candidate_tokens = merged_tokens
                candidate_quantities = merged_quantities
                candidate_counts[rows] = direct_counts[rows]
                candidate_units[rows] = direct_units[rows]
                direct_turns += int(requires_direct.sum())
            done = self._step(
                engines,
                seats,
                opponent_ids,
                opponent_sessions,
                candidate_tokens,
                candidate_quantities,
                candidate_counts,
                candidate_units,
            )
            primitive_turns += len(jobs)
            executor_seconds += time.perf_counter() - executor_started

        candidate_elapsed = time.perf_counter() - started
        terminal_step = int(engines[0].step_index)
        durations_by_block = [
            (start_steps[index + 1] if index + 1 < len(start_steps) else terminal_step) - step
            for index, step in enumerate(start_steps)
        ]
        episode_index = np.tile(
            np.arange(len(jobs), dtype=np.int64),
            len(start_steps),
        )
        durations = np.concatenate(
            [np.full(len(jobs), duration, dtype=np.int64) for duration in durations_by_block]
        )
        starts = np.concatenate([np.full(len(jobs), step, dtype=np.int64) for step in start_steps])

        games: list[CapabilityGameResult] = []
        outcomes = np.empty(len(jobs), dtype=np.float32)
        episode_ids: list[str] = []
        for index, ((seed, seat, opponent_id), engine) in enumerate(
            zip(jobs, engines, strict=True)
        ):
            terminal_cash = float(engine.money(seat))
            opponent_cash = float(engine.money(1 - seat))
            outcome = int(terminal_cash > opponent_cash) - int(terminal_cash < opponent_cash)
            episode_id = f"{opponent_id}:{seed}:{seat}"
            episode_ids.append(episode_id)
            outcomes[index] = outcome
            games.append(
                CapabilityGameResult(
                    episode_id=episode_id,
                    opponent_id=opponent_id,
                    seed=seed,
                    seat=seat,
                    outcome=outcome,
                    terminal_cash=terminal_cash,
                    opponent_cash=opponent_cash,
                )
            )

        direct_outcomes: NDArray[np.float32] | None = None
        control_primitive_turns = 0
        control_elapsed = 0.0
        paired_better = 0
        paired_same = 0
        paired_worse = 0
        direct_only_games = 0
        single_intervention_games = 0
        single_intervention_better = 0
        single_intervention_same = 0
        single_intervention_worse = 0
        multiple_intervention_games = 0
        single_mode_games = {mode: 0 for mode in range(1, 4)}
        single_mode_better = {mode: 0 for mode in range(1, 4)}
        single_mode_worse = {mode: 0 for mode in range(1, 4)}
        if self._collect_direct_control:
            control = collect_paired_direct_control(
                self._backend,
                self._environment,
                jobs,
                maximum_market_orders=self._maximum_market_orders,
                cpu_workers=self._cpu_workers,
            )
            direct_outcomes = control.outcomes
            control_primitive_turns = control.primitive_turns
            control_elapsed = control.elapsed_seconds
            deltas = outcomes - direct_outcomes
            paired_better = int(np.count_nonzero(deltas > 0))
            paired_same = int(np.count_nonzero(deltas == 0))
            paired_worse = int(np.count_nonzero(deltas < 0))
            selected_modes = np.stack(
                [
                    modes[np.arange(len(jobs)), selected]
                    for modes, selected in zip(
                        mode_blocks,
                        selected_blocks,
                        strict=True,
                    )
                ]
            )
            non_direct_counts = np.count_nonzero(selected_modes != 0, axis=0)
            direct_only = non_direct_counts == 0
            direct_only_games = int(np.count_nonzero(direct_only))
            single_intervention = non_direct_counts == 1
            single_intervention_games = int(np.count_nonzero(single_intervention))
            single_intervention_better = int(np.count_nonzero(single_intervention & (deltas > 0)))
            single_intervention_same = int(np.count_nonzero(single_intervention & (deltas == 0)))
            single_intervention_worse = int(np.count_nonzero(single_intervention & (deltas < 0)))
            multiple_intervention_games = int(np.count_nonzero(non_direct_counts > 1))
            single_modes = np.where(
                single_intervention,
                selected_modes.max(axis=0),
                0,
            )
            for mode in single_mode_games:
                mode_mask = single_modes == mode
                single_mode_games[mode] = int(np.count_nonzero(mode_mask))
                single_mode_better[mode] = int(np.count_nonzero(mode_mask & (deltas > 0)))
                single_mode_worse[mode] = int(np.count_nonzero(mode_mask & (deltas < 0)))
            candidate_cash = np.asarray(
                [game.terminal_cash for game in games],
                dtype=np.float64,
            )
            candidate_opponent_cash = np.asarray(
                [game.opponent_cash for game in games],
                dtype=np.float64,
            )
            if not np.array_equal(
                candidate_cash[direct_only],
                control.terminal_cash[direct_only],
            ) or not np.array_equal(
                candidate_opponent_cash[direct_only],
                control.opponent_cash[direct_only],
            ):
                raise RuntimeError("all-DIRECT candidate lanes differ from paired controls")

        selected_ids = np.concatenate(canonical_id_blocks)
        context_id = _fingerprint(self._contract.fingerprint, update)
        record_ids = tuple(
            _fingerprint(context_id, row, int(selected_id))
            for row, selected_id in enumerate(selected_ids)
        )
        batch = TensorCapabilityRolloutBatch(
            root_features=torch.from_numpy(np.concatenate(root_blocks)),
            mode=torch.from_numpy(np.concatenate(mode_blocks)),
            int_fields=torch.from_numpy(np.concatenate(integer_blocks)),
            edit_values=torch.from_numpy(np.concatenate(value_blocks)),
            edit_counts=torch.from_numpy(np.concatenate(count_blocks)),
            edit_mask=torch.from_numpy(np.concatenate(edit_mask_blocks)),
            candidate_features=torch.from_numpy(np.concatenate(feature_blocks)),
            candidate_mask=torch.from_numpy(np.concatenate(candidate_mask_blocks)),
            search_logits=torch.from_numpy(np.concatenate(search_blocks)),
            search_features=torch.empty(
                (len(episode_index), self._max_candidates, 0),
                dtype=torch.float32,
            ),
            selected_indices=torch.from_numpy(np.concatenate(selected_blocks)),
            old_joint_log_probability=torch.from_numpy(np.concatenate(log_probability_blocks)),
            old_values=torch.from_numpy(np.concatenate(old_value_blocks)),
            behavior_factor_counts=torch.ones(len(episode_index), dtype=torch.int64),
            episode_index=torch.from_numpy(episode_index),
            start_steps=torch.from_numpy(starts),
            durations=torch.from_numpy(durations),
            outcomes=torch.from_numpy(outcomes),
            direct_outcomes=(
                None if direct_outcomes is None else torch.from_numpy(direct_outcomes)
            ),
            contract=self._contract,
            episode_ids=tuple(episode_ids),
            context_fingerprints=(context_id,) * len(episode_index),
            record_fingerprints=record_ids,
            selected_canonical_ids=tuple(int(value) for value in selected_ids),
        )
        elapsed = time.perf_counter() - started
        total_primitive_turns = primitive_turns + control_primitive_turns
        return CapabilityRolloutResult(
            batch=batch,
            games=tuple(games),
            diagnostics={
                "games": len(games),
                "macro_decisions": batch.decisions,
                "primitive_turns": primitive_turns,
                "control_primitive_turns": control_primitive_turns,
                "elapsed_seconds": elapsed,
                "candidate_elapsed_seconds": candidate_elapsed,
                "direct_control_elapsed_seconds": control_elapsed,
                "turns_per_second": total_primitive_turns / max(elapsed, 1e-9),
                "decision_seconds": decision_seconds,
                "executor_seconds": executor_seconds,
                "direct_turn_fraction": direct_turns / max(primitive_turns, 1),
                "paired_better": paired_better,
                "paired_same": paired_same,
                "paired_worse": paired_worse,
                "direct_only_games": direct_only_games,
                "single_intervention_games": single_intervention_games,
                "single_intervention_better": single_intervention_better,
                "single_intervention_same": single_intervention_same,
                "single_intervention_worse": single_intervention_worse,
                "multiple_intervention_games": multiple_intervention_games,
                **{
                    f"single_mode_{mode}_games": single_mode_games[mode]
                    for mode in single_mode_games
                },
                **{
                    f"single_mode_{mode}_better": single_mode_better[mode]
                    for mode in single_mode_better
                },
                **{
                    f"single_mode_{mode}_worse": single_mode_worse[mode]
                    for mode in single_mode_worse
                },
            },
        )


__all__ = [
    "CapabilityGameResult",
    "CapabilityRolloutCollector",
    "CapabilityRolloutResult",
]
