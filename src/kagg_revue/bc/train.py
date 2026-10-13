"""Sequential behavior-cloning warm start for the recurrent actor."""

from __future__ import annotations

import json
import math
import queue
import random
import threading
import time
from collections.abc import Iterator
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor
from torch.nn import functional

from kagg_revue.bc.checkpoint import (
    restore_training_checkpoint,
    save_training_checkpoint,
)
from kagg_revue.bc.config import ExperimentSettings, ModelSettings
from kagg_revue.bc.dataset import (
    Partition,
    SequenceBatch,
    SequenceDataset,
    sha256_file,
)
from kagg_revue.core.observability import (
    ScalarLogger,
    observability_report,
    synchronize,
    throughput,
)
from kagg_revue.policy.economics import (
    CANDIDATE_FEATURES,
    PREFIX_FEATURES,
    QUANTITY_FEATURES,
    TURN_FEATURES,
)
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet, parameter_count
from kagg_revue.policy.quantity import quantity_log_probability, quantity_mode
from kagg_revue.policy.runtime import load_actor
from kagg_revue.policy.state import load_causal_actor_state
from kagg_revue.rl.pfsp import actor_fingerprint

SUBMISSION_LIMIT_BYTES = 100_000_000


@dataclass
class _Totals:
    action_loss_sum: float = 0.0
    quantity_loss_sum: float = 0.0
    decisions: int = 0
    quantities: int = 0
    quantity_correct: int = 0
    correct: int = 0
    unit_decisions: int = 0
    unit_correct: int = 0
    market_decisions: int = 0
    market_correct: int = 0
    optimized_turns: int = 0
    batches: int = 0

    def summary(self, settings: ExperimentSettings) -> dict[str, float]:
        """Return behavior diagnostics without promotion authority."""
        action_nll = self.action_loss_sum / max(1, self.decisions)
        quantity_nll = self.quantity_loss_sum / max(1, self.quantities)
        behavior_nll = action_nll + settings.quantity_loss_weight * quantity_nll
        return {
            "objective_nll": behavior_nll,
            "total_loss": behavior_nll,
            "action_nll": action_nll,
            "quantity_nll": quantity_nll,
            "action_accuracy": self.correct / max(1, self.decisions),
            "quantity_accuracy": self.quantity_correct / max(1, self.quantities),
            "unit_accuracy": self.unit_correct / max(1, self.unit_decisions),
            "market_accuracy": self.market_correct / max(1, self.market_decisions),
            "decisions": float(self.decisions),
            "quantity_decisions": float(self.quantities),
            "optimized_turns": float(self.optimized_turns),
            "batches": float(self.batches),
        }


@dataclass(frozen=True)
class _PrefetchError:
    error: BaseException


def _prefetched(
    source: Iterator[SequenceBatch],
    depth: int,
) -> Iterator[SequenceBatch]:
    """Overlap bounded CPU shard decoding/collation with GPU optimization."""
    if depth <= 0:
        yield from source
        return
    buffer: queue.Queue[SequenceBatch | _PrefetchError | None] = queue.Queue(maxsize=depth)
    stopped = threading.Event()

    def enqueue(value: SequenceBatch | _PrefetchError | None) -> bool:
        while not stopped.is_set():
            try:
                buffer.put(value, timeout=0.1)
                return True
            except queue.Full:
                continue
        return False

    def produce() -> None:
        try:
            for batch in source:
                if not enqueue(batch):
                    return
        except BaseException as error:
            enqueue(_PrefetchError(error))
        finally:
            enqueue(None)

    producer = threading.Thread(target=produce, name="bc-batch-prefetch", daemon=True)
    producer.start()
    try:
        while True:
            item = buffer.get()
            if item is None:
                return
            if isinstance(item, _PrefetchError):
                raise item.error
            yield item
    finally:
        stopped.set()
        producer.join()


