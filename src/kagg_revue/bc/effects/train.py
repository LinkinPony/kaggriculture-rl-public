"""End-to-end behavior cloning for atomic-effect policies."""

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

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.effects.config import EffectBcSettings
from kagg_revue.bc.effects.dataset import (
    EffectTeacherManifest,
    EffectTeacherShard,
    load_effect_teacher_manifest,
)
from kagg_revue.bc.effects.learning import run_effect_bc_partition
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.effects.contract import NativeEffectContract
from kagg_revue.policy.effects.model import EffectActorCritic
from kagg_revue.policy.model import parameter_count
from kagg_revue.rl.effects.checkpoint import (
    capture_rng,
    load_checkpoint,
    save_checkpoint,
)
from kagg_revue.rl.effects.initialization import (
    configure_effect_trainable,
    initialize_effect_model,
)


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
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
    manifest: EffectTeacherManifest,
    validation_games: int,
    test_games: int,
) -> dict[str, tuple[EffectTeacherShard, ...]]:
    if any(shard.games != 1 for shard in manifest.shards):
        raise ValueError("effect BC currently requires one physical game per shard")
    if manifest.partitions is not None:
        by_id = {
            shard.shard_id: shard
            for shard in manifest.shards
            if shard.shard_id is not None
        }
        result = {
            name: tuple(by_id[shard_id] for shard_id in manifest.partitions[name])
            for name in ("train", "validation", "test")
        }
        if any(not shards for shards in result.values()):
            raise ValueError("effect BC explicit partition is empty")
        return result
    games = len(manifest.shards)
    training_games = games - validation_games - test_games
    if training_games < 1:
        raise ValueError("effect BC held-out partitions leave no training games")
    validation_end = training_games + validation_games
    return {
        "train": manifest.shards[:training_games],
        "validation": manifest.shards[training_games:validation_end],
        "test": manifest.shards[validation_end:],
    }


def _integer(values: Mapping[str, object], name: str) -> int:
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"effect BC {name} must be an integer")
    return value


def _number(values: Mapping[str, object], name: str) -> float:
    value = values.get(name)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"effect BC metric {name} must be numeric")
    return float(value)


def _completed_optimizer_steps(history: Sequence[Mapping[str, object]]) -> int:
    total = 0
    for item in history:
        training = item.get("training")
        if not isinstance(training, Mapping):
            raise TypeError("effect BC history lacks training metrics")
        total += _integer(cast(Mapping[str, object], training), "optimizer_steps")
    return total


def _contract(
    backend: Any,
    environment: Mapping[str, object],
) -> NativeEffectContract:
    raw = backend.effect_policy_spec()
    if not isinstance(raw, Mapping):
        raise TypeError("native effect specification must be a mapping")
    return NativeEffectContract.from_spec(
        raw,
        board_size=_integer(environment, "boardSize"),
    )


def _validate_dataset(
    manifest: EffectTeacherManifest,
    settings: EffectBcSettings,
    backend: Any,
    environment: Mapping[str, object],
    contract: NativeEffectContract,
    source_actor: Mapping[str, object],
    model: EffectActorCritic,
    *,
    require_clean: bool,
) -> None:
    if manifest.dataset_id != settings.dataset_id:
        raise ValueError("effect BC dataset ID differs from the resolved profile")
    if require_clean and manifest.source.get("worktree_dirty") is not False:
        raise ValueError("effect BC data was not generated from a clean revision")
    if manifest.environment != dict(environment):
        raise ValueError("effect BC environment differs from its dataset")
    if manifest.unit_limit != settings.unit_limit:
        raise ValueError("effect BC unit limit differs from its dataset")
    if manifest.maximum_quantity != model.actor.architecture.maximum_quantity:
        raise ValueError("effect BC quantity range differs from its actor")
    if manifest.effect_abi_version != contract.version:
        raise ValueError("effect BC native ABI differs from its dataset")
    raw_spec = backend.effect_policy_spec()
    spec_sha256 = hashlib.sha256(
        orjson.dumps(raw_spec, option=orjson.OPT_SORT_KEYS)
    ).hexdigest()
    if manifest.effect_spec_sha256 != spec_sha256:
        raise ValueError("effect BC native specification differs from its dataset")
    encoder = backend.actor_encoder_spec()
    codec = backend.action_codec_spec()
    if not isinstance(encoder, Mapping) or not isinstance(codec, Mapping):
        raise TypeError("effect BC actor ABI specifications must be mappings")
    if (
        manifest.actor_encoder_version != str(encoder["version"])
        or manifest.action_codec_version != str(codec["version"])
        or source_actor.get("actor_encoder_version")
        != manifest.actor_encoder_version
        or tuple(cast(Sequence[object], source_actor.get("action_keys", ())))
        != tuple(str(value) for value in codec["keys"])
        or source_actor.get("initialization") != "pretrained"
    ):
        raise ValueError("effect BC actor structure differs from its dataset ABI")


