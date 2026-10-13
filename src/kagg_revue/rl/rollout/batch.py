"""Lockstep multi-environment rollout batching."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass
from threading import Lock
from typing import Any, Protocol, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.cuda.action_graph import CudaActionGraphs
from kagg_revue.policy.cuda.rollout_turn_graph import (
    CudaRolloutTurnGraph,
    CudaRolloutTurnInputs,
)
from kagg_revue.policy.cuda.session import GpuPolicyStateLayout
from kagg_revue.policy.economics import EconomicStateLayout
from kagg_revue.policy.economics.transition import apply_selection
from kagg_revue.policy.facts import OpponentInventoryBounds
from kagg_revue.policy.model import TurnContext
from kagg_revue.policy.runtime import NumericAction, NumericObservation
from kagg_revue.policy.transformer import HistoryState
from kagg_revue.rl.data import RolloutMatch, Trajectory, TurnRecord
from kagg_revue.rl.opening.noise import (
    OpeningResidual,
    PerspectiveKey,
    materialize_opening_residuals,
)
from kagg_revue.rl.outcome import OutcomeActorCritic
from kagg_revue.rl.rollout.storage import BatchedStoredTurns, RolloutPanel


class OfficialAgent(Protocol):
    """Untyped public or deterministic opponent boundary."""

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one official request."""


OfficialFactory = Callable[[str, Mapping[str, Any]], OfficialAgent]
ProgressCallback = Callable[[Trajectory, int, int], None]
Job = tuple[int, int, str]


def _autocast(device: torch.device) -> Any:
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.bfloat16)
    return nullcontext()


def _step_actions(engine: Any, actions: Sequence[dict[str, Any] | NumericAction]) -> None:
    numeric_seats = [
        seat for seat, action in enumerate(actions) if isinstance(action, NumericAction)
    ]
    if len(numeric_seats) == 2:
        width = max(cast(NumericAction, action).decision_count for action in actions)
        tokens = np.zeros((2, width), dtype=np.int64)
        quantities = np.zeros_like(tokens)
        decisions = np.zeros(2, dtype=np.int64)
        units = np.zeros(2, dtype=np.int64)
        for seat, raw in enumerate(actions):
            action = cast(NumericAction, raw)
            tokens[seat, : action.decision_count] = action.tokens
            quantities[seat, : action.decision_count] = action.quantities
            decisions[seat] = action.decision_count
            units[seat] = action.unit_count
        engine.step_numeric(tokens, quantities, decisions, units)
    elif len(numeric_seats) == 1:
        seat = numeric_seats[0]
        numeric = cast(NumericAction, actions[seat])
        engine.step_mixed_numeric(
            seat,
            numeric.tokens,
            numeric.quantities,
            numeric.decision_count,
            numeric.unit_count,
            actions[1 - seat],
        )
    else:
        engine.step(actions[0], actions[1])


def _select_session(payload: tuple[Any, int, int]) -> None:
    session, token, quantity = payload
    session.select(token, quantity)


def rollout_jobs(seeds: Sequence[int], opponents: Sequence[str]) -> list[Job]:
    """Return deterministic official matches for one training rollout panel.

    Self-play needs one match per seed because both policy-controlled seats are
    retained as training perspectives.  Distinct opponents remain paired by
    seat so candidate-versus-opponent outcomes stay comparable.
    """
    if not seeds:
        raise ValueError("rollout seed panel cannot be empty")
    return [
        (int(seed), seat, opponent)
        for seed in seeds
        for opponent in opponents
        for seat in ((0,) if opponent == "self_play" else (0, 1))
    ]


@dataclass
class _Game:
    engine: Any
    seed: int
    candidate_seat: int
    opponent_id: str
    official_opponent: OfficialAgent | None
    records: dict[int, list[TurnRecord]]


@dataclass
class _ActorRow:
    game: int
    player: int
    record: bool
    bounds: OpponentInventoryBounds | None
    previous_tokens: NDArray[np.int64]
    previous_quantities: NDArray[np.int64]
    previous_mask: NDArray[np.bool_]
    opening_residual: OpeningResidual | None


@dataclass(frozen=True)
class _RecordedPerspective:
    """Map one actor row to its final PPO trajectory row."""

    game: int
    player: int
    actor_row: int


@dataclass
class _ActorInputBuffers:
    """Contiguous row metadata and recurrent action inputs for one actor."""

    engines: list[Any]
    players: list[int]
    previous_tokens: NDArray[np.int64]
    previous_quantities: NDArray[np.int64]
    previous_mask: NDArray[np.bool_]
    opening_residual: NDArray[np.float32] | None
    residual_turns: int
    device_opening_residual: Tensor | None = None
    residual_disabled: bool = False


@dataclass
class _StagingBuffer:
    hosts: tuple[Tensor, Tensor]
    device: Tensor
    arrays: tuple[NDArray[np.generic], NDArray[np.generic]]