def build_architecture(dataset: SequenceDataset, settings: ModelSettings) -> ActorArchitecture:
    """Bind configured model dimensions to authenticated tensor/vocabulary shapes."""
    manifest = dataset.manifest
    return ActorArchitecture(
        board_shape=manifest.board_shape,
        unit_shape=manifest.unit_shape,
        global_features=manifest.global_features,
        model_width=settings.model_width,
        entity_width=settings.entity_width,
        attention_heads=settings.attention_heads,
        feedforward_width=settings.feedforward_width,
        latent_tokens=settings.latent_tokens,
        register_tokens=settings.register_tokens,
        scene_layers=settings.scene_layers,
        temporal_layers=settings.temporal_layers,
        action_layers=settings.action_layers,
        max_history=settings.max_history,
        max_decisions=settings.max_decisions,
        unit_action_tokens=len(manifest.unit_candidate_keys),
        market_action_tokens=len(manifest.market_candidate_keys),
        maximum_quantity=settings.maximum_quantity,
        derived_fact_version=manifest.derived_fact_version,
        turn_fact_features=manifest.turn_fact_features,
        prefix_fact_features=manifest.prefix_fact_features,
        candidate_fact_features=manifest.candidate_fact_features,
        fact_dropout=settings.fact_dropout,
        skill_tokens=settings.skill_tokens,
        strategy_tokens=settings.strategy_tokens,
        strategy_version=settings.strategy_version,
        economic_feature_version=settings.economic_feature_version,
        economic_turn_features=(TURN_FEATURES if settings.economic_feature_version else 0),
        economic_prefix_features=(PREFIX_FEATURES if settings.economic_feature_version else 0),
        economic_candidate_features=(
            CANDIDATE_FEATURES if settings.economic_feature_version else 0
        ),
        economic_quantity_features=(
            QUANTITY_FEATURES if settings.economic_feature_version else 0
        ),
    )


def _autocast(device: torch.device) -> Any:
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.bfloat16)
    return nullcontext()


def _tensor(value: np.ndarray[Any, Any], device: torch.device) -> Tensor:
    return torch.as_tensor(value, device=device)


def _batch_tensors(batch: SequenceBatch, device: torch.device) -> tuple[Tensor, ...]:
    return (
        _tensor(batch.board, device),
        _tensor(batch.units, device),
        _tensor(batch.global_features, device),
        _tensor(batch.economic_state, device),
        _tensor(batch.turn_facts, device),
        _tensor(batch.turn_fact_mask, device).bool(),
        _tensor(batch.prefix_facts, device),
        _tensor(batch.candidate_facts, device),
        _tensor(batch.actions, device).long(),
        _tensor(batch.quantities, device),
        _tensor(batch.phases, device).long(),
        _tensor(batch.turn_mask, device).bool(),
        _tensor(batch.loss_mask, device).bool(),
        _tensor(batch.decision_mask, device).bool(),
    )


def _phase_mask(logits: Tensor, phases: Tensor, unit_tokens: int) -> Tensor:
    vocabulary = logits.shape[-1]
    indices = torch.arange(vocabulary, device=logits.device)
    unit_allowed = indices < unit_tokens
    allowed = torch.where(phases[..., None] == 0, unit_allowed, ~unit_allowed)
    return logits.float().masked_fill(~allowed, -torch.inf)


