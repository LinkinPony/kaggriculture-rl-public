"""Batched native population rollout for atomic-effect policies."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.native_batch import (
    create_native_opponent_session,
    step_native_opponent_batch,
)
from kagg_revue.policy.effects.contract import NativeEffectContract
from kagg_revue.policy.effects.data import tensor_state_from_native
from kagg_revue.policy.effects.gpu import (
    EffectDecisionGraphPool,
    EffectTurnGraph,
    PinnedEffectTurnStaging,
)
from kagg_revue.policy.effects.model import EffectActorCritic, EffectPolicy
from kagg_revue.policy.transformer import HistoryState
from kagg_revue.rl.effects.data import EffectRolloutBatch
from kagg_revue.rl.effects.observer import EffectRolloutObserver
from kagg_revue.rl.rollout.batch import Job


def _integer(values: Mapping[str, object], name: str) -> int:
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"effect environment {name} must be an integer")
    return value


def _autocast(device: torch.device) -> Any:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


def _compact_widths(value: object) -> tuple[int, int, int, int, int, int]:
    """Validate the native compact-observation width tuple."""
    if not isinstance(value, tuple) or len(value) != 6:
        raise TypeError("effect compact observation changed its ABI")
    values = tuple(int(item) for item in value)
    return cast(tuple[int, int, int, int, int, int], values)


@dataclass(frozen=True)
class EffectGameResult:
    """Direct terminal result for one trained policy perspective."""

    episode_id: str
    seed: int
    seat: int
    opponent_id: str
    outcome: int
    terminal_cash: float
    opponent_cash: float


@dataclass(frozen=True)
class EffectMatchResult:
    """Complete direct outcomes and coarse hot-path timings."""

    games: tuple[EffectGameResult, ...]
    diagnostics: dict[str, object]


@dataclass(frozen=True)
class EffectRolloutResult:
    """Complete episodes, factor tape, and coarse hot-path timings."""

    batch: EffectRolloutBatch
    games: tuple[EffectGameResult, ...]
    diagnostics: dict[str, object]


@dataclass
class _Perspective:
    engine: Any
    seed: int
    seat: int
    opponent_id: str
    session: Any


@dataclass
class _PhysicalGame:
    """One complete engine and the actor rows that control its candidate seats."""

    engine: Any
    seed: int
    opponent_id: str
    candidate_seat: int | None
    opponent_session: Any | None
    actor_rows: tuple[int, ...]


class EffectRolloutCollector:
    """Run complete current-policy games through the native effect batch."""

    def __init__(
        self,
        backend: BackendApi,
        model: EffectActorCritic,
        contract: NativeEffectContract,
        environment: Mapping[str, object],
        *,
        unit_limit: int,
        cpu_workers: int,
        device: torch.device,
        action_generator: torch.Generator,
        maximum_graph_variants: int = 48,
        sample_actions: bool = True,
        observer: EffectRolloutObserver | None = None,
        retain_behavior_distributions: bool = True,
    ) -> None:
        """Bind exact native state, model ABI, and sampling stream."""
        self._backend = backend
        self._model = model
        self._contract = contract
        self._environment = dict(environment)
        self._unit_limit = unit_limit
        self._workers = cpu_workers
        self._device = device
        self._generator = action_generator
        self._maximum_graph_variants = maximum_graph_variants
        self._sample_actions = sample_actions
        self._observer = observer
        self._retain_behavior_distributions = retain_behavior_distributions
        self._decision_graphs: EffectDecisionGraphPool | None = None
        self._turn_staging: PinnedEffectTurnStaging | None = None
        self._turn_graph: EffectTurnGraph | None = None
        architecture = model.actor.architecture
        if architecture.unit_shape[1] != unit_limit:
            raise ValueError("effect collector unit limit differs from the actor")
        if architecture.board_shape[-1] != contract.board_size:
            raise ValueError("effect collector board size differs from the actor")
        if _integer(self._environment, "episodeSteps") - 1 > architecture.max_history:
            raise ValueError("effect rollout exceeds actor history capacity")

    def _new_session(self) -> Any:
        return self._backend.effect_policy_session(
            self._environment,
            self._unit_limit,
            self._model.actor.architecture.maximum_quantity,
            task_conditioning=self._model.effects.architecture.task_conditioning,
            destination_tasks=self._model.effects.architecture.destination_tasks_enabled,
        )

    def _games(self, jobs: Sequence[Job]) -> tuple[list[_PhysicalGame], list[_Perspective]]:
        """Create complete engines while retaining only candidate-policy rows."""
        if not jobs or len(set(jobs)) != len(jobs):
            raise ValueError("effect rollout jobs must be nonempty and unique")
        assignment: dict[int, str] = {}
        external_seats: dict[tuple[int, str], set[int]] = {}
        for raw_seed, seat, opponent_id in jobs:
            seed = int(raw_seed)
            if seed < 0 or seat not in (0, 1) or not opponent_id:
                raise ValueError("effect rollout job is invalid")
            previous = assignment.setdefault(seed, opponent_id)
            if previous != opponent_id:
                raise ValueError("effect rollout seed cannot target multiple opponents")
            if opponent_id == "self_play":
                if seat != 0:
                    raise ValueError("effect self-play uses one seed-level job")
            else:
                if opponent_id not in self._backend.native_opponent_batch_steps:
                    raise ValueError(f"effect native opponent is unavailable: {opponent_id}")
                external_seats.setdefault((seed, opponent_id), set()).add(seat)
        if any(seats != {0, 1} for seats in external_seats.values()):
            raise ValueError("effect external opponents require paired candidate seats")

        games: list[_PhysicalGame] = []
        perspectives: list[_Perspective] = []
        maximum_orders = _integer(self._environment, "maxMarketOrdersPerTurn")
        for raw_seed, seat, opponent_id in jobs:
            seed = int(raw_seed)
            engine = self._backend.engine(seed, self._environment)
            first_row = len(perspectives)
            if opponent_id == "self_play":
                for player in (0, 1):
                    perspectives.append(
                        _Perspective(
                            engine=engine,
                            seed=seed,
                            seat=player,
                            opponent_id=opponent_id,
                            session=self._new_session(),
                        )
                    )
                games.append(
                    _PhysicalGame(
                        engine=engine,
                        seed=seed,
                        opponent_id=opponent_id,
                        candidate_seat=None,
                        opponent_session=None,
                        actor_rows=(first_row, first_row + 1),
                    )
                )
                continue
            perspectives.append(
                _Perspective(
                    engine=engine,
                    seed=seed,
                    seat=seat,
                    opponent_id=opponent_id,
                    session=self._new_session(),
                )
            )
            games.append(
                _PhysicalGame(
                    engine=engine,
                    seed=seed,
                    opponent_id=opponent_id,
                    candidate_seat=seat,
                    opponent_session=create_native_opponent_session(
                        opponent_id,
                        maximum_orders,
                    ),
                    actor_rows=(first_row,),
                )
            )
        return games, perspectives

    def _advance_games(
        self,
        games: list[_PhysicalGame],
        compiled: Mapping[str, Any],
    ) -> None:
        tokens = np.asarray(compiled["tokens"], dtype=np.int64)
        quantities = np.asarray(compiled["quantities"], dtype=np.int64)
        counts = np.asarray(compiled["decision_counts"], dtype=np.int64)
        units = np.asarray(compiled["unit_counts"], dtype=np.int64)
        self_play = [game for game in games if game.opponent_id == "self_play"]
        if self_play:
            rows = np.asarray(
                [row for game in self_play for row in game.actor_rows],
                dtype=np.int64,
            )
            self._backend.engine_step_numeric_batch(
                [game.engine for game in self_play],
                tokens[rows].reshape(len(self_play), 2, tokens.shape[1]),
                quantities[rows].reshape(len(self_play), 2, quantities.shape[1]),
                counts[rows].reshape(len(self_play), 2),
                units[rows].reshape(len(self_play), 2),
                min(self._workers, len(self_play)),
            )
        external = [game for game in games if game.opponent_id != "self_play"]
        if external:
            rows = np.asarray([game.actor_rows[0] for game in external], dtype=np.int64)
            step_native_opponent_batch(
                self._backend,
                [game.engine for game in external],
                np.asarray([game.candidate_seat for game in external], dtype=np.int64),
                [game.opponent_id for game in external],
                [game.opponent_session for game in external],
                tokens[rows],
                quantities[rows],
                counts[rows],
                units[rows],
                min(self._workers, len(external)),
            )

    @staticmethod
    def _strategy_rows(strategy: Tensor | None, rows: Tensor) -> Tensor | None:
        return None if strategy is None else strategy.index_select(0, rows)

    def collect(self, seeds: Sequence[int]) -> EffectRolloutResult:
        """Collect current-policy self-play for the supplied unique seeds."""
        if not seeds or len(set(seeds)) != len(seeds):
            raise ValueError("effect rollout seeds must be nonempty and unique")
        return self.collect_jobs(tuple((int(seed), 0, "self_play") for seed in seeds))

    def _run_jobs(
        self,
        jobs: Sequence[Job],
        *,
        record_rollout: bool,
    ) -> tuple[EffectRolloutBatch | None, tuple[EffectGameResult, ...], dict[str, object]]:
        """Run one exact panel, optionally retaining its learner tape."""
        games_state, perspectives = self._games(jobs)
        if self._observer is not None and not record_rollout:
            raise ValueError("effect rollout observer requires a retained factor tape")
        engines = [game.engine for game in games_state]
        batch_size = len(perspectives)
        players = np.asarray([game.seat for game in perspectives], dtype=np.int64)
        player_list = players.tolist()
        perspective_engines = [game.engine for game in perspectives]
        sessions = [game.session for game in perspectives]
        if self._observer is not None:
            self._observer.start_group(
                [(game.seed, game.seat) for game in perspectives],
                perspective_engines,
                players,
                _integer(self._environment, "episodeSteps") - 1,
            )
        native_batch = self._backend.effect_policy_batch(
            sessions,
            perspective_engines,
            players,
            self._workers,
            record_rollout,
        )
        architecture = self._model.actor.architecture
        turn_capacity = _integer(self._environment, "episodeSteps") - 1
        histories: HistoryState | None = None
        strategy_state: Tensor | None = None
        if self._device.type == "cuda":
            if self._turn_staging is None:
                self._turn_staging = PinnedEffectTurnStaging(
                    architecture,
                    batch_size,
                    self._device,
                )
                self._decision_graphs = EffectDecisionGraphPool(
                    self._model.effects,
                    self._generator,
                    batch_size,
                    sample=self._sample_actions,
                    maximum_variants=self._maximum_graph_variants,
                    retain_behavior_distributions=(self._retain_behavior_distributions),
                )
            elif self._turn_staging.inputs.board.shape[0] != batch_size:
                raise ValueError("effect rollout batch size changed after CUDA graph capture")
            self._turn_staging.reset_episode()
            if self._turn_graph is not None:
                self._turn_graph.reset_episode()
            previous_tokens = self._turn_staging.inputs.previous_actions
            previous_quantities = self._turn_staging.inputs.previous_quantities
            previous_mask = self._turn_staging.inputs.previous_mask
        else:
            previous_tokens = torch.zeros(
                (batch_size, architecture.max_decisions),
                dtype=torch.long,
                device=self._device,
            )
            previous_quantities = torch.zeros_like(previous_tokens)
            previous_mask = torch.zeros_like(previous_tokens, dtype=torch.bool)
        board_store: NDArray[np.float16] | None = None
        unit_store: NDArray[np.float16] | None = None
        global_store: NDArray[np.float32] | None = None
        economic_store: NDArray[np.int32] | None = None
        action_store = (
            np.zeros(
                (batch_size, turn_capacity, architecture.max_decisions),
                dtype=np.int64,
            )
            if record_rollout
            else None
        )
        quantity_store = None if action_store is None else np.zeros_like(action_store)
        action_counts = (
            np.zeros((batch_size, turn_capacity), dtype=np.int64) if record_rollout else None
        )
        turn = 0
        factors = 0
        policy_factors = 0
        encode_seconds = 0.0
        observation_seconds = 0.0
        inference_seconds = 0.0
        transition_seconds = 0.0
        compilation_seconds = 0.0
        environment_seconds = 0.0
        maximum_actor_seconds = 0.0
        actor_total_seconds = 0.0
        actor_overage_seconds = 0.0
        started = time.perf_counter()
        self._model.eval()
        all_rows = np.arange(batch_size, dtype=np.int64)
        market_limit = _integer(self._environment, "maxMarketOrdersPerTurn")
        graphs = self._decision_graphs
        if graphs is not None:
            graphs.start_recording(
                batch_size * turn_capacity * (self._unit_limit + market_limit + 1)
            )
        graph_capture_before = 0.0 if graphs is None else graphs.capture_seconds
        graph_variants_before = 0 if graphs is None else graphs.variant_count
        turn_capture_before = 0.0 if self._turn_graph is None else self._turn_graph.capture_seconds

        while not all(bool(engine.done) for engine in engines):
            if turn >= turn_capacity:
                raise RuntimeError("effect rollout exceeded configured episode capacity")
            actor_started = time.perf_counter()
            encoded_started = time.perf_counter()
            turn_staging = self._turn_staging
            if turn_staging is None:
                raw = self._backend.engine_policy_turn_inputs(
                    perspective_engines,
                    player_list,
                    self._unit_limit,
                    self._workers,
                )
                board_np = np.asarray(raw[0], dtype=np.float16)
                units_np = np.asarray(raw[1], dtype=np.float16)
                global_np = np.asarray(raw[2], dtype=np.float32)
                economic_np = np.asarray(raw[4], dtype=np.int32)
            else:
                turn_staging.install_native(
                    self._backend,
                    perspective_engines,
                    player_list,
                    self._unit_limit,
                    self._workers,
                )
                board_np = turn_staging.board
                units_np = turn_staging.units
                global_np = turn_staging.global_features
                economic_np = turn_staging.economic_state
            if record_rollout and board_store is None:
                board_store = np.empty(
                    (batch_size, turn_capacity, *board_np.shape[1:]),
                    dtype=np.float16,
                )
                unit_store = np.empty(
                    (batch_size, turn_capacity, *units_np.shape[1:]),
                    dtype=np.float16,
                )
                global_store = np.empty(
                    (batch_size, turn_capacity, global_np.shape[1]),
                    dtype=np.float32,
                )
                economic_store = np.empty(
                    (batch_size, turn_capacity, economic_np.shape[1]),
                    dtype=np.int32,
                )
            if record_rollout:
                if (
                    board_store is None
                    or unit_store is None
                    or global_store is None
                    or economic_store is None
                ):
                    raise RuntimeError("effect rollout storage initialization failed")
                board_store[:, turn] = board_np
                unit_store[:, turn] = units_np
                global_store[:, turn] = global_np
                economic_store[:, turn] = economic_np
            if self._observer is not None:
                self._observer.begin_turn(
                    perspective_engines,
                    players,
                    turn,
                )
            if turn_staging is None:
                board = torch.as_tensor(board_np, device=self._device)
                units = torch.as_tensor(units_np, device=self._device)
                global_features = torch.as_tensor(global_np, device=self._device)
                economic = (
                    torch.as_tensor(economic_np, device=self._device)
                    if architecture.economic_feature_version is not None
                    else None
                )
                with torch.inference_mode(), _autocast(self._device):
                    (
                        context,
                        tile_context,
                        strategy,
                        histories,
                        strategy_state,
                    ) = self._model.start_turn(
                        board,
                        units,
                        global_features,
                        previous_tokens,
                        previous_quantities,
                        previous_mask,
                        histories,
                        strategy_state,
                        economic,
                    )
            else:
                if self._turn_graph is None:
                    self._turn_graph = EffectTurnGraph(
                        self._model.actor,
                        turn_staging.inputs,
                        self._model.effects.architecture.tile_count,
                    )
                context, tile_context, strategy = self._turn_graph.replay(turn_staging.inputs)
                if graphs is None:
                    raise RuntimeError("effect CUDA turn has no decision graph pool")
                graphs.start_turn(context, tile_context, strategy)
            encode_seconds += time.perf_counter() - encoded_started
            native_batch.reset_transaction()

            if graphs is None:
                observation_started = time.perf_counter()
                payload = cast(Mapping[str, Any], native_batch.observe(all_rows))
                observation_seconds += time.perf_counter() - observation_started
                state = tensor_state_from_native(payload, self._device)
                inference_started = time.perf_counter()
                with torch.inference_mode(), _autocast(self._device):
                    root = self._model.effects(
                        context,
                        tile_context,
                        state,
                        strategy,
                        mask_candidates=False,
                    )
                root_logits = root.candidate_logits
                root_values = root.value
                inference_seconds += time.perf_counter() - inference_started

                active = all_rows
                work_iterations = 0
                while active.size:
                    candidate_mask_np = np.asarray(payload["candidate_mask"], dtype=np.bool_)
                    policy_factors += int(np.count_nonzero(candidate_mask_np.sum(axis=1) > 1))
                    width = candidate_mask_np.shape[1]
                    active_tensor = torch.as_tensor(active, device=self._device)
                    candidate_mask = torch.as_tensor(
                        candidate_mask_np,
                        device=self._device,
                        dtype=torch.bool,
                    )
                    inference_started = time.perf_counter()
                    with torch.inference_mode(), _autocast(self._device):
                        work_logits = root_logits.index_select(0, active_tensor)[:, :width]
                        if self._model.effects.architecture.task_conditioning:
                            work_logits = self._model.effects.forward_logits(
                                context.index_select(0, active_tensor),
                                tile_context.index_select(0, active_tensor),
                                tensor_state_from_native(payload, self._device),
                                self._strategy_rows(strategy, active_tensor),
                            )
                        selection = EffectPolicy.select_logits(
                            work_logits,
                            root_values.index_select(0, active_tensor),
                            sample=self._sample_actions,
                            candidate_mask=candidate_mask,
                            generator=self._generator,
                            compute_entropy=False,
                        )
                    selected = selection.indices.cpu().numpy().astype(np.int64, copy=False)
                    log_probability = (
                        selection.log_probability.cpu().numpy().astype(np.float32, copy=False)
                    )
                    values = selection.value.cpu().numpy().astype(np.float32, copy=False)
                    inference_seconds += time.perf_counter() - inference_started
                    transition_started = time.perf_counter()
                    phases = np.asarray(
                        native_batch.advance(
                            selected,
                            log_probability,
                            values,
                            turn,
                        ),
                        dtype=np.int64,
                    )
                    transition_seconds += time.perf_counter() - transition_started
                    factors += int(active.size)
                    active = active[phases == self._contract.work_phase]
                    work_iterations += 1
                    if work_iterations > self._unit_limit + 1:
                        raise RuntimeError("effect ranked work set did not terminate")
                    if active.size:
                        observation_started = time.perf_counter()
                        payload = cast(Mapping[str, Any], native_batch.observe(active))
                        observation_seconds += time.perf_counter() - observation_started

                active = all_rows
                market_iterations = 0
                while active.size:
                    observation_started = time.perf_counter()
                    payload = cast(Mapping[str, Any], native_batch.observe(active))
                    observation_seconds += time.perf_counter() - observation_started
                    candidate_mask_np = np.asarray(payload["candidate_mask"], dtype=np.bool_)
                    policy_factors += int(np.count_nonzero(candidate_mask_np.sum(axis=1) > 1))
                    state = tensor_state_from_native(payload, self._device)
                    active_tensor = torch.as_tensor(active, device=self._device)
                    inference_started = time.perf_counter()
                    with torch.inference_mode(), _autocast(self._device):
                        logits = self._model.effects.forward_logits(
                            context.index_select(0, active_tensor),
                            tile_context.index_select(0, active_tensor),
                            state,
                            self._strategy_rows(strategy, active_tensor),
                        )
                        selection = EffectPolicy.select_logits(
                            logits,
                            root_values.index_select(0, active_tensor),
                            sample=self._sample_actions,
                            generator=self._generator,
                            compute_entropy=False,
                        )
                    selected = selection.indices.cpu().numpy().astype(np.int64, copy=False)
                    log_probability = (
                        selection.log_probability.cpu().numpy().astype(np.float32, copy=False)
                    )
                    values = selection.value.cpu().numpy().astype(np.float32, copy=False)
                    inference_seconds += time.perf_counter() - inference_started
                    transition_started = time.perf_counter()
                    phases = np.asarray(
                        native_batch.advance(
                            selected,
                            log_probability,
                            values,
                            turn,
                        ),
                        dtype=np.int64,
                    )
                    transition_seconds += time.perf_counter() - transition_started
                    factors += int(active.size)
                    active = active[phases != self._contract.done_phase]
                    market_iterations += 1
                    if market_iterations > market_limit + 1:
                        raise RuntimeError("effect market list did not terminate")
            else:
                observation_started = time.perf_counter()
                widths = _compact_widths(native_batch.observe_compact(all_rows))
                observation_seconds += time.perf_counter() - observation_started
                policy_factors += widths[5]
                inference_started = time.perf_counter()
                selected, behavior_offset = graphs.decode_root(
                    widths,
                    all_rows,
                    native_batch,
                )
                inference_seconds += time.perf_counter() - inference_started
                transition_started = time.perf_counter()
                phases = np.asarray(
                    native_batch.advance_indexed(
                        selected,
                        behavior_offset,
                        turn,
                    ),
                    dtype=np.int64,
                )
                transition_seconds += time.perf_counter() - transition_started
                factors += batch_size
                active = all_rows[phases == self._contract.work_phase]
                work_iterations = 1
                while active.size:
                    if work_iterations > self._unit_limit:
                        raise RuntimeError("effect ranked work set did not terminate")
                    observation_started = time.perf_counter()
                    widths = _compact_widths(native_batch.observe_compact(active))
                    observation_seconds += time.perf_counter() - observation_started
                    policy_factors += widths[5]
                    inference_started = time.perf_counter()
                    selected, behavior_offset = graphs.decode_work(
                        widths,
                        active,
                        native_batch,
                    )
                    inference_seconds += time.perf_counter() - inference_started
                    transition_started = time.perf_counter()
                    phases = np.asarray(
                        native_batch.advance_indexed(
                            selected,
                            behavior_offset,
                            turn,
                        ),
                        dtype=np.int64,
                    )
                    transition_seconds += time.perf_counter() - transition_started
                    factors += int(active.size)
                    active = active[phases == self._contract.work_phase]
                    work_iterations += 1

                active = all_rows
                market_iterations = 0
                while active.size:
                    if market_iterations > market_limit:
                        raise RuntimeError("effect market list did not terminate")
                    observation_started = time.perf_counter()
                    widths = _compact_widths(native_batch.observe_compact(active))
                    observation_seconds += time.perf_counter() - observation_started
                    policy_factors += widths[5]
                    inference_started = time.perf_counter()
                    selected, behavior_offset = graphs.decode_market(
                        widths,
                        active,
                        native_batch,
                    )
                    inference_seconds += time.perf_counter() - inference_started
                    transition_started = time.perf_counter()
                    phases = np.asarray(
                        native_batch.advance_indexed(
                            selected,
                            behavior_offset,
                            turn,
                        ),
                        dtype=np.int64,
                    )
                    transition_seconds += time.perf_counter() - transition_started
                    factors += int(active.size)
                    active = active[phases != self._contract.done_phase]
                    market_iterations += 1

            compilation_started = time.perf_counter()
            compiled = cast(Mapping[str, Any], native_batch.actions())
            tokens = np.asarray(compiled["tokens"], dtype=np.int64)
            quantities = np.asarray(compiled["quantities"], dtype=np.int64)
            counts = np.asarray(compiled["decision_counts"], dtype=np.int64)
            if tokens.shape[1] > architecture.max_decisions:
                raise RuntimeError("compiled effect action exceeds actor history capacity")
            if record_rollout:
                if action_store is None or quantity_store is None or action_counts is None:
                    raise RuntimeError("effect rollout action storage was not initialized")
                action_store[:, turn, : tokens.shape[1]] = tokens
                quantity_store[:, turn, : quantities.shape[1]] = quantities
                action_counts[:, turn] = counts
            if turn_staging is None:
                previous_tokens.zero_()
                previous_quantities.zero_()
                previous_mask.zero_()
                previous_tokens[:, : tokens.shape[1]] = torch.as_tensor(tokens, device=self._device)
                previous_quantities[:, : quantities.shape[1]] = torch.as_tensor(
                    quantities, device=self._device
                )
                positions = torch.arange(architecture.max_decisions, device=self._device)
                previous_mask.copy_(
                    positions[None] < torch.as_tensor(counts, device=self._device)[:, None]
                )
            else:
                turn_staging.install_previous(tokens, quantities, counts)
            compilation_seconds += time.perf_counter() - compilation_started
            actor_seconds = time.perf_counter() - actor_started
            maximum_actor_seconds = max(maximum_actor_seconds, actor_seconds)
            actor_total_seconds += actor_seconds
            actor_overage_seconds += max(0.0, actor_seconds - 1.0)
            environment_started = time.perf_counter()
            self._advance_games(games_state, compiled)
            environment_seconds += time.perf_counter() - environment_started
            turn += 1

        finalization_started = time.perf_counter()
        outcomes = np.empty(batch_size, dtype=np.float32)
        games: list[EffectGameResult] = []
        for index, game in enumerate(perspectives):
            terminal_cash = float(game.engine.money(game.seat))
            opponent_cash = float(game.engine.money(1 - game.seat))
            outcome = int(terminal_cash > opponent_cash) - int(terminal_cash < opponent_cash)
            outcomes[index] = outcome
            games.append(
                EffectGameResult(
                    episode_id=f"{game.opponent_id}:{game.seed}:{game.seat}",
                    seed=game.seed,
                    seat=game.seat,
                    opponent_id=game.opponent_id,
                    outcome=outcome,
                    terminal_cash=terminal_cash,
                    opponent_cash=opponent_cash,
                )
            )
        behavior_export_started = time.perf_counter()
        device_behavior = None if graphs is None else graphs.finish_recording()
        behavior_export_seconds = time.perf_counter() - behavior_export_started
        native_export_seconds = 0.0
        batch_wrap_seconds = 0.0
        critic_seconds = 0.0
        buckets: list[Mapping[str, Any]] = []
        rollout_batch: EffectRolloutBatch | None = None
        if record_rollout:
            if any(
                value is None
                for value in (
                    board_store,
                    unit_store,
                    global_store,
                    economic_store,
                    action_store,
                    quantity_store,
                    action_counts,
                )
            ):
                raise RuntimeError("effect rollout completed without an official turn")
            native_export_started = time.perf_counter()
            buckets = cast(list[Mapping[str, Any]], native_batch.export_rollout_buckets())
            native_export_seconds = time.perf_counter() - native_export_started
            if self._observer is not None:
                buckets = self._observer.relabel_buckets(buckets)
            batch_wrap_started = time.perf_counter()
            rollout_batch = EffectRolloutBatch.from_native_buckets(
                board=cast(NDArray[np.float16], board_store)[:, :turn],
                units=cast(NDArray[np.float16], unit_store)[:, :turn],
                global_features=cast(NDArray[np.float32], global_store)[:, :turn],
                economic_state=cast(NDArray[np.int32], economic_store)[:, :turn],
                actions=cast(NDArray[np.int64], action_store)[:, :turn],
                quantities=cast(NDArray[np.int64], quantity_store)[:, :turn],
                decision_counts=cast(NDArray[np.int64], action_counts)[:, :turn],
                decisions=buckets,
                outcomes=outcomes,
                device_behavior=device_behavior,
            )
            batch_wrap_seconds = time.perf_counter() - batch_wrap_started
            if self._model.critic is not None:
                from kagg_revue.rl.effects.value import attach_behavior_values

                critic_started = time.perf_counter()
                rollout_batch = attach_behavior_values(self._model.critic, rollout_batch)
                critic_seconds = time.perf_counter() - critic_started
            if self._observer is not None:
                self._observer.finish_group()
        finalization_seconds = time.perf_counter() - finalization_started
        elapsed = time.perf_counter() - started
        return (
            rollout_batch,
            tuple(games),
            {
                "physical_games": len(engines),
                "episodes": batch_size,
                "official_turns": batch_size * turn,
                "policy_factors": policy_factors,
                "factors": factors,
                "native_rollout_buckets": len(buckets),
                "maximum_batched_actor_seconds": maximum_actor_seconds,
                "batched_actor_total_seconds": actor_total_seconds,
                "batched_actor_overage_seconds_at_one_second": actor_overage_seconds,
                "encode_seconds": encode_seconds,
                "native_observation_seconds": observation_seconds,
                "inference_seconds": inference_seconds,
                "native_transition_seconds": transition_seconds,
                "action_compilation_seconds": compilation_seconds,
                "environment_seconds": environment_seconds,
                "finalization_seconds": finalization_seconds,
                "behavior_export_seconds": behavior_export_seconds,
                "native_export_seconds": native_export_seconds,
                "batch_wrap_seconds": batch_wrap_seconds,
                "critic_seconds": critic_seconds,
                "elapsed_seconds": elapsed,
                "physical_games_per_second": len(engines) / elapsed,
                "device": str(self._device),
                "optimized_cuda_path": graphs is not None,
                "graph_capture_seconds": (
                    0.0 if graphs is None else graphs.capture_seconds - graph_capture_before
                ),
                "graph_variants_created": (
                    0 if graphs is None else graphs.variant_count - graph_variants_before
                ),
                "turn_graph_capture_seconds": (
                    0.0
                    if self._turn_graph is None
                    else self._turn_graph.capture_seconds - turn_capture_before
                ),
            },
        )

    def collect_jobs(self, jobs: Sequence[Job]) -> EffectRolloutResult:
        """Collect an exact self-play/native-opponent learner panel."""
        batch, games, diagnostics = self._run_jobs(jobs, record_rollout=True)
        if batch is None:
            raise RuntimeError("effect rollout failed to retain its learner tape")
        return EffectRolloutResult(batch=batch, games=games, diagnostics=diagnostics)

    def evaluate_jobs(self, jobs: Sequence[Job]) -> EffectMatchResult:
        """Run complete matches without retaining training-only factor tapes."""
        batch, games, diagnostics = self._run_jobs(jobs, record_rollout=False)
        if batch is not None:
            raise RuntimeError("effect evaluation unexpectedly retained a learner tape")
        return EffectMatchResult(games=games, diagnostics=diagnostics)

    def close(self) -> None:
        """Release graph-private CUDA allocations."""
        if self._device.type == "cuda":
            torch.cuda.synchronize(self._device)
        if self._decision_graphs is not None:
            self._decision_graphs.close()
        if self._turn_graph is not None:
            self._turn_graph.close()
        self._decision_graphs = None
        self._turn_graph = None
        self._turn_staging = None


__all__ = [
    "EffectGameResult",
    "EffectMatchResult",
    "EffectRolloutCollector",
    "EffectRolloutResult",
]