class _TensorExchange:
    """Reuse pinned host and device buffers on one rollout CUDA stream."""

    def __init__(self, device: torch.device) -> None:
        self._device = device
        self._uploads: dict[str, _StagingBuffer] = {}
        self._downloads: dict[str, tuple[Tensor, Tensor]] = {}
        self._slot = 0
        self._turn_index = 0
        self.action_graphs: CudaActionGraphs | None = None
        self.policy_turn_graph: CudaRolloutTurnGraph | None = None

    def begin_turn(self) -> int:
        """Select one of two host slots while retaining fixed device addresses."""
        self._slot = self._turn_index % 2
        self._turn_index += 1
        return self._slot

    def _upload_buffer(
        self,
        name: str,
        shape: torch.Size | tuple[int, ...],
        dtype: torch.dtype,
    ) -> _StagingBuffer:
        """Return a persistent pinned/device allocation with an exact ABI."""
        staging = self._uploads.get(name)
        if staging is None or staging.hosts[0].shape != shape or staging.hosts[0].dtype != dtype:
            hosts = tuple(
                torch.empty(
                    shape,
                    dtype=dtype,
                    device="cpu",
                    pin_memory=True,
                )
                for _ in range(2)
            )
            staging = _StagingBuffer(
                hosts=cast(tuple[Tensor, Tensor], hosts),
                device=torch.empty_like(hosts[0], device=self._device),
                arrays=cast(
                    tuple[NDArray[np.generic], NDArray[np.generic]],
                    tuple(host.numpy() for host in hosts),
                ),
            )
            self._uploads[name] = staging
        return staging

    def host_array(
        self,
        name: str,
        shape: tuple[int, ...],
        dtype: np.dtype[np.generic] | type[np.generic],
    ) -> NDArray[np.generic]:
        """Expose one persistent pinned allocation to a native ``*_into`` ABI."""
        if self._device.type != "cuda":
            raise RuntimeError("pinned rollout inputs require a CUDA device")
        normalized = np.dtype(dtype)
        torch_dtypes = {
            np.dtype(np.float16): torch.float16,
            np.dtype(np.float32): torch.float32,
            np.dtype(np.int32): torch.int32,
            np.dtype(np.int64): torch.int64,
            np.dtype(np.bool_): torch.bool,
        }
        torch_dtype = torch_dtypes.get(normalized)
        if torch_dtype is None:
            raise TypeError(f"unsupported rollout staging dtype: {normalized}")
        return self._upload_buffer(name, shape, torch_dtype).arrays[self._slot]

    def upload(self, name: str, value: NDArray[np.generic]) -> Tensor:
        """Stage one NumPy array without synchronizing its CUDA stream."""
        source = torch.from_numpy(value)
        if self._device.type != "cuda":
            return source.to(self._device)
        staging = self._upload_buffer(name, source.shape, source.dtype)
        host = staging.hosts[self._slot]
        if source.data_ptr() != host.data_ptr():
            host.copy_(source)
        staging.device.copy_(host, non_blocking=True)
        return staging.device

    def download(self, name: str, value: Tensor) -> Tensor:
        """Queue one device-to-pinned-host transfer for a later joint wait."""
        if self._device.type != "cuda":
            return value.detach().cpu()
        hosts = self._downloads.get(name)
        if hosts is None or hosts[0].shape != value.shape or hosts[0].dtype != value.dtype:
            hosts = cast(
                tuple[Tensor, Tensor],
                tuple(
                    torch.empty(
                        value.shape,
                        dtype=value.dtype,
                        device="cpu",
                        pin_memory=True,
                    )
                    for _ in range(2)
                ),
            )
            self._downloads[name] = hosts
        host = hosts[self._slot]
        host.copy_(value, non_blocking=True)
        return host

    def synchronize(self) -> None:
        """Wait once after all outputs required by the native state machine."""
        if self._device.type == "cuda":
            torch.cuda.current_stream(self._device).synchronize()

    def reset_episode(self) -> None:
        """Reset stateful graphs while retaining their fixed-address buffers."""
        self._slot = 0
        self._turn_index = 0
        if self.policy_turn_graph is not None:
            self.policy_turn_graph.reset_episode()

    def close(self) -> None:
        """Drop graph-owned and staging allocations with their persistent lane."""
        if self.action_graphs is not None:
            self.action_graphs.close()
            self.action_graphs = None
        if self.policy_turn_graph is not None:
            self.policy_turn_graph.close()
            self.policy_turn_graph = None
        self._uploads.clear()
        self._downloads.clear()


@dataclass
class _RolloutLane:
    """Fixed-shape CUDA resources reused by one rollout group across panels."""

    candidate_row_count: int
    historical_row_count: int
    generator: torch.Generator
    stream: torch.cuda.Stream | None
    exchange: _TensorExchange
    historical_generator: torch.Generator | None
    historical_stream: torch.cuda.Stream | None
    historical_exchange: _TensorExchange | None
    candidate_buffers: list[_TurnBuffer]
    historical_buffers: list[_TurnBuffer]


@dataclass
class _NumericStepBuffers:
    """Fixed-address native environment-step workspace for one group."""

    engines: list[Any]
    tokens: NDArray[np.int64]
    quantities: NDArray[np.int64]
    decision_counts: NDArray[np.int64]
    unit_counts: NDArray[np.int64]
    candidate_players: NDArray[np.int64]


@dataclass
class _RolloutGroup:
    games: list[_Game]
    rows: list[_ActorRow]
    candidate_rows: dict[int, int]
    opponent_rows: dict[int, int]
    generator: torch.Generator
    stream: torch.cuda.Stream | None
    exchange: _TensorExchange
    historical_rows: list[_ActorRow]
    historical_row_by_game: dict[int, int]
    historical_opponent_id: str | None
    historical_generator: torch.Generator | None
    historical_stream: torch.cuda.Stream | None
    historical_exchange: _TensorExchange | None
    native_official_sessions: dict[str, dict[int, Any]]
    candidate_buffers: list[_TurnBuffer]
    historical_buffers: list[_TurnBuffer]
    record_store: RolloutPanel | None
    recorded_perspectives: tuple[_RecordedPerspective, ...]
    record_rows: slice | NDArray[np.int64]
    numeric_step: _NumericStepBuffers
    candidate_inputs: _ActorInputBuffers
    historical_inputs: _ActorInputBuffers
    storage_pending: list[Future[None] | None]
    history: HistoryState | None = None
    strategy: Tensor | None = None
    historical_history: HistoryState | None = None
    historical_strategy: Tensor | None = None
    pending: tuple[Future[None], ...] = ()
    closed: bool = False
    turn_index: int = 0