def _step(
    model: TurnPolicyNet,
    batch: SequenceBatch,
    settings: ExperimentSettings,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
) -> _Totals:
    (
        board,
        units,
        globals_,
        economic_state,
        turn_facts,
        turn_fact_mask,
        prefix_facts,
        candidate_facts,
        actions,
        quantities,
        phases,
        turn_mask,
        loss_mask,
        decision_mask,
    ) = _batch_tensors(batch, device)
    optimized = decision_mask & loss_mask[..., None]
    if optimizer is not None:
        optimizer.zero_grad(set_to_none=True)
    with _autocast(device):
        encoding = model.encode_sequence(
            board,
            units,
            globals_,
            actions,
            quantities,
            turn_mask,
            decision_mask,
            turn_facts if model.architecture.turn_fact_features else None,
            turn_fact_mask if model.architecture.turn_fact_features else None,
            economic_state if model.architecture.economic_feature_version else None,
        )
        skills = model.select_sequence_skills(
            encoding,
            turn_mask,
            sample=model.training,
        )
        output = model.decode_sequence(
            encoding,
            actions,
            quantities,
            phases,
            decision_mask,
            prefix_facts if model.architecture.prefix_fact_features else None,
            candidate_facts if model.architecture.candidate_fact_features else None,
            skills,
            economic_state=(
                economic_state if model.architecture.economic_feature_version else None
            ),
        )
        logits = _phase_mask(output.action_logits, phases, model.architecture.unit_action_tokens)
        action_losses = functional.cross_entropy(
            logits.flatten(0, -2),
            actions.clamp(min=0).flatten(),
            reduction="none",
        ).view_as(actions)
        action_loss = (action_losses * optimized).sum() / optimized.sum().clamp_min(1)
        quantity_mask = optimized & (quantities > 0)
        quantity_losses = -quantity_log_probability(
            output.quantity_logits,
            quantities,
        )
        if torch.any(quantity_mask & ~torch.isfinite(quantity_losses)):
            maximum = model.architecture.maximum_quantity
            raise ValueError(f"BC quantity target exceeds actor vocabulary 1..{maximum}")
        masked_quantity_losses = torch.where(
            quantity_mask,
            quantity_losses,
            torch.zeros_like(quantity_losses),
        )
        quantity_loss = masked_quantity_losses.sum() / quantity_mask.sum().clamp_min(1)
        loss = action_loss + settings.quantity_loss_weight * quantity_loss
    if optimizer is not None:
        loss.backward()  # type: ignore[no-untyped-call]
        torch.nn.utils.clip_grad_norm_(model.parameters(), settings.gradient_clip)
        optimizer.step()
    predicted = logits.argmax(dim=-1)
    predicted_quantities = quantity_mode(output.quantity_logits)
    correct = (predicted == actions) & optimized
    quantity_correct = (predicted_quantities == quantities) & quantity_mask
    unit = optimized & (phases == 0)
    market = optimized & (phases == 1)
    return _Totals(
        action_loss_sum=float((action_losses * optimized).sum().detach().item()),
        quantity_loss_sum=float(masked_quantity_losses.sum().detach().item()),
        decisions=int(optimized.sum().item()),
        quantities=int(quantity_mask.sum().item()),
        quantity_correct=int(quantity_correct.sum().item()),
        correct=int(correct.sum().item()),
        unit_decisions=int(unit.sum().item()),
        unit_correct=int((correct & unit).sum().item()),
        market_decisions=int(market.sum().item()),
        market_correct=int((correct & market).sum().item()),
        optimized_turns=int((turn_mask & loss_mask).sum().item()),
        batches=1,
    )


def _merge(total: _Totals, update: _Totals) -> None:
    total.action_loss_sum += update.action_loss_sum
    total.quantity_loss_sum += update.quantity_loss_sum
    total.decisions += update.decisions
    total.quantities += update.quantities
    total.quantity_correct += update.quantity_correct
    total.correct += update.correct
    total.unit_decisions += update.unit_decisions
    total.unit_correct += update.unit_correct
    total.market_decisions += update.market_decisions
    total.market_correct += update.market_correct
    total.optimized_turns += update.optimized_turns
    total.batches += update.batches


def _run_partition(
    model: TurnPolicyNet,
    dataset: SequenceDataset,
    settings: ExperimentSettings,
    partition: Partition,
    device: torch.device,
    epoch: int,
    optimizer: torch.optim.Optimizer | None,
) -> dict[str, float]:
    model.train(optimizer is not None)
    total = _Totals()
    context = nullcontext() if optimizer is not None else torch.inference_mode()
    synchronize(device)
    started = time.perf_counter()
    batches = dataset.iter_batches(
        partition,
        settings.batch_sequences,
        settings.unroll_length,
        settings.burn_in,
        model.architecture.max_decisions,
        settings.seed,
        epoch,
        loader_workers=settings.loader_workers,
        shuffle=optimizer is not None,
    )
    with context:
        for batch in _prefetched(batches, settings.prefetch_batches):
            _merge(total, _step(model, batch, settings, device, optimizer))
    synchronize(device)
    elapsed = time.perf_counter() - started
    summary = total.summary(settings)
    summary.update(
        {
            "elapsed_seconds": elapsed,
            "turns_per_second": throughput(total.optimized_turns, elapsed),
            "decisions_per_second": throughput(total.decisions, elapsed),
        }
    )
    return summary


