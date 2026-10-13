"""Concurrent complete-game rollout streams for atomic-effect policies."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import cast

import torch

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.effects.contract import NativeEffectContract
from kagg_revue.policy.effects.model import EffectActorCritic
from kagg_revue.rl.effects.data import EffectRolloutBatch
from kagg_revue.rl.effects.rollout import EffectRolloutCollector, EffectRolloutResult
from kagg_revue.rl.rollout.batch import Job


def shard_effect_jobs(jobs: Sequence[Job], count: int) -> tuple[tuple[Job, ...], ...]:
    """Split seed-level job groups without separating paired external seats."""
    if not jobs or count < 1:
        raise ValueError("effect rollout sharding needs jobs and a positive shard count")
    grouped: dict[int, list[Job]] = {}
    opponents: dict[int, str] = {}
    for raw_job in jobs:
        seed, _seat, opponent_id = raw_job
        job = (int(seed), int(_seat), opponent_id)
        previous = opponents.setdefault(job[0], opponent_id)
        if previous != opponent_id:
            raise ValueError("effect rollout seed cannot target multiple opponents")
        grouped.setdefault(job[0], []).append(job)
    if count > len(grouped):
        raise ValueError("effect rollout needs at least one seed group per actor stream")
    groups = tuple(tuple(values) for values in grouped.values())
    quotient, remainder = divmod(len(groups), count)
    result: list[tuple[Job, ...]] = []
    start = 0
    for index in range(count):
        stop = start + quotient + int(index < remainder)
        result.append(tuple(job for group in groups[start:stop] for job in group))
        start = stop
    return tuple(result)


def _metric(result: EffectRolloutResult, name: str) -> float:
    value = result.diagnostics[name]
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"effect rollout metric {name} is not numeric")
    return float(value)


class EffectRolloutFleet:
    """Keep one persistent native/CUDA collector per local actor stream."""

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
        action_generators: Sequence[torch.Generator],
        maximum_graph_variants: int,
        sample_actions: bool = True,
    ) -> None:
        """Allocate stable stream-local graph and native batch resources."""
        if not action_generators:
            raise ValueError("effect rollout fleet needs at least one actor stream")
        if next(model.parameters()).device != device:
            raise ValueError("effect rollout fleet model must reside on its rank device")
        self._device = device
        self._streams = tuple(
            (
                torch.cuda.Stream(device=device)  # type: ignore[no-untyped-call]
                if device.type == "cuda" and len(action_generators) > 1
                else None
            )
            for _generator in action_generators
        )
        stream_workers = max(1, cpu_workers // len(action_generators))
        self._collectors = tuple(
            EffectRolloutCollector(
                backend,
                model,
                contract,
                environment,
                unit_limit=unit_limit,
                cpu_workers=stream_workers,
                device=device,
                action_generator=generator,
                maximum_graph_variants=maximum_graph_variants,
                sample_actions=sample_actions,
            )
            for generator in action_generators
        )
        self._executor = (
            ThreadPoolExecutor(
                max_workers=len(self._collectors),
                thread_name_prefix="effect-actor",
            )
            if len(self._collectors) > 1
            else None
        )

    def _collect_one(self, index: int, jobs: Sequence[Job]) -> EffectRolloutResult:
        stream = self._streams[index]
        if self._device.type == "cuda":
            if stream is None:
                with torch.cuda.device(self._device):
                    return self._collectors[index].collect_jobs(jobs)
            with torch.cuda.device(self._device), torch.cuda.stream(stream):
                return self._collectors[index].collect_jobs(jobs)
        return self._collectors[index].collect_jobs(jobs)

    def collect_jobs(self, jobs: Sequence[Job]) -> EffectRolloutResult:
        """Collect every seed group and concatenate only at the coarse boundary."""
        started = time.perf_counter()
        shards = shard_effect_jobs(jobs, len(self._collectors))
        if self._device.type == "cuda":
            producer = torch.cuda.current_stream(self._device)
            for stream in self._streams:
                if stream is not None:
                    stream.wait_stream(producer)
        if self._executor is None:
            results = [self._collect_one(0, shards[0])]
        else:
            futures = [
                self._executor.submit(self._collect_one, index, shard)
                for index, shard in enumerate(shards)
            ]
            results = [future.result() for future in futures]
        if self._device.type == "cuda":
            consumer = torch.cuda.current_stream(self._device)
            for stream in self._streams:
                if stream is not None:
                    consumer.wait_stream(stream)
        elapsed = time.perf_counter() - started
        batch = EffectRolloutBatch.concatenate([result.batch for result in results], validate=False)
        summed = (
            "physical_games",
            "episodes",
            "official_turns",
            "policy_factors",
            "factors",
            "native_rollout_buckets",
            "graph_variants_created",
        )
        maximum = (
            "maximum_batched_actor_seconds",
            "batched_actor_total_seconds",
            "batched_actor_overage_seconds_at_one_second",
            "encode_seconds",
            "native_observation_seconds",
            "inference_seconds",
            "native_transition_seconds",
            "action_compilation_seconds",
            "environment_seconds",
            "finalization_seconds",
            "behavior_export_seconds",
            "native_export_seconds",
            "batch_wrap_seconds",
            "critic_seconds",
            "turn_graph_capture_seconds",
        )
        diagnostics: dict[str, object] = {
            name: sum(int(_metric(result, name)) for result in results) for name in summed
        }
        diagnostics.update(
            {name: max(_metric(result, name) for result in results) for name in maximum}
        )
        physical_games = int(cast(int, diagnostics["physical_games"]))
        diagnostics.update(
            {
                "elapsed_seconds": elapsed,
                "physical_games_per_second": physical_games / elapsed,
                "device": str(self._device),
                "optimized_cuda_path": all(
                    result.diagnostics["optimized_cuda_path"] is True for result in results
                ),
                "graph_capture_seconds": sum(
                    _metric(result, "graph_capture_seconds") for result in results
                ),
                "actor_streams": len(self._collectors),
                "stream_elapsed_seconds": [
                    _metric(result, "elapsed_seconds") for result in results
                ],
            }
        )
        games = tuple(game for result in results for game in result.games)
        if len(games) != batch.episode_count:
            raise RuntimeError("effect rollout fleet lost a trained perspective")
        return EffectRolloutResult(batch=batch, games=games, diagnostics=diagnostics)

    def close(self) -> None:
        """Join worker threads and release stream-local CUDA graphs."""
        if self._executor is not None:
            self._executor.shutdown(wait=True)
        for stream in self._streams:
            if stream is not None:
                stream.synchronize()
        for collector in self._collectors:
            collector.close()


__all__ = ["EffectRolloutFleet", "shard_effect_jobs"]
