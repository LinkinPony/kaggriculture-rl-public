"""Complete official-rule rollouts for terminal-outcome training."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol, cast

import torch

from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.process import PublicAgentProcess
from kagg_revue.opponents.registry import (
    create_trusted_runtime,
    trusted_runtime_identity,
)
from kagg_revue.policy.economics import EconomicStateLayout
from kagg_revue.policy.runtime import BaselineAgent
from kagg_revue.rl.data import RolloutMatch, Trajectory
from kagg_revue.rl.opening.noise import OpeningNoisePlan
from kagg_revue.rl.outcome import OutcomeActorCritic
from kagg_revue.rl.rollout.scheduler import BatchedRolloutRunner, Job, rollout_jobs


class _OfficialAgent(Protocol):
    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one official request."""


class RolloutCollector:
    """Generate one GPU-batched paired-seat panel against frozen opponents."""

    def __init__(
        self,
        backend: BackendApi,
        model: OutcomeActorCritic,
        repository_root: Path,
        public_agent_manifest: Path,
        environment: Mapping[str, object],
        opponents: tuple[str, ...],
        device: torch.device,
        unit_limit: int,
        batch_games: int,
        cpu_workers: int,
        actor_streams: int,
        gpu_policy_session: bool,
        sampling_seed: int,
        host_memory_limit_gib: float,
        gpu_memory_fraction: float,
        *,
        frozen_actor_models: Mapping[str, OutcomeActorCritic] | None = None,
        frozen_actor_identities: Mapping[str, Mapping[str, object]] | None = None,
    ) -> None:
        """Bind one model, authenticate opponents, and bound host concurrency."""
        self._backend = backend
        self._model = model
        self._repository_root = repository_root
        self._environment = dict(environment)
        episode_steps = self._environment.get("episodeSteps")
        if not isinstance(episode_steps, int) or isinstance(episode_steps, bool):
            raise TypeError("rollout environment episodeSteps must be an integer")
        self._episode_steps = episode_steps
        self._opponents = opponents
        self._device = device
        self._unit_limit = unit_limit
        self._batch_games = batch_games
        self._cpu_workers = cpu_workers
        self._actor_streams = actor_streams
        self._gpu_policy_session = gpu_policy_session
        self._sampling_seed = sampling_seed
        self._host_memory_limit_bytes = int(host_memory_limit_gib * 1024**3)
        self._gpu_memory_fraction = gpu_memory_fraction
        self._last_performance: dict[str, object] = {}
        self._last_matches: tuple[RolloutMatch, ...] = ()
        self._capacity: dict[str, object] = {}
        manifest = backend.load_public_agent_manifest(public_agent_manifest)
        self._public_records = manifest.by_id()
        self._frozen_actor_models = dict(frozen_actor_models or {})
        self._frozen_actor_identities = {
            opponent_id: dict(identity)
            for opponent_id, identity in (frozen_actor_identities or {}).items()
        }
        if set(self._frozen_actor_models) != set(self._frozen_actor_identities):
            raise ValueError("frozen actor models and identities differ")
        collisions = set(self._frozen_actor_models) & set(self._public_records)
        if collisions:
            raise ValueError(
                f"frozen actor identities collide with the manifest: {sorted(collisions)}"
            )
        reserved = {"self_play", "deterministic_incumbent"}
        unknown = (
            set(opponents)
            - reserved
            - set(self._public_records)
            - set(self._frozen_actor_models)
        )
        if unknown:
            raise KeyError(f"rollout opponents are absent from the manifest: {sorted(unknown)}")
        self._standard_runner = self._new_runner(opponents, self._frozen_actor_models)
        self._historical_runner: BatchedRolloutRunner | None = None
        self._historical_model: OutcomeActorCritic | None = None

    @property
    def opponent_identities(self) -> dict[str, object]:
        """Return immutable identities for every configured opponent."""
        identities: dict[str, object] = {}
        for opponent in self._opponents:
            if opponent in self._frozen_actor_identities:
                identities[opponent] = dict(self._frozen_actor_identities[opponent])
            elif opponent in {"self_play", "deterministic_incumbent"}:
                identities[opponent] = {"kind": opponent}
            else:
                record = self._public_records[opponent]
                trusted = trusted_runtime_identity(record)
                identities[opponent] = {
                    "kind": "public_notebook",
                    "notebook_ref": record.notebook_ref,
                    "notebook_id": record.notebook_id,
                    "artifact_sha256": record.sha256,
                    "process_isolated": trusted is None,
                    **({"training_runtime": trusted} if trusted is not None else {}),
                }
        return identities

    @property
    def last_performance(self) -> dict[str, object]:
        """Return non-synchronizing phase timings for the most recent panel."""
        return dict(self._last_performance)

    @property
    def capacity(self) -> dict[str, object]:
        """Return the latest pre-allocation host/GPU memory bound."""
        return dict(self._capacity)

    @property
    def last_matches(self) -> tuple[RolloutMatch, ...]:
        """Return actual environment matches before perspective expansion."""
        return self._last_matches

    @staticmethod
    def _available_host_memory() -> int:
        with Path("/proc/meminfo").open(encoding="utf-8") as stream:
            for line in stream:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
        raise RuntimeError("host available memory is absent from /proc/meminfo")

    def _validate_capacity(
        self,
        jobs: Sequence[Job],
        historical_opponents: frozenset[str],
    ) -> None:
        architecture = self._model.actor.architecture
        if not jobs:
            raise ValueError("rollout job panel cannot be empty")
        groups = [
            jobs[start : start + self._batch_games]
            for start in range(0, len(jobs), self._batch_games)
        ]
        group_actor_rows = [
            sum(
                2 if opponent == "self_play" or opponent in historical_opponents else 1
                for _, _, opponent in group
            )
            for group in groups
        ]
        actor_rows = max(group_actor_rows)
        total_actor_rows = sum(group_actor_rows)
        active_actor_streams = (
            min(self._actor_streams, len(groups))
            if self._device.type == "cuda" and not historical_opponents
            else 1
        )
        concurrent_actor_rows = sum(sorted(group_actor_rows, reverse=True)[:active_actor_streams])
        decisions = architecture.max_decisions
        stored_turn_bytes = 2 * (
            math.prod(architecture.board_shape)
            + math.prod(architecture.unit_shape)
            + decisions * architecture.prefix_fact_features
            + decisions * architecture.action_tokens * architecture.candidate_fact_features
            + decisions * architecture.turn_fact_features
        )
        stored_turn_bytes += 4 * architecture.global_features
        if architecture.economic_feature_version is not None:
            stored_turn_bytes += (
                4
                * EconomicStateLayout.create(
                    architecture.board_shape[-1],
                    architecture.unit_shape[1],
                ).width
            )
        stored_turn_bytes += decisions * (architecture.action_tokens + 8 + 8 + 8 + 1 + 4)
        stored_turn_bytes += 8 + 4 + 4  # skill id, skill log-probability, and value
        turns = self._episode_steps - 1
        process_isolated_public_games = sum(
            opponent not in {"self_play", "deterministic_incumbent", *historical_opponents}
            and trusted_runtime_identity(self._public_records[opponent]) is None
            for _, _, opponent in jobs
        )
        host_estimate = (
            2 * len(jobs) * turns * stored_turn_bytes
            + process_isolated_public_games * 256 * 1024**2
        )
        host_available = self._available_host_memory()
        host_allowed = min(self._host_memory_limit_bytes, int(0.75 * host_available))
        if host_estimate > host_allowed:
            raise MemoryError(
                "rollout host-memory estimate exceeds the configured/available bound: "
                f"{host_estimate} > {host_allowed} bytes"
            )

        gpu_estimate = 0
        gpu_allowed = 0
        gpu_free = 0
        if self._device.type == "cuda":
            element_bytes = 2
            history_cache = (
                total_actor_rows
                * architecture.temporal_layers
                * architecture.max_history
                * architecture.model_width
                * 2
                * element_bytes
            )
            action_cache = (
                concurrent_actor_rows
                * architecture.action_layers
                * architecture.max_decisions
                * architecture.model_width
                * 2
                * element_bytes
            )
            model_bytes = sum(
                parameter.numel() * parameter.element_size()
                for parameter in self._model.parameters()
            )
            gpu_estimate = model_bytes + 2 * history_cache + 3 * action_cache
            gpu_free, _ = torch.cuda.mem_get_info(self._device)
            gpu_allowed = int(gpu_free * self._gpu_memory_fraction)
            if gpu_estimate > gpu_allowed:
                raise MemoryError(
                    "rollout GPU-memory estimate exceeds the free-memory bound: "
                    f"{gpu_estimate} > {gpu_allowed} bytes"
                )
        self._capacity = {
            "games": len(jobs),
            "training_trajectories": sum(
                2 if opponent == "self_play" else 1 for _, _, opponent in jobs
            ),
            "maximum_actor_rows": actor_rows,
            "total_actor_rows": total_actor_rows,
            "concurrent_actor_rows": concurrent_actor_rows,
            "actor_streams": active_actor_streams,
            "host_estimated_bytes": host_estimate,
            "host_available_bytes": host_available,
            "host_allowed_bytes": host_allowed,
            "gpu_estimated_bytes": gpu_estimate,
            "gpu_free_bytes": gpu_free,
            "gpu_allowed_bytes": gpu_allowed,
            "process_isolated_public_games": process_isolated_public_games,
        }

    def _official_opponent(
        self, opponent_id: str, configuration: Mapping[str, Any]
    ) -> _OfficialAgent:
        if opponent_id == "deterministic_incumbent":
            return BaselineAgent(self._backend, configuration)
        record = self._public_records[opponent_id]
        trusted = create_trusted_runtime(
            record,
            self._repository_root,
            configuration,
        )
        if trusted is not None:
            return trusted
        return cast(
            _OfficialAgent,
            PublicAgentProcess(record, self._repository_root, configuration),
        )

    def _new_runner(
        self,
        opponents: tuple[str, ...],
        historical_models: Mapping[str, OutcomeActorCritic],
    ) -> BatchedRolloutRunner:
        """Create one fixed-shape runner whose CUDA lanes survive every update."""
        return BatchedRolloutRunner(
            self._backend,
            self._model,
            self._environment,
            opponents,
            self._official_opponent,
            self._device,
            self._unit_limit,
            self._batch_games,
            self._cpu_workers,
            self._actor_streams,
            self._gpu_policy_session,
            self._sampling_seed,
            historical_models,
        )

    def collect(
        self,
        seeds: Sequence[int],
        progress: Callable[[Trajectory, int, int], None] | None = None,
        historical_opponent: tuple[str, OutcomeActorCritic] | None = None,
        sampling_seed: int | None = None,
        opening_plan: OpeningNoisePlan | None = None,
    ) -> list[Trajectory]:
        """Collect the whole panel through the sole GPU-batched production path."""
        self._model.eval()
        if historical_opponent is None:
            opponents = self._opponents
            historical_models = self._frozen_actor_models
            runner = self._standard_runner
        else:
            opponent_id, historical_model = historical_opponent
            if not opponent_id or opponent_id in {
                "self_play",
                "deterministic_incumbent",
            }:
                raise ValueError("historical actor needs a distinct immutable identity")
            opponents = (opponent_id,)
            historical_models = {opponent_id: historical_model}
            if self._historical_runner is None:
                self._historical_model = historical_model
                self._historical_runner = self._new_runner(
                    opponents,
                    historical_models,
                )
            else:
                if historical_model is not self._historical_model:
                    raise ValueError("historical rollout must update the resident model in place")
                self._historical_runner.set_historical_opponent(
                    opponent_id,
                    historical_model,
                )
            runner = self._historical_runner
        historical_ids = frozenset(historical_models)
        jobs = rollout_jobs(seeds, opponents)
        self._validate_capacity(jobs, historical_ids)
        runner.set_sampling_seed(self._sampling_seed if sampling_seed is None else sampling_seed)
        runner.set_opening_residuals({} if opening_plan is None else opening_plan.assignments)
        trajectories = runner.collect_jobs(jobs, progress)
        self._last_matches = runner.last_matches
        self._last_performance = runner.diagnostics
        return trajectories

    def collect_jobs(
        self,
        jobs: Sequence[Job],
        progress: Callable[[Trajectory, int, int], None] | None = None,
        *,
        sampling_seed: int | None = None,
        opening_plan: OpeningNoisePlan | None = None,
        force_opening_buffer: bool = False,
    ) -> list[Trajectory]:
        """Collect one explicit weighted per-seed panel."""
        unknown = {opponent_id for _, _, opponent_id in jobs} - set(self._opponents)
        if unknown:
            raise ValueError(f"rollout jobs name unconfigured opponents: {sorted(unknown)}")
        self._model.eval()
        self._validate_capacity(jobs, frozenset(self._frozen_actor_models))
        self._standard_runner.set_sampling_seed(
            self._sampling_seed if sampling_seed is None else sampling_seed
        )
        self._standard_runner.set_opening_residuals(
            {} if opening_plan is None else opening_plan.assignments,
            force_buffer=force_opening_buffer,
        )
        trajectories = self._standard_runner.collect_jobs(jobs, progress)
        self._last_matches = self._standard_runner.last_matches
        self._last_performance = self._standard_runner.diagnostics
        return trajectories

    def close(self) -> None:
        """Release persistent rollout graphs after all updates complete."""
        self._standard_runner.close()
        if self._historical_runner is not None:
            self._historical_runner.close()


__all__ = ["RolloutCollector"]
