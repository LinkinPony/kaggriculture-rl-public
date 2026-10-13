"""Batched complete official matches for unit-task terminal-WDL PPO."""

from __future__ import annotations

import gc
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.native_batch import (
    create_native_opponent_session,
    step_native_opponent_batch,
)
from kagg_revue.opponents.registry import trusted_runtime_identity
from kagg_revue.policy.cuda.capture import clear_cublas_workspaces
from kagg_revue.policy.cuda.session import GpuPolicyStateLayout
from kagg_revue.policy.facts import OpponentInventoryBounds
from kagg_revue.policy.runtime import BaselineAgent, TurnPolicyAgent
from kagg_revue.policy.tasks.gpu.market import TaskMarketGraph
from kagg_revue.policy.tasks.gpu.packing import (
    create_h200_rollout_policy,
    refresh_h200_rollout_policy,
)
from kagg_revue.policy.tasks.gpu.planning import TaskPlanningGraph
from kagg_revue.policy.tasks.gpu.turn import TaskTurnGraph, TaskTurnInputs
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.policy.tasks.runtime import (
    CompactTaskTrace,
    decode_market_actions,
    plan_unit_tasks,
    task_context,
)
from kagg_revue.policy.transformer import HistoryState
from kagg_revue.rl.data import Trajectory, TurnRecord
from kagg_revue.rl.rollout.population import weighted_rollout_jobs
from kagg_revue.rl.rollout.storage import BatchedStoredTurns, RolloutPanel
from kagg_revue.rl.tasks.data import (
    TaskDecisionRecord,
    TaskTapeEpisode,
    records_from_traces,
)
from kagg_revue.rl.tasks.model import TaskTapeActorCritic
from kagg_revue.rl.tasks.storage import CompactTaskPanel

IntArray = NDArray[np.int64]
BoolArray = NDArray[np.bool_]
Job = tuple[int, int, str]