@dataclass
class _TurnBuffer:
    board: NDArray[np.float32] | NDArray[np.float16]
    units: NDArray[np.float32] | NDArray[np.float16]
    globals_: NDArray[np.float32] | NDArray[np.float16]
    economic_state: NDArray[np.int32] | NDArray[np.int64]
    turn_facts: NDArray[np.float32]
    prefix_facts: NDArray[np.float16]
    candidate_facts: NDArray[np.float16]
    legal: NDArray[np.bool_]
    actions: NDArray[np.int64]
    quantities: NDArray[np.int64]
    phases: NDArray[np.int64]
    decisions: NDArray[np.bool_]
    log_probability: NDArray[np.float32]
    skill_id: int = -1
    skill_log_probability: float = 0.0
    old_value: float = 0.0

    def numeric_action(self, unit_count: int) -> NumericAction:
        """Return the selected prefix as one native action."""
        count = int(self.decisions.sum())
        if count < 1:
            raise RuntimeError("batched sampled turn contains no decisions")
        return NumericAction(
            tokens=self.actions[:count],
            quantities=self.quantities[:count],
            decision_count=count,
            unit_count=unit_count,
        )

    def record(self) -> TurnRecord:
        """Freeze the valid prefix for a later PPO update."""
        count = int(self.decisions.sum())

        def half(value: NDArray[np.float32] | NDArray[np.float16]) -> NDArray[np.float16]:
            return (
                cast(NDArray[np.float16], value)
                if value.dtype == np.float16
                else value.astype(np.float16)
            )

        def single(value: NDArray[np.float32] | NDArray[np.float16]) -> NDArray[np.float32]:
            return (
                cast(NDArray[np.float32], value)
                if value.dtype == np.float32
                else value.astype(np.float32)
            )

        return TurnRecord(
            board=half(self.board),
            units=half(self.units),
            global_features=single(self.globals_),
            economic_state=self.economic_state.copy(),
            turn_facts=self.turn_facts.astype(np.float16),
            prefix_facts=self.prefix_facts[:count].copy(),
            candidate_facts=self.candidate_facts[:count].copy(),
            legal_mask=self.legal[:count].copy(),
            actions=self.actions[:count].copy(),
            quantities=self.quantities[:count].copy(),
            phases=self.phases[:count].copy(),
            decision_mask=self.decisions[:count].copy(),
            old_log_probability=self.log_probability[:count].copy(),
            skill_id=self.skill_id,
            old_skill_log_probability=self.skill_log_probability,
            old_value=self.old_value,
        )


@dataclass(frozen=True)
class _SampledTurn:
    actions: list[NumericAction]
    records: list[_TurnBuffer | None]
    batched_records: BatchedStoredTurns | None
    history: HistoryState | None
    strategy: Tensor | None
    historical_actions: list[NumericAction] | None
    historical_history: HistoryState | None
    historical_strategy: Tensor | None
    exchange_slot: int
    elapsed_seconds: float