def export_actor(path: Path, model: TurnPolicyNet, dataset: SequenceDataset) -> dict[str, object]:
    """Write an inference-only FP16 artifact and report its actual byte size."""
    state: dict[str, Tensor] = {}
    for key, value in model.state_dict().items():
        tensor = value.detach().cpu()
        state[key] = tensor.half() if tensor.is_floating_point() else tensor
    payload = {
        "artifact_version": (
            "turn-policy-actor-v6"
            if model.architecture.economic_feature_version is not None
            else "turn-policy-actor-v4"
        ),
        "architecture": model.architecture_json(),
        "actor_encoder_version": dataset.manifest.actor_encoder_version,
        "derived_fact_version": dataset.manifest.derived_fact_version,
        "economic_feature_version": model.architecture.economic_feature_version,
        "action_codec_version": dataset.manifest.action_codec_version,
        "action_keys": [
            *dataset.manifest.unit_candidate_keys,
            *dataset.manifest.market_candidate_keys,
        ],
        "model_state": state,
    }
    temporary = path.with_suffix(".pt.tmp")
    torch.save(payload, temporary)
    temporary.replace(path)
    size = path.stat().st_size
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": size,
        "submission_limit_bytes": SUBMISSION_LIMIT_BYTES,
        "weight_artifact_within_limit": size < SUBMISSION_LIMIT_BYTES,
        "dtype": "float16",
    }


