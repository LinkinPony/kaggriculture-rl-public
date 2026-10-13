"""End-to-end random-initialized BC for canonical intent policies."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import shutil
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import orjson
import torch
from torch import distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.intents.config import IntentBcSettings
from kagg_revue.bc.intents.dataset import (
    IntentTeacherManifest,
    IntentTeacherShard,
    load_intent_teacher_manifest,
)
from kagg_revue.bc.intents.learning import run_intent_bc_partition
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.intents.contract import NativeIntentContract
from kagg_revue.policy.intents.model import IntentActorCritic
from kagg_revue.policy.model import parameter_count
from kagg_revue.rl.intents.checkpoint import (
    capture_rng,
    load_checkpoint,
    save_checkpoint,
)
from kagg_revue.rl.intents.initialization import initialize_intent_model
from kagg_revue.rl.intents.learning import IntentSequenceEvaluator


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, default=str), encoding="utf-8")
    temporary.replace(path)


def _alias(source: Path, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    try:
        os.link(source, temporary)
    except OSError:
        shutil.copy2(source, temporary)
    temporary.replace(destination)


def _partitions(
    manifest: IntentTeacherManifest,
    validation_games: int,
    test_games: int,
) -> dict[str, tuple[IntentTeacherShard, ...]]:
    if any(shard.games != 1 for shard in manifest.shards):
        raise ValueError("intent BC currently requires one complete physical game per shard")
    games = len(manifest.shards)
    training_games = games - validation_games - test_games
    if training_games < 1:
        raise ValueError("intent BC held-out partitions leave no training games")
    validation_end = training_games + validation_games
    return {
        "train": manifest.shards[:training_games],
        "validation": manifest.shards[training_games:validation_end],
        "test": manifest.shards[validation_end:],
    }


def _integer(values: Mapping[str, object], name: str) -> int:
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"intent BC environment {name} must be an integer")
    return value


def _number(values: Mapping[str, object], name: str) -> float:
    value = values.get(name)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"intent BC metric {name} must be numeric")
    return float(value)


def _completed_optimizer_steps(history: Sequence[Mapping[str, object]]) -> int:
    total = 0
    for item in history:
        training = item.get("training")
        if not isinstance(training, Mapping):
            raise TypeError("intent BC history lacks training metrics")
        total += _integer(cast(Mapping[str, object], training), "optimizer_steps")
    return total


def _contract(backend: Any, environment: Mapping[str, object]) -> NativeIntentContract:
    raw = backend.intent_ledger_spec()
    if not isinstance(raw, Mapping):
        raise TypeError("native intent specification must be a mapping")
    return NativeIntentContract.from_spec(raw, board_size=_integer(environment, "boardSize"))


def _validate_dataset(
    manifest: IntentTeacherManifest,
    settings: IntentBcSettings,
    backend: Any,
    environment: Mapping[str, object],
    contract: NativeIntentContract,
    source_actor: Mapping[str, object],
) -> None:
    if manifest.dataset_id != settings.dataset_id:
        raise ValueError("intent BC dataset ID differs from the resolved profile")
    if manifest.source.get("worktree_dirty") is not False:
        raise ValueError("intent BC production data was not generated from a clean revision")
    if manifest.environment != dict(environment):
        raise ValueError("intent BC environment differs from its dataset")
    if manifest.unit_limit != settings.unit_limit:
        raise ValueError("intent BC unit limit differs from its dataset")
    if manifest.intent_abi_version != contract.version:
        raise ValueError("intent BC native ABI differs from its dataset")
    raw_spec = backend.intent_ledger_spec()
    spec_sha256 = hashlib.sha256(orjson.dumps(raw_spec, option=orjson.OPT_SORT_KEYS)).hexdigest()
    if manifest.intent_spec_sha256 != spec_sha256:
        raise ValueError("intent BC native specification differs from its dataset")
    encoder = backend.actor_encoder_spec()
    codec = backend.action_codec_spec()
    if not isinstance(encoder, Mapping) or not isinstance(codec, Mapping):
        raise TypeError("intent BC actor ABI specifications must be mappings")
    if (
        manifest.actor_encoder_version != str(encoder["version"])
        or manifest.action_codec_version != str(codec["version"])
        or source_actor.get("actor_encoder_version") != manifest.actor_encoder_version
        or tuple(cast(Sequence[object], source_actor.get("action_keys", ())))
        != tuple(str(value) for value in codec["keys"])
        or source_actor.get("initialization") != "random"
    ):
        raise ValueError("intent BC actor structure differs from its dataset ABI")


def _trainable_parameters(model: IntentActorCritic) -> list[nn.Parameter]:
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if not parameters:
        raise RuntimeError("intent BC froze every model parameter")
    return parameters


def _checkpoint(
    path: Path,
    model: IntentActorCritic,
    optimizer: torch.optim.Optimizer,
    *,
    epoch: int,
    contract: NativeIntentContract,
    resolved: Mapping[str, object],
    source_actor: Mapping[str, object],
    source: Mapping[str, object],
    randomizer: random.Random,
    generator: torch.Generator,
    device: torch.device,
) -> dict[str, object]:
    return save_checkpoint(
        path,
        model,
        optimizer,
        update=epoch,
        contract=contract,
        resolved_config=resolved,
        source_actor=source_actor,
        source_revision=source,
        rng_state=capture_rng(randomizer, generator, device),
    )


def train_intent_bc(raw_settings: IntentBcSettings, repository_root: Path) -> dict[str, object]:
    """Train deployment-relevant intent parameters from a fresh random initialization."""
    root = repository_root.resolve()
    source = source_identity(root)
    if source["worktree_dirty"]:
        raise RuntimeError("intent BC requires a clean committed source revision")
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    rank = int(os.environ.get("RANK", "0"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    if world_size < 1 or rank < 0 or rank >= world_size:
        raise ValueError("intent BC distributed rank environment is invalid")
    requested_device = torch.device(raw_settings.optimization.device)
    distributed = world_size > 1
    if distributed:
        if requested_device.type != "cuda" or not torch.cuda.is_available():
            raise RuntimeError("distributed intent BC requires CUDA")
        if local_rank < 0 or local_rank >= torch.cuda.device_count():
            raise ValueError("intent BC local rank has no CUDA device")
        device = torch.device("cuda", local_rank)
        torch.cuda.set_device(device)
        dist.init_process_group(backend="nccl")
    else:
        device = requested_device
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("intent BC requested CUDA but no GPU is available")

    dataset_dir = (root / raw_settings.dataset_dir).resolve()
    output_dir = (root / raw_settings.output_dir).resolve()
    architecture_actor = (root / raw_settings.architecture_actor).resolve()
    if not dataset_dir.is_relative_to((root / "data" / "external").resolve()):
        raise ValueError("intent BC dataset escaped data/external/")
    if not output_dir.is_relative_to((root / "outputs").resolve()):
        raise ValueError("intent BC output escaped outputs/")
    if not architecture_actor.is_relative_to((root / "outputs").resolve()):
        raise ValueError("intent BC architecture source escaped outputs/")
    if not architecture_actor.is_file():
        raise FileNotFoundError(
            f"intent BC architecture source does not exist: {architecture_actor}"
        )
    report_path = output_dir / "training-report.json"
    metrics_path = output_dir / "metrics.jsonl"
    checkpoints = output_dir / "checkpoints"
    if rank == 0:
        if output_dir.exists():
            raise FileExistsError(f"intent BC output already exists: {output_dir}")
        output_dir.mkdir(parents=True)
        checkpoints.mkdir()
    if distributed:
        dist.barrier()

    torch.set_num_threads(raw_settings.optimization.cpu_threads)
    torch.set_float32_matmul_precision("high")
    random.seed(raw_settings.optimization.seed)
    np.random.seed(raw_settings.optimization.seed)
    torch.manual_seed(raw_settings.optimization.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(raw_settings.optimization.seed)
    randomizer = random.Random(raw_settings.optimization.seed)
    generator = torch.Generator(device=device).manual_seed(
        raw_settings.optimization.seed + rank + 1
    )
    backend = load_backend(root)
    engine = backend.engine(seed=0, configuration=raw_settings.environment)
    environment = cast(dict[str, object], engine.configuration)
    contract = _contract(backend, environment)
    model, measured_contract, source_actor = initialize_intent_model(
        architecture_actor,
        backend,
        environment,
        raw_settings.unit_limit,
        raw_settings.model,
        device,
        random_actor=True,
    )
    if measured_contract != contract:
        raise RuntimeError("intent BC initialization observed an unstable native ABI")
    manifest = load_intent_teacher_manifest(dataset_dir)
    _validate_dataset(
        manifest,
        raw_settings,
        backend,
        environment,
        contract,
        source_actor,
    )
    partitions = _partitions(
        manifest,
        raw_settings.validation_games,
        raw_settings.test_games,
    )
    for name, shards in partitions.items():
        if len(shards) % raw_settings.optimization.games_per_batch:
            raise ValueError(f"intent BC {name} games do not fill the global batch")

    trainable = _trainable_parameters(model)
    training_model: nn.Module = IntentSequenceEvaluator(model)
    if distributed:
        training_model = DistributedDataParallel(
            training_model,
            device_ids=[device.index],
            output_device=device.index,
            forward_sync_buffers=False,
            static_graph=True,
        )
    optimizer = torch.optim.AdamW(
        trainable,
        lr=raw_settings.optimization.learning_rate,
        weight_decay=raw_settings.optimization.weight_decay,
        fused=device.type == "cuda",
    )
    resolved: dict[str, object] = {
        "intent_bc": raw_settings.model_dump(mode="json"),
        "environment": environment,
        "dataset": {
            "path": str(raw_settings.dataset_dir / "manifest.json"),
            "sha256": sha256_file(dataset_dir / "manifest.json"),
            "dataset_id": manifest.dataset_id,
        },
        "initialization": {
            "mode": "random",
            "seed": raw_settings.optimization.seed,
            "architecture_only_source": source_actor,
            "loaded_source_weights": False,
        },
        "distributed": {"world_size": world_size, "backend": "nccl" if distributed else None},
        "partitions": {
            name: {
                "games": len(shards),
                "seed_start": shards[0].seed_start,
                "seed_stop_exclusive": shards[-1].seed_start + 1,
            }
            for name, shards in partitions.items()
        },
    }
    if rank == 0:
        _write_json(output_dir / "resolved-settings.json", resolved)
        _write_json(
            output_dir / "run-status.json",
            {
                "status": "running",
                "started_at": datetime.now(UTC).isoformat(),
                "epoch": 0,
                "world_size": world_size,
            },
        )
        initial = _checkpoint(
            checkpoints / "initial-random.pt",
            model,
            optimizer,
            epoch=0,
            contract=contract,
            resolved=resolved,
            source_actor=source_actor,
            source=source,
            randomizer=randomizer,
            generator=generator,
            device=device,
        )
    else:
        initial = {}
    if distributed:
        dist.barrier()

    best_epoch = 0
    best_objective = math.inf
    history: list[dict[str, object]] = []
    total_started = time.perf_counter()
    for epoch in range(1, raw_settings.optimization.epochs + 1):
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        epoch_started = time.perf_counter()
        training = run_intent_bc_partition(
            model,
            dataset_dir,
            partitions["train"],
            "train",
            raw_settings,
            device,
            optimizer,
            epoch,
            training_model=training_model,
            rank=rank,
            world_size=world_size,
        )
        validation = run_intent_bc_partition(
            model,
            dataset_dir,
            partitions["validation"],
            "validation",
            raw_settings,
            device,
            None,
            epoch,
            rank=rank,
            world_size=world_size,
        )
        objective = _number(validation, "joint_turn_nll")
        selected = objective < best_objective
        if selected:
            best_epoch = epoch
            best_objective = objective
        peak = torch.tensor(
            [
                torch.cuda.max_memory_allocated(device) if device.type == "cuda" else 0,
                torch.cuda.max_memory_reserved(device) if device.type == "cuda" else 0,
            ],
            dtype=torch.int64,
            device=device,
        )
        if distributed:
            dist.all_reduce(peak, op=dist.ReduceOp.MAX)
        system = {
            "elapsed_seconds": time.perf_counter() - epoch_started,
            "total_elapsed_seconds": time.perf_counter() - total_started,
            "cuda_peak_allocated_bytes": int(peak[0]),
            "cuda_peak_reserved_bytes": int(peak[1]),
        }
        if rank == 0:
            checkpoint_path = checkpoints / f"epoch-{epoch:04d}.pt"
            checkpoint = _checkpoint(
                checkpoint_path,
                model,
                optimizer,
                epoch=epoch,
                contract=contract,
                resolved=resolved,
                source_actor=source_actor,
                source=source,
                randomizer=randomizer,
                generator=generator,
                device=device,
            )
            if selected:
                _alias(checkpoint_path, checkpoints / "best.pt")
            _alias(checkpoint_path, checkpoints / "latest.pt")
            row: dict[str, object] = {
                "epoch": epoch,
                "training": training,
                "validation": validation,
                "system": system,
                "checkpoint": checkpoint,
                "best": selected,
            }
            history.append(row)
            with metrics_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            _write_json(
                output_dir / "run-status.json",
                {
                    "status": "running",
                    "updated_at": datetime.now(UTC).isoformat(),
                    "epoch": epoch,
                    "optimizer_steps": _completed_optimizer_steps(history),
                    "world_size": world_size,
                },
            )
            print(json.dumps(row, sort_keys=True, default=str), flush=True)
        if distributed:
            dist.barrier()
    if best_epoch < 1:
        raise RuntimeError("intent BC produced no selected checkpoint")
    del training_model, optimizer, model
    if device.type == "cuda":
        torch.cuda.empty_cache()
    if distributed:
        dist.barrier()
    best_model, best_metadata = load_checkpoint(checkpoints / "best.pt", contract, device)
    best_model.actor.requires_grad_(False)
    best_model.actor.scene.requires_grad_(True)
    best_model.actor.temporal.requires_grad_(True)
    test = run_intent_bc_partition(
        best_model,
        dataset_dir,
        partitions["test"],
        "test",
        raw_settings,
        device,
        None,
        best_epoch,
        rank=rank,
        world_size=world_size,
    )
    report: dict[str, object] = {
        "schema_version": "canonical-intent-bc-training-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "training_complete",
        "purpose": "behavior warm start; no policy promotion authority",
        "objective": {
            "policy": "joint canonical transaction NLL on a fixed episode-turn surface",
            "critic": "episode-balanced direct terminal W/D/L cross-entropy",
            "checkpoint_selection": "minimum held-out joint transaction NLL",
        },
        "source": source,
        "dataset": cast(Mapping[str, object], resolved["dataset"]),
        "initialization": cast(Mapping[str, object], resolved["initialization"]),
        "execution": {
            "device": str(device),
            "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
            "world_size": world_size,
            "parameter_count": parameter_count(best_model),
            "trainable_parameter_count": sum(
                parameter.numel()
                for parameter in best_model.parameters()
                if parameter.requires_grad
            ),
        },
        "initial_checkpoint": initial,
        "epochs": history,
        "best": {
            "epoch": best_epoch,
            "validation_joint_turn_nll": best_objective,
            "checkpoint": best_metadata["checkpoint_identity"],
        },
        "test": test,
        "metrics": {"path": str(metrics_path), "sha256": sha256_file(metrics_path)},
    }
    if rank == 0:
        _write_json(report_path, report)
        _write_json(
            output_dir / "run-status.json",
            {
                "status": "complete",
                "completed_at": datetime.now(UTC).isoformat(),
                "epoch": raw_settings.optimization.epochs,
                "best_epoch": best_epoch,
                "optimizer_steps": _completed_optimizer_steps(history),
                "world_size": world_size,
            },
        )
    if distributed:
        dist.barrier()
        dist.destroy_process_group()
    return report if rank == 0 else {}


__all__ = ["train_intent_bc"]