class _OfficialAgent(Protocol):
    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one official action request."""


@dataclass
class _Game:
    engine: Any
    match_index: int
    seed: int
    seat: int
    opponent_id: str
    official_opponent: _OfficialAgent | None
    native_opponent_session: Any | None
    task_session: Any
    bounds: OpponentInventoryBounds | None
    turns: list[TurnRecord]
    market_masks: list[BoolArray]
    tasks: list[TaskDecisionRecord]


def _step_native_games(
    backend: BackendApi,
    games: Sequence[_Game],
    tokens: IntArray,
    quantities: IntArray,
    decision_counts: IntArray,
    unit_counts: IntArray,
    workers: int,
) -> float:
    """Advance one native opponent batch and return its actual work time."""
    started = time.perf_counter()
    step_native_opponent_batch(
        backend,
        [game.engine for game in games],
        np.asarray([game.seat for game in games], dtype=np.int64),
        [game.opponent_id for game in games],
        [game.native_opponent_session for game in games],
        tokens,
        quantities,
        decision_counts,
        unit_counts,
        workers,
    )
    return time.perf_counter() - started


def _step_self_play_games(
    backend: BackendApi,
    engines: Sequence[Any],
    tokens: IntArray,
    quantities: IntArray,
    decision_counts: IntArray,
    unit_counts: IntArray,
    workers: int,
) -> float:
    """Advance both live-policy seats once through the native batch ABI."""
    started = time.perf_counter()
    backend.engine_step_numeric_batch(
        list(engines),
        tokens,
        quantities,
        decision_counts,
        unit_counts,
        workers,
    )
    return time.perf_counter() - started


@dataclass(frozen=True)
class TaskRolloutReport:
    """Direct outcome and production-shaped inference diagnostics."""

    episodes: tuple[TaskTapeEpisode, ...]
    maximum_actor_seconds: float
    remaining_overage_seconds: float
    task_decisions: int
    market_factors: int
    phase_seconds: Mapping[str, float]


@dataclass
class _CudaRolloutLane:
    """Persistent fixed-batch CUDA programs for one serial actor lane."""

    stream: torch.cuda.Stream
    generator: torch.Generator
    decision_graph: TaskPlanningGraph
    market_graph: TaskMarketGraph
    turn_graph: TaskTurnGraph | None = None


def task_rollout_jobs(seeds: Sequence[int], opponents: Sequence[str]) -> list[Job]:
    """Build physical jobs while retaining both self-play perspectives later."""
    if not seeds or not opponents:
        raise ValueError("task rollout needs nonempty seeds and opponents")
    return [
        (int(seed), seat, opponent)
        for seed in seeds
        for opponent in opponents
        for seat in ((0,) if opponent == "self_play" else (0, 1))
    ]


def _group_jobs(jobs: Sequence[Job], actor_capacity: int) -> list[list[Job]]:
    """Pack physical jobs by the number of live-policy actor rows they need."""
    if actor_capacity < 1:
        raise ValueError("task rollout actor capacity must be positive")
    groups: list[list[Job]] = []
    current: list[Job] = []
    rows = 0
    for job in jobs:
        job_rows = 2 if job[2] == "self_play" else 1
        if job_rows > actor_capacity:
            raise ValueError("task rollout batch cannot hold one self-play match")
        if current and rows + job_rows > actor_capacity:
            groups.append(current)
            current = []
            rows = 0
        current.append(job)
        rows += job_rows
    if current:
        groups.append(current)
    return groups


def _autocast(device: torch.device) -> Any:
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.bfloat16)
    return nullcontext()


class TaskRolloutCollector:
    """Collect one bounded paired panel through the native task compiler."""

    def __init__(
        self,
        backend: BackendApi,
        model: TaskTapeActorCritic,
        contract: NativeTaskContract,
        repository_root: Path,
        public_agent_manifest: Path,
        environment: Mapping[str, object],
        opponent_weights: Mapping[str, float],
        device: torch.device,
        *,
        batch_games: int,
        cpu_workers: int,
        actor_streams: int,
        sampling_seed: int,
        act_timeout_seconds: float,
        remaining_overage_seconds: float,
        initial_actor: Path | None,
        rank: int = 0,
        world_size: int = 1,
    ) -> None:
        """Authenticate the ladder and bind production inference capacities."""
        if batch_games < 1 or cpu_workers < 1 or actor_streams < 1:
            raise ValueError("task rollout batch and worker counts must be positive")
        if rank < 0 or rank >= world_size:
            raise ValueError("task rollout rank is outside the distributed world")
        if act_timeout_seconds <= 0.0 or remaining_overage_seconds < 0.0:
            raise ValueError("task rollout time budgets must be non-negative")
        self._backend = backend
        self._model = model
        self._contract = contract
        self._repository_root = repository_root
        self._environment = dict(environment)
        episode_steps = self._environment.get("episodeSteps")
        if (
            not isinstance(episode_steps, int)
            or isinstance(episode_steps, bool)
            or episode_steps < 2
        ):
            raise ValueError("task rollout environment has invalid episode steps")
        self._turn_capacity = episode_steps - 1
        self._opponent_weights = dict(opponent_weights)
        self._opponents = tuple(self._opponent_weights)
        self._device = device
        self._batch_games = batch_games
        self._cpu_workers = cpu_workers
        self._actor_streams = actor_streams
        self._workers_per_stream = max(1, cpu_workers // actor_streams)
        self._sampling_seed = sampling_seed
        self._rank = rank
        self._world_size = world_size
        self._act_timeout = act_timeout_seconds
        self._initial_overage = remaining_overage_seconds
        self._initial_actor = initial_actor
        self._frozen_actor_lanes: dict[int, TurnPolicyAgent] = {}
        manifest_path = (
            public_agent_manifest
            if public_agent_manifest.is_absolute()
            else repository_root / public_agent_manifest
        )
        manifest = backend.load_public_agent_manifest(manifest_path)
        self._public_records = manifest.by_id()
        builtins = {"self_play", "deterministic_incumbent", "frozen_initial_actor"}
        unknown = set(self._opponents) - builtins - set(self._public_records)
        if unknown:
            raise KeyError(f"task rollout opponents are not authenticated: {sorted(unknown)}")
        if "frozen_initial_actor" in self._opponents and (
            initial_actor is None or not initial_actor.is_file()
        ):
            raise FileNotFoundError("task rollout frozen initial actor is absent")
        self._native_opponents = (
            {"deterministic_incumbent"} if "deterministic_incumbent" in self._opponents else set()
        ) | {
            opponent
            for opponent in self._opponents
            if opponent in backend.native_opponent_batch_steps
            and opponent in self._public_records
            and trusted_runtime_identity(self._public_records[opponent]) is not None
        }
        codec = cast(Mapping[str, object], backend.action_codec_spec())
        self._has_quantity = np.asarray(codec["has_quantity"], dtype=np.bool_)
        self._cuda_streams = (
            [
                torch.cuda.Stream(device=self._device)  # type: ignore[no-untyped-call]
                for _ in range(self._actor_streams)
            ]
            if self._device.type == "cuda"
            else []
        )
        self._cuda_lanes: dict[tuple[int, int], _CudaRolloutLane] = {}
        self._rollout_tasks = (
            create_h200_rollout_policy(model.tasks)
            if device.type == "cuda" and model.tasks.factorized is not None
            else model.tasks
        )
        architecture = model.actor.architecture
        fact_spec = cast(Mapping[str, object], backend.derived_fact_spec())
        products = fact_spec.get("products")
        if not isinstance(products, int) or isinstance(products, bool):
            raise ValueError("native derived-fact product count is invalid")
        self._fact_products = products
        if architecture.unit_shape[1] != contract.unit_limit:
            raise ValueError("task rollout model and compiler unit limits differ")
        market_orders = self._environment.get("maxMarketOrdersPerTurn")
        if not isinstance(market_orders, int) or isinstance(market_orders, bool):
            raise ValueError("task rollout environment lacks market order capacity")
        self._maximum_market_orders = market_orders
        if architecture.max_decisions < contract.unit_limit + market_orders:
            raise ValueError("task rollout actor cannot hold units plus market orders")
        if architecture.skill_tokens:
            raise ValueError("task rollout v1 does not admit latent skill samples")
        self._gpu_policy_layout = GpuPolicyStateLayout.from_spec(
            cast(
                Mapping[str, int],
                backend.gpu_policy_state_spec(
                    architecture.board_shape[-1],
                    contract.unit_limit,
                ),
            ),
            board_size=architecture.board_shape[-1],
            unit_limit=contract.unit_limit,
        )
        if device.type == "cpu":
            torch.set_num_threads(cpu_workers)

    def _cuda_lane(self, lane_index: int, batch_size: int) -> _CudaRolloutLane:
        """Return persistent graph storage for one lane and fixed batch size."""
        key = (lane_index, batch_size)
        lane = self._cuda_lanes.get(key)
        if lane is not None:
            return lane
        generator = torch.Generator(device=self._device)
        lane = _CudaRolloutLane(
            stream=self._cuda_streams[lane_index],
            generator=generator,
            decision_graph=TaskPlanningGraph(
                self._rollout_tasks,
                generator,
                self._contract.prefix_capacity + self._contract.unit_limit,
            ),
            market_graph=TaskMarketGraph(
                self._model.actor,
                self._gpu_policy_layout,
                self._has_quantity,
                generator,
            ),
        )
        self._cuda_lanes[key] = lane
        return lane

    def release_cuda_graphs(self) -> None:
        """Release persistent inference graphs when the collector is retired."""
        if self._device.type != "cuda" or not self._cuda_lanes:
            return
        torch.cuda.synchronize(self._device)
        lanes = tuple(self._cuda_lanes.values())
        self._cuda_lanes.clear()
        for lane in lanes:
            lane.decision_graph.close()
            lane.market_graph.close()
            if lane.turn_graph is not None:
                lane.turn_graph.close()
        del lane, lanes
        gc.collect()
        clear_cublas_workspaces()
        torch.cuda.empty_cache()

    @property
    def opponent_identities(self) -> dict[str, object]:
        """Return the exact frozen ladder identities used by collection."""
        result: dict[str, object] = {}
        for opponent in self._opponents:
            if opponent == "self_play":
                result[opponent] = {
                    "kind": "self_play",
                    "identity": "current_live_task_policy",
                    "training_perspectives_per_match": 2,
                }
            elif opponent == "deterministic_incumbent":
                result[opponent] = {"kind": "deterministic_incumbent"}
            elif opponent == "frozen_initial_actor":
                initial_actor = self._initial_actor
                if initial_actor is None:
                    raise RuntimeError("task rollout frozen initial actor disappeared")
                result[opponent] = {
                    "kind": "frozen_initial_actor",
                    "path": str(initial_actor),
                    "sha256": sha256_file(initial_actor),
                    "sample": False,
                }
            else:
                record = self._public_records[opponent]
                native_identity = trusted_runtime_identity(record)
                result[opponent] = {
                    "kind": "public_notebook",
                    "notebook_ref": record.notebook_ref,
                    "notebook_id": record.notebook_id,
                    "artifact_sha256": record.sha256,
                    "native_runtime": native_identity,
                }
        return result

    def _opponent(self, opponent_id: str, lane: int) -> _OfficialAgent:
        if opponent_id == "deterministic_incumbent":
            return BaselineAgent(self._backend, self._environment)
        if opponent_id == "frozen_initial_actor":
            opponent = self._frozen_actor_lanes.get(lane)
            if opponent is None:
                initial_actor = self._initial_actor
                if initial_actor is None:
                    raise RuntimeError("task rollout frozen initial actor disappeared")
                opponent = TurnPolicyAgent(
                    self._backend,
                    self._environment,
                    initial_actor,
                    str(self._device),
                    self._contract.unit_limit,
                    sample=False,
                    cpu_threads=self._cpu_workers,
                )
                self._frozen_actor_lanes[lane] = opponent
            return opponent
        return cast(
            _OfficialAgent,
            self._backend.public_agent_runtime(
                self._public_records[opponent_id],
                self._repository_root,
                self._environment,
            ),
        )

    def _game(
        self,
        job: Job,
        lane: int,
        *,
        engine: Any,
        match_index: int,
    ) -> _Game:
        seed, seat, opponent_id = job
        bounds = (
            OpponentInventoryBounds(self._fact_products)
            if self._model.actor.architecture.turn_fact_features
            else None
        )
        native = opponent_id in self._native_opponents
        self_play = opponent_id == "self_play"
        return _Game(
            engine=engine,
            match_index=match_index,
            seed=seed,
            seat=seat,
            opponent_id=opponent_id,
            official_opponent=(None if native or self_play else self._opponent(opponent_id, lane)),
            native_opponent_session=(
                (
                    self._backend.deterministic_incumbent_session(self._environment)
                    if opponent_id == "deterministic_incumbent"
                    else create_native_opponent_session(
                        opponent_id,
                        self._maximum_market_orders,
                    )
                )
                if native
                else None
            ),
            task_session=self._backend.unit_task_session(
                self._environment,
                self._contract.unit_limit,
                self._contract.maximum_quantity,
            ),
            bounds=bounds,
            turns=[],
            market_masks=[],
            tasks=[],
        )

    def _games(self, jobs: Sequence[Job], lane_offset: int) -> list[_Game]:
        """Expand self-play matches into two actor rows sharing one engine."""
        games: list[_Game] = []
        for match_index, (seed, seat, opponent_id) in enumerate(jobs):
            engine = self._backend.engine(seed, self._environment)
            seats = (0, 1) if opponent_id == "self_play" else (seat,)
            for player in seats:
                games.append(
                    self._game(
                        (seed, player, opponent_id),
                        lane_offset + len(games),
                        engine=engine,
                        match_index=match_index,
                    )
                )
        return games

    def _turn_facts(
        self,
        policy_batch: Any,
        games: list[_Game],
    ) -> tuple[Tensor | None, Tensor | None, list[NDArray[np.float16]]]:
        architecture = self._model.actor.architecture
        if not architecture.turn_fact_features:
            empty = [np.zeros((0, 0), dtype=np.float16) for _ in games]
            return None, None, empty
        snapshots = cast(Mapping[str, object], policy_batch.flow_snapshots())
        steps = np.asarray(snapshots["step"], dtype=np.int64)
        markets = np.asarray(snapshots["market_inventory"], dtype=np.int64)
        towns = np.asarray(snapshots["town_consumption"], dtype=np.int64)
        gains = np.asarray(snapshots["opponent_unit_gain_upper"], dtype=np.int64)
        lowers: list[IntArray] = []
        uppers: list[IntArray] = []
        for row, game in enumerate(games):
            if game.bounds is None:
                raise RuntimeError("task rollout lost opponent inventory bounds")
            lower, upper = game.bounds.update(
                {
                    "step": int(steps[row]),
                    "market_inventory": markets[row],
                    "town_consumption": towns[row],
                    "opponent_unit_gain_upper": gains[row],
                }
            )
            lowers.append(lower)
            uppers.append(upper)
        raw = cast(
            Mapping[str, object],
            policy_batch.turn_facts_batch(np.stack(lowers), np.stack(uppers)),
        )
        values = np.asarray(raw["values"], dtype=np.float32)
        counts = np.asarray(raw["counts"], dtype=np.int64)
        if (
            values.ndim != 3
            or values.shape[0] != len(games)
            or values.shape[2] != architecture.turn_fact_features
            or counts.shape != (len(games),)
        ):
            raise ValueError("native batched turn facts differ from the task actor")
        mask = np.arange(values.shape[1])[None, :] < counts[:, None]
        return (
            torch.as_tensor(values, device=self._device),
            torch.as_tensor(mask, dtype=torch.bool, device=self._device),
            [values[index, : int(count)].astype(np.float16) for index, count in enumerate(counts)],
        )

    def _collect_group(
        self,
        jobs: Sequence[Job],
        generator: torch.Generator,
        *,
        sample: bool,
        group_index: int,
        cuda_lane: _CudaRolloutLane | None,
    ) -> tuple[
        list[TaskTapeEpisode],
        float,
        float,
        int,
        int,
        dict[str, float],
    ]:
        lane_offset = group_index * self._batch_games
        games = self._games(jobs, lane_offset)
        batch_size = len(games)
        self_play_rows: list[tuple[int, int]] = []
        for match_index, job in enumerate(jobs):
            if job[2] != "self_play":
                continue
            rows_by_seat = {
                game.seat: row for row, game in enumerate(games) if game.match_index == match_index
            }
            if set(rows_by_seat) != {0, 1}:
                raise RuntimeError("task self-play match lost one actor seat")
            self_play_rows.append((rows_by_seat[0], rows_by_seat[1]))
        architecture = self._model.actor.architecture
        histories: HistoryState | None = None
        strategy: Tensor | None = None
        previous_tokens = torch.zeros(
            (batch_size, architecture.max_decisions),
            dtype=torch.long,
            device=self._device,
        )
        previous_quantities = torch.zeros_like(previous_tokens)
        previous_mask = torch.zeros_like(previous_tokens, dtype=torch.bool)
        overage = self._initial_overage
        maximum_actor_seconds = 0.0
        task_decisions = 0
        market_factors = 0
        turn_index = 0
        phase_seconds = {
            "policy_inputs": 0.0,
            "start_turn": 0.0,
            "task_decode": 0.0,
            "market_decode": 0.0,
            "record": 0.0,
            "environment": 0.0,
            "cuda_graph_capture": 0.0,
        }
        gpu_graphs = (
            self._device.type == "cuda"
            and sample
            and not architecture.turn_fact_features
            and not architecture.prefix_fact_features
            and not architecture.candidate_fact_features
        )
        rollout_panel = (
            RolloutPanel(batch_size, self._turn_capacity, architecture) if gpu_graphs else None
        )
        market_mask_panel = (
            np.zeros(
                (
                    batch_size,
                    self._turn_capacity,
                    architecture.max_decisions,
                ),
                dtype=np.bool_,
            )
            if gpu_graphs
            else None
        )
        compact_task_panel: CompactTaskPanel | None = None
        market_graph = cuda_lane.market_graph if gpu_graphs and cuda_lane else None
        turn_graph = cuda_lane.turn_graph if gpu_graphs and cuda_lane else None
        decision_graph = cuda_lane.decision_graph if gpu_graphs and cuda_lane else None
        stream = cuda_lane.stream if cuda_lane is not None else None
        turn_capture_before = 0.0 if turn_graph is None else turn_graph.capture_seconds
        decision_capture_before = 0.0 if decision_graph is None else decision_graph.capture_seconds
        market_capture_before = 0.0 if market_graph is None else market_graph.capture_seconds
        stream_context = torch.cuda.stream(stream) if stream is not None else nullcontext()
        with (
            ThreadPoolExecutor(
                max_workers=min(self._workers_per_stream, batch_size),
                thread_name_prefix=f"task-rollout-{self._rank}-{group_index}",
            ) as environment_executor,
            stream_context,
        ):
            if turn_graph is not None:
                turn_graph.reset()
            while not all(bool(game.engine.done) for game in games):
                started = time.perf_counter()
                engines = [game.engine for game in games]
                players = [game.seat for game in games]
                policy_batch = self._backend.engine_policy_session_batch(
                    engines,
                    players,
                    self._contract.unit_limit,
                    self._workers_per_stream,
                )
                board_raw, units_raw, global_raw = policy_batch.encode_compact()
                board_values = np.asarray(board_raw, dtype=np.float16)
                unit_values = np.asarray(units_raw, dtype=np.float16)
                global_values = np.asarray(global_raw, dtype=np.float32)
                board = torch.as_tensor(board_values, device=self._device)
                units = torch.as_tensor(unit_values, device=self._device)
                global_features = torch.as_tensor(global_values, device=self._device)
                compact_state_values = np.asarray(policy_batch.gpu_state_compact(), dtype=np.int32)
                compact_task_state = torch.as_tensor(compact_state_values, device=self._device)
                economic_values = (
                    compact_state_values
                    if architecture.economic_feature_version is not None
                    else np.zeros((batch_size, 0), dtype=np.int32)
                )
                economic_state = (
                    compact_task_state
                    if architecture.economic_feature_version is not None
                    else None
                )
                turn_facts, turn_fact_mask, stored_turn_facts = self._turn_facts(
                    policy_batch, games
                )
                phase_seconds["policy_inputs"] += time.perf_counter() - started

                phase_started = time.perf_counter()
                with torch.inference_mode(), _autocast(self._device):
                    if gpu_graphs:
                        turn_inputs = TaskTurnInputs(
                            board=board,
                            units=units,
                            global_features=global_features,
                            previous_actions=previous_tokens,
                            previous_quantities=previous_quantities,
                            previous_mask=previous_mask,
                            economic_state=economic_state,
                        )
                        if turn_graph is None:
                            turn_graph = TaskTurnGraph(
                                self._model.actor,
                                turn_inputs,
                                self._model.market.behavior_value,
                            )
                            if cuda_lane is not None:
                                cuda_lane.turn_graph = turn_graph
                        context, market_values = turn_graph.decode(turn_inputs)
                    else:
                        context, histories, strategy, _skill = self._model.actor.start_turn(
                            board,
                            units,
                            global_features,
                            previous_tokens,
                            previous_quantities,
                            previous_mask,
                            histories,
                            turn_facts,
                            turn_fact_mask,
                            economic_state,
                            strategy,
                            sample_skill=False,
                        )
                        market_values = None
                phase_seconds["start_turn"] += time.perf_counter() - phase_started

                phase_started = time.perf_counter()
                with torch.inference_mode(), _autocast(self._device):
                    compiled, traces = plan_unit_tasks(
                        self._backend,
                        self._model.tasks,
                        self._contract,
                        [game.task_session for game in games],
                        engines,
                        np.asarray(players, dtype=np.int64),
                        task_context(context),
                        compact_task_state,
                        workers=self._workers_per_stream,
                        sample=sample,
                        generator=generator,
                        record=True,
                        decision_graph=decision_graph,
                    )
                phase_seconds["task_decode"] += time.perf_counter() - phase_started

                phase_started = time.perf_counter()
                with torch.inference_mode(), _autocast(self._device):
                    market = (
                        market_graph.decode(
                            context,
                            compact_task_state,
                            compiled,
                            policy_batch,
                        )
                        if market_graph is not None
                        else decode_market_actions(
                            self._model.actor,
                            context,
                            games,
                            policy_batch,
                            compiled,
                            self._has_quantity,
                            sample=sample,
                            generator=generator,
                        )
                    )
                    if market_values is None:
                        economic_features = (
                            self._model.actor.economics.turn_features(
                                economic_state, global_features
                            )
                            if self._model.actor.economics is not None
                            and economic_state is not None
                            else None
                        )
                        market_values = self._model.market.behavior_value(
                            context.memory[:, 0],
                            global_features,
                            context.memory[:, 1:],
                            context.memory_mask[:, 1:],
                            economic_features,
                            context.strategy,
                        )
                phase_seconds["market_decode"] += time.perf_counter() - phase_started
                if architecture.turn_fact_features:
                    own_flows = np.asarray(
                        policy_batch.own_market_flow_bounds_batch(),
                        dtype=np.int64,
                    )
                    for row, game in enumerate(games):
                        if game.bounds is None:
                            raise RuntimeError("task rollout lost opponent bounds after decoding")
                        game.bounds.record_own_flow(own_flows[row])
                elapsed = time.perf_counter() - started
                maximum_actor_seconds = max(maximum_actor_seconds, elapsed)
                overage -= max(0.0, elapsed - self._act_timeout)
                if overage < 0.0:
                    raise TimeoutError("unit-task actor exhausted official overage time")

                native_rows = np.asarray(
                    [
                        row
                        for row, game in enumerate(games)
                        if game.native_opponent_session is not None
                    ],
                    dtype=np.int64,
                )
                native_future = None
                if native_rows.size:
                    native_games = [games[int(row)] for row in native_rows]
                    native_future = environment_executor.submit(
                        _step_native_games,
                        self._backend,
                        native_games,
                        market.tokens[native_rows],
                        market.quantities[native_rows],
                        market.decision_counts[native_rows],
                        market.unit_counts[native_rows],
                        min(
                            self._workers_per_stream,
                            int(native_rows.size),
                        ),
                    )
                self_play_future = None
                if self_play_rows:
                    row_index = np.asarray(self_play_rows, dtype=np.int64)
                    flat_rows = row_index.reshape(-1)
                    if np.array_equal(flat_rows, np.arange(batch_size, dtype=np.int64)):
                        self_play_tokens = market.tokens.reshape(len(self_play_rows), 2, -1)
                        self_play_quantities = market.quantities.reshape(len(self_play_rows), 2, -1)
                        self_play_decisions = market.decision_counts.reshape(len(self_play_rows), 2)
                        self_play_units = market.unit_counts.reshape(len(self_play_rows), 2)
                    else:
                        self_play_tokens = market.tokens[row_index]
                        self_play_quantities = market.quantities[row_index]
                        self_play_decisions = market.decision_counts[row_index]
                        self_play_units = market.unit_counts[row_index]
                    self_play_future = environment_executor.submit(
                        _step_self_play_games,
                        self._backend,
                        [games[row0].engine for row0, _row1 in self_play_rows],
                        self_play_tokens,
                        self_play_quantities,
                        self_play_decisions,
                        self_play_units,
                        min(self._workers_per_stream, len(self_play_rows)),
                    )

                phase_started = time.perf_counter()
                episode_map = np.arange(batch_size, dtype=np.int64)
                market_value_values = market_values.detach().float().to(device="cpu").numpy()
                if isinstance(traces, CompactTaskTrace):
                    if compact_task_panel is None:
                        compact_task_panel = CompactTaskPanel(batch_size)
                    compact_task_panel.append(traces, turn_index)
                    task_decisions += int(traces.counts.sum())
                else:
                    records = records_from_traces(traces, episode_map, turn_index)
                    task_decisions += len(records)
                    for expanded_record in records:
                        games[expanded_record.episode_index].tasks.append(expanded_record)
                market_factors += int(market.policy_factor_mask.sum())
                if rollout_panel is not None and market_mask_panel is not None:
                    column = rollout_panel.reserve()
                    rollout_panel.append_batched_reserved(
                        column,
                        BatchedStoredTurns(
                            board=board_values,
                            units=unit_values,
                            global_features=global_values,
                            economic_state=economic_values,
                            legal_mask=market.legal_mask.transpose(1, 0, 2),
                            actions=market.tokens.T,
                            quantities=market.quantities.T,
                            phases=market.phases.T,
                            decision_mask=market.decision_mask.T,
                            old_log_probability=market.old_log_probability.T,
                            skill_ids=None,
                            old_skill_log_probability=None,
                            old_values=market_value_values,
                            inactive_values_initialized=True,
                        ),
                        slice(None),
                    )
                    market_mask_panel[:, column] = market.policy_factor_mask
                else:
                    for row, game in enumerate(games):
                        count = int(market.decision_counts[row])
                        game.turns.append(
                            TurnRecord(
                                board=board_values[row].copy(),
                                units=unit_values[row].copy(),
                                global_features=global_values[row].copy(),
                                economic_state=economic_values[row].copy(),
                                turn_facts=stored_turn_facts[row],
                                prefix_facts=market.prefix_facts[row, :count].copy(),
                                candidate_facts=market.candidate_facts[row, :count].copy(),
                                legal_mask=market.legal_mask[row, :count].copy(),
                                actions=market.tokens[row, :count].copy(),
                                quantities=market.quantities[row, :count].copy(),
                                phases=market.phases[row, :count].copy(),
                                decision_mask=market.decision_mask[row, :count].copy(),
                                old_log_probability=market.old_log_probability[row, :count].copy(),
                                skill_id=-1,
                                old_skill_log_probability=0.0,
                                old_value=float(market_value_values[row]),
                            )
                        )
                        game.market_masks.append(market.policy_factor_mask[row].copy())
                phase_seconds["record"] += time.perf_counter() - phase_started

                environment_started = time.perf_counter()
                official_rows = [
                    row for row, game in enumerate(games) if game.official_opponent is not None
                ]
                market_tokens = market.tokens
                market_quantities = market.quantities
                market_decision_counts = market.decision_counts
                market_unit_counts = market.unit_counts

                def advance_official(
                    row: int,
                    tokens: IntArray = market_tokens,
                    quantities: IntArray = market_quantities,
                    decision_counts: IntArray = market_decision_counts,
                    unit_counts: IntArray = market_unit_counts,
                ) -> None:
                    game = games[row]
                    opponent = game.official_opponent
                    if opponent is None:
                        raise RuntimeError("official task opponent disappeared")
                    opponent_seat = 1 - game.seat
                    opponent_action = opponent.act(
                        cast(
                            Mapping[str, Any],
                            game.engine.observation(opponent_seat),
                        )
                    )
                    game.engine.step_mixed_numeric(
                        game.seat,
                        tokens[row],
                        quantities[row],
                        int(decision_counts[row]),
                        int(unit_counts[row]),
                        opponent_action,
                    )

                tuple(environment_executor.map(advance_official, official_rows))
                native_seconds = 0.0
                if native_future is not None:
                    native_seconds = native_future.result()
                self_play_seconds = 0.0
                if self_play_future is not None:
                    self_play_seconds = self_play_future.result()
                phase_seconds["environment"] += max(
                    native_seconds,
                    self_play_seconds,
                    time.perf_counter() - environment_started,
                )
                previous_tokens = torch.as_tensor(
                    market.tokens, dtype=torch.long, device=self._device
                )
                previous_quantities = torch.as_tensor(
                    market.quantities, dtype=torch.long, device=self._device
                )
                previous_mask = torch.as_tensor(
                    market.decision_mask, dtype=torch.bool, device=self._device
                )
                turn_index += 1
        if stream is not None:
            stream.synchronize()
        phase_seconds["cuda_graph_capture"] = (
            (0.0 if turn_graph is None else turn_graph.capture_seconds)
            - turn_capture_before
            + (0.0 if decision_graph is None else decision_graph.capture_seconds)
            - decision_capture_before
            + (0.0 if market_graph is None else market_graph.capture_seconds)
            - market_capture_before
        )

        episodes: list[TaskTapeEpisode] = []
        for row, game in enumerate(games):
            own_cash = float(game.engine.money(game.seat))
            opponent_cash = float(game.engine.money(1 - game.seat))
            outcome = int(own_cash > opponent_cash) - int(own_cash < opponent_cash)
            episode_id = f"task-{game.seed}-{game.seat}-{game.opponent_id}"
            episodes.append(
                TaskTapeEpisode(
                    trajectory=Trajectory(
                        episode_id=episode_id,
                        opponent_id=game.opponent_id,
                        seed=game.seed,
                        seat=game.seat,
                        turns=(
                            rollout_panel.trajectory(row)
                            if rollout_panel is not None
                            else tuple(game.turns)
                        ),
                        outcome=outcome,
                        terminal_cash=own_cash,
                        opponent_cash=opponent_cash,
                    ),
                    market_factor_mask=(
                        market_mask_panel[row, : rollout_panel.length]
                        if rollout_panel is not None and market_mask_panel is not None
                        else np.stack(game.market_masks)
                    ),
                    task_records=tuple(game.tasks),
                    compact_task_turns=(
                        compact_task_panel.episode(row)
                        if compact_task_panel is not None
                        else ()
                    ),
                )
            )
        for row0, row1 in self_play_rows:
            first = episodes[row0].trajectory
            second = episodes[row1].trajectory
            if (
                first.outcome != -second.outcome
                or first.terminal_cash != second.opponent_cash
                or first.opponent_cash != second.terminal_cash
            ):
                raise RuntimeError("task self-play terminal perspectives lost symmetry")
        return (
            episodes,
            maximum_actor_seconds,
            overage,
            task_decisions,
            market_factors,
            phase_seconds,
        )

    def collect(
        self,
        seeds: Sequence[int],
        *,
        update: int = 0,
        sample: bool = True,
        full_panel: bool = False,
    ) -> TaskRolloutReport:
        """Collect weighted training jobs or a full held-out opponent panel."""
        self._model.eval()
        self._model.tasks.prepare_rollout()
        if self._rollout_tasks is not self._model.tasks:
            refresh_h200_rollout_policy(
                self._rollout_tasks,
                self._model.tasks,
            )
        if self._device.type == "cuda":
            torch.cuda.current_stream(self._device).synchronize()
        jobs = (
            task_rollout_jobs(seeds, self._opponents)
            if full_panel
            else list(
                weighted_rollout_jobs(
                    seeds,
                    self._opponent_weights,
                    rank=self._rank,
                    world_size=self._world_size,
                    sampling_seed=self._sampling_seed + update * 1_000_003,
                )
            )
        )
        episodes: list[TaskTapeEpisode] = []
        maximum = 0.0
        remaining = self._initial_overage
        task_decisions = 0
        market_factors = 0
        phase_seconds: dict[str, float] = {}
        groups = _group_jobs(jobs, self._batch_games)
        active_streams = min(self._actor_streams, len(groups))

        def collect_group(
            payload: tuple[int, int, Sequence[Job]],
        ) -> tuple[
            int,
            list[TaskTapeEpisode],
            float,
            float,
            int,
            int,
            dict[str, float],
        ]:
            lane_index, group_index, group = payload
            actor_rows = sum(2 if job[2] == "self_play" else 1 for job in group)
            cuda_lane = (
                self._cuda_lane(lane_index, actor_rows) if self._device.type == "cuda" else None
            )
            generator = (
                cuda_lane.generator
                if cuda_lane is not None
                else torch.Generator(device=self._device)
            )
            generator.manual_seed(
                self._sampling_seed
                + update * 1_000_003
                + self._rank * 10_000_019
                + group_index * 2_000_033
            )
            return (
                group_index,
                *self._collect_group(
                    group,
                    generator,
                    sample=sample,
                    group_index=group_index,
                    cuda_lane=cuda_lane,
                ),
            )

        lane_payloads = [
            [
                (lane_index, group_index, groups[group_index])
                for group_index in range(lane_index, len(groups), active_streams)
            ]
            for lane_index in range(active_streams)
        ]

        def collect_lane(
            payloads: Sequence[tuple[int, int, Sequence[Job]]],
        ) -> tuple[
            tuple[
                int,
                list[TaskTapeEpisode],
                float,
                float,
                int,
                int,
                dict[str, float],
            ],
            ...,
        ]:
            return tuple(collect_group(payload) for payload in payloads)

        cudnn_sdp_enabled = bool(
            self._device.type == "cuda"
            and active_streams > 1
            and cast(
                Callable[[], bool],
                torch.backends.cuda.cudnn_sdp_enabled,
            )()
        )
        if cudnn_sdp_enabled:
            # cuDNN SDPA's execution plan can fail when one module is invoked
            # concurrently from independent CUDA streams. Flash/efficient SDPA
            # are stream-safe and retain the H200 accelerated attention path.
            torch.backends.cuda.enable_cudnn_sdp(False)
        try:
            with ThreadPoolExecutor(
                max_workers=active_streams,
                thread_name_prefix=f"task-actor-{self._rank}",
            ) as actor_executor:
                lane_results = tuple(actor_executor.map(collect_lane, lane_payloads))
                results = tuple(
                    sorted(
                        (result for lane_result in lane_results for result in lane_result),
                        key=lambda result: result[0],
                    )
                )
        finally:
            if cudnn_sdp_enabled:
                torch.backends.cuda.enable_cudnn_sdp(True)
        for result in results:
            (
                _group_index,
                group_episodes,
                elapsed,
                overage,
                tasks,
                markets,
                phases,
            ) = result
            episodes.extend(group_episodes)
            maximum = max(maximum, elapsed)
            remaining = min(remaining, overage)
            task_decisions += tasks
            market_factors += markets
            for name, seconds in phases.items():
                phase_seconds[name] = phase_seconds.get(name, 0.0) + seconds
        return TaskRolloutReport(
            episodes=tuple(episodes),
            maximum_actor_seconds=maximum,
            remaining_overage_seconds=remaining,
            task_decisions=task_decisions,
            market_factors=market_factors,
            phase_seconds=phase_seconds,
        )


__all__ = ["TaskRolloutCollector", "TaskRolloutReport", "task_rollout_jobs"]
