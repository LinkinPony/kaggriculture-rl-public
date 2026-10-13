"""Complete-match native rollout with event-batched structured-plan inference."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.plans.model import StructuredPlanPolicy
from kagg_revue.policy.plans.observation import UNIT_SHAPE
from kagg_revue.rl.plans.contract import PlanVersionContract
from kagg_revue.rl.plans.data import TensorPlanRolloutBatch
from kagg_revue.rl.plans.exchange import PlanTensorExchange
from kagg_revue.rl.plans.graphs import PlanEventGraphCache
from kagg_revue.rl.plans.inference import PlanPolicyRuntime
from kagg_revue.rl.plans.population import (
    PlanHistoricalSnapshot,
    PlanSelfPlayPopulation,
)
from kagg_revue.rl.plans.storage import (
    build_batch,
    freeze_plan_actions,
    freeze_policy_output,
    new_blocks,
    record_policy,
)
from kagg_revue.rl.rollout.population import weighted_rollout_jobs


@dataclass(frozen=True)
class PlanGameResult:
    """Direct terminal outcome for one complete official-rule candidate game."""

    episode_id: str
    opponent_id: str
    seed: int
    seat: int
    outcome: int
    terminal_cash: float
    opponent_cash: float


@dataclass(frozen=True)
class PlanRolloutResult:
    """One finite on-policy panel plus direct throughput/outcome diagnostics."""

    batch: TensorPlanRolloutBatch
    games: tuple[PlanGameResult, ...]
    historical_opponent_id: str
    historical_opponent_update: int
    diagnostics: dict[str, object]


def _event_bits(values: NDArray[np.uint64], count: int) -> NDArray[np.float32]:
    positions = np.arange(count, dtype=np.uint64)
    return ((values[:, None] >> positions[None]) & np.uint64(1)).astype(np.float32)


def _training_perspectives(
    jobs: Sequence[tuple[int, int, str]],
) -> tuple[tuple[int, int, str], ...]:
    """Add the opposite actor perspective of each physical self-play match."""
    opposite = (
        (seed, 1 - seat, opponent) for seed, seat, opponent in jobs if opponent == "self_play"
    )
    return (*jobs, *opposite)


class StructuredPlanRolloutCollector:
    """Run native games while batching only seats whose plans need decisions."""

    def __init__(
        self,
        backend: BackendApi,
        policy: StructuredPlanPolicy,
        population: PlanSelfPlayPopulation,
        environment: Mapping[str, object],
        contract: PlanVersionContract,
        *,
        historical_fraction: float,
        event_count: int,
        inference_batch_size: int,
        event_cuda_graph_max_batch_size: int,
        cpu_workers: int,
        device: torch.device,
        historical_device: torch.device,
        rollout_rank: int,
        rollout_world_size: int,
        sampling_seed: int,
        action_generator: torch.Generator,
    ) -> None:
        """Bind the frozen actor, compiler ABI, population, and batch capacities."""
        self._backend = backend
        self._policy = policy
        self._population = population
        self._environment = dict(environment)
        self._contract = contract
        if not 0.0 < historical_fraction < 1.0:
            raise ValueError("structured-plan historical fraction must lie in (0, 1)")
        self._historical_fraction = historical_fraction
        self._event_count = event_count
        self._inference_batch_size = inference_batch_size
        if not 0 <= event_cuda_graph_max_batch_size <= inference_batch_size:
            raise ValueError("structured-plan event graph capacity is invalid")
        self._event_cuda_graph_max_batch_size = event_cuda_graph_max_batch_size
        self._cpu_workers = cpu_workers
        self._device = device
        self._historical_device = historical_device
        if rollout_rank < 0 or rollout_rank >= rollout_world_size:
            raise ValueError("structured-plan rollout rank is outside its shard group")
        self._rollout_rank = rollout_rank
        self._rollout_world_size = rollout_world_size
        self._sampling_seed = sampling_seed
        self._action_generator = action_generator
        self._historical_generator = torch.Generator(device=historical_device)
        self._current_event_graphs = (
            PlanEventGraphCache(
                policy,
                action_generator,
                device=device,
                record_statistics=True,
                maximum_batch_size=event_cuda_graph_max_batch_size,
            )
            if event_cuda_graph_max_batch_size
            else None
        )
        self._historical_event_graphs: PlanEventGraphCache | None = None
        self._exchanges: dict[
            tuple[str, int, int],
            PlanTensorExchange,
        ] = {}

    def _exchange(
        self,
        device: torch.device,
        decision_capacity: int,
    ) -> PlanTensorExchange:
        """Reuse fixed staging addresses across rollout updates and graphs."""
        key = (str(device), decision_capacity, self._inference_batch_size)
        exchange = self._exchanges.get(key)
        if exchange is None:
            exchange = PlanTensorExchange(
                device,
                decision_capacity=decision_capacity,
                inference_capacity=self._inference_batch_size,
            )
            self._exchanges[key] = exchange
        return exchange

    @staticmethod
    def _graph_counters(
        *caches: PlanEventGraphCache | None,
    ) -> tuple[int, int, int]:
        """Sum cumulative graph counters over current and history policies."""
        values = [cache.counters() for cache in caches if cache is not None]
        return (
            sum(value[0] for value in values),
            sum(value[1] for value in values),
            sum(value[2] for value in values),
        )

    def _rich_observations(
        self,
        engines: Sequence[Any],
        players: NDArray[np.int64],
        exchange: PlanTensorExchange,
    ) -> dict[str, NDArray[Any]]:
        """Encode old-policy entities and exact economics in one native pass."""
        batch = len(engines)
        values = exchange.native_observations(batch)
        if batch == 0:
            return {
                name: values[name]
                for name in (
                    "board",
                    "units",
                    "global_features",
                    "economic_state",
                )
            }
        self._backend.engine_policy_turn_inputs_compact_into(
            list(engines),
            players.tolist(),
            UNIT_SHAPE[1],
            min(self._cpu_workers, batch),
            values["board"],
            values["units"],
            values["global_features"],
            values["unit_counts"],
            values["economic_state"],
        )
        return {
            name: values[name]
            for name in (
                "board",
                "units",
                "global_features",
                "economic_state",
            )
        }

    def _jobs(
        self,
        seeds: Sequence[int],
        update: int,
        historical_identity: str,
    ) -> tuple[tuple[int, int, str], ...]:
        return weighted_rollout_jobs(
            seeds,
            {
                "self_play": 1.0 - self._historical_fraction,
                historical_identity: self._historical_fraction,
            },
            rank=self._rollout_rank,
            world_size=self._rollout_world_size,
            sampling_seed=self._sampling_seed + update * 1_000_003,
        )

    def _native_advance(
        self,
        engines: list[Any],
        seats: NDArray[np.int64],
        candidate_sessions: list[Any],
        opponent_plan_sessions: list[Any],
    ) -> tuple[NDArray[np.bool_], NDArray[np.int64]]:
        result = cast(
            Mapping[str, Any],
            self._backend.structured_plan_advance_self_play_batch(
                engines,
                seats,
                candidate_sessions,
                opponent_plan_sessions,
                min(self._cpu_workers, len(engines)),
            ),
        )
        done = np.asarray(result["done"], dtype=np.bool_)
        advanced = np.asarray(result["advanced_turns"], dtype=np.int64)
        if done.shape != (len(engines),) or advanced.shape != (len(engines),):
            raise RuntimeError("structured-plan native scheduler result lost alignment")
        if bool(np.any(advanced < 0)):
            raise RuntimeError("structured-plan native scheduler moved backwards")
        return done, advanced

    def collect(self, seeds: Sequence[int], *, update: int) -> PlanRolloutResult:
        """Collect complete matches and freeze every conditional behavior mask."""
        if not seeds:
            raise ValueError("structured-plan rollout needs at least one seed")
        selected_history: PlanHistoricalSnapshot = self._population.select(update)
        historical_policy = self._population.policy(selected_history)
        historical_generator = self._historical_generator
        historical_generator.manual_seed(
            (self._sampling_seed + update * 2_000_033 + 97) % (2**63 - 1)
        )
        if self._event_cuda_graph_max_batch_size:
            if self._historical_event_graphs is None:
                self._historical_event_graphs = PlanEventGraphCache(
                    historical_policy,
                    historical_generator,
                    device=self._historical_device,
                    record_statistics=False,
                    maximum_batch_size=self._event_cuda_graph_max_batch_size,
                )
            elif not self._historical_event_graphs.matches(
                historical_policy,
                historical_generator,
            ):
                raise RuntimeError("structured-plan historical graph binding changed")
        graph_counters_before = self._graph_counters(
            self._current_event_graphs,
            self._historical_event_graphs,
        )
        jobs = self._jobs(seeds, update, selected_history.identity)
        training_jobs = _training_perspectives(jobs)
        engines = [
            self._backend.engine(seed=int(seed), configuration=self._environment)
            for seed, _seat, _opponent in jobs
        ]
        seats = np.asarray([seat for _seed, seat, _opponent in jobs], dtype=np.int64)
        opponent_ids = tuple(opponent for _seed, _seat, opponent in jobs)
        candidate_sessions = [
            self._backend.structured_plan_session(self._environment) for _ in jobs
        ]
        opponent_plan_sessions = [
            self._backend.structured_plan_session(self._environment)
            for _ in opponent_ids
        ]
        self_play_indices = np.asarray(
            [index for index, value in enumerate(opponent_ids) if value == "self_play"],
            dtype=np.int64,
        )
        historical_indices = np.asarray(
            [
                index
                for index, value in enumerate(opponent_ids)
                if value == selected_history.identity
            ],
            dtype=np.int64,
        )
        if self_play_indices.size == 0 or historical_indices.size == 0:
            raise RuntimeError("structured-plan rollout omitted one self-play population arm")

        training_engines = [*engines]
        training_engines.extend(engines[int(index)] for index in self_play_indices)
        decision_sessions = [*candidate_sessions]
        decision_sessions.extend(
            opponent_plan_sessions[int(index)] for index in self_play_indices
        )
        decision_sessions.extend(
            opponent_plan_sessions[int(index)] for index in historical_indices
        )
        decision_engines = [*engines]
        decision_engines.extend(engines[int(index)] for index in self_play_indices)
        decision_engines.extend(engines[int(index)] for index in historical_indices)
        decision_players = np.concatenate(
            (
                seats,
                1 - seats[self_play_indices],
                1 - seats[historical_indices],
            )
        )
        decision_policy = np.concatenate(
            (
                np.zeros(len(jobs) + self_play_indices.size, dtype=np.int8),
                np.ones(historical_indices.size, dtype=np.int8),
            )
        )
        decision_episode = np.concatenate(
            (
                np.arange(len(jobs), dtype=np.int64),
                np.arange(len(jobs), len(training_jobs), dtype=np.int64),
                np.full(historical_indices.size, -1, dtype=np.int64),
            )
        )
        if len(training_engines) != len(training_jobs):
            raise RuntimeError("structured-plan training perspectives lost alignment")
        if not (
            len(decision_sessions)
            == len(decision_engines)
            == decision_players.size
            == decision_policy.size
            == decision_episode.size
        ):
            raise RuntimeError("structured-plan decision population lost alignment")

        exchange = self._exchange(self._device, len(decision_sessions))
        historical_exchange = (
            exchange
            if self._historical_device == self._device
            else self._exchange(self._historical_device, len(decision_sessions))
        )
        current_runtime = PlanPolicyRuntime(
            self._policy,
            self._action_generator,
            np.flatnonzero(decision_policy == 0).astype(np.int64, copy=False),
            decision_capacity=len(decision_sessions),
            inference_capacity=self._inference_batch_size,
            device=self._device,
            record_statistics=True,
            event_graphs=self._current_event_graphs,
        )
        historical_runtime = PlanPolicyRuntime(
            historical_policy,
            historical_generator,
            np.flatnonzero(decision_policy == 1).astype(np.int64, copy=False),
            decision_capacity=len(decision_sessions),
            inference_capacity=self._inference_batch_size,
            device=self._historical_device,
            record_statistics=False,
            event_graphs=self._historical_event_graphs,
        )
        blocks = new_blocks()
        event_sources = np.zeros(self._event_count, dtype=np.int64)
        primitive_turns = 0
        event_scan_seconds = 0.0
        rich_observation_seconds = 0.0
        inference_seconds = 0.0
        native_tick_seconds = 0.0
        historical_decisions = 0
        scheduler_rounds = 0
        inference_calls = 0
        inference_rows_total = 0
        ready_rows_total = 0
        started = time.perf_counter()
        done = np.zeros(len(jobs), dtype=np.bool_)
        self._policy.eval()

        while not bool(done.all()):
            scheduler_rounds += 1
            applied_this_round = 0
            event_started = time.perf_counter()
            panel = cast(
                Mapping[str, Any],
                self._backend.structured_plan_ready_observations_batch(
                    decision_sessions,
                    decision_engines,
                    decision_players,
                    self._cpu_workers,
                ),
            )
            ready_sources = np.asarray(panel["indices"], dtype=np.int64)
            ready_rows_total += int(ready_sources.size)
            event_scan_seconds += time.perf_counter() - event_started

            rich_started = time.perf_counter()
            rich = self._rich_observations(
                [decision_engines[int(index)] for index in ready_sources],
                decision_players[ready_sources],
                exchange,
            )
            rich_observation_seconds += time.perf_counter() - rich_started

            decision_started = time.perf_counter()
            ready_policy = decision_policy[ready_sources]
            expanded_events = _event_bits(
                np.asarray(panel["event_mask"], dtype=np.uint64),
                self._event_count,
            )
            scheduled: list[tuple[int, tuple[Any, ...]]] = []
            for policy_index, runtime, policy_exchange in (
                (0, current_runtime, exchange),
                (1, historical_runtime, historical_exchange),
            ):
                policy_rows = np.flatnonzero(ready_policy == policy_index).astype(
                    np.int64,
                    copy=False,
                )
                results = runtime.infer(
                    panel,
                    rich,
                    expanded_events,
                    ready_sources,
                    policy_rows,
                    policy_exchange,
                )
                scheduled.append((policy_index, results))
            for policy_index, results in scheduled:
                for result in results:
                    inference_calls += 1
                    inference_rows_total += int(result.sources.size)
                    chunk_rows = result.panel_rows
                    sources = result.sources
                    sessions = [decision_sessions[int(index)] for index in sources]
                    chunk_engines = [decision_engines[int(index)] for index in sources]
                    players = decision_players[sources]
                    frozen_policy = (
                        freeze_policy_output(result.policy_output)
                        if result.policy_output is not None
                        else None
                    )
                    frozen_actions = (
                        frozen_policy
                        if frozen_policy is not None
                        else freeze_plan_actions(result.actions)
                    )
                    self._backend.structured_plan_apply_batch(
                        sessions,
                        chunk_engines,
                        players,
                        frozen_actions.mode,
                        frozen_actions.line_operations,
                        frozen_actions.line_values,
                        frozen_actions.global_operation,
                        frozen_actions.global_values,
                        min(self._cpu_workers, int(sources.size)),
                    )
                    applied_this_round += int(sources.size)
                    if policy_index == 1:
                        if frozen_policy is not None:
                            raise RuntimeError(
                                "historical plan inference produced learner statistics"
                            )
                        historical_decisions += int(sources.size)
                        continue
                    if frozen_policy is None:
                        raise RuntimeError(
                            "current plan inference omitted learner statistics"
                        )
                    frozen = frozen_policy

                    episode_indices = decision_episode[sources]
                    if bool(np.any(episode_indices < 0)):
                        raise RuntimeError("historical decisions entered the PPO batch")
                    indices = np.arange(sources.size, dtype=np.int64)
                    selected_events = expanded_events[chunk_rows]
                    event_sources += selected_events.astype(np.int64).sum(axis=0)
                    blocks["board"].append(rich["board"][chunk_rows].copy())
                    blocks["units"].append(rich["units"][chunk_rows].copy())
                    blocks["global_features"].append(
                        rich["global_features"][chunk_rows].copy()
                    )
                    blocks["economic_state"].append(
                        rich["economic_state"][chunk_rows].copy()
                    )
                    blocks["features"].append(
                        np.asarray(panel["features"], dtype=np.float32)[chunk_rows]
                    )
                    blocks["journal"].append(
                        np.asarray(panel["journal"], dtype=np.float32)[chunk_rows]
                    )
                    blocks["events"].append(selected_events)
                    blocks["active_lines"].append(
                        np.asarray(panel["active_lines"], dtype=np.int64)[chunk_rows]
                    )
                    blocks["active_line_mask"].append(
                        np.asarray(panel["active_line_mask"], dtype=np.bool_)[chunk_rows]
                    )
                    blocks["global_plan"].append(
                        np.asarray(panel["global_plan"], dtype=np.int64)[chunk_rows]
                    )
                    blocks["mode"].append(frozen.mode)
                    blocks["line_operations"].append(frozen.line_operations)
                    blocks["line_values"].append(frozen.line_values)
                    blocks["global_operation"].append(frozen.global_operation)
                    blocks["global_values"].append(frozen.global_values)
                    record_policy(blocks, frozen, indices)
                    blocks["episode_index"].append(episode_indices)
                    blocks["start_step"].append(
                        np.fromiter(
                            (
                                int(decision_engines[int(source)].step_index)
                                for source in sources
                            ),
                            dtype=np.int64,
                            count=indices.size,
                        )
                    )
            inference_seconds += time.perf_counter() - decision_started

            native_started = time.perf_counter()
            done, advanced = self._native_advance(
                engines,
                seats,
                candidate_sessions,
                opponent_plan_sessions,
            )
            native_tick_seconds += time.perf_counter() - native_started
            primitive_turns += int(advanced.sum())
            if (
                not bool(done.all())
                and applied_this_round == 0
                and not bool(advanced.any())
            ):
                raise RuntimeError("structured-plan native scheduler made no progress")

        elapsed = time.perf_counter() - started
        episode_index = np.concatenate(blocks["episode_index"]).astype(np.int64, copy=False)
        start_steps = np.concatenate(blocks["start_step"]).astype(np.int64, copy=False)
        durations = np.empty_like(start_steps)
        for episode in range(len(training_jobs)):
            episode_rows = np.flatnonzero(episode_index == episode)
            terminal_step = int(training_engines[episode].step_index)
            ends = np.append(start_steps[episode_rows][1:], terminal_step)
            durations[episode_rows] = ends - start_steps[episode_rows]

        games: list[PlanGameResult] = []
        outcomes = np.empty(len(training_jobs), dtype=np.float32)
        episode_ids: list[str] = []
        for index, ((seed, seat, opponent_id), engine) in enumerate(
            zip(training_jobs, training_engines, strict=True)
        ):
            opponent_cash = float(engine.money(1 - seat))
            terminal_cash = float(engine.money(seat))
            outcomes[index] = int(terminal_cash > opponent_cash) - int(
                terminal_cash < opponent_cash
            )
            episode_ids.append(f"{opponent_id}:{seed}:{seat}")
        for offset, game_index in enumerate(self_play_indices):
            perspective = len(jobs) + offset
            if outcomes[perspective] != -outcomes[int(game_index)]:
                raise RuntimeError("self-play training outcomes lost seat symmetry")
        for index, ((seed, seat, opponent_id), engine) in enumerate(
            zip(jobs, engines, strict=True)
        ):
            terminal_cash = float(engine.money(seat))
            opponent_cash = float(engine.money(1 - seat))
            games.append(
                PlanGameResult(
                    episode_ids[index],
                    opponent_id,
                    seed,
                    seat,
                    int(outcomes[index]),
                    terminal_cash,
                    opponent_cash,
                )
            )
        batch = build_batch(
            blocks,
            episode_index,
            start_steps,
            durations,
            outcomes,
            episode_ids,
            self._contract,
        )
        graph_counters_after = self._graph_counters(
            self._current_event_graphs,
            self._historical_event_graphs,
        )
        graph_counters = tuple(
            after - before
            for before, after in zip(
                graph_counters_before,
                graph_counters_after,
                strict=True,
            )
        )
        return PlanRolloutResult(
            batch=batch,
            games=tuple(games),
            historical_opponent_id=selected_history.identity,
            historical_opponent_update=selected_history.update,
            diagnostics={
                "games": len(games),
                "training_episodes": batch.episodes,
                "population": self._population.report(selected_history),
                "current_games": int(self_play_indices.size),
                "historical_games": int(historical_indices.size),
                "primitive_turns": primitive_turns,
                "actor_decisions": batch.decisions,
                "historical_opponent_decisions": historical_decisions,
                "inference_devices": [
                    str(self._device),
                    str(self._historical_device),
                ],
                "scheduler_rounds": scheduler_rounds,
                "inference_calls": inference_calls,
                "event_cuda_graph_captures": graph_counters[0],
                "event_cuda_graph_replays": graph_counters[1],
                "event_cuda_graph_eager_calls": graph_counters[2],
                "mean_ready_rows_per_round": ready_rows_total / scheduler_rounds,
                "mean_inference_batch": inference_rows_total / max(inference_calls, 1),
                "day_history_advances": current_runtime.day_advances,
                "historical_day_history_advances": historical_runtime.day_advances,
                "actor_decisions_per_game": batch.decisions / len(games),
                "actor_decisions_per_training_episode": (batch.decisions / batch.episodes),
                "training_outcomes": {
                    "wins": int(np.count_nonzero(outcomes > 0)),
                    "ties": int(np.count_nonzero(outcomes == 0)),
                    "losses": int(np.count_nonzero(outcomes < 0)),
                },
                "mean_plan_duration": float(np.mean(durations)),
                "p95_plan_duration": float(np.percentile(durations, 95)),
                "mean_patch_lines": float(
                    (batch.actions.line_operations != 0).float().sum(dim=1).mean()
                ),
                "mean_active_lines": float(batch.inputs.active_line_mask.float().sum(dim=1).mean()),
                "elapsed_seconds": elapsed,
                "games_per_second": len(games) / max(elapsed, 1e-9),
                "turns_per_second": primitive_turns / max(elapsed, 1e-9),
                "decisions_per_second": (
                    (batch.decisions + historical_decisions) / max(elapsed, 1e-9)
                ),
                "training_decisions_per_second": (
                    batch.decisions / max(elapsed, 1e-9)
                ),
                "primitive_turns_per_second": primitive_turns / max(elapsed, 1e-9),
                "event_scan_seconds": event_scan_seconds,
                "rich_observation_seconds": rich_observation_seconds,
                "inference_seconds": inference_seconds,
                "native_tick_seconds": native_tick_seconds,
                "host_orchestration_seconds": max(
                    0.0,
                    elapsed
                    - event_scan_seconds
                    - rich_observation_seconds
                    - inference_seconds
                    - native_tick_seconds,
                ),
                "event_source_counts": {
                    str(index): int(value) for index, value in enumerate(event_sources) if value > 0
                },
            },
        )


__all__ = ["PlanGameResult", "PlanRolloutResult", "StructuredPlanRolloutCollector"]