def train_policy(
    model_settings: ModelSettings,
    settings: ExperimentSettings,
    dataset: SequenceDataset,
    output_dir: Path,
    source: dict[str, object],
) -> dict[str, object]:
    """Train one joint actor and export its best behavior checkpoint."""
    device = torch.device(settings.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA training was requested but no GPU is available")
    random.seed(settings.seed)
    np.random.seed(settings.seed)
    torch.manual_seed(settings.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(settings.seed)
    torch.set_float32_matmul_precision("high")
    architecture = build_architecture(dataset, model_settings)
    initialization: dict[str, object]
    if settings.initial_actor is None:
        model = TurnPolicyNet(architecture).to(device)
        initialization = {"kind": "random"}
    else:
        model, keys, encoder_version, fact_version = load_actor(settings.initial_actor, device)
        expected_keys = (
            *dataset.manifest.unit_candidate_keys,
            *dataset.manifest.market_candidate_keys,
        )
        if model.architecture != architecture:
            raise ValueError("initial actor architecture differs from the BC profile and dataset")
        if keys != expected_keys:
            raise ValueError("initial actor vocabulary differs from the BC dataset")
        if encoder_version != dataset.manifest.actor_encoder_version:
            raise ValueError("initial actor encoder differs from the BC dataset")
        if fact_version != dataset.manifest.derived_fact_version:
            raise ValueError("initial actor derived facts differ from the BC dataset")
        initialization = {
            "kind": "actor_artifact",
            "path": str(settings.initial_actor),
            "sha256": sha256_file(settings.initial_actor),
            "actor_state_sha256": actor_fingerprint(model),
            "optimizer_imported": False,
        }
    if architecture.strategy_tokens:
        longest_sequence = max(
            ref.stop - ref.start
            for refs in dataset.refs.values()
            for ref in refs
        )
        if longest_sequence > settings.unroll_length:
            raise ValueError(
                "persistent-strategy BC unroll must cover every episode-start sequence"
            )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.learning_rate,
        weight_decay=settings.weight_decay,
        fused=device.type == "cuda",
    )
    checkpoint_path = output_dir / "checkpoint.pt"
    metrics_path = output_dir / "metrics.jsonl"
    best_objective = math.inf
    best_epoch = 0
    initial_epoch = 0
    resume: dict[str, object] | None = None
    if settings.resume_checkpoint is not None:
        resume_state = restore_training_checkpoint(
            settings.resume_checkpoint,
            checkpoint_path,
            model,
            dataset,
            optimizer,
            device,
        )
        initial_epoch = resume_state.epoch
        best_objective = resume_state.objective
        resume = resume_state.report
        best_epoch = initial_epoch
    if settings.epochs <= initial_epoch:
        raise ValueError("target epochs must exceed the resume checkpoint epoch")
    epochs: list[dict[str, object]] = []
    logger = ScalarLogger(
        output_dir,
        settings.observability,
        run_metadata={
            "kind": "behavior_warm_start",
            "dataset_id": dataset.manifest.dataset_id,
            "device": str(device),
            "architecture": architecture.model_dump(mode="json"),
        },
    )
    try:
        for epoch in range(initial_epoch + 1, settings.epochs + 1):
            if device.type == "cuda":
                torch.cuda.reset_peak_memory_stats(device)
            epoch_started = time.perf_counter()
            training = _run_partition(model, dataset, settings, "train", device, epoch, optimizer)
            validation = _run_partition(model, dataset, settings, "validation", device, epoch, None)
            system = {
                "elapsed_seconds": time.perf_counter() - epoch_started,
                "cuda_peak_allocated_bytes": (
                    torch.cuda.max_memory_allocated(device) if device.type == "cuda" else 0
                ),
                "cuda_peak_reserved_bytes": (
                    torch.cuda.max_memory_reserved(device) if device.type == "cuda" else 0
                ),
            }
            row: dict[str, object] = {
                "epoch": epoch,
                "training": training,
                "validation": validation,
                "system": system,
            }
            epochs.append(row)
            with metrics_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, sort_keys=True) + "\n")
            logger.scalars("bc/training", training, epoch)
            logger.scalars("bc/validation", validation, epoch)
            logger.scalars("bc/system", system, epoch)
            print(json.dumps(row, sort_keys=True), flush=True)
            deployment_objective = validation["objective_nll"]
            selected_epoch = (
                settings.checkpoint_selection == "final_epoch"
                or deployment_objective < best_objective
            )
            if selected_epoch:
                best_objective = deployment_objective
                best_epoch = epoch
                save_training_checkpoint(
                    checkpoint_path,
                    model,
                    dataset,
                    optimizer,
                    epoch,
                    validation,
                )
        saved = torch.load(checkpoint_path, map_location=device, weights_only=True)
        saved_state = saved.get("model_state")
        if not isinstance(saved_state, dict):
            raise ValueError("best BC checkpoint lacks model state")
        load_causal_actor_state(model, saved_state)
        test = _run_partition(model, dataset, settings, "test", device, best_epoch, None)
        logger.scalars("bc/test", test, best_epoch)
    finally:
        logger.close()
    actor_artifact = export_actor(output_dir / "actor-fp16.pt", model, dataset)
    report: dict[str, object] = {
        "schema_version": "turn-policy-training-v6",
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "behavior warm start; no promotion authority",
        "source": source,
        "execution": {
            "device": str(device),
            "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        },
        "observability": observability_report(logger),
        "architecture": architecture.model_dump(mode="json"),
        "parameter_count": parameter_count(model),
        "initialization": initialization,
        "dataset": {
            "path": str(dataset.root),
            "manifest_sha256": dataset.manifest_sha256,
            "dataset_id": dataset.manifest.dataset_id,
            "split": dataset.split_summary(),
        },
        "best_epoch": best_epoch,
        "training_span": {
            "initial_epoch": initial_epoch,
            "target_epoch": settings.epochs,
        },
        "resume": resume,
        "checkpoint_selection": settings.checkpoint_selection,
        "epochs": epochs,
        "test": test,
        "checkpoint": {
            "path": str(checkpoint_path),
            "sha256": sha256_file(checkpoint_path),
        },
        "actor_artifact": actor_artifact,
    }
    (output_dir / "training-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


__all__ = ["build_architecture", "export_actor", "train_policy"]
