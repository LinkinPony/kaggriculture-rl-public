"""Concurrent scheduling around batched actor turn sampling."""

from __future__ import annotations

import gc
import time
from collections.abc import Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from contextlib import nullcontext, suppress
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.policy.runtime import NumericAction
from kagg_revue.rl.data import RolloutMatch, Trajectory
from kagg_revue.rl.opening.noise import (
    OpeningResidual,
    PerspectiveKey,
    normalized_action_head_direction,
)
from kagg_revue.rl.outcome import OutcomeActorCritic
from kagg_revue.rl.rollout.batch import (
    Job,
    OfficialFactory,
    ProgressCallback,
    _ActorInputBuffers,
    _ActorRow,
    _BatchedTurnSampler,
    _Game,
    _NumericStepBuffers,
    _RecordedPerspective,
    _RolloutGroup,
    _RolloutLane,
    _SampledTurn,
    _step_actions,
    _TensorExchange,
    _TurnBuffer,
    rollout_jobs,
)
from kagg_revue.rl.rollout.storage import RolloutPanel


def _group_rollout_jobs(
    jobs: Sequence[Job],
    batch_games: int,
    *,
    isolate_opponents: bool,
) -> tuple[tuple[Job, ...], ...]:
    """Batch jobs without mixing GPU actor opponents into another lineage."""
    if batch_games < 1:
        raise ValueError("rollout batch size must be positive")
    groups: list[tuple[Job, ...]] = []
    start = 0
    while start < len(jobs):
        lineage_stop = len(jobs)
        if isolate_opponents:
            opponent_id = jobs[start][2]
            lineage_stop = start + 1
            while lineage_stop < len(jobs) and jobs[lineage_stop][2] == opponent_id:
                lineage_stop += 1
        for offset in range(start, lineage_stop, batch_games):
            groups.append(tuple(jobs[offset : min(offset + batch_games, lineage_stop)]))
        start = lineage_stop
    return tuple(groups)


