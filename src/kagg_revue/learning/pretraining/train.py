"""A fixed multi-date initialization budget before independent online RL."""

import json
import time
from collections.abc import Callable
from typing import Any

import numpy as np
import torch

from kagg_revue.artifacts.io import write_json
from kagg_revue.datasets.demonstrations.loading import Dataset
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import any_stop, rank_world, restore_rng
from kagg_revue.learning.pretraining import telemetry
from kagg_revue.learning.pretraining.artifacts import checkpoint
from kagg_revue.learning.pretraining.optimization import Optimizer
from kagg_revue.learning.pretraining.stopping import observe
from kagg_revue.learning.progress import publish
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.state import load_member


def initialize(
    config: Experiment,
    settings: RuntimeSettings,
    state: dict[str, Any],
    stopped: Callable[[], bool],
    *,
    dataset_class: type[Dataset] = Dataset,
) -> None:
    """Resume own-run BC, then select its final or validation-best RL baseline."""
    source = config.demonstrations
    if source is None or "rl_initial" in state:
        return
    if state["completed_update"]:
        raise ValueError("cannot initialize demonstrations after online RL has started")
    rank, world = rank_world()
    device = torch.device(settings.devices[rank])
    if source.batch_rows % world:
        raise ValueError("BC global batches must divide across devices")
    torch.manual_seed(config.seed)
    actor, payload = load_member(config, state, state["latest"], device)
    complete_trajectories = (
        json.loads(source.manifest.read_text()).get("sequence_format") == "complete-turn-seat-v1"
    )
    if config.memory_turns or complete_trajectories:
        from kagg_revue.datasets.sequences.loading import SequenceDataset

        dataset_class = SequenceDataset
    dataset = dataset_class(
        source.manifest,
        source.sha256,
        actor.layout,
        config.environment,
        (
            (config.train_seed, config.train_seed + config.updates * config.games),
            (
                config.evaluation.selection_seed,
                config.evaluation.selection_seed + config.evaluation.games // 2,
            ),
            (
                config.evaluation.confirmation_seed,
                config.evaluation.confirmation_seed + config.evaluation.games // 2,
            ),
            (
                source.behavior_seed,
                source.behavior_seed + max(source.behavior_games, source.control_games // 2),
            ),
        ),
    )
    if config.memory_turns or complete_trajectories:
        assert isinstance(dataset, SequenceDataset)
        dataset.configure(source.batch_rows, world, config.seed)
    if rank == 0:
        write_json(
            config.output_dir / "demonstration-qualification.json",
            {
                "manifest": str(source.manifest),
                "sha256": source.sha256,
                "all_array_hashes_verified": True,
                "coverage": dataset.manifest["coverage"],
                "teacher_selection": dataset.manifest.get("teacher_selection"),
                "selected_teacher_trajectories": dataset.manifest.get(
                    "selected_teacher_trajectories"
                ),
            },
        )
    optimizer: Optimizer
    if config.memory_turns:
        from kagg_revue.learning.sequences.pretraining import SequenceOptimizer

        optimizer = SequenceOptimizer(
            actor,
            settings,
            source.learning_rate,
            loss=source.loss,
            joint_learning_rate=source.joint_learning_rate,
        )
    elif complete_trajectories:
        from kagg_revue.learning.pretraining.flat import FlatSequenceOptimizer

        optimizer = FlatSequenceOptimizer(actor, settings, source.learning_rate, loss=source.loss)
    else:
        optimizer = Optimizer(actor, settings, source.learning_rate, loss=source.loss)
    progress = state.get(
        "pretraining",
        {
            "cursor": 0,
            "optimizer_steps": 0,
            "rows": 0,
            "epoch_rows": 0,
            "epoch_loss_sum": 0.0,
            "records": [],
            "dataset_sha256": source.sha256,
        },
    ).copy()
    loss_identity = {} if source.loss is None else {"loss": source.loss.model_dump(mode="json")}
    if progress["cursor"]:
        if progress.get("loss") != loss_identity.get("loss"):
            raise ValueError("BC loss changed across recovery; create a separate run")
        if payload.get("pretraining") != progress or progress["dataset_sha256"] != source.sha256:
            raise ValueError("demonstration cursor and checkpoint identity disagree")
        optimizer.optimizer.load_state_dict(payload["optimizer"])
        if device.type == "cuda":
            restore_rng(payload, device, config)
        else:
            torch.set_rng_state(payload["rng"]["cpu"].cpu())
    progress.update(loss_identity)
    del payload
    training = dataset.partition("train")
    shards = len(training)
    started = time.perf_counter()
    while progress["cursor"] < source.epochs * shards:
        if any_stop(stopped(), device):
            break
        epoch, offset = divmod(progress["cursor"], shards)
        ordering = np.random.default_rng([config.seed, epoch, 70]).permutation(training)
        index = int(ordering[offset])
        rates = source.rates(progress["cursor"], source.epochs * shards)
        for group, rate in zip(optimizer.optimizer.param_groups, rates, strict=False):
            group["lr"] = rate
        result = optimizer.shard(dataset, index, source.batch_rows, (config.seed, epoch, index))
        progress["cursor"] += 1
        progress["optimizer_steps"] += result["optimizer_steps"]
        progress["rows"] += result["rows"]
        progress["epoch_rows"] += result["rows"]
        progress["epoch_loss_sum"] += result["loss_sum"]
        telemetry.accumulate(progress, result)
        boundary = progress["cursor"] % shards == 0
        early_stop = False
        if boundary:
            validation_started = time.perf_counter()
            heldout = [
                optimizer.shard(dataset, i, source.batch_rows, None)
                for i in dataset.partition("selection")
            ]
            validation_rows = sum(row["rows"] for row in heldout)
            record = {
                "epoch": epoch + 1,
                "train_nll": telemetry.mean_nll(
                    progress["epoch_loss_sum"],
                    progress["epoch_rows"],
                    progress.get("epoch_field_totals", [0.0] * 15),
                    source.loss,
                ),
                "selection_nll": telemetry.partition_nll(heldout, source.loss),
                "selection_rows": validation_rows,
                "train_rows": progress["epoch_rows"],
                "optimizer_steps": progress["optimizer_steps"],
                **loss_identity,
            }
            diagnostics = telemetry.epoch_metrics(
                progress, heldout, time.perf_counter() - validation_started
            )
            if complete_trajectories:
                record.update(diagnostics)
            progress["records"].append(record)
            progress.update(
                epoch_rows=0, epoch_loss_sum=0.0, epoch_field_totals=[0.0] * 15, epoch_seconds=0.0
            )
            if source.early_stopping is not None:
                early_stop = observe(progress, source.early_stopping)
            if rank == 0:
                telemetry.publish_epoch(
                    config.output_dir / "pretraining",
                    {**record, **diagnostics},
                    time.perf_counter() - started,
                )
                print(json.dumps({"phase": "demonstration_epoch", **record}), flush=True)
        halt = any_stop(stopped(), device)
        complete = early_stop or progress["cursor"] == source.epochs * shards
        if complete and config.pretraining_only and source.early_stopping is None:
            confirmation = [
                optimizer.shard(dataset, i, source.batch_rows, None)
                for i in dataset.partition("confirmation")
            ]
            count = sum(item["rows"] for item in confirmation)
            if count:
                progress["confirmation"] = {
                    "rows": count,
                    "nll": telemetry.partition_nll(confirmation, source.loss),
                    "fields": telemetry.epoch_metrics({}, confirmation, 0.0)["validation"],
                    "epoch": epoch + 1,
                    "scope": "Full confirmation split, evaluated only after the fixed BC budget.",
                    **loss_identity,
                }
                if rank == 0:
                    write_json(
                        config.output_dir / "pretraining" / "confirmation.json",
                        progress["confirmation"],
                    )
        if complete and source.early_stopping is not None:
            progress["completion_reason"] = "patience" if early_stop else "epoch_limit"
        if boundary or halt or progress["cursor"] % source.checkpoint_shards == 0:
            checkpoint(
                config,
                settings,
                state,
                optimizer,
                progress,
                complete=complete,
            )
        if rank != 0:
            if halt or complete:
                break
            continue
        telemetry.append(
            config.output_dir / "pretraining",
            "batches.jsonl",
            {
                "batch": progress["cursor"],
                "epoch": epoch + 1,
                "nll": result["loss_sum"] / result["rows"],
                "rows": result["rows"],
                "optimizer_steps": progress["optimizer_steps"],
                "gradient_norm": result.get("gradient_norm"),
                "learning_rates": [group["lr"] for group in optimizer.optimizer.param_groups],
                "fields": telemetry.domain_metrics(result.get("field_totals", [0.0] * 15)),
                "performance": result.get("performance", {}),
                **loss_identity,
            },
        )
        if boundary and source.behavior_games and not halt:
            from kagg_revue.learning.behavior import Audit, measure

            with torch.random.fork_rng(devices=[device]):
                behavior = measure(
                    config,
                    state,
                    f"pretraining/shard-{progress['cursor']:06d}.pt",
                    Audit(
                        runs=(config.output_dir,),
                        output_dir=config.output_dir / "pretraining",
                        games=source.behavior_games,
                        seed=source.behavior_seed,
                        device=str(device),
                    ),
                )
            write_json(
                config.output_dir / "pretraining" / f"epoch-{epoch + 1}-behavior.json", behavior
            )
        if boundary and source.control_games and not halt:
            from kagg_revue.learning.pretraining.evaluation import controls

            with torch.random.fork_rng(devices=[device]):
                controls(config, settings, state, optimizer.actor, epoch + 1)
        publish(
            config,
            state,
            "demonstrations",
            cursor=progress["cursor"],
            total_shards=source.epochs * shards,
            epoch=epoch + 1,
            epochs=source.epochs,
            rows=progress["rows"],
            optimizer_steps=progress["optimizer_steps"],
            shard_nll=result["loss_sum"] / result["rows"],
            selection_nll=progress["records"][-1]["selection_nll"] if progress["records"] else None,
            elapsed_seconds=time.perf_counter() - started,
            epoch_rows=progress["epoch_rows"],
            epoch_nll=telemetry.mean_nll(
                progress["epoch_loss_sum"],
                progress["epoch_rows"],
                progress.get("epoch_field_totals", [0.0] * 15),
                source.loss,
            )
            if progress["epoch_rows"]
            else None,
            batches_per_epoch=shards,
            learning_rate=source.learning_rate,
            bc_batch_rows=source.batch_rows,
            performance=result.get("performance", {}),
            fields=telemetry.domain_metrics(result.get("field_totals", [0.0] * 15)),
            early_stopping=progress.get("early_stopping"),
            completion_reason=progress.get("completion_reason"),
            **loss_identity,
        )
        print(
            json.dumps(
                {
                    "phase": "demonstrations",
                    "cursor": progress["cursor"],
                    "total_shards": source.epochs * shards,
                    "rows": progress["rows"],
                    "optimizer_steps": progress["optimizer_steps"],
                    "shard_nll": result["loss_sum"] / result["rows"],
                    "elapsed_seconds": time.perf_counter() - started,
                    **({"performance": result["performance"]} if "performance" in result else {}),
                }
            ),
            flush=True,
        )
        if halt or complete:
            break
