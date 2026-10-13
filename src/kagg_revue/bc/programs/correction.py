"""DAgger-style teacher labels on conditional-program student states."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import time
from collections import Counter
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import orjson
import torch

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.programs.config import ProgramBcSettings
from kagg_revue.bc.programs.correction_batch import prepare_correction_batch
from kagg_revue.bc.programs.fused_teacher import FusedTeacherCompiler
from kagg_revue.bc.programs.generation import (
    _agent_identities,
    _partitions,
    _write_json,
)
from kagg_revue.bc.programs.prepare import resolve_program_bc_settings
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.runtime import load_actor
from kagg_revue.rl.programs.checkpoint import load_program_checkpoint
from kagg_revue.rl.programs.model import ProgramActorCritic
from kagg_revue.rl.programs.rollout import ProgramRolloutCollector


def _student_model(
    settings: ProgramBcSettings,
    contract: NativeProgramContract,
    architecture: ActorArchitecture,
    device: torch.device,
) -> tuple[ProgramActorCritic, dict[str, object]]:
    correction = settings.correction_source
    if correction is None:
        raise ValueError("program correction source is absent")
    model, metadata = load_program_checkpoint(
        correction.student_checkpoint,
        contract,
        device,
    )
    expected = contract.architecture(
        context_width=architecture.model_width,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
    )
    if model.actor.architecture != architecture or model.programs.architecture != expected:
        raise ValueError("program correction student differs from its profile")
    model.eval()
    return model, metadata


def prepare_program_corrections(
    raw_settings: ProgramBcSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Generate teacher program targets on complete frozen-student rollouts."""
    root = repository_root.resolve()
    settings = resolve_program_bc_settings(raw_settings, root)
    correction = settings.correction_source
    if correction is None:
        raise ValueError("program correction preparation requires a correction source")
    source = source_identity(root)
    if bool(source["worktree_dirty"]):
        raise RuntimeError("program correction preparation requires a clean source tree")
    if settings.dataset_dir.exists():
        raise FileExistsError(f"program correction dataset exists: {settings.dataset_dir}")
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.output_dir / "data-preparation-report.json"
    if report_path.exists():
        raise FileExistsError(f"program correction report exists: {report_path}")
    backend = load_backend(root)
    environment = cast(
        dict[str, object],
        dict(backend.engine(seed=0, configuration=settings.environment).configuration),
    )
    identities = _agent_identities(
        backend,
        correction.public_agent_manifest,
        (correction.teacher, correction.opponent),
    )
    actor, action_keys, encoder_version, fact_version = load_actor(
        settings.initial_actor,
        torch.device("cpu"),
    )
    architecture = actor.architecture
    contract = NativeProgramContract.from_spec(
        cast(
            Mapping[str, object],
            backend.conditional_program_spec(environment, settings.abi.unit_limit),
        )
    )
    device = torch.device(correction.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA program correction requested without a GPU")
    model, student_metadata = _student_model(
        settings,
        contract,
        architecture,
        device,
    )
    seeds = tuple(range(correction.seed_start, correction.seed_start + correction.seeds))
    partitions_by_seed, selection = _partitions(
        seeds,
        partition_seed=settings.optimization.seed,
        validation_fraction=correction.validation_fraction,
        test_fraction=correction.test_fraction,
        semantics=(
            "paired seats from one frozen student checkpoint against one frozen "
            "authenticated opponent; no outcome or cash filtering"
        ),
    )
    codec = ReplayActionEncoder(cast(Mapping[str, Any], backend.action_codec_spec()))
    maximum_orders = environment.get("maxMarketOrdersPerTurn")
    if not isinstance(maximum_orders, int) or isinstance(maximum_orders, bool):
        raise ValueError("program correction requires integer market order capacity")
    fused_teacher = (
        FusedTeacherCompiler(
            backend,
            maximum_orders,
            architecture,
            codec,
            contract,
            correction.teacher_workers or correction.workers,
        )
        if correction.fuse_teacher
        else None
    )
    collector = ProgramRolloutCollector(
        backend,
        model,
        contract,
        root,
        correction.public_agent_manifest,
        environment,
        {correction.opponent: 1.0},
        device,
        batch_games=2 * correction.batch_seeds,
        cpu_workers=correction.workers,
        actor_streams=correction.actor_streams,
        cpu_threads=settings.optimization.cpu_threads,
        host_memory_limit_gib=correction.host_memory_limit_gib,
        sampling_seed=settings.optimization.seed + 91_003,
        act_timeout_seconds=1.0,
        remaining_overage_seconds=60.0,
        use_cuda_graphs=correction.use_cuda_graphs,
        use_full_turn_graph=correction.use_full_turn_graph,
        observer=fused_teacher,
    )
    (root / "tmp").mkdir(parents=True, exist_ok=True)
    build_path = Path(tempfile.mkdtemp(prefix="program-corrections-", dir=root / "tmp"))
    (build_path / "shards").mkdir()
    records: list[dict[str, object]] = []
    phase_seconds = {
        "student_rollout": 0.0,
        "teacher_replay_and_compile": 0.0,
        "shard_write": 0.0,
    }
    rollout_phase_seconds: dict[str, float] = {}
    program_phase_seconds: dict[str, float] = {}
    physical_games = 0
    started = time.perf_counter()
    try:
        with ThreadPoolExecutor(
            max_workers=correction.shard_workers,
            thread_name_prefix="program-correction-shard",
        ) as shard_executor:
            for batch_index, first in enumerate(
                range(0, len(seeds), correction.batch_seeds),
                start=1,
            ):
                physical_games += prepare_correction_batch(
                    backend=backend,
                    collector=collector,
                    environment=environment,
                    architecture=architecture,
                    codec=codec,
                    contract=contract,
                    workers=correction.workers,
                    shard_executor=shard_executor,
                    build_path=build_path,
                    batch_seeds=seeds[first : first + correction.batch_seeds],
                    partitions_by_seed=partitions_by_seed,
                    records=records,
                    phase_seconds=phase_seconds,
                    rollout_phase_seconds=rollout_phase_seconds,
                    program_phase_seconds=program_phase_seconds,
                    fused_teacher=fused_teacher,
                )
                print(
                    json.dumps(
                        {
                            "completed_batches": batch_index,
                            "batches": len(seeds) // correction.batch_seeds,
                            "completed_shards": len(records),
                            "elapsed_seconds": time.perf_counter() - started,
                            "phase_seconds": phase_seconds,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        records.sort(key=lambda row: str(row["shard_id"]))
        partitions = {
            partition: tuple(
                str(row["shard_id"])
                for row in records
                if row["partition"] == partition
            )
            for partition in ("train", "validation", "test")
        }
        outcomes = Counter(int(cast(int, row["outcome"])) for row in records)
        actor_identity = {
            "path": str(settings.initial_actor),
            "sha256": sha256_file(settings.initial_actor),
            "size_bytes": settings.initial_actor.stat().st_size,
            "actor_encoder_version": encoder_version,
            "derived_fact_version": fact_version,
            "action_keys": list(action_keys),
        }
        checkpoint_identity = cast(
            Mapping[str, object],
            student_metadata["checkpoint_identity"],
        )
        program_architecture = model.programs.architecture
        stable = {
            "selection_id": selection["selection_id"],
            "teacher": identities[correction.teacher],
            "opponent": identities[correction.opponent],
            "student_checkpoint_sha256": checkpoint_identity["sha256"],
            "source_actor_sha256": actor_identity["sha256"],
            "program_architecture": program_architecture.model_dump(mode="json"),
            "shards": [
                {"shard_id": row["shard_id"], "sha256": row["sha256"]}
                for row in records
            ],
        }
        dataset_id = hashlib.sha256(
            orjson.dumps(stable, option=orjson.OPT_SORT_KEYS)
        ).hexdigest()
        manifest: dict[str, object] = {
            "schema_version": "conditional-program-bc-dataset-v1",
            "dataset_id": dataset_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "source": {
                "kind": "student_state_teacher_correction",
                "source_revision": source,
                "student_checkpoint": dict(checkpoint_identity),
                "student_checkpoint_training_source": student_metadata.get(
                    "source_identity"
                ),
                "teacher": {
                    "agent_id": correction.teacher,
                    **cast(dict[str, object], identities[correction.teacher]),
                },
                "opponent": {
                    "agent_id": correction.opponent,
                    **cast(dict[str, object], identities[correction.opponent]),
                },
                "public_agent_manifest": {
                    "path": str(correction.public_agent_manifest),
                    "sha256": sha256_file(correction.public_agent_manifest),
                },
            },
            "source_actor_identity": actor_identity,
            "native_backend": backend.identity,
            "native_program_abi": contract.version,
            "actor_architecture": architecture.model_dump(mode="json"),
            "program_architecture": program_architecture.model_dump(mode="json"),
            "action_keys": list(action_keys),
            "environment": environment,
            "translation": {
                "states": "greedy frozen-student complete matches",
                "actor_history": "student actions actually executed",
                "program_targets": "Kaito v48 queried before each student action",
                "teacher_program_compiler": (
                    "fused_native_teacher_trace_v3"
                    if fused_teacher is not None
                    else "native_teacher_trace_v2"
                ),
                "scheduled_sampling": False,
            },
            "selection": selection,
            "partitions": partitions,
            "shards": records,
        }
        _write_json(build_path / "manifest.json", manifest)
        settings.dataset_dir.parent.mkdir(parents=True, exist_ok=True)
        build_path.replace(settings.dataset_dir)
        report: dict[str, object] = {
            "schema_version": "conditional-program-bc-correction-report-v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": {
                "path": str(settings.dataset_dir),
                "manifest_sha256": sha256_file(settings.dataset_dir / "manifest.json"),
                "dataset_id": dataset_id,
                "shards": len(records),
            },
            "source": manifest["source"],
            "selection": selection,
            "translation": manifest["translation"],
            "partitions": {name: len(values) for name, values in partitions.items()},
            "student_outcomes": {
                "wins": outcomes[1],
                "ties": outcomes[0],
                "losses": outcomes[-1],
            },
            "execution": {
                "physical_games": physical_games,
                "elapsed_seconds": time.perf_counter() - started,
                "games_per_second": physical_games
                / max(time.perf_counter() - started, 1e-9),
                "phase_seconds": phase_seconds,
                "rollout_phase_seconds": rollout_phase_seconds,
                "program_phase_seconds": program_phase_seconds,
                "teacher_overlap": (
                    {
                        "native_seconds": fused_teacher.native_seconds,
                        "action_seconds": fused_teacher.action_seconds,
                        "compiler_seconds": fused_teacher.compiler_seconds,
                        "wait_seconds": fused_teacher.wait_seconds,
                        "clone_seconds": fused_teacher.clone_seconds,
                    }
                    if fused_teacher is not None
                    else None
                ),
            },
        }
        _write_json(report_path, report)
        return report
    finally:
        collector.close()
        if fused_teacher is not None:
            fused_teacher.close()
        if build_path.exists():
            shutil.rmtree(build_path)


__all__ = ["prepare_program_corrections"]