class BatchedRolloutRunner(_BatchedTurnSampler):
    """Advance complete official games around concurrent batched actor calls."""

    def set_sampling_seed(self, sampling_seed: int) -> None:
        """Reset every persistent lane to one update-local reproducible stream."""
        self._sampling_seed = sampling_seed % (2**63 - 1)
        for group_index, lane in enumerate(self._rollout_lanes):
            lane.generator.manual_seed(
                (self._sampling_seed + 1_000_003 * (group_index + 1)) % (2**63 - 1)
            )
            if lane.historical_generator is not None:
                lane.historical_generator.manual_seed(
                    (self._sampling_seed + 2_000_033 * (group_index + 1)) % (2**63 - 1)
                )

    def _games(
        self, jobs: Sequence[Job]
    ) -> tuple[list[_Game], list[_ActorRow], list[_ActorRow], str | None]:
        games: list[_Game] = []
        rows: list[_ActorRow] = []
        historical_rows: list[_ActorRow] = []
        historical_ids: set[str] = set()
        for index, (seed, seat, opponent_id) in enumerate(jobs):
            engine = self._backend.engine(seed=seed, configuration=self._environment)
            configuration = cast(Mapping[str, Any], dict(engine.configuration))
            self_play = opponent_id == "self_play"
            historical = opponent_id in self._historical_models
            if historical:
                historical_ids.add(opponent_id)
            games.append(
                _Game(
                    engine=engine,
                    seed=seed,
                    candidate_seat=seat,
                    opponent_id=opponent_id,
                    official_opponent=(
                        None
                        if self_play or historical
                        else self._official_factory(opponent_id, configuration)
                    ),
                    records={},
                )
            )
            rows.append(
                self._new_row(
                    index,
                    seat,
                    True,
                    self._opening_residuals.get(
                        (opponent_id, int(seed), int(seat)),
                    ),
                )
            )
            if self_play:
                opponent_player = 1 - seat
                rows.append(
                    self._new_row(
                        index,
                        opponent_player,
                        True,
                        self._opening_residuals.get(
                            (opponent_id, int(seed), int(opponent_player)),
                        ),
                    )
                )
            elif historical:
                historical_rows.append(self._new_row(index, 1 - seat, False))
        if len(historical_ids) > 1:
            raise ValueError("one rollout group cannot mix historical actor snapshots")
        if historical_rows and len(historical_rows) != len(games):
            raise ValueError("one rollout group cannot mix GPU and official opponents")
        historical_id = next(iter(historical_ids), None)
        return games, rows, historical_rows, historical_id

    @staticmethod
    def _close_game(game: _Game) -> None:
        opponent = game.official_opponent
        close = getattr(opponent, "close", None)
        if callable(close):
            close()

    @staticmethod
    def _advance_game(
        payload: tuple[
            _Game,
            NumericAction,
            NumericAction | None,
        ],
    ) -> None:
        game, candidate_action, opponent_action = payload
        if opponent_action is None:
            if game.official_opponent is None:
                raise RuntimeError("batched official opponent was not initialized")
            observation = game.engine.observation(1 - game.candidate_seat)
            numeric_act = getattr(game.official_opponent, "act_numeric", None)
            opponent: dict[str, Any] | NumericAction = (
                numeric_act(observation)
                if callable(numeric_act)
                else game.official_opponent.act(observation)
            )
        else:
            opponent = opponent_action
        actions: list[dict[str, Any] | NumericAction] = [opponent, opponent]
        actions[game.candidate_seat] = candidate_action
        _step_actions(game.engine, actions)

    def _new_group(self, jobs: Sequence[Job], group_index: int) -> _RolloutGroup:
        games, rows, historical_rows, historical_id = self._games(jobs)
        if group_index == len(self._rollout_lanes):
            generator = torch.Generator(device=self._device)
            generator.manual_seed(
                (self._sampling_seed + 1_000_003 * (group_index + 1)) % (2**63 - 1)
            )
            historical_generator: torch.Generator | None = None
            historical_stream: torch.cuda.Stream | None = None
            historical_exchange: _TensorExchange | None = None
            if historical_rows:
                historical_generator = torch.Generator(device=self._device)
                historical_generator.manual_seed(
                    (self._sampling_seed + 2_000_033 * (group_index + 1)) % (2**63 - 1)
                )
                historical_stream = (
                    torch.cuda.Stream(device=self._device)  # type: ignore[no-untyped-call]
                    if self._device.type == "cuda"
                    else None
                )
                historical_exchange = _TensorExchange(self._device)
            self._rollout_lanes.append(
                _RolloutLane(
                    candidate_row_count=len(rows),
                    historical_row_count=len(historical_rows),
                    generator=generator,
                    stream=(
                        torch.cuda.Stream(device=self._device)  # type: ignore[no-untyped-call]
                        if self._device.type == "cuda"
                        else None
                    ),
                    exchange=_TensorExchange(self._device),
                    historical_generator=historical_generator,
                    historical_stream=historical_stream,
                    historical_exchange=historical_exchange,
                    candidate_buffers=(
                        []
                        if self._uses_facts
                        else [
                            self._new_buffer(
                                None,
                                allocate_decisions=not self._gpu_policy_session,
                            )
                            for _ in rows
                        ]
                    ),
                    historical_buffers=(
                        []
                        if self._uses_facts
                        else [
                            self._new_buffer(
                                None,
                                allocate_decisions=not self._gpu_policy_session,
                            )
                            for _ in historical_rows
                        ]
                    ),
                )
            )
        lane = self._rollout_lanes[group_index]
        if lane.candidate_row_count != len(rows) or lane.historical_row_count != len(
            historical_rows
        ):
            raise ValueError(
                "persistent rollout panel shape changed; create a new runner for a "
                "different seed or opponent cardinality"
            )
        if lane.exchange.policy_turn_graph is not None:
            self._cuda_graph_reuse_groups += 1
            self._whole_turn_graph_reuse_groups += 1
        if (
            lane.historical_exchange is not None
            and lane.historical_exchange.policy_turn_graph is not None
        ):
            self._cuda_graph_reuse_groups += 1
            self._whole_turn_graph_reuse_groups += 1
        candidate_stream_context = (
            torch.cuda.stream(lane.stream) if lane.stream is not None else nullcontext()
        )
        with candidate_stream_context:
            lane.exchange.reset_episode()
        historical_stream_context = (
            torch.cuda.stream(lane.historical_stream)
            if lane.historical_stream is not None
            else nullcontext()
        )
        with historical_stream_context:
            if lane.historical_exchange is not None:
                lane.historical_exchange.reset_episode()
        candidate_inputs = self._new_actor_inputs(games, rows)
        historical_inputs = self._new_actor_inputs(games, historical_rows)
        candidate_rows = {
            row.game: index
            for index, row in enumerate(rows)
            if row.player == games[row.game].candidate_seat
        }
        opponent_rows = {
            row.game: index
            for index, row in enumerate(rows)
            if row.player != games[row.game].candidate_seat
        }
        if len(candidate_rows) != len(games):
            raise RuntimeError("rollout group omitted a candidate-controlled actor row")
        recorded_perspectives = tuple(
            _RecordedPerspective(row.game, row.player, index)
            for index, row in enumerate(rows)
            if row.record
        )
        record_indices = [perspective.actor_row for perspective in recorded_perspectives]
        if not record_indices:
            raise RuntimeError("rollout group has no training perspectives")
        record_step = record_indices[1] - record_indices[0] if len(record_indices) > 1 else 1
        regular_rows = all(
            value == record_indices[0] + index * record_step
            for index, value in enumerate(record_indices)
        )
        record_rows: slice | NDArray[np.int64] = (
            slice(
                record_indices[0],
                record_indices[0] + len(record_indices) * record_step,
                record_step,
            )
            if regular_rows
            else np.asarray(record_indices, dtype=np.int64)
        )
        native_official_sessions: dict[str, dict[int, Any]] = {}
        for game_index, game in enumerate(games):
            session = getattr(game.official_opponent, "native_session", None)
            batch_kind = getattr(game.official_opponent, "native_batch_kind", None)
            if (
                bool(getattr(game.official_opponent, "native_rollout_required", False))
                and session is None
            ):
                raise RuntimeError("native-only official opponent lacks its rollout session")
            if session is not None:
                if not isinstance(batch_kind, str) or not batch_kind:
                    raise RuntimeError("native official opponent lacks its batch identity")
                if batch_kind not in self._backend.native_opponent_batch_steps:
                    raise RuntimeError(
                        f"native official opponent batch is unavailable: {batch_kind}"
                    )
                native_official_sessions.setdefault(batch_kind, {})[game_index] = session
        return _RolloutGroup(
            games=games,
            rows=rows,
            candidate_rows=candidate_rows,
            opponent_rows=opponent_rows,
            generator=lane.generator,
            stream=lane.stream,
            exchange=lane.exchange,
            historical_rows=historical_rows,
            historical_row_by_game={row.game: index for index, row in enumerate(historical_rows)},
            historical_opponent_id=historical_id,
            historical_generator=lane.historical_generator,
            historical_stream=lane.historical_stream,
            historical_exchange=lane.historical_exchange,
            native_official_sessions=native_official_sessions,
            candidate_buffers=lane.candidate_buffers,
            historical_buffers=lane.historical_buffers,
            record_store=(
                None
                if self._uses_facts
                else RolloutPanel(
                    len(recorded_perspectives),
                    self._turn_capacity,
                    self._model.actor.architecture,
                )
            ),
            recorded_perspectives=recorded_perspectives,
            record_rows=record_rows,
            numeric_step=_NumericStepBuffers(
                engines=[game.engine for game in games],
                tokens=np.empty(
                    (
                        len(games),
                        2,
                        self._model.actor.architecture.max_decisions,
                    ),
                    dtype=np.int64,
                ),
                quantities=np.empty(
                    (
                        len(games),
                        2,
                        self._model.actor.architecture.max_decisions,
                    ),
                    dtype=np.int64,
                ),
                decision_counts=np.empty((len(games), 2), dtype=np.int64),
                unit_counts=np.empty((len(games), 2), dtype=np.int64),
                candidate_players=np.asarray(
                    [game.candidate_seat for game in games], dtype=np.int64
                ),
            ),
            candidate_inputs=candidate_inputs,
            historical_inputs=historical_inputs,
            storage_pending=[None, None],
        )

    def set_historical_opponent(
        self,
        opponent_id: str,
        model: OutcomeActorCritic,
    ) -> None:
        """Retarget one historical runner without replacing captured parameters."""
        if not opponent_id:
            raise ValueError("historical opponent identity cannot be empty")
        resident_models = tuple(self._historical_models.values())
        if len(resident_models) != 1 or resident_models[0] is not model:
            raise ValueError("historical runner requires its resident model instance")
        self._historical_models = {opponent_id: model}
        self._opponents = (opponent_id,)

    def set_opening_residuals(
        self,
        assignments: Mapping[PerspectiveKey, OpeningResidual],
        *,
        force_buffer: bool = False,
    ) -> None:
        """Install one panel-local immutable opening-residual plan."""
        self._opening_residuals = dict(assignments)
        self._force_opening_residual_buffer = force_buffer

    @staticmethod
    def _disable_completed_residual(inputs: _ActorInputBuffers, turn_index: int) -> None:
        """Zero a proposal residual once while retaining CUDA Graph addresses."""
        if (
            inputs.residual_disabled
            or inputs.residual_turns == 0
            or turn_index < inputs.residual_turns
        ):
            return
        if inputs.device_opening_residual is None:
            if inputs.opening_residual is None:
                raise RuntimeError("opening residual horizon lacks residual weights")
            inputs.opening_residual.fill(0.0)
        else:
            inputs.device_opening_residual.zero_()
        inputs.residual_disabled = True

    @staticmethod
    def _wait_for_environment(pending: tuple[Future[None], ...]) -> None:
        for future in pending:
            future.result()

    @staticmethod
    def _union_seconds(intervals: list[tuple[float, float]]) -> float:
        if not intervals:
            return 0.0
        total = 0.0
        start, end = sorted(intervals)[0]
        for next_start, next_end in sorted(intervals)[1:]:
            if next_start > end:
                total += end - start
                start, end = next_start, next_end
            else:
                end = max(end, next_end)
        return total + end - start

    def _sample_group(self, group: _RolloutGroup, executor: ThreadPoolExecutor) -> _SampledTurn:
        actor_started = time.perf_counter()
        capture_required = self._gpu_policy_session and (
            group.exchange.policy_turn_graph is None
            or (
                group.historical_exchange is not None
                and group.historical_exchange.policy_turn_graph is None
            )
        )
        historical_model = (
            self._historical_models[group.historical_opponent_id]
            if group.historical_opponent_id is not None
            else None
        )
        exchange_slot = group.exchange.begin_turn()
        if group.historical_exchange is not None:
            group.historical_exchange.begin_turn()

        def sample_candidate() -> tuple[
            list[NumericAction],
            list[_TurnBuffer | None],
            Any,
            Any,
            Any,
        ]:
            stream_context = (
                torch.cuda.stream(group.stream) if group.stream is not None else nullcontext()
            )
            with stream_context:
                self._disable_completed_residual(group.candidate_inputs, group.turn_index)
                return self._sample_turn(
                    group.games,
                    group.rows,
                    group.history,
                    group.strategy,
                    executor,
                    group.generator,
                    group.exchange,
                    group.candidate_buffers,
                    group.candidate_inputs,
                )

        def sample_historical() -> tuple[
            list[NumericAction],
            list[_TurnBuffer | None],
            Any,
            Any,
            Any,
        ]:
            if (
                historical_model is None
                or group.historical_generator is None
                or group.historical_exchange is None
            ):
                raise RuntimeError("historical rollout group lacks GPU lane state")
            stream_context = (
                torch.cuda.stream(group.historical_stream)
                if group.historical_stream is not None
                else nullcontext()
            )
            with stream_context:
                return self._sample_turn(
                    group.games,
                    group.historical_rows,
                    group.historical_history,
                    group.historical_strategy,
                    executor,
                    group.historical_generator,
                    group.historical_exchange,
                    group.historical_buffers,
                    group.historical_inputs,
                    model=historical_model,
                )

        historical_result: (
            tuple[
                list[NumericAction],
                list[_TurnBuffer | None],
                Any,
                Any,
                Any,
            ]
            | None
        ) = None
        capture_context = self._graph_initialization_lock if capture_required else nullcontext()
        with capture_context:
            candidate_result = sample_candidate()
            if historical_model is not None:
                historical_result = sample_historical()
                with self._diagnostic_lock:
                    self._historical_serial_turns += 1

        sampled, records, history, strategy, batched_records = candidate_result
        group.turn_index += 1
        historical_actions: list[NumericAction] | None = None
        historical_history: Any = None
        historical_strategy: Any = None
        if historical_result is not None:
            (
                historical_actions,
                _,
                historical_history,
                historical_strategy,
                _,
            ) = historical_result
        sampling_elapsed = time.perf_counter() - actor_started
        return _SampledTurn(
            actions=sampled,
            records=records,
            batched_records=batched_records,
            history=history,
            strategy=strategy,
            historical_actions=historical_actions,
            historical_history=historical_history,
            historical_strategy=historical_strategy,
            exchange_slot=exchange_slot,
            elapsed_seconds=sampling_elapsed,
        )

    def _schedule_environment(
        self,
        group: _RolloutGroup,
        sampled: _SampledTurn,
        executor: ThreadPoolExecutor,
    ) -> None:
        group.history = sampled.history
        group.strategy = sampled.strategy
        group.historical_history = sampled.historical_history
        group.historical_strategy = sampled.historical_strategy
        work: list[tuple[_Game, NumericAction, NumericAction | None]] = []
        stored_turns: list[_TurnBuffer] = []
        pending: list[Future[None]] = []
        numeric_official_actions: dict[int, NumericAction] = {}
        if not group.native_official_sessions and all(
            game.official_opponent is not None
            and callable(getattr(game.official_opponent, "act_numeric", None))
            for game in group.games
        ):
            for game_index, game in enumerate(group.games):
                if game.official_opponent is None:
                    raise RuntimeError("numeric official rollout lacks an opponent")
                numeric_act = getattr(game.official_opponent, "act_numeric", None)
                if not callable(numeric_act):
                    raise RuntimeError("numeric official rollout lost its action method")
                numeric_official_actions[game_index] = cast(
                    NumericAction,
                    numeric_act(game.engine.observation(1 - game.candidate_seat)),
                )
        for perspective in group.recorded_perspectives:
            game = group.games[perspective.game]
            record = sampled.records[perspective.actor_row]
            if record is None:
                raise RuntimeError("batched actor omitted a requested training record")
            if group.record_store is None:
                game.records.setdefault(perspective.player, []).append(record.record())
            else:
                stored_turns.append(record)
        for game_index, game in enumerate(group.games):
            candidate_row = group.candidate_rows[game_index]
            historical_row = group.historical_row_by_game.get(game_index)
            if historical_row is not None and sampled.historical_actions is None:
                raise RuntimeError("historical rollout omitted opponent actions")
            work.append(
                (
                    game,
                    sampled.actions[candidate_row],
                    (
                        sampled.historical_actions[historical_row]
                        if historical_row is not None and sampled.historical_actions is not None
                        else (
                            sampled.actions[group.opponent_rows[game_index]]
                            if game_index in group.opponent_rows
                            else numeric_official_actions.get(game_index)
                        )
                    ),
                )
            )
        if group.record_store is not None:
            column = group.record_store.reserve()
            previous = group.storage_pending[sampled.exchange_slot]
            if previous is not None:
                raise RuntimeError("rollout host slot was reused before its panel write")
            if sampled.batched_records is None:
                storage_future = executor.submit(
                    group.record_store.append_reserved,
                    column,
                    tuple(stored_turns),
                )
                pending.append(storage_future)
            else:
                storage_future = executor.submit(
                    group.record_store.append_batched_reserved,
                    column,
                    sampled.batched_records,
                    group.record_rows,
                )
                group.storage_pending[sampled.exchange_slot] = storage_future
                reuse_slot = 1 - sampled.exchange_slot
                reuse_pending = group.storage_pending[reuse_slot]
                if reuse_pending is not None:
                    pending.append(reuse_pending)
                    group.storage_pending[reuse_slot] = None
        step = group.numeric_step
        native_index_set: set[int] = set()
        native_count = 0
        for batch_kind, indexed_sessions in group.native_official_sessions.items():
            native_indices = list(indexed_sessions)
            native_index_set.update(native_indices)
            start = native_count
            stop = start + len(native_indices)
            for target, game_index in enumerate(native_indices, start=start):
                game, candidate_action, _opponent_action = work[game_index]
                player = game.candidate_seat
                count = candidate_action.decision_count
                step.tokens[target, player, :count] = candidate_action.tokens
                step.quantities[target, player, :count] = candidate_action.quantities
                step.decision_counts[target, player] = count
                step.unit_counts[target, player] = candidate_action.unit_count
                step.candidate_players[target] = player
            pending.append(
                executor.submit(
                    self._backend.native_opponent_batch_steps[batch_kind],
                    [work[index][0].engine for index in native_indices],
                    step.candidate_players[start:stop],
                    [indexed_sessions[index] for index in native_indices],
                    step.tokens[start:stop],
                    step.quantities[start:stop],
                    step.decision_counts[start:stop],
                    step.unit_counts[start:stop],
                    self._policy_workers,
                )
            )
            native_count = stop

        numeric_work = [
            payload
            for index, payload in enumerate(work)
            if index not in native_index_set and payload[2] is not None
        ]
        for relative, (game, candidate_action, raw_opponent_action) in enumerate(numeric_work):
            index = native_count + relative
            if raw_opponent_action is None:
                raise RuntimeError("numeric rollout omitted its opponent action")
            actions = [raw_opponent_action, raw_opponent_action]
            actions[game.candidate_seat] = candidate_action
            for player, action in enumerate(actions):
                count = action.decision_count
                step.tokens[index, player, :count] = action.tokens
                step.quantities[index, player, :count] = action.quantities
                step.decision_counts[index, player] = count
                step.unit_counts[index, player] = action.unit_count
        numeric_count = len(numeric_work)
        if numeric_count:
            start = native_count
            stop = start + numeric_count
            pending.append(
                executor.submit(
                    self._backend.engine_step_numeric_batch,
                    [game.engine for game, _, _ in numeric_work],
                    step.tokens[start:stop],
                    step.quantities[start:stop],
                    step.decision_counts[start:stop],
                    step.unit_counts[start:stop],
                    self._policy_workers,
                )
            )

        external_work = [
            payload
            for index, payload in enumerate(work)
            if index not in native_index_set and payload[2] is None
        ]
        pending.extend(executor.submit(self._advance_game, payload) for payload in external_work)
        group.pending = tuple(pending)
        self._environment_tasks += len(work)

    @staticmethod
    def _trajectories(group: _RolloutGroup) -> list[Trajectory]:
        trajectories: list[Trajectory] = []
        for panel_row, perspective in enumerate(group.recorded_perspectives):
            game = group.games[perspective.game]
            residual = group.rows[perspective.actor_row].opening_residual
            stored_residual: NDArray[np.float32] | None = None
            if residual is not None:
                materialized = group.candidate_inputs.opening_residual
                if materialized is None:
                    raise RuntimeError("opening-noise trajectory lacks residual storage")
                stored_residual = normalized_action_head_direction(
                    residual.seed,
                    materialized.shape[1],
                    materialized.shape[2],
                )
                stored_residual *= np.float32(residual.scale)
            terminal_cash = float(game.engine.money(perspective.player))
            opponent_cash = float(game.engine.money(1 - perspective.player))
            outcome = int(terminal_cash > opponent_cash) - int(terminal_cash < opponent_cash)
            trajectories.append(
                # The learner reuses this exact episode residual when it
                # evaluates the behavior-policy likelihood for PPO.
                Trajectory(
                    episode_id=(f"{game.opponent_id}:{game.seed}:{perspective.player}"),
                    opponent_id=game.opponent_id,
                    seed=game.seed,
                    seat=perspective.player,
                    turns=(
                        tuple(game.records[perspective.player])
                        if group.record_store is None
                        else group.record_store.trajectory(panel_row)
                    ),
                    outcome=outcome,
                    terminal_cash=terminal_cash,
                    opponent_cash=opponent_cash,
                    opening_residual=stored_residual,
                    opening_residual_seed=-1 if residual is None else residual.seed,
                    opening_residual_direction=(-1 if residual is None else residual.direction_id),
                    opening_residual_scale=0.0 if residual is None else residual.scale,
                    opening_residual_turns=(0 if residual is None else residual.prefix_turns),
                )
            )
        return trajectories

    @staticmethod
    def _matches(group: _RolloutGroup) -> list[RolloutMatch]:
        """Return one direct outcome row per actual environment match."""
        matches: list[RolloutMatch] = []
        for game in group.games:
            terminal_cash = float(game.engine.money(game.candidate_seat))
            opponent_cash = float(game.engine.money(1 - game.candidate_seat))
            outcome = int(terminal_cash > opponent_cash) - int(terminal_cash < opponent_cash)
            matches.append(
                RolloutMatch(
                    match_id=f"{game.opponent_id}:{game.seed}:{game.candidate_seat}",
                    opponent_id=game.opponent_id,
                    seed=game.seed,
                    candidate_seat=game.candidate_seat,
                    outcome=outcome,
                    terminal_cash=terminal_cash,
                    opponent_cash=opponent_cash,
                )
            )
        return matches

    @property
    def last_matches(self) -> tuple[RolloutMatch, ...]:
        """Return actual matches from the most recently completed panel."""
        return tuple(self._last_matches)

    def _close_group(self, group: _RolloutGroup, executor: ThreadPoolExecutor) -> None:
        if group.closed:
            return
        tuple(executor.map(self._close_game, group.games))
        group.closed = True

    @staticmethod
    def _finish_storage(group: _RolloutGroup) -> None:
        """Finish the final double-buffered panel writes before exposing views."""
        for index, future in enumerate(group.storage_pending):
            if future is not None:
                future.result()
                group.storage_pending[index] = None

    def _abort_groups(self, groups: Sequence[_RolloutGroup], executor: ThreadPoolExecutor) -> None:
        for group in groups:
            for future in group.pending:
                future.cancel()
            for storage_future in group.storage_pending:
                if storage_future is not None:
                    storage_future.cancel()
        for group in groups:
            for future in group.pending:
                if not future.cancelled():
                    with suppress(Exception):
                        future.result()
            group.pending = ()
            for index, storage_future in enumerate(group.storage_pending):
                if storage_future is not None and not storage_future.cancelled():
                    with suppress(Exception):
                        storage_future.result()
                group.storage_pending[index] = None
            self._close_group(group, executor)

    def _release_groups(self, groups: Sequence[_RolloutGroup]) -> None:
        """Release episode objects while retaining fixed-shape CUDA lanes."""
        if self._device.type == "cuda":
            torch.cuda.synchronize(self._device)
        for group in groups:
            group.games.clear()
            group.rows.clear()
            group.candidate_rows.clear()
            group.opponent_rows.clear()
            group.historical_rows.clear()
            group.historical_row_by_game.clear()
            group.candidate_inputs.engines.clear()
            group.candidate_inputs.players.clear()
            group.historical_inputs.engines.clear()
            group.historical_inputs.players.clear()
            group.numeric_step.engines.clear()
            group.history = None
            group.strategy = None
            group.historical_history = None
            group.historical_strategy = None
            group.pending = ()
            group.record_store = None
            group.storage_pending.clear()

    def close(self) -> None:
        """Release every persistent lane after the runner is no longer used."""
        if self._device.type == "cuda":
            torch.cuda.synchronize(self._device)
        for lane in self._rollout_lanes:
            lane.exchange.close()
            if lane.historical_exchange is not None:
                lane.historical_exchange.close()
        self._rollout_lanes.clear()
        gc.collect()
        if self._device.type == "cuda":
            torch.cuda.empty_cache()

    def collect_jobs(
        self, jobs: Sequence[Job], progress: ProgressCallback | None = None
    ) -> list[Trajectory]:
        """Collect an explicit bounded shard of the paired rollout panel."""
        if not jobs:
            self._last_matches = []
            return []
        self._reset_diagnostics()
        self._last_matches = []
        groups: list[_RolloutGroup] = []
        trajectories: list[Trajectory] = []
        matches: list[RolloutMatch] = []
        job_groups = _group_rollout_jobs(
            jobs,
            self._batch_games,
            isolate_opponents=bool(self._historical_models),
        )
        group_count = len(job_groups)
        # Behavior-recording and action-only CUDA Graphs are numerically unsafe
        # when their replays overlap. Historical groups therefore share one
        # scheduler lane and execute candidate then opponent; self-play keeps
        # its configured cross-group concurrency.
        self._active_actor_streams = (
            min(self._configured_actor_streams, group_count)
            if self._device.type == "cuda" and not self._historical_models
            else 1
        )
        self._policy_workers = max(1, self._cpu_workers // self._active_actor_streams)
        collection_started = time.perf_counter()
        actor_intervals: list[tuple[float, float]] = []
        environment_intervals: list[tuple[float, float]] = []
        pending: dict[Future[Any], tuple[bool, _RolloutGroup, float]] = {}
        with ThreadPoolExecutor(
            max_workers=min(self._cpu_workers, len(jobs)),
            thread_name_prefix="rollout-environment",
        ) as executor:
            try:
                for group_index, group_jobs in enumerate(job_groups):
                    groups.append(
                        self._new_group(
                            group_jobs,
                            group_index,
                        )
                    )
                self._groups = len(groups)
                total_trajectories = sum(len(group.recorded_perspectives) for group in groups)
                with ThreadPoolExecutor(
                    max_workers=self._active_actor_streams,
                    thread_name_prefix="rollout-actor",
                ) as actor_executor:
                    for group in groups:
                        started = time.perf_counter()
                        future = actor_executor.submit(self._sample_group, group, executor)
                        pending[future] = (True, group, started)
                    capturing_graphs = self._gpu_policy_session and any(
                        group.exchange.policy_turn_graph is None
                        or (
                            group.historical_exchange is not None
                            and group.historical_exchange.policy_turn_graph is None
                        )
                        for group in groups
                    )
                    if capturing_graphs:
                        # Global-mode CUDA capture forbids another stream from
                        # starting ordinary work until every group owns its graph.
                        wait(set(pending))
                    while pending:
                        completed, _ = wait(
                            set(pending),
                            return_when=FIRST_COMPLETED,
                        )
                        for future in completed:
                            actor_event, group, started = pending.pop(future)
                            if actor_event:
                                sampled = future.result()
                                actor_intervals.append((started, time.perf_counter()))
                                self._actor_work_seconds += sampled.elapsed_seconds
                                self._schedule_environment(group, sampled, executor)
                                environment_started = time.perf_counter()
                                environment_future = executor.submit(
                                    self._wait_for_environment, group.pending
                                )
                                pending[environment_future] = (
                                    False,
                                    group,
                                    environment_started,
                                )
                                continue
                            future.result()
                            environment_intervals.append((started, time.perf_counter()))
                            group.pending = ()
                            done = [bool(game.engine.done) for game in group.games]
                            if any(done) and not all(done):
                                raise RuntimeError(
                                    "batched rollout environments terminated out of lockstep"
                                )
                            if all(done):
                                self._finish_storage(group)
                                completed_trajectories = self._trajectories(group)
                                matches.extend(self._matches(group))
                                self._close_group(group, executor)
                                for trajectory in completed_trajectories:
                                    trajectories.append(trajectory)
                                    if progress is not None:
                                        progress(
                                            trajectory,
                                            len(trajectories),
                                            total_trajectories,
                                        )
                                continue
                            actor_started = time.perf_counter()
                            actor_future = actor_executor.submit(
                                self._sample_group, group, executor
                            )
                            pending[actor_future] = (
                                True,
                                group,
                                actor_started,
                            )
            except BaseException:
                for future in pending:
                    future.cancel()
                self._abort_groups(groups, executor)
                self._release_groups(groups)
                raise
        collection_elapsed = time.perf_counter() - collection_started
        actor_seconds = self._union_seconds(actor_intervals)
        self._actor_seconds += actor_seconds
        self._environment_seconds += max(0.0, collection_elapsed - actor_seconds)
        self._environment_wait_seconds += self._union_seconds(environment_intervals)
        self._last_matches = matches
        self._release_groups(groups)
        return trajectories

    def collect(
        self, seeds: Sequence[int], progress: ProgressCallback | None = None
    ) -> list[Trajectory]:
        """Collect the complete paired panel in bounded lockstep groups."""
        return self.collect_jobs(rollout_jobs(seeds, self._opponents), progress)


__all__ = [
    "BatchedRolloutRunner",
    "Job",
    "OfficialFactory",
    "ProgressCallback",
    "rollout_jobs",
]
