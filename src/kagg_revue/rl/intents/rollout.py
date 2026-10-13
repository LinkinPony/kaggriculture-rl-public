"""Batched native self-play rollout for canonical intent-ledger PPO."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.intents.contract import NativeIntentContract
from kagg_revue.policy.intents.gpu import (
    IntentGpuTransactionGraph,
    IntentTurnGraph,
    PinnedIntentTurnStaging,
)
from kagg_revue.policy.intents.model import IntentActorCritic, IntentPolicy
from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.policy.transformer import HistoryState
from kagg_revue.rl.intents.data import (
    IntentRolloutBatch,
    tensor_state_from_native,
)


def _integer(values: Mapping[str, object], name: str) -> int:
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"intent environment {name} must be an integer")
    return value


@dataclass(frozen=True)
class IntentGameResult:
    """Direct terminal result for one self-play perspective."""

    episode_id: str
    seed: int
    seat: int
    outcome: int
    terminal_cash: float
    opponent_cash: float


@dataclass(frozen=True)
class IntentRolloutResult:
    """Complete episodes plus behavior and throughput diagnostics."""

    batch: IntentRolloutBatch
    games: tuple[IntentGameResult, ...]
    diagnostics: dict[str, object]


@dataclass
class _Perspective:
    engine: Any
    seed: int
    seat: int
    session: Any


def _autocast(device: torch.device) -> Any:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


class IntentRolloutCollector:
    """Run complete current-policy self-play through the native dispatcher."""

    def __init__(
        self,
        backend: BackendApi,
        model: IntentActorCritic,
        contract: NativeIntentContract,
        environment: Mapping[str, object],
        *,
        unit_limit: int,
        cpu_workers: int,
        max_transaction_steps: int,
        device: torch.device,
        action_generator: torch.Generator,
        sample_actions: bool = True,
    ) -> None:
        """Bind the measured native ABI and persistent rollout resources."""
        self._backend = backend
        self._model = model
        self._contract = contract
        self._environment = dict(environment)
        self._unit_limit = unit_limit
        self._workers = cpu_workers
        self._maximum_steps = max_transaction_steps
        self._device = device
        self._generator = action_generator
        self._sample_actions = sample_actions
        self._transaction_graph: IntentGpuTransactionGraph | None = None
        self._turn_staging: PinnedIntentTurnStaging | None = None
        self._turn_graph: IntentTurnGraph | None = None
        architecture = model.actor.architecture
        if architecture.unit_shape[1] != unit_limit:
            raise ValueError("intent collector unit limit differs from the actor")
        if architecture.board_shape[-1] != contract.board_size:
            raise ValueError("intent collector board size differs from the actor")
        if _integer(self._environment, "episodeSteps") - 1 > architecture.max_history:
            raise ValueError("intent rollout exceeds the actor history capacity")

    def _perspectives(self, seeds: Sequence[int]) -> tuple[list[Any], list[_Perspective]]:
        engines = [self._backend.engine(int(seed), self._environment) for seed in seeds]
        perspectives = [
            _Perspective(
                engine=engine,
                seed=int(seed),
                seat=seat,
                session=self._backend.intent_ledger_session(self._environment),
            )
            for seed, engine in zip(seeds, engines, strict=True)
            for seat in (0, 1)
        ]
        return engines, perspectives

    def _advance(
        self,
        engines: list[Any],
        compiled: Mapping[str, Any],
    ) -> None:
        rows = len(engines)
        tokens = np.asarray(compiled["tokens"], dtype=np.int64)
        quantities = np.asarray(compiled["quantities"], dtype=np.int64)
        counts = np.asarray(compiled["decision_counts"], dtype=np.int64)
        units = np.asarray(compiled["unit_counts"], dtype=np.int64)
        self._backend.engine_step_numeric_batch(
            engines,
            tokens.reshape(rows, 2, tokens.shape[1]),
            quantities.reshape(rows, 2, quantities.shape[1]),
            counts.reshape(rows, 2),
            units.reshape(rows, 2),
            min(self._workers, rows),
        )

    def collect(self, seeds: Sequence[int]) -> IntentRolloutResult:
        """Collect complete paired perspectives and frozen behavior tensors."""
        if not seeds or len(set(seeds)) != len(seeds):
            raise ValueError("intent rollout seeds must be nonempty and unique")
        engines, perspectives = self._perspectives(seeds)
        batch = len(perspectives)
        players = np.asarray([game.seat for game in perspectives], dtype=np.int64)
        player_list = players.tolist()
        perspective_engines = [game.engine for game in perspectives]
        sessions = [game.session for game in perspectives]
        native_batch = self._backend.intent_ledger_batch(
            sessions,
            perspective_engines,
            players,
            self._workers,
        )
        architecture = self._model.actor.architecture
        turn_capacity = _integer(self._environment, "episodeSteps") - 1
        histories: HistoryState | None = None
        strategy: Tensor | None = None
        if self._device.type == "cuda":
            if self._turn_staging is None:
                self._turn_staging = PinnedIntentTurnStaging(
                    architecture,
                    batch,
                    self._device,
                )
            elif self._turn_staging.inputs.board.shape[0] != batch:
                raise ValueError("intent rollout batch size changed after CUDA graph capture")
            self._turn_staging.reset_episode()
            if self._turn_graph is not None:
                self._turn_graph.reset_episode()
            previous_tokens = self._turn_staging.inputs.previous_actions
            previous_quantities = self._turn_staging.inputs.previous_quantities
            previous_mask = self._turn_staging.inputs.previous_mask
        else:
            previous_tokens = torch.zeros(
                (batch, architecture.max_decisions), dtype=torch.long, device=self._device
            )
            previous_quantities = torch.zeros_like(previous_tokens)
            previous_mask = torch.zeros_like(previous_tokens, dtype=torch.bool)
        board_store: NDArray[np.float16] | None = None
        unit_store: NDArray[np.float16] | None = None
        global_store: NDArray[np.float32] | None = None
        economic_store: NDArray[np.int32] | None = None
        action_store = np.zeros((batch, turn_capacity, architecture.max_decisions), dtype=np.int64)
        quantity_store = np.zeros_like(action_store)
        action_counts = np.zeros((batch, turn_capacity), dtype=np.int64)
        turn = 0
        pseudo_steps = 0
        forced_steps = 0
        maximum_actor_seconds = 0.0
        encode_seconds = 0.0
        policy_seconds = 0.0
        environment_seconds = 0.0
        observation_seconds = 0.0
        decision_seconds = 0.0
        recording_seconds = 0.0
        selection_seconds = 0.0
        compilation_seconds = 0.0
        history_staging_seconds = 0.0
        started = time.perf_counter()
        self._model.eval()
        if self._device.type == "cuda" and self._transaction_graph is None:
            self._transaction_graph = IntentGpuTransactionGraph(
                self._model.intents,
                self._generator,
                batch,
                self._unit_limit,
                maximum_steps=self._maximum_steps,
                episode_steps=_integer(self._environment, "episodeSteps"),
                turns_per_day=_integer(self._environment, "turnsPerDay"),
                sample=self._sample_actions,
            )
        graphs = self._transaction_graph
        if graphs is not None:
            graphs.start_recording(batch * turn_capacity * (self._maximum_steps + 9))
        capture_seconds_before = 0.0 if graphs is None else graphs.capture_seconds
        graph_variants_before = 0 if graphs is None else graphs.variant_count
        turn_capture_before = 0.0 if self._turn_graph is None else self._turn_graph.capture_seconds

        while not all(bool(engine.done) for engine in engines):
            if turn >= turn_capacity:
                raise RuntimeError("intent rollout exceeded configured episode capacity")
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
            if board_store is None:
                board_store = np.empty(
                    (batch, turn_capacity, *board_np.shape[1:]), dtype=np.float16
                )
                unit_store = np.empty((batch, turn_capacity, *units_np.shape[1:]), dtype=np.float16)
                global_store = np.empty(
                    (batch, turn_capacity, global_np.shape[1]), dtype=np.float32
                )
                economic_store = np.empty(
                    (batch, turn_capacity, economic_np.shape[1]), dtype=np.int32
                )
            if unit_store is None or global_store is None or economic_store is None:
                raise RuntimeError("intent rollout storage initialization failed")
            board_store[:, turn] = board_np
            unit_store[:, turn] = units_np
            global_store[:, turn] = global_np
            economic_store[:, turn] = economic_np
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
                    context, tile_context, histories, strategy = self._model.start_turn(
                        board,
                        units,
                        global_features,
                        previous_tokens,
                        previous_quantities,
                        previous_mask,
                        histories,
                        strategy,
                        economic,
                    )
            else:
                if self._turn_graph is None:
                    self._turn_graph = IntentTurnGraph(
                        self._model.actor,
                        turn_staging.inputs,
                        self._model.intents.architecture.tile_count,
                    )
                context, tile_context = self._turn_graph.replay(turn_staging.inputs)
            encode_seconds += time.perf_counter() - encoded_started

            active = np.arange(batch, dtype=np.int64)
            policy_started = time.perf_counter()
            if graphs is not None:
                observation_started = time.perf_counter()
                payload = cast(
                    Mapping[str, Any],
                    native_batch.observe(active, self._maximum_steps),
                )
                auxiliary = cast(Mapping[str, Any], native_batch.device_auxiliary())
                observation_seconds += time.perf_counter() - observation_started
                decision_started = time.perf_counter()
                trace = graphs.replay(
                    payload,
                    auxiliary,
                    economic_np,
                    context,
                    tile_context,
                )
                decision_seconds += time.perf_counter() - decision_started
                selection_started = time.perf_counter()
                forced_steps += int(
                    native_batch.replay_transaction(
                        trace.selected,
                        trace.selected_fields,
                        trace.counts,
                        trace.behavior_offset,
                        turn,
                        self._maximum_steps,
                    )
                )
                selection_seconds += time.perf_counter() - selection_started
                pseudo_steps += int(trace.counts.sum())
            else:
                native_batch.reset_transaction()
                transaction_iterations = 0
                while active.size:
                    if transaction_iterations > self._maximum_steps + 8:
                        raise RuntimeError("intent transaction failed to reach COMMIT")
                    observation_started = time.perf_counter()
                    payload = cast(
                        Mapping[str, Any],
                        native_batch.observe(active, self._maximum_steps),
                    )
                    candidate_mask = np.asarray(payload["candidate_mask"], dtype=np.bool_)
                    forced_steps += int(np.count_nonzero(candidate_mask.sum(axis=1) == 1))
                    observation_seconds += time.perf_counter() - observation_started
                    decision_started = time.perf_counter()
                    state = tensor_state_from_native(payload, candidate_mask, self._device)
                    active_tensor = torch.as_tensor(active, device=self._device)
                    with torch.inference_mode(), _autocast(self._device):
                        selection = self._model.intents.select(
                            context[active_tensor],
                            tile_context[active_tensor],
                            state,
                            sample=self._sample_actions,
                            generator=self._generator,
                            compute_entropy=False,
                        )
                    selected = selection.indices.cpu().numpy().astype(np.int64, copy=False)
                    old_log_probability = (
                        selection.log_probability.cpu().numpy().astype(np.float32, copy=False)
                    )
                    old_value = selection.value.cpu().numpy().astype(np.float32, copy=False)
                    decision_seconds += time.perf_counter() - decision_started
                    recording_started = time.perf_counter()
                    native_batch.record_prepared(
                        selected,
                        old_log_probability,
                        old_value,
                        turn,
                    )
                    recording_seconds += time.perf_counter() - recording_started
                    selection_started = time.perf_counter()
                    phases = np.asarray(
                        native_batch.select(active, selected),
                        dtype=np.int64,
                    )
                    selection_seconds += time.perf_counter() - selection_started
                    pseudo_steps += int(active.size)
                    active = active[phases != self._contract.done_phase]
                    transaction_iterations += 1
            policy_seconds += time.perf_counter() - policy_started

            compilation_started = time.perf_counter()
            compiled = cast(
                Mapping[str, Any],
                self._backend.intent_ledger_actions_batch(
                    sessions,
                    perspective_engines,
                    players,
                    self._workers,
                ),
            )
            tokens = np.asarray(compiled["tokens"], dtype=np.int64)
            quantities = np.asarray(compiled["quantities"], dtype=np.int64)
            counts = np.asarray(compiled["decision_counts"], dtype=np.int64)
            if tokens.shape[1] > architecture.max_decisions:
                raise RuntimeError("compiled intent action exceeds actor history capacity")
            compilation_seconds += time.perf_counter() - compilation_started
            history_started = time.perf_counter()
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
            history_staging_seconds += time.perf_counter() - history_started
            actor_seconds = time.perf_counter() - actor_started
            maximum_actor_seconds = max(maximum_actor_seconds, actor_seconds)

            environment_started = time.perf_counter()
            self._advance(engines, compiled)
            environment_seconds += time.perf_counter() - environment_started
            turn += 1

        finalization_started = time.perf_counter()
        games: list[IntentGameResult] = []
        outcomes = np.empty(batch, dtype=np.float32)
        for index, game in enumerate(perspectives):
            terminal_cash = float(game.engine.money(game.seat))
            opponent_cash = float(game.engine.money(1 - game.seat))
            outcome = int(terminal_cash > opponent_cash) - int(terminal_cash < opponent_cash)
            outcomes[index] = outcome
            games.append(
                IntentGameResult(
                    episode_id=f"self_play:{game.seed}:{game.seat}",
                    seed=game.seed,
                    seat=game.seat,
                    outcome=outcome,
                    terminal_cash=terminal_cash,
                    opponent_cash=opponent_cash,
                )
            )
        if any(value is None for value in (board_store, unit_store, global_store, economic_store)):
            raise RuntimeError("intent rollout completed without an official turn")
        device_behavior = None if graphs is None else graphs.finish_recording()
        collated = cast(
            Sequence[Mapping[str, Any]],
            native_batch.export_rollout_buckets(),
        )
        rollout_batch = IntentRolloutBatch.from_native_buckets(
            board=cast(NDArray[np.float16], board_store)[:, :turn],
            units=cast(NDArray[np.float16], unit_store)[:, :turn],
            global_features=cast(NDArray[np.float32], global_store)[:, :turn],
            economic_state=cast(NDArray[np.int32], economic_store)[:, :turn],
            actions=action_store[:, :turn],
            quantities=quantity_store[:, :turn],
            decision_counts=action_counts[:, :turn],
            decisions=collated,
            outcomes=outcomes,
            device_behavior=device_behavior,
        )
        finalization_seconds = time.perf_counter() - finalization_started
        elapsed = time.perf_counter() - started
        return IntentRolloutResult(
            batch=rollout_batch,
            games=tuple(games),
            diagnostics={
                "physical_games": len(engines),
                "episodes": batch,
                "official_turns": batch * turn,
                "pseudo_steps": pseudo_steps,
                "policy_steps": int(rollout_batch.policy_mask.sum()),
                "forced_steps": forced_steps,
                "maximum_batched_actor_seconds": maximum_actor_seconds,
                "encode_seconds": encode_seconds,
                "policy_seconds": policy_seconds,
                "environment_seconds": environment_seconds,
                "native_observation_seconds": observation_seconds,
                "decision_seconds": decision_seconds,
                "recording_seconds": recording_seconds,
                "native_selection_seconds": selection_seconds,
                "action_compilation_seconds": compilation_seconds,
                "history_staging_seconds": history_staging_seconds,
                "finalization_seconds": finalization_seconds,
                "native_rollout_buckets": len(collated),
                "graph_capture_seconds": (
                    0.0 if graphs is None else graphs.capture_seconds - capture_seconds_before
                ),
                "graph_variants_created": (
                    0 if graphs is None else graphs.variant_count - graph_variants_before
                ),
                "turn_graph_capture_seconds": (
                    0.0
                    if self._turn_graph is None
                    else self._turn_graph.capture_seconds - turn_capture_before
                ),
                "elapsed_seconds": elapsed,
                "episodes_per_second": batch / elapsed,
            },
        )

    def close(self) -> None:
        """Release graph-private CUDA allocations."""
        if self._transaction_graph is not None:
            self._transaction_graph.close()
        if self._turn_graph is not None:
            self._turn_graph.close()


class IntentRolloutFleet:
    """Run independent seed shards concurrently across rollout devices."""

    def __init__(
        self,
        backend: BackendApi,
        model: IntentActorCritic,
        contract: NativeIntentContract,
        environment: Mapping[str, object],
        *,
        unit_limit: int,
        cpu_workers: int,
        max_transaction_steps: int,
        devices: Sequence[torch.device],
        action_generators: Sequence[torch.Generator],
        actor_streams_per_device: int = 1,
        sample_actions: bool = True,
    ) -> None:
        """Create one persistent model/graph collector per CUDA device."""
        if (
            not devices
            or actor_streams_per_device < 1
            or len(action_generators) != len(devices) * actor_streams_per_device
        ):
            raise ValueError("intent rollout devices, streams, and generators must align")
        if len(set(devices)) != len(devices):
            raise ValueError("intent rollout fleet devices must be unique")
        primary = next(model.parameters()).device
        if primary != devices[0]:
            raise ValueError("intent rollout fleet must begin on the learner device")
        self._primary = model
        self._devices = tuple(devices)
        self._models = [model]
        for device in self._devices[1:]:
            replica = IntentActorCritic(
                TurnPolicyNet(model.actor.architecture),
                IntentPolicy(model.intents.architecture),
            ).to(device)
            replica.load_state_dict(model.state_dict(), strict=True)
            replica.requires_grad_(False).eval()
            self._models.append(replica)
        stream_workers = max(1, cpu_workers // actor_streams_per_device)
        stream_models = [model for model in self._models for _ in range(actor_streams_per_device)]
        self._stream_devices = tuple(
            device for device in self._devices for _ in range(actor_streams_per_device)
        )
        self._streams = tuple(
            (
                torch.cuda.Stream(device=device)  # type: ignore[no-untyped-call]
                if device.type == "cuda"
                else None
            )
            for device in self._stream_devices
        )
        self._collectors = [
            IntentRolloutCollector(
                backend,
                shard_model,
                contract,
                environment,
                unit_limit=unit_limit,
                cpu_workers=stream_workers,
                max_transaction_steps=max_transaction_steps,
                device=device,
                action_generator=generator,
                sample_actions=sample_actions,
            )
            for shard_model, device, generator in zip(
                stream_models,
                self._stream_devices,
                action_generators,
                strict=True,
            )
        ]
        self._executor = (
            ThreadPoolExecutor(max_workers=len(self._collectors), thread_name_prefix="intent-gpu")
            if len(self._collectors) > 1
            else None
        )

    def _synchronize_replicas(self) -> float:
        """Publish current learner weights into persistent secondary replicas."""
        started = time.perf_counter()
        state = self._primary.state_dict()
        for model, device in zip(self._models[1:], self._devices[1:], strict=True):
            model.load_state_dict(state, strict=True)
            if device.type == "cuda":
                torch.cuda.synchronize(device)
        return time.perf_counter() - started

    @staticmethod
    def _seed_shards(seeds: Sequence[int], count: int) -> tuple[tuple[int, ...], ...]:
        """Split complete physical games evenly without separating their seats."""
        quotient, remainder = divmod(len(seeds), count)
        result: list[tuple[int, ...]] = []
        start = 0
        for index in range(count):
            stop = start + quotient + int(index < remainder)
            result.append(tuple(int(seed) for seed in seeds[start:stop]))
            start = stop
        if any(not shard for shard in result):
            raise ValueError("intent rollout fleet needs at least one seed per device")
        return tuple(result)

    def _collect_one(self, index: int, seeds: Sequence[int]) -> IntentRolloutResult:
        device = self._stream_devices[index]
        stream = self._streams[index]
        if device.type == "cuda":
            if stream is None:
                raise RuntimeError("intent CUDA actor stream is absent")
            with torch.cuda.device(device), torch.cuda.stream(stream):
                return self._collectors[index].collect(seeds)
        return self._collectors[index].collect(seeds)

    def collect(self, seeds: Sequence[int]) -> IntentRolloutResult:
        """Collect all device shards and join their compact native buckets."""
        started = time.perf_counter()
        replica_seconds = self._synchronize_replicas()
        shards = self._seed_shards(seeds, len(self._collectors))
        if self._executor is None:
            results = [self._collect_one(0, shards[0])]
        else:
            futures = [
                self._executor.submit(self._collect_one, index, shard)
                for index, shard in enumerate(shards)
            ]
            results = [future.result() for future in futures]
        elapsed = time.perf_counter() - started
        batch = IntentRolloutBatch.concatenate([result.batch for result in results])

        def metric(result: IntentRolloutResult, name: str) -> float:
            value = result.diagnostics[name]
            if not isinstance(value, int | float):
                raise TypeError(f"intent rollout metric {name} is not numeric")
            return float(value)

        summed = (
            "physical_games",
            "episodes",
            "official_turns",
            "pseudo_steps",
            "policy_steps",
            "forced_steps",
            "graph_variants_created",
            "native_rollout_buckets",
        )
        maximum = (
            "maximum_batched_actor_seconds",
            "encode_seconds",
            "policy_seconds",
            "environment_seconds",
            "native_observation_seconds",
            "decision_seconds",
            "recording_seconds",
            "native_selection_seconds",
            "action_compilation_seconds",
            "history_staging_seconds",
            "finalization_seconds",
            "turn_graph_capture_seconds",
        )
        diagnostics: dict[str, object] = {
            name: sum(int(metric(result, name)) for result in results) for name in summed
        }
        diagnostics.update(
            {name: max(metric(result, name) for result in results) for name in maximum}
        )
        diagnostics.update(
            {
                "graph_capture_seconds": sum(
                    metric(result, "graph_capture_seconds") for result in results
                ),
                "elapsed_seconds": elapsed,
                "episodes_per_second": batch.episode_count / elapsed,
                "replica_sync_seconds": replica_seconds,
                "rollout_devices": [str(device) for device in self._devices],
                "actor_streams": len(self._collectors),
                "device_elapsed_seconds": [metric(result, "elapsed_seconds") for result in results],
            }
        )
        return IntentRolloutResult(
            batch=batch,
            games=tuple(game for result in results for game in result.games),
            diagnostics=diagnostics,
        )

    def close(self) -> None:
        """Release worker threads and every collector's CUDA graphs."""
        if self._executor is not None:
            self._executor.shutdown(wait=True)
        for collector in self._collectors:
            collector.close()


__all__ = [
    "IntentGameResult",
    "IntentRolloutCollector",
    "IntentRolloutFleet",
    "IntentRolloutResult",
]
