"""Concurrent multi-device rollout for conditional-program PPO."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from typing import Any

import torch

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.rl.programs.config import ProgramRlSettings
from kagg_revue.rl.programs.model import ProgramActorCritic
from kagg_revue.rl.programs.rollout import (
    ProgramRolloutCollector,
    ProgramRolloutReport,
)


def _maximum_phases(
    reports: tuple[ProgramRolloutReport, ...],
    attribute: str,
) -> dict[str, float]:
    mappings = [getattr(report, attribute) for report in reports]
    names = {name for mapping in mappings for name in mapping}
    return {name: max(float(mapping.get(name, 0.0)) for mapping in mappings) for name in names}


class ProgramRolloutPool:
    """Run disjoint paired panels concurrently on persistent model replicas."""

    def __init__(
        self,
        backend: BackendApi,
        model: ProgramActorCritic,
        contract: NativeProgramContract,
        repository_root: Path,
        public_agent_manifest: Path | None,
        environment: Mapping[str, object],
        opponent_weights: Mapping[str, float],
        devices: tuple[torch.device, ...],
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
    ) -> None:
        """Create one collector and policy replica per rollout device."""
        if len(devices) < 2 or len(set(devices)) != len(devices):
            raise ValueError("program rollout pool needs distinct devices")
        if next(model.parameters()).device != devices[0]:
            raise ValueError("program rollout primary model is on another device")
        if batch_games % len(devices):
            raise ValueError("program rollout batch must divide across devices")
        local_capacity = batch_games // len(devices)
        if actor_streams % len(devices):
            raise ValueError("program rollout streams must divide across devices")
        local_streams = actor_streams // len(devices)
        if local_capacity < 2:
            raise ValueError("program rollout device cannot hold self-play")
        self._devices = devices
        replicas = [model]
        for device in devices[1:]:
            with torch.cuda.device(device) if device.type == "cuda" else torch.no_grad():
                replicas.append(deepcopy(model).to(device))
        self._models = tuple(replicas)
        world_size = len(devices)
        self._collectors = tuple(
            ProgramRolloutCollector(
                backend,
                replica,
                contract,
                repository_root,
                public_agent_manifest,
                environment,
                opponent_weights,
                device,
                batch_games=local_capacity,
                cpu_workers=cpu_workers,
                actor_streams=local_streams,
                cpu_threads=cpu_threads,
                host_memory_limit_gib=(host_memory_limit_gib / world_size),
                sampling_seed=sampling_seed,
                act_timeout_seconds=act_timeout_seconds,
                remaining_overage_seconds=remaining_overage_seconds,
                use_cuda_graphs=use_cuda_graphs,
                rank=rank,
                world_size=world_size,
            )
            for rank, (replica, device) in enumerate(zip(self._models, devices, strict=True))
        )
        identities = self._collectors[0].opponent_identities
        if any(collector.opponent_identities != identities for collector in self._collectors[1:]):
            raise RuntimeError("program rollout ranks authenticated different opponents")
        self._opponent_identities = identities
        self._executors = tuple(
            ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix=f"program-rollout-{rank}",
            )
            for rank in range(world_size)
        )
        self._graphs_ready = not use_cuda_graphs

    @property
    def opponent_identities(self) -> Mapping[str, object]:
        """Return the common authenticated rollout population."""
        return self._opponent_identities

    @torch.inference_mode()
    def _synchronize_replicas(self) -> None:
        state = self._models[0].state_dict()
        for replica, device in zip(self._models[1:], self._devices[1:], strict=True):
            replica.load_state_dict(state, strict=True)
            if device.type == "cuda":
                torch.cuda.synchronize(device)

    @staticmethod
    def _collect_rank(
        collector: ProgramRolloutCollector,
        device: torch.device,
        seeds: tuple[int, ...],
        update: int,
        sample: bool,
    ) -> tuple[ProgramRolloutReport, float]:
        if device.type == "cuda":
            torch.cuda.set_device(device)
        started = time.perf_counter()
        report = collector.collect(seeds, update=update, sample=sample)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        return report, time.perf_counter() - started

    def collect(
        self,
        seeds: Sequence[int],
        *,
        update: int,
        sample: bool = True,
    ) -> ProgramRolloutReport:
        """Collect and merge one exact globally weighted paired panel."""
        seed_tuple = tuple(int(seed) for seed in seeds)
        if len(seed_tuple) % len(self._collectors):
            raise ValueError("program rollout seeds must divide across devices")
        self._synchronize_replicas()
        if not self._graphs_ready and sample:
            # CUDA Graph construction and Triton first-use setup hold process-global
            # runtime state.  Keep the permanent per-device worker threads, but let
            # each rank finish its one-time capture before starting the next rank.
            results = tuple(
                executor.submit(
                    self._collect_rank,
                    collector,
                    device,
                    seed_tuple,
                    update,
                    sample,
                ).result()
                for executor, collector, device in zip(
                    self._executors,
                    self._collectors,
                    self._devices,
                    strict=True,
                )
            )
            self._graphs_ready = True
        else:
            futures = [
                executor.submit(
                    self._collect_rank,
                    collector,
                    device,
                    seed_tuple,
                    update,
                    sample,
                )
                for executor, collector, device in zip(
                    self._executors,
                    self._collectors,
                    self._devices,
                    strict=True,
                )
            ]
            results = tuple(future.result() for future in futures)
        reports = tuple(result[0] for result in results)
        rank_seconds = tuple(result[1] for result in results)
        episodes = tuple(episode for report in reports for episode in report.episodes)
        if len(episodes) != 2 * len(seed_tuple):
            raise RuntimeError("program rollout pool lost a training perspective")
        return ProgramRolloutReport(
            episodes=episodes,
            physical_games=sum(report.physical_games for report in reports),
            maximum_actor_seconds=max(report.maximum_actor_seconds for report in reports),
            remaining_overage_seconds=min(report.remaining_overage_seconds for report in reports),
            official_turns=sum(report.official_turns for report in reports),
            program_decisions=sum(report.program_decisions for report in reports),
            official_decisions=sum(report.official_decisions for report in reports),
            host_bytes=sum(report.host_bytes for report in reports),
            device_bytes=sum(report.device_bytes for report in reports),
            phase_seconds=_maximum_phases(reports, "phase_seconds"),
            program_phase_seconds=_maximum_phases(reports, "program_phase_seconds"),
            rank_seconds=rank_seconds,
        )

    def close(self) -> None:
        """Stop worker threads and release all captured graphs."""
        for executor in self._executors:
            executor.shutdown(wait=True, cancel_futures=True)
        for collector in self._collectors:
            collector.close()


ProgramRolloutDriver = ProgramRolloutCollector | ProgramRolloutPool


def create_program_rollout(
    settings: ProgramRlSettings,
    repository_root: Path,
    backend: BackendApi,
    model: ProgramActorCritic,
    contract: NativeProgramContract,
    environment: Mapping[str, object],
    *,
    use_cuda_graphs: bool = True,
) -> ProgramRolloutDriver:
    """Create the configured single- or multi-device rollout driver."""
    devices = tuple(torch.device(value) for value in settings.rollout.devices)
    common: dict[str, Any] = {
        "batch_games": settings.rollout.batch_games,
        "cpu_workers": settings.rollout.cpu_workers,
        "actor_streams": settings.rollout.actor_streams,
        "cpu_threads": settings.cpu_threads,
        "host_memory_limit_gib": settings.rollout.host_memory_limit_gib,
        "sampling_seed": settings.seed + 17_171,
        "act_timeout_seconds": settings.act_timeout_seconds,
        "remaining_overage_seconds": settings.remaining_overage_seconds,
        "use_cuda_graphs": use_cuda_graphs,
    }
    if len(devices) == 1:
        return ProgramRolloutCollector(
            backend,
            model,
            contract,
            repository_root,
            settings.public_agent_manifest,
            environment,
            settings.opponent_weights,
            devices[0],
            **common,
        )
    return ProgramRolloutPool(
        backend,
        model,
        contract,
        repository_root,
        settings.public_agent_manifest,
        dict(environment),
        settings.opponent_weights,
        devices,
        **common,
    )


__all__ = [
    "ProgramRolloutDriver",
    "ProgramRolloutPool",
    "create_program_rollout",
]