class _BatchedTurnSampler:
    """Prepare and sample lockstep actor turns for a bounded game batch."""

    def __init__(
        self,
        backend: BackendApi,
        model: OutcomeActorCritic,
        environment: Mapping[str, object],
        opponents: tuple[str, ...],
        official_factory: OfficialFactory,
        device: torch.device,
        unit_limit: int,
        batch_games: int,
        cpu_workers: int,
        actor_streams: int,
        gpu_policy_session: bool,
        sampling_seed: int,
        historical_models: Mapping[str, OutcomeActorCritic] | None = None,
    ) -> None:
        """Bind one frozen model snapshot and bounded environment batch."""
        self._backend = backend
        self._model = model
        self._environment = dict(environment)
        self._opponents = opponents
        self._official_factory = official_factory
        self._device = device
        self._unit_limit = unit_limit
        self._batch_games = batch_games
        self._cpu_workers = cpu_workers
        self._configured_actor_streams = actor_streams
        self._gpu_policy_session = gpu_policy_session
        self._historical_models = dict(historical_models or {})
        self._rollout_lanes: list[_RolloutLane] = []
        self._graph_initialization_lock = Lock()
        self._diagnostic_lock = Lock()
        self._active_actor_streams = 1
        self._policy_workers = cpu_workers
        self._actor_seconds = 0.0
        self._actor_work_seconds = 0.0
        self._environment_seconds = 0.0
        self._environment_wait_seconds = 0.0
        self._environment_tasks = 0
        self._groups = 0
        self._cuda_graph_groups = 0
        self._whole_turn_graph_groups = 0
        self._cuda_graph_reuse_groups = 0
        self._whole_turn_graph_reuse_groups = 0
        self._cuda_graph_capture_seconds = 0.0
        self._actor_input_work_seconds = 0.0
        self._actor_policy_work_seconds = 0.0
        self._actor_postprocess_work_seconds = 0.0
        self._historical_serial_turns = 0
        self._last_matches: list[RolloutMatch] = []
        self._opening_residuals: Mapping[PerspectiveKey, OpeningResidual] = {}
        self._force_opening_residual_buffer = False
        self._sampling_seed = sampling_seed % (2**63 - 1)
        architecture = model.actor.architecture
        episode_steps = self._environment.get("episodeSteps")
        if not isinstance(episode_steps, int) or isinstance(episode_steps, bool):
            raise TypeError("rollout environment episodeSteps must be an integer")
        if episode_steps < 2:
            raise ValueError("rollout environment must allow at least one transition")
        self._turn_capacity = episode_steps - 1
        for opponent_id, historical_model in self._historical_models.items():
            if not opponent_id:
                raise ValueError("historical opponent identity cannot be empty")
            if historical_model.actor.architecture_json() != model.actor.architecture_json():
                raise ValueError("historical opponent architecture differs from the actor")
            historical_model.eval()
        codec = cast(Mapping[str, Any], backend.action_codec_spec())
        self._unit_tokens = int(codec["unit_tokens"])
        self._has_quantity_array = np.asarray(codec["has_quantity"], dtype=np.bool_)
        self._has_quantity = torch.as_tensor(
            self._has_quantity_array, device=device, dtype=torch.bool
        )
        self._uses_facts = architecture.turn_fact_features > 0
        if self._gpu_policy_session:
            if device.type != "cuda":
                raise ValueError("GPU PolicySession rollout requires a CUDA device")
            if self._uses_facts:
                raise ValueError("GPU PolicySession rollout does not support derived facts")
        _, _, board_height, board_width = architecture.board_shape
        if board_height != board_width:
            raise ValueError("GPU PolicySession rollout requires a square board")
        raw_layout = cast(
            Mapping[str, int],
            backend.gpu_policy_state_spec(board_width, unit_limit),
        )
        self._gpu_policy_layout = GpuPolicyStateLayout.from_spec(
            raw_layout,
            board_size=board_width,
            unit_limit=unit_limit,
        )
        fact_spec = cast(Mapping[str, Any], backend.derived_fact_spec())
        self._products = int(fact_spec["products"])

    def _reset_diagnostics(self) -> None:
        """Start per-panel timings without disturbing persistent lane state."""
        self._active_actor_streams = 1
        self._policy_workers = self._cpu_workers
        self._actor_seconds = 0.0
        self._actor_work_seconds = 0.0
        self._environment_seconds = 0.0
        self._environment_wait_seconds = 0.0
        self._environment_tasks = 0
        self._groups = 0
        self._cuda_graph_groups = 0
        self._whole_turn_graph_groups = 0
        self._cuda_graph_reuse_groups = 0
        self._whole_turn_graph_reuse_groups = 0
        self._cuda_graph_capture_seconds = 0.0
        self._actor_input_work_seconds = 0.0
        self._actor_policy_work_seconds = 0.0
        self._actor_postprocess_work_seconds = 0.0
        self._historical_serial_turns = 0

    @property
    def diagnostics(self) -> dict[str, object]:
        """Return phase timing without adding synchronization to the hot path."""
        return {
            "device": str(self._device),
            "cpu_workers": self._cpu_workers,
            "actor_streams": self._active_actor_streams,
            "policy_workers_per_stream": self._policy_workers,
            "groups": self._groups,
            "actor_seconds": self._actor_seconds,
            "actor_work_seconds": self._actor_work_seconds,
            "actor_input_work_seconds": self._actor_input_work_seconds,
            "actor_policy_work_seconds": self._actor_policy_work_seconds,
            "actor_postprocess_work_seconds": self._actor_postprocess_work_seconds,
            "environment_seconds": self._environment_seconds,
            "environment_wait_seconds": self._environment_wait_seconds,
            "environment_tasks": self._environment_tasks,
            "pipeline_depth": self._groups,
            "cuda_graph_groups": self._cuda_graph_groups,
            "whole_turn_cuda_graph_groups": self._whole_turn_graph_groups,
            "full_actor_turn_cuda_graph_groups": self._whole_turn_graph_groups,
            "cuda_graph_reuse_groups": self._cuda_graph_reuse_groups,
            "whole_turn_cuda_graph_reuse_groups": (self._whole_turn_graph_reuse_groups),
            "resident_rollout_lanes": len(self._rollout_lanes),
            "gpu_policy_session": self._gpu_policy_session,
            "cuda_graph_capture_seconds": self._cuda_graph_capture_seconds,
            "historical_serial_turns": self._historical_serial_turns,
        }

    def _new_row(
        self,
        game: int,
        player: int,
        record: bool,
        opening_residual: OpeningResidual | None = None,
    ) -> _ActorRow:
        decisions = self._model.actor.architecture.max_decisions
        return _ActorRow(
            game=game,
            player=player,
            record=record,
            bounds=OpponentInventoryBounds(self._products) if self._uses_facts else None,
            previous_tokens=np.zeros(decisions, dtype=np.int64),
            previous_quantities=np.zeros(decisions, dtype=np.int64),
            previous_mask=np.zeros(decisions, dtype=np.bool_),
            opening_residual=opening_residual,
        )

    def _new_actor_inputs(
        self,
        games: list[_Game],
        rows: list[_ActorRow],
    ) -> _ActorInputBuffers:
        """Bind row objects to one allocation reused for every sampled turn."""
        shape = (len(rows), self._model.actor.architecture.max_decisions)
        tokens = np.zeros(shape, dtype=np.int64)
        quantities = np.zeros(shape, dtype=np.int64)
        mask = np.zeros(shape, dtype=np.bool_)
        for index, row in enumerate(rows):
            row.previous_tokens = tokens[index]
            row.previous_quantities = quantities[index]
            row.previous_mask = mask[index]
        architecture = self._model.actor.architecture
        identities = [row.opening_residual for row in rows]
        active_turns = {identity.prefix_turns for identity in identities if identity is not None}
        if len(active_turns) > 1:
            raise ValueError("one rollout group cannot mix opening residual horizons")
        return _ActorInputBuffers(
            engines=[games[row.game].engine for row in rows],
            players=[row.player for row in rows],
            previous_tokens=tokens,
            previous_quantities=quantities,
            previous_mask=mask,
            opening_residual=materialize_opening_residuals(
                identities,
                architecture.action_tokens,
                architecture.model_width,
                force=self._force_opening_residual_buffer or bool(self._opening_residuals),
            ),
            residual_turns=next(iter(active_turns), 0),
        )

    def _new_buffer(
        self,
        session: Any | None,
        encoded_value: NumericObservation | None = None,
        *,
        allocate_decisions: bool = True,
    ) -> _TurnBuffer:
        architecture = self._model.actor.architecture
        if encoded_value is not None:
            encoded = encoded_value
        elif session is not None:
            encoded = cast(
                NumericObservation,
                tuple(np.asarray(value, dtype=np.float32) for value in session.encode()),
            )
        else:
            encoded = cast(
                NumericObservation,
                (
                    np.empty(architecture.board_shape, dtype=np.float32),
                    np.empty(architecture.unit_shape, dtype=np.float32),
                    np.empty(architecture.global_features, dtype=np.float32),
                ),
            )
        board, units, globals_ = encoded
        turn_facts = np.zeros((0, architecture.turn_fact_features), dtype=np.float32)
        economic_width = (
            EconomicStateLayout.create(
                architecture.board_shape[-1],
                architecture.unit_shape[1],
            ).width
            if architecture.economic_feature_version is not None
            else 0
        )
        decision_capacity = architecture.max_decisions if allocate_decisions else 0
        return _TurnBuffer(
            board=board,
            units=units,
            globals_=globals_,
            economic_state=np.zeros(economic_width, dtype=np.int32),
            turn_facts=turn_facts,
            prefix_facts=np.zeros(
                (architecture.max_decisions, architecture.prefix_fact_features),
                dtype=np.float16,
            ),
            candidate_facts=np.zeros(
                (
                    architecture.max_decisions,
                    architecture.action_tokens,
                    architecture.candidate_fact_features,
                ),
                dtype=np.float16,
            ),
            legal=np.zeros((decision_capacity, architecture.action_tokens), dtype=np.bool_),
            actions=np.full(decision_capacity, -1, dtype=np.int64),
            quantities=np.zeros(decision_capacity, dtype=np.int64),
            phases=np.zeros(decision_capacity, dtype=np.int64),
            decisions=np.zeros(decision_capacity, dtype=np.bool_),
            log_probability=np.zeros(architecture.max_decisions, dtype=np.float32),
        )

    @staticmethod
    def _reuse_buffer(
        buffer: _TurnBuffer,
        encoded: NumericObservation,
        *,
        clear_decisions: bool,
    ) -> None:
        """Retarget one persistent row buffer and clear mutable turn state."""
        buffer.board, buffer.units, buffer.globals_ = encoded
        if clear_decisions:
            buffer.actions.fill(-1)
            buffer.quantities.fill(0)
            buffer.phases.fill(0)
            buffer.decisions.fill(False)
            buffer.log_probability.fill(0)
        buffer.skill_id = -1
        buffer.skill_log_probability = 0.0
        buffer.old_value = 0.0

    def _turn_input(self, payload: tuple[list[_Game], _ActorRow]) -> tuple[Any, _TurnBuffer]:
        games, row = payload
        architecture = self._model.actor.architecture
        session = games[row.game].engine.policy_session(row.player, self._unit_limit)
        buffer = self._new_buffer(session)
        if self._uses_facts:
            if row.bounds is None:
                raise RuntimeError("batched fact actor lacks opponent bounds")
            lower, upper = row.bounds.update(cast(Mapping[str, Any], session.flow_snapshot()))
            buffer.turn_facts = np.asarray(session.turn_facts(lower, upper), dtype=np.float32)
            if buffer.turn_facts.ndim != 2 or buffer.turn_facts.shape[1] != (
                architecture.turn_fact_features
            ):
                raise ValueError("batched rollout turn facts differ from the actor")
        return session, buffer

    def _turn_inputs(
        self,
        games: list[_Game],
        rows: list[_ActorRow],
        executor: ThreadPoolExecutor,
        exchange: _TensorExchange,
        reusable_buffers: list[_TurnBuffer] | None,
        actor_inputs: _ActorInputBuffers,
    ) -> tuple[
        list[Any],
        list[_TurnBuffer],
        NumericObservation | None,
        NDArray[np.int64] | None,
        Any | None,
        Tensor | None,
        Tensor | None,
        Tensor | None,
    ]:
        architecture = self._model.actor.architecture
        if not self._uses_facts:
            if self._gpu_policy_session:
                batch = len(rows)
                board_output = exchange.host_array(
                    "turn_board",
                    (batch, *architecture.board_shape),
                    np.float16,
                )
                unit_output = exchange.host_array(
                    "turn_units",
                    (batch, *architecture.unit_shape),
                    np.float16,
                )
                global_output = exchange.host_array(
                    "turn_globals",
                    (batch, architecture.global_features),
                    np.float32,
                )
                count_output = exchange.host_array(
                    "turn_unit_counts",
                    (batch,),
                    np.int64,
                )
                state_output = exchange.host_array(
                    "gpu_policy_state",
                    (batch, self._gpu_policy_layout.width),
                    np.int32,
                )
                self._backend.engine_policy_turn_inputs_compact_into(
                    actor_inputs.engines,
                    actor_inputs.players,
                    self._unit_limit,
                    self._policy_workers,
                    board_output,
                    unit_output,
                    global_output,
                    count_output,
                    state_output,
                )
                sessions: list[Any] = []
                encoded = cast(
                    NumericObservation,
                    (board_output, unit_output, global_output),
                )
                unit_counts = cast(NDArray[np.int64], count_output)
                policy_state_value = cast(NDArray[np.int32], state_output)
                policy_batch = None
            else:
                sessions = [
                    games[row.game].engine.policy_session(
                        row.player,
                        self._unit_limit,
                    )
                    for row in rows
                ]
                policy_batch = self._backend.policy_session_batch(
                    sessions,
                    self._policy_workers,
                )
                unit_counts = None
                encoded = cast(
                    NumericObservation,
                    tuple(np.asarray(value, dtype=np.float32) for value in policy_batch.encode()),
                )
                policy_state_value = None
                if architecture.economic_feature_version is not None:
                    economic_state_values = np.asarray(
                        policy_batch.gpu_state(),
                        dtype=np.int32,
                    )
                    if economic_state_values.shape != (
                        len(rows),
                        self._gpu_policy_layout.width,
                    ):
                        raise ValueError("native economic state differs from the actor")
                    for index, buffer in enumerate(reusable_buffers or ()):
                        buffer.economic_state = economic_state_values[index]
            if reusable_buffers is None or len(reusable_buffers) != len(rows):
                raise RuntimeError("raw rollout lacks its persistent row buffers")
            buffers = reusable_buffers
            for index, buffer in enumerate(buffers):
                self._reuse_buffer(
                    buffer,
                    cast(
                        NumericObservation,
                        tuple(value[index] for value in encoded),
                    ),
                    clear_decisions=not self._gpu_policy_session,
                )
            if self._gpu_policy_session:
                if policy_state_value is None:
                    raise RuntimeError("GPU rollout lacks compact policy state")
                policy_state = exchange.upload(
                    "gpu_policy_state",
                    policy_state_value,
                )
                if architecture.economic_feature_version is not None:
                    for index, buffer in enumerate(buffers):
                        buffer.economic_state = policy_state_value[index]
            else:
                policy_state = None
            return (
                sessions,
                buffers,
                encoded,
                unit_counts,
                policy_batch,
                None,
                None,
                policy_state,
            )
        values = tuple(executor.map(self._turn_input, ((games, row) for row in rows)))
        sessions = [value[0] for value in values]
        buffers = [value[1] for value in values]
        maximum = max(buffer.turn_facts.shape[0] for buffer in buffers)
        facts = np.zeros((len(rows), maximum, architecture.turn_fact_features), dtype=np.float32)
        mask = np.zeros((len(rows), maximum), dtype=np.bool_)
        for index, buffer in enumerate(buffers):
            count = buffer.turn_facts.shape[0]
            facts[index, :count] = buffer.turn_facts
            mask[index, :count] = True
        return (
            sessions,
            buffers,
            None,
            None,
            None,
            exchange.upload("turn_facts", facts),
            exchange.upload("turn_fact_mask", mask),
            None,
        )

    def _decision_inputs(
        self,
        sessions: list[Any],
        buffers: list[_TurnBuffer],
        decision: int,
        executor: ThreadPoolExecutor,
        policy_batch: Any | None,
        exchange: _TensorExchange,
    ) -> tuple[
        NDArray[np.bool_],
        NDArray[np.int64],
        Tensor,
        Tensor | None,
        Tensor | None,
        Tensor,
    ]:
        architecture = self._model.actor.architecture
        active = np.asarray([int(session.phase) != 2 for session in sessions], dtype=np.bool_)
        phases = np.zeros(len(sessions), dtype=np.int64)
        legal = np.zeros((len(sessions), architecture.action_tokens), dtype=np.bool_)
        prefix = np.zeros((len(sessions), architecture.prefix_fact_features), dtype=np.float32)
        candidates = np.zeros(
            (
                len(sessions),
                architecture.action_tokens,
                architecture.candidate_fact_features,
            ),
            dtype=np.float32,
        )
        if not self._uses_facts:
            if policy_batch is None:
                raise RuntimeError("raw rollout lacks a native policy-session batch")
            raw_phase_values, raw_legal_values = policy_batch.decision_inputs()
            raw_phases = np.asarray(raw_phase_values, dtype=np.int64)
            active = raw_phases != 2
            phases = raw_phases.copy()
            phases[~active] = 0
            legal = np.asarray(raw_legal_values, dtype=np.bool_)
            if phases.shape != (len(sessions),) or legal.shape != (
                len(sessions),
                architecture.action_tokens,
            ):
                raise ValueError("native policy-session batch differs from the actor")
            legal[~active, 0] = True
            for native_index in np.flatnonzero(active):
                if not legal[native_index].any():
                    raise ValueError("batched rollout session contains no legal action")
                buffers[native_index].phases[decision] = phases[native_index]
                buffers[native_index].legal[decision] = legal[native_index]
            return (
                active,
                phases,
                exchange.upload("decision_phases", phases),
                None,
                None,
                exchange.upload("decision_legal", legal),
            )
        active_indices = np.flatnonzero(active)
        for index in active_indices:
            session = sessions[int(index)]
            phases[index] = int(session.phase)
        expensive = [
            int(index) for index in active_indices if phases[index] == 0 or self._uses_facts
        ]

        def session_values(index: int) -> tuple[int, NDArray[np.bool_], Any, Any]:
            session = sessions[index]
            return (
                index,
                np.asarray(session.legal_mask(), dtype=np.bool_),
                session.prefix_facts() if self._uses_facts else None,
                session.candidate_facts() if self._uses_facts else None,
            )

        for fact_index, legal_value, prefix_value, candidate_value in executor.map(
            session_values, expensive
        ):
            legal[fact_index] = legal_value
            if self._uses_facts:
                prefix[fact_index] = np.asarray(prefix_value, dtype=np.float32)
                candidates[fact_index] = np.asarray(candidate_value, dtype=np.float32)
        for index in active_indices:
            if not legal[index].any():
                raise ValueError("batched rollout session contains no legal action")
            buffers[index].phases[decision] = phases[index]
            buffers[index].legal[decision] = legal[index]
            if self._uses_facts:
                buffers[index].prefix_facts[decision] = prefix[index]
                buffers[index].candidate_facts[decision] = candidates[index]
        legal[~active, 0] = True
        return (
            active,
            phases,
            exchange.upload("decision_phases", phases),
            exchange.upload("decision_prefix", prefix) if self._uses_facts else None,
            (exchange.upload("decision_candidates", candidates) if self._uses_facts else None),
            exchange.upload("decision_legal", legal),
        )

    def _sample_whole_gpu_turn(
        self,
        model: OutcomeActorCritic,
        inputs: CudaRolloutTurnInputs,
        encoded: NumericObservation,
        buffers: list[_TurnBuffer],
        generator: torch.Generator,
        exchange: _TensorExchange,
        *,
        record_behavior: bool,
    ) -> BatchedStoredTurns | None:
        """Replay one complete GPU-resident PolicySession and download once."""
        if exchange.policy_turn_graph is None:
            sampling_state = generator.get_state()
            exchange.policy_turn_graph = CudaRolloutTurnGraph(
                model.actor,
                inputs,
                self._gpu_policy_layout,
                self._has_quantity,
                generator,
                behavior_value=(model.behavior_value if record_behavior else None),
            )
            generator.set_state(sampling_state)
            self._cuda_graph_groups += 1
            self._whole_turn_graph_groups += 1
            self._cuda_graph_capture_seconds += exchange.policy_turn_graph.capture_seconds
        graph = exchange.policy_turn_graph
        graph.start_turn(inputs)
        graph.replay()
        token_host = exchange.download("turn_tokens", graph.tokens)
        quantity_host = exchange.download("turn_quantities", graph.quantities)
        decision_host = exchange.download("turn_decisions", graph.decisions)
        final_phase_host = exchange.download("turn_final_phases", graph.final_phases)
        phase_host = exchange.download("turn_phases", graph.phases) if record_behavior else None
        legal_host = exchange.download("turn_legal", graph.legal) if record_behavior else None
        log_probability = graph.log_probabilities
        value = graph.value
        if record_behavior and (log_probability is None or value is None):
            raise RuntimeError("rollout CUDA Graph omitted requested behavior statistics")
        log_probability_host = (
            exchange.download("turn_log_probabilities", log_probability)
            if log_probability is not None
            else None
        )
        value_host = exchange.download("turn_values", value) if value is not None else None
        skill_ids = graph.skill_ids if record_behavior else None
        skill_log_probability = graph.skill_log_probability if record_behavior else None
        skill_id_host = (
            exchange.download("turn_skill_ids", skill_ids) if skill_ids is not None else None
        )
        skill_log_probability_host = (
            exchange.download("turn_skill_log_probabilities", skill_log_probability)
            if skill_log_probability is not None
            else None
        )
        exchange.synchronize()
        final_phases = final_phase_host.numpy()
        if np.any(final_phases != 2):
            raise RuntimeError("whole-turn CUDA Graph exceeded actor decision capacity")
        token_values = token_host.numpy()
        quantity_values = quantity_host.numpy().astype(np.int64, copy=False)
        decision_values = decision_host.numpy()
        phase_values = None if phase_host is None else phase_host.numpy()
        legal_values = None if legal_host is None else legal_host.numpy()
        log_probability_values = (
            None if log_probability_host is None else log_probability_host.numpy()
        )
        value_values = None if value_host is None else value_host.numpy()
        skill_id_values = None if skill_id_host is None else skill_id_host.numpy()
        skill_log_probability_values = (
            None if skill_log_probability_host is None else skill_log_probability_host.numpy()
        )
        for index, buffer in enumerate(buffers):
            if not decision_values[:, index].any():
                raise RuntimeError("whole-turn CUDA Graph produced an empty action")
            buffer.actions = token_values[:, index]
            buffer.quantities = quantity_values[:, index]
            buffer.decisions = decision_values[:, index]
            if phase_values is not None and legal_values is not None:
                buffer.phases = phase_values[:, index]
                buffer.legal = legal_values[:, index]
            if log_probability_values is not None:
                buffer.log_probability = log_probability_values[:, index]
            if value_values is not None:
                buffer.old_value = float(value_values[index])
            if skill_id_values is not None:
                buffer.skill_id = int(skill_id_values[index])
            if skill_log_probability_values is not None:
                buffer.skill_log_probability = float(skill_log_probability_values[index])
        if not record_behavior:
            return None
        if (
            phase_values is None
            or legal_values is None
            or log_probability_values is None
            or value_values is None
        ):
            raise RuntimeError("rollout CUDA Graph omitted batched behavior arrays")
        if (
            encoded[0].dtype != np.float16
            or encoded[1].dtype != np.float16
            or encoded[2].dtype != np.float32
        ):
            raise RuntimeError("whole-turn rollout observations violate the FP16/FP32 compact ABI")
        return BatchedStoredTurns(
            board=cast(NDArray[np.float16], encoded[0]),
            units=cast(NDArray[np.float16], encoded[1]),
            global_features=encoded[2],
            economic_state=np.stack([buffer.economic_state for buffer in buffers]),
            legal_mask=cast(NDArray[np.bool_], legal_values),
            actions=cast(NDArray[np.int64], token_values),
            quantities=quantity_values,
            phases=cast(NDArray[np.int64], phase_values),
            decision_mask=cast(NDArray[np.bool_], decision_values),
            old_log_probability=cast(NDArray[np.float32], log_probability_values),
            skill_ids=(
                None if skill_id_values is None else cast(NDArray[np.int64], skill_id_values)
            ),
            old_skill_log_probability=(
                None
                if skill_log_probability_values is None
                else cast(NDArray[np.float32], skill_log_probability_values)
            ),
            old_values=cast(NDArray[np.float32], value_values),
        )

    def _sample_turn(
        self,
        games: list[_Game],
        rows: list[_ActorRow],
        history: HistoryState | None,
        strategy: Tensor | None,
        executor: ThreadPoolExecutor,
        generator: torch.Generator,
        exchange: _TensorExchange,
        reusable_buffers: list[_TurnBuffer] | None,
        actor_inputs: _ActorInputBuffers,
        model: OutcomeActorCritic | None = None,
    ) -> tuple[
        list[NumericAction],
        list[_TurnBuffer | None],
        HistoryState | None,
        Tensor | None,
        BatchedStoredTurns | None,
    ]:
        input_started = time.perf_counter()
        active_model = self._model if model is None else model
        architecture = active_model.actor.architecture
        (
            sessions,
            buffers,
            encoded_batch,
            gpu_unit_counts,
            policy_batch,
            turn_facts,
            turn_fact_mask,
            policy_state,
        ) = self._turn_inputs(
            games,
            rows,
            executor,
            exchange,
            reusable_buffers,
            actor_inputs,
        )
        board_values = (
            encoded_batch[0]
            if encoded_batch is not None
            else np.stack([buffer.board for buffer in buffers])
        )
        unit_values = (
            encoded_batch[1]
            if encoded_batch is not None
            else np.stack([buffer.units for buffer in buffers])
        )
        global_values = (
            encoded_batch[2]
            if encoded_batch is not None
            else np.stack([buffer.globals_ for buffer in buffers])
        )
        board = exchange.upload("turn_board", board_values)
        units = exchange.upload("turn_units", unit_values)
        globals_ = exchange.upload("turn_globals", global_values)
        previous_tokens = exchange.upload("previous_tokens", actor_inputs.previous_tokens)
        previous_quantities = exchange.upload(
            "previous_quantities",
            actor_inputs.previous_quantities,
        )
        previous_mask = exchange.upload("previous_mask", actor_inputs.previous_mask)
        if (
            actor_inputs.opening_residual is not None
            and actor_inputs.device_opening_residual is None
        ):
            actor_inputs.device_opening_residual = exchange.upload(
                "opening_residual",
                actor_inputs.opening_residual,
            )
        action_head_noise = actor_inputs.device_opening_residual
        economic_state = None
        if architecture.economic_feature_version is not None:
            economic_state = (
                policy_state
                if policy_state is not None
                else exchange.upload(
                    "economic_state",
                    np.stack([buffer.economic_state for buffer in buffers]),
                )
            )
        input_elapsed = time.perf_counter() - input_started
        policy_started = time.perf_counter()
        eager_skill_id_host: Tensor | None = None
        batched_records: BatchedStoredTurns | None = None
        with torch.inference_mode(), _autocast(self._device):
            context: TurnContext | None = None
            next_history: HistoryState | None
            next_strategy: Tensor | None
            if policy_state is not None:
                if history is not None:
                    raise RuntimeError("episode CUDA Graph history escaped its owner")
                if encoded_batch is None:
                    raise RuntimeError("GPU PolicySession lacks encoded observations")
                batched_records = self._sample_whole_gpu_turn(
                    active_model,
                    CudaRolloutTurnInputs(
                        board=board,
                        units=units,
                        global_features=globals_,
                        previous_actions=previous_tokens,
                        previous_quantities=previous_quantities,
                        previous_mask=previous_mask,
                        policy_state=policy_state,
                        action_head_noise=action_head_noise,
                    ),
                    encoded_batch,
                    buffers,
                    generator,
                    exchange,
                    record_behavior=any(row.record for row in rows),
                )
                next_history = None
                next_strategy = None
            else:
                context, next_history, next_strategy, skill = active_model.actor.start_turn(
                    board,
                    units,
                    globals_,
                    previous_tokens,
                    previous_quantities,
                    previous_mask,
                    history,
                    turn_facts,
                    turn_fact_mask,
                    economic_state,
                    strategy,
                    sample_skill=True,
                    generator=generator,
                )
                if skill is not None:
                    eager_skill_id_host = exchange.download("turn_skill_ids", skill.ids)
            use_graph = (
                self._device.type == "cuda"
                and self._active_actor_streams == 1
                and not self._uses_facts
                and policy_state is None
                and architecture.economic_feature_version is None
            )
            if use_graph and exchange.action_graphs is None:
                if context is None:
                    raise RuntimeError("action graph lacks current-turn context")
                exchange.action_graphs = CudaActionGraphs(
                    active_model.actor,
                    context,
                    self._has_quantity,
                    generator,
                    action_head_noise,
                )
                self._cuda_graph_groups += 1
                self._cuda_graph_capture_seconds += exchange.action_graphs.capture_seconds
            graph = exchange.action_graphs if use_graph else None
            if graph is not None:
                if context is None:
                    raise RuntimeError("action graph lacks current-turn context")
                graph.start_turn(context, action_head_noise)
                action_state = None
            elif policy_state is None:
                if context is None:
                    raise RuntimeError("eager decoder lacks current-turn context")
                action_state = active_model.actor.action.initial_state(context)
            else:
                action_state = None
            previous_token: Tensor | None = None
            previous_quantity: Tensor | None = None
            for decision in range(architecture.max_decisions):
                if policy_state is not None:
                    break
                (
                    active,
                    phase_values,
                    phases,
                    prefix,
                    candidates,
                    legal,
                ) = self._decision_inputs(
                    sessions,
                    buffers,
                    decision,
                    executor,
                    policy_batch,
                    exchange,
                )
                if not active.any():
                    break
                if graph is not None:
                    token, quantity = graph.step(decision, phases, legal)
                else:
                    if action_state is None:
                        raise RuntimeError("eager decoder lacks action state")
                    if context is None:
                        raise RuntimeError("eager decoder lacks current-turn context")
                    economic_prefix = None
                    economic_candidates = None
                    if active_model.actor.economics is not None:
                        if economic_state is None:
                            raise RuntimeError("economic decoder lacks compact state")
                        economic_prefix = active_model.actor.economics.prefix_features(
                            economic_state,
                            phases,
                        )
                        economic_candidates = active_model.actor.economics.candidate_features(
                            economic_state,
                            phases,
                        )
                    logits, hidden, action_state = active_model.actor.action.next_cached(
                        previous_token,
                        previous_quantity,
                        phases,
                        context,
                        action_state,
                        prefix,
                        candidates,
                        economic_prefix,
                        economic_candidates,
                        action_head_noise,
                    )
                    logits = logits.float().masked_fill(~legal, -torch.inf)
                    probabilities = torch.softmax(logits, dim=-1)
                    token = torch.multinomial(
                        probabilities,
                        1,
                        generator=generator,
                    ).squeeze(-1)
                    selected_candidate = (
                        candidates[torch.arange(token.shape[0], device=self._device), token]
                        if candidates is not None
                        else None
                    )
                    quantity_logits = active_model.actor.action.quantity_logits(
                        hidden,
                        token,
                        selected_candidate,
                        (
                            active_model.actor.economics.quantity_features(
                                economic_state,
                                token,
                            )
                            if active_model.actor.economics is not None
                            and economic_state is not None
                            else None
                        ),
                    )
                    sampled_quantity = active_model.actor.choose_quantity(
                        quantity_logits,
                        sample=True,
                        generator=generator,
                    )
                    quantity_mask = self._has_quantity[token]
                    quantity = torch.where(
                        quantity_mask,
                        sampled_quantity,
                        torch.zeros_like(sampled_quantity),
                    )
                    if active_model.actor.economics is not None:
                        if economic_state is None:
                            raise RuntimeError("economic decoder lost compact state")
                        apply_selection(
                            economic_state,
                            token,
                            quantity,
                            exchange.upload("decision_active", active),
                            active_model.actor.economics.layout,
                        )
                token_host = exchange.download("selected_tokens", token)
                quantity_host = exchange.download("selected_quantities", quantity)
                exchange.synchronize()
                token_values = token_host.numpy()
                quantity_values = quantity_host.numpy()
                active_indices = np.flatnonzero(active)
                if policy_batch is not None:
                    policy_batch.select(token_values, quantity_values, active)
                else:
                    unit_indices = [
                        int(index) for index in active_indices if phase_values[index] == 0
                    ]
                    tuple(
                        executor.map(
                            _select_session,
                            (
                                (
                                    sessions[index],
                                    int(token_values[index]),
                                    int(quantity_values[index]),
                                )
                                for index in unit_indices
                            ),
                        )
                    )
                    for active_index in active_indices:
                        row_index = int(active_index)
                        if phase_values[row_index] != 0:
                            _select_session(
                                (
                                    sessions[row_index],
                                    int(token_values[row_index]),
                                    int(quantity_values[row_index]),
                                )
                            )
                for active_index in active_indices:
                    row_index = int(active_index)
                    buffers[row_index].actions[decision] = int(token_values[row_index])
                    buffers[row_index].quantities[decision] = int(quantity_values[row_index])
                    buffers[row_index].decisions[decision] = True
                previous_token = token
                previous_quantity = quantity
            if policy_state is None and any(int(session.phase) != 2 for session in sessions):
                raise RuntimeError("batched sampled action exceeded actor decision capacity")
        policy_elapsed = time.perf_counter() - policy_started
        postprocess_started = time.perf_counter()
        if eager_skill_id_host is not None:
            exchange.synchronize()
            skill_id_values = eager_skill_id_host.numpy()
            for index, buffer in enumerate(buffers):
                buffer.skill_id = int(skill_id_values[index])
        actions: list[NumericAction] = []
        records: list[_TurnBuffer | None] = []
        for row_index, (actor_row, buffer) in enumerate(zip(rows, buffers, strict=True)):
            session = sessions[row_index] if sessions else None
            if actor_row.bounds is not None:
                if session is None:
                    raise RuntimeError("derived-fact rollout lacks a policy session")
                actor_row.bounds.record_own_flow(session.own_market_flow_bounds())
            if gpu_unit_counts is not None:
                unit_count = int(gpu_unit_counts[row_index])
            elif session is not None:
                unit_count = int(session.unit_count)
            else:
                raise RuntimeError("rollout row lacks an exact unit count")
            action = buffer.numeric_action(unit_count)
            count = action.decision_count
            actor_row.previous_tokens.fill(0)
            actor_row.previous_quantities.fill(0)
            actor_row.previous_mask.fill(False)
            actor_row.previous_tokens[:count] = action.tokens
            actor_row.previous_quantities[:count] = action.quantities
            actor_row.previous_mask[:count] = True
            actions.append(action)
            records.append(buffer if actor_row.record else None)
        postprocess_elapsed = time.perf_counter() - postprocess_started
        with self._diagnostic_lock:
            self._actor_input_work_seconds += input_elapsed
            self._actor_policy_work_seconds += policy_elapsed
            self._actor_postprocess_work_seconds += postprocess_elapsed
        return actions, records, next_history, next_strategy, batched_records


__all__ = ["OfficialFactory", "rollout_jobs"]
