"""One bounded rollout, native teacher labeling, and shard-write batch."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.programs.dataset import save_program_replay_shard
from kagg_revue.bc.programs.fused_teacher import FusedTeacherCompiler
from kagg_revue.bc.programs.student_state import translate_student_episodes
from kagg_revue.bc.programs.translate import ProgramReplaySeat
from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.rl.programs.rollout import ProgramRolloutCollector


def _save_translated_shard(
    task: tuple[Path, ProgramReplaySeat],
) -> dict[str, object]:
    """Compress and authenticate one independent correction shard."""
    return save_program_replay_shard(*task)


def prepare_correction_batch(
    *,
    backend: BackendApi,
    collector: ProgramRolloutCollector,
    environment: Mapping[str, object],
    architecture: ActorArchitecture,
    codec: ReplayActionEncoder,
    contract: NativeProgramContract,
    workers: int,
    shard_executor: ThreadPoolExecutor,
    build_path: Path,
    batch_seeds: Sequence[int],
    partitions_by_seed: Mapping[int, str],
    records: list[dict[str, object]],
    phase_seconds: dict[str, float],
    rollout_phase_seconds: dict[str, float],
    program_phase_seconds: dict[str, float],
    fused_teacher: FusedTeacherCompiler | None = None,
) -> int:
    """Append one exact correction batch and return its physical game count."""
    phase_started = time.perf_counter()
    rollout = collector.collect(batch_seeds, update=0, sample=False)
    phase_seconds["student_rollout"] += time.perf_counter() - phase_started
    for name, value in rollout.phase_seconds.items():
        rollout_phase_seconds[name] = rollout_phase_seconds.get(name, 0.0) + value
    for name, value in rollout.program_phase_seconds.items():
        program_phase_seconds[name] = program_phase_seconds.get(name, 0.0) + value
    phase_started = time.perf_counter()
    translated_episodes = (
        fused_teacher.translate(rollout.episodes)
        if fused_teacher is not None
        else translate_student_episodes(
            backend,
            rollout.episodes,
            environment,
            architecture,
            codec,
            contract,
            workers,
        )
    )
    phase_seconds["teacher_replay_and_compile"] += time.perf_counter() - phase_started
    phase_started = time.perf_counter()
    shard_ids = [
        f"correction-{episode.seed}-student-seat-{episode.seat}"
        for episode in rollout.episodes
    ]
    relative_paths = [Path("shards") / f"{shard_id}.npz" for shard_id in shard_ids]
    identities = tuple(
        shard_executor.map(
            _save_translated_shard,
            (
                (build_path / relative, translated)
                for relative, translated in zip(
                    relative_paths,
                    translated_episodes,
                    strict=True,
                )
            ),
        )
    )
    for episode, translated, shard_id, relative, identity in zip(
        rollout.episodes,
        translated_episodes,
        shard_ids,
        relative_paths,
        identities,
        strict=True,
    ):
        records.append(
            {
                "shard_id": shard_id,
                "path": str(relative),
                **identity,
                "episode_id": episode.episode_id,
                "source_date": "student-state-teacher-correction",
                "seat": episode.seat,
                "partition": partitions_by_seed[episode.seed],
                "terminal_cash": episode.terminal_cash,
                "opponent_cash": episode.opponent_cash,
                "statistics": dict(translated.statistics),
            }
        )
    phase_seconds["shard_write"] += time.perf_counter() - phase_started
    return rollout.physical_games


__all__ = ["prepare_correction_batch"]