def _trainable_parameters(model: EffectActorCritic) -> list[nn.Parameter]:
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if not parameters:
        raise RuntimeError("effect BC froze every model parameter")
    return parameters


def _checkpoint(
    path: Path,
    model: EffectActorCritic,
    optimizer: torch.optim.Optimizer,
    *,
    epoch: int,
    contract: NativeEffectContract,
    resolved: Mapping[str, object],
    source_actor: Mapping[str, object],
    source: Mapping[str, object],
    dataset: Mapping[str, object],
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
        opponent_identities={"behavior_teacher": dict(dataset)},
        population_state={
            "schema_version": "atomic-effect-bc-population-v1",
            "weights": {"rank8_teacher": 1.0},
        },
        rng_state=capture_rng(randomizer, generator, device),
    )


def train_effect_bc(
    raw_settings: EffectBcSettings,
    repository_root: Path,
    *,
    smoke: bool = False,
) -> dict[str, object]:
    """Train deployment-relevant effect parameters from a pretrained actor."""
    root = repository_root.resolve()
    source = source_identity(root)
    if source["worktree_dirty"] and not smoke:
        raise RuntimeError("effect BC requires a clean committed source revision")
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    rank = int(os.environ.get("RANK", "0"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    if world_size < 1 or rank < 0 or rank >= world_size:
        raise ValueError("effect BC distributed rank environment is invalid")
    if smoke:
        raw_settings = raw_settings.model_copy(
            update={
                "output_dir": raw_settings.output_dir.with_name(
                    f"{raw_settings.output_dir.name}-smoke"
                ),
                "optimization": raw_settings.optimization.model_copy(
                    update={"epochs": 1, "games_per_batch": world_size}
                ),
            }
        )
    requested_device = torch.device(raw_settings.optimization.device)
    distributed = world_size > 1
    if distributed:
        if requested_device.type != "cuda" or not torch.cuda.is_available():
            raise RuntimeError("distributed effect BC requires CUDA")
        if local_rank < 0 or local_rank >= torch.cuda.device_count():
            raise ValueError("effect BC local rank has no CUDA device")
        device = torch.device("cuda", local_rank)
        torch.cuda.set_device(device)
        dist.init_process_group(backend="nccl")
    else:
        device = requested_device
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("effect BC requested CUDA but no GPU is available")

    dataset_dir = (root / raw_settings.dataset_dir).resolve()
    output_dir = (root / raw_settings.output_dir).resolve()
    initial_actor = (root / raw_settings.initial_actor).resolve()
    initial_checkpoint = (
        None
        if raw_settings.initial_checkpoint is None
        else (root / raw_settings.initial_checkpoint).resolve()
    )
    if not dataset_dir.is_relative_to((root / "data" / "external").resolve()):
        raise ValueError("effect BC dataset escaped data/external/")
    if not output_dir.is_relative_to((root / "outputs").resolve()):
        raise ValueError("effect BC output escaped outputs/")
    if not initial_actor.is_relative_to((root / "outputs").resolve()):
        raise ValueError("effect BC initial actor escaped outputs/")
    if not initial_actor.is_file():
        raise FileNotFoundError(f"effect BC initial actor does not exist: {initial_actor}")
    if initial_checkpoint is not None:
        if not initial_checkpoint.is_relative_to((root / "outputs").resolve()):
            raise ValueError("effect BC initial checkpoint escaped outputs/")
        if not initial_checkpoint.is_file():
            raise FileNotFoundError(
                f"effect BC initial checkpoint does not exist: {initial_checkpoint}"
            )
    report_path = output_dir / "training-report.json"
    metrics_path = output_dir / "metrics.jsonl"
    checkpoints = output_dir / "checkpoints"
    if rank == 0:
        if output_dir.exists():
            raise FileExistsError(f"effect BC output already exists: {output_dir}")
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
    model, measured_contract, source_actor = initialize_effect_model(
        initial_actor,
        backend,
        environment,
        raw_settings.unit_limit,
        raw_settings.model,
        device,
        random_actor=False,
    )
    if measured_contract != contract:
        raise RuntimeError("effect BC initialization observed an unstable native ABI")
    initialization: dict[str, object] = {
        "mode": "pretrained_actor_random_effect_head",
        "seed": raw_settings.optimization.seed,
        "source_actor": source_actor,
    }
    if initial_checkpoint is not None:
        checkpoint_model, checkpoint_metadata = load_checkpoint(
            initial_checkpoint,
            contract,
            device,
        )
        checkpoint_source_actor = checkpoint_metadata.get("source_actor")
        if (
            checkpoint_model.actor.architecture != model.actor.architecture
            or checkpoint_model.effects.architecture != model.effects.architecture
            or not isinstance(checkpoint_source_actor, Mapping)
            or any(
                checkpoint_source_actor.get(name) != source_actor.get(name)
                for name in ("sha256", "actor_encoder_version", "action_keys")
            )
        ):
            raise ValueError("effect BC initial checkpoint differs from its profile")
        model = checkpoint_model
        configure_effect_trainable(
            model,
            train_turn_encoder=raw_settings.model.train_turn_encoder,
        )
        initialization = {
            "mode": "frozen_checkpoint_finetune",
            "optimizer": "reset",
            "checkpoint": checkpoint_metadata["checkpoint_identity"],
            "checkpoint_training_source": checkpoint_metadata.get("source_revision"),
            "source_actor": source_actor,
        }
    manifest = load_effect_teacher_manifest(dataset_dir)
    _validate_dataset(
        manifest,
        raw_settings,
        backend,
        environment,
        contract,
        source_actor,
        model,
        require_clean=not smoke,
    )
    partitions = (
        {
            name: manifest.shards[:world_size]
            for name in ("train", "validation", "test")
        }
        if smoke
        else _partitions(
            manifest,
            raw_settings.validation_games,
            raw_settings.test_games,
        )
    )
    for name, shards in partitions.items():
        if len(shards) % raw_settings.optimization.games_per_batch:
            raise ValueError(f"effect BC {name} games do not fill the global batch")

    trainable = _trainable_parameters(model)
    optimizer = torch.optim.AdamW(
        trainable,
        lr=raw_settings.optimization.learning_rate,
        weight_decay=raw_settings.optimization.weight_decay,
        fused=device.type == "cuda",
    )
    dataset_identity: dict[str, object] = {
        "path": str(raw_settings.dataset_dir / "manifest.json"),
        "sha256": sha256_file(dataset_dir / "manifest.json"),
        "dataset_id": manifest.dataset_id,
        "teacher": manifest.teacher,
    }
    resolved: dict[str, object] = {
        "effect_bc": raw_settings.model_dump(mode="json"),
        "environment": environment,
        "dataset": dataset_identity,
        "initialization": initialization,
        "distributed": {
            "world_size": world_size,
            "backend": "nccl" if distributed else None,
        },
        "partitions": {
            name: {
                "games": len(shards),
                "physical_games": sum(
                    shard.physical_games or shard.games for shard in shards
                ),
                "minimum_seed": min(shard.seed_start for shard in shards),
                "maximum_seed": max(shard.seed_start for shard in shards),
                "source_groups": sorted(
                    {
                        shard.source_group or "rank8_demonstration"
                        for shard in shards
                    }
                ),
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
        training = run_effect_bc_partition(
            model,
            dataset_dir,
            partitions["train"],
            "train",
            raw_settings,
            device,
            optimizer,
            epoch,
            rank=rank,
            world_size=world_size,
        )
        validation = run_effect_bc_partition(
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
        objective = _number(validation, "official_turn_nll")
        selected = objective < best_objective
        if selected:
            best_epoch = epoch
            best_objective = objective
        peak = torch.tensor(
            [
                torch.cuda.max_memory_allocated(device)
                if device.type == "cuda"
                else 0,
                torch.cuda.max_memory_reserved(device)
                if device.type == "cuda"
                else 0,
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
                dataset=dataset_identity,
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
        raise RuntimeError("effect BC produced no selected checkpoint")
    del optimizer, model
    if device.type == "cuda":
        torch.cuda.empty_cache()
    if distributed:
        dist.barrier()
    best_model, best_metadata = load_checkpoint(
        checkpoints / "best.pt",
        contract,
        device,
    )
    configure_effect_trainable(
        best_model,
        train_turn_encoder=raw_settings.model.train_turn_encoder,
    )
    test = run_effect_bc_partition(
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
        "schema_version": "atomic-effect-bc-training-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "training_complete",
        "purpose": "behavior warm start; no policy promotion authority",
        "objective": {
            "policy": "teacher-choice NLL balanced by official turn and episode",
            "critic": "direct terminal W/D/L cross-entropy",
            "checkpoint_selection": "minimum held-out teacher-choice NLL",
        },
        "source": source,
        "dataset": dataset_identity,
        "initialization": cast(Mapping[str, object], resolved["initialization"]),
        "execution": {
            "device": str(device),
            "gpu": (
                torch.cuda.get_device_name(device)
                if device.type == "cuda"
                else None
            ),
            "world_size": world_size,
            "parameter_count": parameter_count(best_model),
            "trainable_parameter_count": sum(
                parameter.numel()
                for parameter in best_model.parameters()
                if parameter.requires_grad
            ),
        },
        "epochs": history,
        "best": {
            "epoch": best_epoch,
            "validation_official_turn_nll": best_objective,
            "checkpoint": best_metadata["checkpoint_identity"],
        },
        "test": test,
        "metrics": {
            "path": str(metrics_path),
            "sha256": sha256_file(metrics_path),
        },
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


__all__ = ["train_effect_bc"]
