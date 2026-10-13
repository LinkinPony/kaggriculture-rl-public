"""Batched complete native matches for conditional-program PPO."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.native_batch import (
    create_native_opponent_session,
    step_native_opponent_batch,
)
from kagg_revue.opponents.registry import trusted_runtime_identity
from kagg_revue.policy.cuda.capture import serialized_graph_build
from kagg_revue.policy.programs.gpu import (
    ProgramDecisionGraphShards,
    ProgramGpuTurnSwitchGraph,
    ProgramTurnGraph,
    ProgramTurnInputs,
)
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.runtime import (
    compact_mask_width,
    decode_program_turn,
    decode_program_turn_cuda,
    program_context,
)
from kagg_revue.policy.transformer import HistoryState
from kagg_revue.rl.programs.data import ProgramEpisode
from kagg_revue.rl.programs.model import ProgramActorCritic
from kagg_revue.rl.programs.observer import ProgramRolloutObserver
from kagg_revue.rl.programs.storage import (
    ProgramGpuGroupStorage,
    ProgramGroupStorage,
)
from kagg_revue.rl.rollout.population import weighted_rollout_jobs

Job = tuple[int, int, str]


@dataclass
class _Game:
    """Episode-local engine, compiler, and opponent state."""

    engine: Any
    match_index: int
    seed: int
    seat: int
    opponent_id: str
    program_session: Any
    opponent_session: Any | None


@dataclass(frozen=True)
class ProgramRolloutReport:
    """Complete episodes and direct inference diagnostics."""

    episodes: tuple[ProgramEpisode, ...]
    physical_games: int
    maximum_actor_seconds: float
    remaining_overage_seconds: float
    official_turns: int
    program_decisions: int
    official_decisions: int
    host_bytes: int
    device_bytes: int
    phase_seconds: Mapping[str, float]
    program_phase_seconds: Mapping[str, float]
    rank_seconds: tuple[float, ...]


def _autocast(device: torch.device) -> Any:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


def _group_jobs(jobs: Sequence[Job], actor_capacity: int) -> tuple[tuple[Job, ...], ...]:
    """Pack physical matches by their live-policy row count."""
    groups: list[tuple[Job, ...]] = []
    current: list[Job] = []
    rows = 0
    for job in jobs:
        required = 2 if job[2] == "self_play" else 1
        if required > actor_capacity:
            raise ValueError("conditional-program batch cannot hold one self-play match")
        if current and rows + required > actor_capacity:
            groups.append(tuple(current))
            current = []
            rows = 0
        current.append(job)
        rows += required
    if current:
        groups.append(tuple(current))
    return tuple(groups)


class ProgramRolloutCollector:
    """Collect paired complete matches through native program compilation."""

    def __init__(
        self,
        backend: BackendApi,
        model: ProgramActorCritic,
        contract: NativeProgramContract,
        repository_root: Path,
        public_agent_manifest: Path | None,
        environment: Mapping[str, object],
        opponent_weights: Mapping[str, float],
        device: torch.device,
        *,
        batch_games: int,
        cpu_workers: int,
        actor_streams: int,
        cpu_threads: int,
        host_memory_limit_gib: float,
        sampling_seed: int,
        act_timeout_seconds: float,
        remaining_overage_seconds: float,
        use_cuda_graphs: bool = True,
        use_full_turn_graph: bool = False,
        observer: ProgramRolloutObserver | None = None,
        rank: int = 0,
        world_size: int = 1,
    ) -> None:
        """Authenticate a native-only opponent population and runtime limits."""
        self._backend = backend
        self._model = model
        self._contract = contract
        self._environment = dict(environment)
        self._weights = dict(opponent_weights)
        self._device = device
        self._batch_games = batch_games
        self._workers = cpu_workers
        self._actor_streams = actor_streams
        self._host_limit = int(host_memory_limit_gib * 1024**3)
        self._sampling_seed = sampling_seed
        self._act_timeout = act_timeout_seconds
        self._initial_overage = remaining_overage_seconds
        self._use_cuda_graphs = use_cuda_graphs
        self._use_full_turn_graph = use_full_turn_graph
        self._observer = observer
        if rank < 0 or rank >= world_size:
            raise ValueError("conditional-program rollout rank is invalid")
        self._rank = rank
        self._world_size = world_size
        episode_steps = self._environment.get("episodeSteps")
        market_orders = self._environment.get("maxMarketOrdersPerTurn")
        if not isinstance(episode_steps, int) or isinstance(episode_steps, bool):
            raise ValueError("conditional-program rollout lacks integer episodeSteps")
        if not isinstance(market_orders, int) or isinstance(market_orders, bool):
            raise ValueError("conditional-program rollout lacks market order capacity")
        turns_per_day = self._environment.get("turnsPerDay")
        if not isinstance(turns_per_day, int) or isinstance(turns_per_day, bool):
            raise ValueError("conditional-program rollout lacks integer turnsPerDay")
        self._turn_capacity = episode_steps - 1
        self._market_orders = market_orders
        self._turns_per_day = turns_per_day
        public_opponents = tuple(
            opponent
            for opponent in self._weights
            if opponent not in {"self_play", "deterministic_incumbent"}
        )
        records: Mapping[str, Any] = {}
        if public_opponents:
            if public_agent_manifest is None:
                raise ValueError("public conditional-program opponents require a manifest")
            manifest_path = (
                public_agent_manifest
                if public_agent_manifest.is_absolute()
                else repository_root / public_agent_manifest
            )
            records = backend.load_public_agent_manifest(manifest_path).by_id()
        self._opponent_identities: dict[str, object] = {}
        for opponent in self._weights:
            if opponent == "self_play":
                self._opponent_identities[opponent] = {
                    "kind": "self_play",
                    "identity": "current_live_conditional_program_policy",
                    "training_perspectives_per_match": 2,
                }
                continue
            if opponent == "deterministic_incumbent":
                self._opponent_identities[opponent] = {"kind": "native_deterministic_incumbent"}
                continue
            record = records.get(opponent)
            identity = None if record is None else trusted_runtime_identity(record)
            if (
                record is None
                or identity is None
                or opponent not in backend.native_opponent_batch_steps
            ):
                raise KeyError(
                    f"conditional-program PPO requires authenticated native opponents: {opponent}"
                )
            self._opponent_identities[opponent] = {
                "kind": "public_notebook_native",
                "notebook_ref": record.notebook_ref,
                "notebook_id": record.notebook_id,
                "artifact_sha256": record.sha256,
                "native_runtime": identity,
            }
        architecture = model.actor.architecture
        if architecture.unit_shape[1] != contract.unit_limit:
            raise ValueError("conditional-program rollout model and compiler differ")
        if architecture.max_decisions < contract.maximum_decisions:
            raise ValueError("conditional-program action history is too short")
        if contract.maximum_market_orders != market_orders:
            raise ValueError("conditional-program contract and environment differ")
        if architecture.turn_fact_features or architecture.skill_tokens:
            raise ValueError("conditional-program rollout cannot reproduce actor context")
        if device.type == "cpu":
            torch.set_num_threads(cpu_threads)
        if actor_streams > batch_games // 2:
            raise ValueError("conditional-program rollout has too many actor streams")
        if device.type != "cuda" and actor_streams != 1:
            raise ValueError("conditional-program CPU rollout requires one actor stream")
        self._turn_graphs: dict[int, ProgramTurnGraph] = {}
        self._program_generators: dict[int, torch.Generator] = {}
        self._decision_graphs: dict[int, ProgramDecisionGraphShards] = {}
        self._program_graphs: dict[tuple[int, bool], ProgramGpuTurnSwitchGraph] = {}

    def close(self) -> None:
        """Release CUDA Graph pools retained across rollout panels."""
        for turn_graph in self._turn_graphs.values():
            turn_graph.close()
        self._turn_graphs.clear()
        for decision_graph in self._decision_graphs.values():
            decision_graph.close()
        self._decision_graphs.clear()
        for program_graph in self._program_graphs.values():
            program_graph.close()
        self._program_graphs.clear()
        self._program_generators.clear()

    @property
    def opponent_identities(self) -> Mapping[str, object]:
        """Return the authenticated native population bound to this collector."""
        return self._opponent_identities

    def _program_session(self) -> Any:
        return self._backend.conditional_program_session(
            self._environment, self._contract.unit_limit
        )

    def _opponent_session(self, opponent: str) -> Any | None:
        if opponent == "self_play":
            return None
        if opponent == "deterministic_incumbent":
            return self._backend.deterministic_incumbent_session(self._environment)
        return create_native_opponent_session(opponent, self._market_orders)

    def _games(self, jobs: Sequence[Job]) -> list[_Game]:
        games: list[_Game] = []
        for match_index, (seed, seat, opponent) in enumerate(jobs):
            engine = self._backend.engine(seed, self._environment)
            seats = (0, 1) if opponent == "self_play" else (seat,)
            for player in seats:
                games.append(
                    _Game(
                        engine=engine,
                        match_index=match_index,
                        seed=seed,
                        seat=player,
                        opponent_id=opponent,
                        program_session=self._program_session(),
                        opponent_session=self._opponent_session(opponent),
                    )
                )
        return games

    def _advance(self, games: Sequence[_Game], rollout: Any) -> None:
        self_play: list[tuple[int, int]] = []
        by_match: dict[int, dict[int, int]] = {}
        for row, game in enumerate(games):
            if game.opponent_id == "self_play":
                by_match.setdefault(game.match_index, {})[game.seat] = row
        for rows in by_match.values():
            if set(rows) != {0, 1}:
                raise RuntimeError("conditional-program self-play lost one seat")
            self_play.append((rows[0], rows[1]))
        if self_play:
            indices = np.asarray(self_play, dtype=np.int64)
            self._backend.engine_step_numeric_batch(
                [games[first].engine for first, _second in self_play],
                rollout.compiled.tokens[indices],
                rollout.compiled.quantities[indices],
                rollout.compiled.decision_counts[indices],
                rollout.compiled.unit_counts[indices],
                min(self._workers, len(self_play)),
            )
        native_rows = np.asarray(
            [row for row, game in enumerate(games) if game.opponent_id != "self_play"],
            dtype=np.int64,
        )
        if native_rows.size:
            selected = [games[int(row)] for row in native_rows]
            step_native_opponent_batch(
                self._backend,
                [game.engine for game in selected],
                np.asarray([game.seat for game in selected], dtype=np.int64),
                [game.opponent_id for game in selected],
                [game.opponent_session for game in selected],
                rollout.compiled.tokens[native_rows],
                rollout.compiled.quantities[native_rows],
                rollout.compiled.decision_counts[native_rows],
                rollout.compiled.unit_counts[native_rows],
                min(self._workers, int(native_rows.size)),
            )

    def _collect_group(
        self,
        jobs: Sequence[Job],
        *,
        sample: bool,
        generator: torch.Generator,
        decision_graphs: ProgramDecisionGraphShards | None,
        program_graph: ProgramGpuTurnSwitchGraph | None,
    ) -> tuple[
        list[ProgramEpisode],
        dict[str, float],
        dict[str, float],
        float,
        float,
        int,
        int,
        int,
        int,
    ]:
        games = self._games(jobs)
        batch = len(games)
        engines = [game.engine for game in games]
        players = np.asarray([game.seat for game in games], dtype=np.int64)
        if self._observer is not None:
            self._observer.start_group(
                [(game.seed, game.seat) for game in games],
                engines,
                players,
                self._turn_capacity,
            )
        architecture = self._model.actor.architecture
        histories: HistoryState | None = None
        strategy: Tensor | None = None
        previous_tokens = torch.zeros(
            (batch, architecture.max_decisions), dtype=torch.long, device=self._device
        )
        previous_quantities = torch.zeros_like(previous_tokens)
        previous_mask = torch.zeros_like(previous_tokens, dtype=torch.bool)
        storage: ProgramGroupStorage | ProgramGpuGroupStorage | None = None
        turn_graph: ProgramTurnGraph | None = None
        phase_seconds = {
            "encode": 0.0,
            "actor": 0.0,
            "program": 0.0,
            "record": 0.0,
            "environment": 0.0,
            "cuda_graph_capture": 0.0,
        }
        program_phase_seconds: dict[str, float] = {}
        maximum_actor = 0.0
        overage = self._initial_overage
        program_decisions = 0
        official_decisions = 0
        while not all(bool(game.engine.done) for game in games):
            actor_started = time.perf_counter()
            phase_started = actor_started
            policy_batch = self._backend.engine_policy_session_batch(
                engines,
                players.tolist(),
                self._contract.unit_limit,
                self._workers,
            )
            board_raw, units_raw, global_raw = policy_batch.encode_compact()
            board_values = np.asarray(board_raw, dtype=np.float16)
            unit_values = np.asarray(units_raw, dtype=np.float16)
            global_values = np.asarray(global_raw, dtype=np.float32)
            compact_values = np.asarray(policy_batch.gpu_state_compact(), dtype=np.int32)
            economic_values = (
                compact_values
                if architecture.economic_feature_version is not None
                else np.zeros((batch, 0), dtype=np.int32)
            )
            board = torch.as_tensor(board_values, device=self._device)
            units = torch.as_tensor(unit_values, device=self._device)
            global_features = torch.as_tensor(global_values, device=self._device)
            compact_state = torch.as_tensor(compact_values, device=self._device)
            economic_state = (
                compact_state if architecture.economic_feature_version is not None else None
            )
            storage_economic_state = (
                compact_state
                if architecture.economic_feature_version is not None
                else torch.empty((batch, 0), dtype=torch.int32, device=self._device)
            )
            phase_seconds["encode"] += time.perf_counter() - phase_started
            if self._observer is not None:
                self._observer.begin_turn(engines, players)

            if storage is None:
                if program_graph is not None:
                    storage = ProgramGpuGroupStorage(
                        batch,
                        self._turn_capacity,
                        board,
                        units,
                        global_features,
                        storage_economic_state,
                        self._contract,
                        compact_mask_width(self._contract),
                        architecture.max_decisions,
                    )
                else:
                    storage = ProgramGroupStorage(
                        batch,
                        self._turn_capacity,
                        board_values,
                        unit_values,
                        global_values,
                        economic_values,
                        self._contract,
                        compact_mask_width(self._contract),
                        architecture.max_decisions,
                    )

            phase_started = time.perf_counter()
            turn_capture_seconds = 0.0
            with torch.inference_mode(), _autocast(self._device):
                if self._device.type == "cuda" and self._use_cuda_graphs:
                    turn_inputs = ProgramTurnInputs(
                        board=board,
                        units=units,
                        global_features=global_features,
                        previous_actions=previous_tokens,
                        previous_quantities=previous_quantities,
                        previous_mask=previous_mask,
                        economic_state=economic_state,
                    )
                    if turn_graph is None:
                        turn_graph = self._turn_graphs.get(batch)
                        if turn_graph is None:
                            with serialized_graph_build():
                                turn_graph = ProgramTurnGraph(self._model.actor, turn_inputs)
                            self._turn_graphs[batch] = turn_graph
                            turn_capture_seconds = turn_graph.capture_seconds
                        else:
                            turn_graph.reset()
                    context = turn_graph.decode(turn_inputs)
                else:
                    context, histories, strategy, _skill = self._model.actor.start_turn(
                        board,
                        units,
                        global_features,
                        previous_tokens,
                        previous_quantities,
                        previous_mask,
                        histories,
                        economic_state=economic_state,
                        strategy_state=strategy,
                        sample_skill=False,
                    )
                program_state, tile_tokens = program_context(architecture, context)
            actor_phase_seconds = time.perf_counter() - phase_started
            phase_seconds["actor"] += max(0.0, actor_phase_seconds - turn_capture_seconds)
            phase_seconds["cuda_graph_capture"] += turn_capture_seconds

            phase_started = time.perf_counter()
            decision_capture_before = 0.0
            if program_graph is not None:
                decision_capture_before = program_graph.capture_seconds
            elif decision_graphs is not None:
                decision_capture_before = decision_graphs.capture_seconds
            with _autocast(self._device):
                if program_graph is not None:
                    if not isinstance(storage, ProgramGpuGroupStorage):
                        raise RuntimeError("CUDA program graph lost its device storage")
                    compiled_destinations, trace_destinations = storage.destinations()
                    rollout = decode_program_turn_cuda(
                        self._model.programs,
                        self._contract,
                        program_graph,
                        compact_state,
                        program_state,
                        tile_tokens,
                        step=int(engines[0].step_index),
                        compiled_destinations=compiled_destinations,
                        trace_destinations=trace_destinations,
                    )
                else:
                    rollout = decode_program_turn(
                        self._backend,
                        self._model.programs,
                        self._contract,
                        [game.program_session for game in games],
                        engines,
                        players,
                        program_state,
                        tile_tokens,
                        workers=self._workers,
                        sample=sample,
                        generator=generator,
                        validate_inputs=False,
                        decision_graphs=decision_graphs,
                        timings=program_phase_seconds,
                    )
            program_elapsed = time.perf_counter() - phase_started
            decision_capture_after = 0.0
            if program_graph is not None:
                decision_capture_after = program_graph.capture_seconds
            elif decision_graphs is not None:
                decision_capture_after = decision_graphs.capture_seconds
            decision_capture_seconds = max(0.0, decision_capture_after - decision_capture_before)
            if program_graph is not None:
                program_phase_seconds["gpu_turn"] = program_phase_seconds.get(
                    "gpu_turn", 0.0
                ) + max(0.0, program_elapsed - decision_capture_seconds)
            phase_seconds["program"] += max(0.0, program_elapsed - decision_capture_seconds)
            phase_seconds["cuda_graph_capture"] += decision_capture_seconds
            actor_elapsed = max(
                0.0,
                time.perf_counter()
                - actor_started
                - turn_capture_seconds
                - decision_capture_seconds,
            )
            maximum_actor = max(maximum_actor, actor_elapsed)
            overage -= max(0.0, actor_elapsed - self._act_timeout)
            if overage < 0.0:
                raise TimeoutError("conditional-program actor exhausted official overage")

            phase_started = time.perf_counter()
            if isinstance(storage, ProgramGpuGroupStorage):
                storage.append(
                    board,
                    units,
                    global_features,
                    storage_economic_state,
                    rollout,
                )
            else:
                storage.append(
                    board_values,
                    unit_values,
                    global_values,
                    economic_values,
                    rollout,
                )
            trace_counts_host = rollout.trace_decision_counts_host
            program_decisions += int(
                np.asarray(
                    rollout.trace.decision_counts
                    if trace_counts_host is None
                    else trace_counts_host
                ).sum()
            )
            official_decisions += int(rollout.compiled.decision_counts.sum())
            phase_seconds["record"] += time.perf_counter() - phase_started

            phase_started = time.perf_counter()
            if self._observer is not None:
                self._observer.finish_turn()
            self._advance(games, rollout)
            phase_seconds["environment"] += time.perf_counter() - phase_started
            compiled_width = rollout.compiled.tokens.shape[1]
            if program_graph is not None and compiled_width == architecture.max_decisions:
                device_output = program_graph.compiler.output()
                previous_tokens = device_output.tokens
                previous_quantities = device_output.quantities
                counts = device_output.decision_counts
            else:
                previous_tokens = torch.zeros(
                    (batch, architecture.max_decisions),
                    dtype=torch.long,
                    device=self._device,
                )
                previous_quantities = torch.zeros_like(previous_tokens)
                previous_tokens[:, :compiled_width] = torch.as_tensor(
                    rollout.compiled.tokens, dtype=torch.long, device=self._device
                )
                previous_quantities[:, :compiled_width] = torch.as_tensor(
                    rollout.compiled.quantities, dtype=torch.long, device=self._device
                )
                counts = torch.as_tensor(
                    rollout.compiled.decision_counts,
                    dtype=torch.long,
                    device=self._device,
                )
            previous_mask = (
                torch.arange(architecture.max_decisions, device=self._device)[None]
                < counts[:, None]
            )
        if storage is None or storage.length != self._turn_capacity:
            raise RuntimeError("conditional-program match ended outside its official horizon")
        if self._observer is not None:
            self._observer.finish_group()
        episodes: list[ProgramEpisode] = []
        for row, game in enumerate(games):
            own_cash = float(game.engine.money(game.seat))
            opponent_cash = float(game.engine.money(1 - game.seat))
            outcome = int(own_cash > opponent_cash) - int(own_cash < opponent_cash)
            episodes.append(
                storage.episode(
                    row,
                    episode_id=(f"program-{game.seed}-{game.seat}-{game.opponent_id}"),
                    opponent_id=game.opponent_id,
                    seed=game.seed,
                    seat=game.seat,
                    outcome=outcome,
                    terminal_cash=own_cash,
                    opponent_cash=opponent_cash,
                )
            )
        for first, game in enumerate(games):
            if game.opponent_id != "self_play" or game.seat != 0:
                continue
            second = next(
                index
                for index, candidate in enumerate(games)
                if candidate.match_index == game.match_index and candidate.seat == 1
            )
            if (
                episodes[first].outcome != -episodes[second].outcome
                or episodes[first].terminal_cash != episodes[second].opponent_cash
                or episodes[first].opponent_cash != episodes[second].terminal_cash
            ):
                raise RuntimeError("conditional-program self-play perspectives lost symmetry")
        return (
            episodes,
            phase_seconds,
            program_phase_seconds,
            maximum_actor,
            overage,
            program_decisions,
            official_decisions,
            storage.nbytes,
            storage.device_nbytes,
        )

    def collect(
        self,
        seeds: Sequence[int],
        *,
        update: int,
        sample: bool = True,
    ) -> ProgramRolloutReport:
        """Collect one panel under the explicit device owning the frozen model."""
        if self._device.type == "cuda":
            with torch.cuda.device(self._device):
                return self._collect(seeds, update=update, sample=sample)
        return self._collect(seeds, update=update, sample=sample)

    def _collect(
        self,
        seeds: Sequence[int],
        *,
        update: int,
        sample: bool,
    ) -> ProgramRolloutReport:
        """Collect one weighted paired panel with the current frozen behavior."""
        self._model.eval()
        self._model.programs.refresh_rollout_parameters()
        jobs = weighted_rollout_jobs(
            seeds,
            self._weights,
            rank=self._rank,
            world_size=self._world_size,
            sampling_seed=self._sampling_seed + update,
        )
        groups = _group_jobs(jobs, self._batch_games)
        episodes: list[ProgramEpisode] = []
        phases: dict[str, float] = {}
        program_phases: dict[str, float] = {}
        maximum_actor = 0.0
        minimum_overage = self._initial_overage
        program_decisions = 0
        official_decisions = 0
        host_bytes = 0
        device_bytes = 0
        for group_index, group in enumerate(groups):
            actor_rows = sum(2 if job[2] == "self_play" else 1 for job in group)
            generator = self._program_generators.get(actor_rows)
            if generator is None:
                generator = torch.Generator(device=self._device)
                self._program_generators[actor_rows] = generator
            group_seed = (
                self._sampling_seed + update * 1_000_003 + self._rank * 10_000_019 + group_index
            )
            generator.manual_seed(group_seed)
            decision_graphs: ProgramDecisionGraphShards | None = None
            program_graph: ProgramGpuTurnSwitchGraph | None = None
            if (
                self._device.type == "cuda"
                and self._use_cuda_graphs
                and (sample or self._use_full_turn_graph)
            ):
                graph_key = (actor_rows, sample)
                program_graph = self._program_graphs.get(graph_key)
                if program_graph is None:
                    program_graph = ProgramGpuTurnSwitchGraph(
                        self._model.programs,
                        self._contract,
                        actor_rows,
                        generator,
                        episode_steps=self._turn_capacity + 1,
                        turns_per_day=self._turns_per_day,
                        sample=sample,
                    )
                    self._program_graphs[graph_key] = program_graph
                else:
                    program_graph.reset()
                program_graph.manual_seed(group_seed)
            elif self._device.type == "cuda" and self._use_cuda_graphs:
                decision_graphs = self._decision_graphs.get(actor_rows)
                if decision_graphs is None:
                    decision_graphs = ProgramDecisionGraphShards(
                        self._model.programs,
                        actor_rows,
                        self._actor_streams,
                        sample=False,
                    )
                    self._decision_graphs[actor_rows] = decision_graphs
                decision_graphs.manual_seed(group_seed)
            (
                group_episodes,
                group_phases,
                group_program_phases,
                group_maximum,
                group_overage,
                group_program_decisions,
                group_official_decisions,
                group_bytes,
                group_device_bytes,
            ) = self._collect_group(
                group,
                sample=sample,
                generator=generator,
                decision_graphs=decision_graphs,
                program_graph=program_graph,
            )
            episodes.extend(group_episodes)
            for name, value in group_phases.items():
                phases[name] = phases.get(name, 0.0) + value
            for name, value in group_program_phases.items():
                program_phases[name] = program_phases.get(name, 0.0) + value
            maximum_actor = max(maximum_actor, group_maximum)
            minimum_overage = min(minimum_overage, group_overage)
            program_decisions += group_program_decisions
            official_decisions += group_official_decisions
            host_bytes += group_bytes
            device_bytes += group_device_bytes
            if host_bytes > self._host_limit:
                raise MemoryError("conditional-program rollout exceeded its host memory limit")
        expected = 2 * len(seeds) // self._world_size
        if len(episodes) != expected:
            raise RuntimeError("conditional-program paired rollout lost an episode")
        return ProgramRolloutReport(
            episodes=tuple(episodes),
            physical_games=len(jobs),
            maximum_actor_seconds=maximum_actor,
            remaining_overage_seconds=minimum_overage,
            official_turns=sum(episode.turn_count for episode in episodes),
            program_decisions=program_decisions,
            official_decisions=official_decisions,
            host_bytes=host_bytes,
            device_bytes=device_bytes,
            phase_seconds=phases,
            program_phase_seconds=program_phases,
            rank_seconds=(),
        )


__all__ = ["ProgramRolloutCollector", "ProgramRolloutReport"]
