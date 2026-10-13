"""BC on operating decisions, selected by held-out complete-match behavior."""

import json
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import Policy, imitation_loss
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import Settings
from kagg_revue.production.data import load_shard
from kagg_revue.production.evaluation import panel
from kagg_revue.production.prepare import prepare


def _heldout(
    settings: Settings,
    policy: Policy,
    forward: Callable[[torch.Tensor, torch.Tensor, torch.Tensor], torch.Tensor],
    shards: list[dict[str, Any]],
    device: torch.device,
) -> dict[str, float | int]:
    """Measure row-weighted proposal likelihood on a complete held-out partition."""
    started = time.perf_counter()
    total, rows = 0.0, 0
    policy.eval()
    with (
        torch.no_grad(),
        torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"),
    ):
        for shard in shards:
            observations, actions, steps = load_shard(settings.bc.directory, shard, device)
            for start in range(0, len(steps), settings.bc.batch_rows):
                stop = min(start + settings.bc.batch_rows, len(steps))
                logits = forward(observations[start:stop], steps[start:stop], actions[start:stop])
                loss = imitation_loss(
                    logits,
                    actions[start:stop],
                    policy.field_weights(actions[start:stop], steps[start:stop]),
                )
                total += float(loss) * (stop - start)
                rows += stop - start
            del observations, actions, steps
    return {"nll": total / rows, "rows": rows, "seconds": time.perf_counter() - started}


def _initialize_prior(
    settings: Settings, policy: Policy, training: list[dict[str, Any]], device: torch.device
) -> None:
    """Initialize only explicitly enabled legacy empirical time tables."""
    counts = np.zeros(tuple(policy.prior.shape), dtype=np.float64)
    base = np.arange(policy.layout.decisions * policy.layout.factors).reshape(
        policy.layout.decisions, 1, policy.layout.factors
    )
    for shard in training:
        labels = np.load(settings.bc.directory / shard["actions"], mmap_mode="r")
        weights = None
        if policy.layout.work:
            labels_device = torch.as_tensor(np.asarray(labels, dtype=np.int64), device=device)
            steps = torch.arange(policy.layout.decisions, device=device).repeat_interleave(
                labels.shape[1]
            )
            weights = policy.field_weights(labels_device.flatten(0, 1), steps).cpu().numpy().ravel()
            del labels_device
        counts += np.bincount(
            (base * policy.layout.vocabulary_size + labels).ravel(),
            minlength=counts.size,
            weights=weights,
        ).reshape(counts.shape)
    counts += settings.bc.prior_pseudocount
    prior = np.log(counts / counts.sum(-1, keepdims=True)).astype(np.float32)
    if settings.bc.greedy_prior_bias:
        # Preserve the demonstrated greedy plan while starting exploration near
        # it. This is an explicit strategic initialization, not a rollout-only
        # temperature: the trainable logits and replay distribution stay shared.
        preferred = prior.argmax(-1, keepdims=True)
        np.put_along_axis(
            prior,
            preferred,
            np.take_along_axis(prior, preferred, -1) + settings.bc.greedy_prior_bias,
            axis=-1,
        )
    with torch.no_grad():
        policy.prior.copy_(torch.from_numpy(prior).to(device))


def _train(settings: Settings) -> Path:
    """Fit state-conditioned work proposals on disjoint BC shards."""
    torch.set_num_threads(settings.cpu_threads)
    torch.manual_seed(settings.seed)
    device = torch.device(settings.devices[0])
    if device.type == "cuda":
        torch.cuda.set_device(device)
    manifest = json.loads(prepare(settings).read_text())
    shards = manifest["shards"]
    if len(shards) < 2:
        raise ValueError("BC requires independent training and holdout game shards")
    training = [s for s in shards if s.get("partition", "train") == "train"]
    validation = [s for s in shards if s.get("partition") == "validation"]
    if not validation:
        training, validation = shards[:-1], shards[-1:]
    policy = Policy.from_layout(ContractLayout.resolve(settings)).to(device)
    if settings.model.time_prior:
        _initialize_prior(settings, policy, training, device)
    forward = (
        torch.compile(policy, fullgraph=True, dynamic=False)
        if settings.compile and policy.layout.work
        else policy
    )
    optimizer = torch.optim.AdamW(
        policy.parameters(),
        lr=settings.bc.learning_rate,
        weight_decay=0.0,
        fused=device.type == "cuda",
    )
    identity = provenance(settings)
    identity["demonstrations_sha256"] = digest(settings.bc.directory / "manifest.json")
    directory = settings.output_dir / "bc"
    write_json(settings.output_dir / "resolved-config.json", settings.model_dump(mode="json"))
    write_json(settings.output_dir / "run-status.json", {"status": "running", "pid": os.getpid()})
    write_json(directory / "source.json", identity)
    reports = []
    best = (float("-inf"), float("-inf"), float("-inf"))
    best_epoch = 0
    output = directory / "best.pt"
    started = time.perf_counter()
    for epoch in range(settings.bc.epochs + 1):
        epoch_started = time.perf_counter()
        losses = []
        io_seconds, learner_seconds, train_rows = 0.0, 0.0, 0
        first_step_seconds = None
        if epoch:
            policy.train()
            for completed, shard_index in enumerate(torch.randperm(len(training)).tolist(), 1):
                shard = training[shard_index]
                phase = time.perf_counter()
                observations, actions, steps = load_shard(settings.bc.directory, shard, device)
                if device.type == "cuda":
                    torch.cuda.synchronize(device)
                io_seconds += time.perf_counter() - phase
                permutation = torch.randperm(len(steps), device=device)
                for indices in torch.split(permutation, settings.bc.batch_rows):
                    phase = time.perf_counter()
                    optimizer.zero_grad(set_to_none=True)
                    with torch.autocast(
                        device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"
                    ):
                        logits = forward(observations[indices], steps[indices], actions[indices])
                        loss = imitation_loss(
                            logits,
                            actions[indices],
                            policy.field_weights(actions[indices], steps[indices]),
                        )
                    loss.backward()  # type: ignore[no-untyped-call]
                    torch.nn.utils.clip_grad_norm_(policy.parameters(), 1.0)
                    optimizer.step()
                    losses.append(float(loss.detach()))
                    duration = time.perf_counter() - phase
                    if first_step_seconds is None:
                        first_step_seconds = duration
                    learner_seconds += duration
                    train_rows += len(indices)
                del observations, actions, steps
                if completed % 5 == 0 or completed == len(training):
                    print(
                        json.dumps(
                            {
                                "phase": "bc",
                                "epoch": epoch,
                                "shards": completed,
                                "total": len(training),
                                "optimizer_steps": len(losses),
                                "train_nll": float(np.mean(losses)),
                                "elapsed_seconds": time.perf_counter() - epoch_started,
                            }
                        ),
                        flush=True,
                    )
        heldout = _heldout(settings, policy, forward, validation, device)
        validation_finished = time.perf_counter()
        result = panel(settings, policy, settings.evaluation_seed)
        reports.append(
            {
                "epoch": epoch,
                "train_nll": float(np.mean(losses)) if losses else None,
                "heldout_nll": heldout["nll"],
                "elapsed_seconds": time.perf_counter() - started,
                "epoch_seconds": time.perf_counter() - epoch_started,
                "training_and_validation_seconds": validation_finished - epoch_started,
                "optimizer_steps": len(losses),
                "data_io_seconds": io_seconds,
                "learner_seconds": learner_seconds,
                "first_optimizer_step_seconds": first_step_seconds,
                "validation_seconds": heldout["seconds"],
                "train_rows": train_rows,
                "training_rows_per_second": train_rows / (io_seconds + learner_seconds)
                if train_rows
                else None,
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(device)
                if device.type == "cuda"
                else None,
                "peak_reserved_bytes": torch.cuda.max_memory_reserved(device)
                if device.type == "cuda"
                else None,
                **result,
            }
        )
        print(
            json.dumps(
                {key: value for key, value in reports[-1].items() if key not in {"games", "timing"}}
            ),
            flush=True,
        )
        quality = (result["wins"], -result["losses"], result["mean_cash"])
        if quality > best:
            best = quality
            best_epoch = epoch
            save_policy(
                output,
                policy,
                settings,
                epoch=epoch,
                provenance=identity,
                optimizer=optimizer.state_dict(),
            )
        save_policy(
            directory / f"epoch-{epoch:03d}.pt",
            policy,
            settings,
            epoch=epoch,
            provenance=identity,
            optimizer=optimizer.state_dict(),
            cpu_rng=torch.get_rng_state(),
            cuda_rng=torch.cuda.get_rng_state(device) if device.type == "cuda" else None,
        )
        write_json(directory / "report.json", reports)
        if settings.mode == "bc":
            with (settings.output_dir / "metrics.jsonl").open("a") as stream:
                stream.write(
                    json.dumps(
                        {
                            "epoch": epoch,
                            "training": {"objective_nll": reports[-1]["train_nll"]},
                            "validation": {
                                "objective_nll": reports[-1]["heldout_nll"],
                                "mean_terminal_cash": result["mean_cash"],
                            },
                            "system": {"elapsed_seconds": time.perf_counter() - epoch_started},
                        }
                    )
                    + "\n"
                )
    save_policy(
        directory / "last.pt",
        policy,
        settings,
        epoch=settings.bc.epochs,
        provenance=identity,
        optimizer=optimizer.state_dict(),
    )
    test = [s for s in shards if s.get("partition") == "test"]
    if test:
        payload = torch.load(output, map_location=device, weights_only=False)
        policy.load_state_dict(payload["model"])
        del payload
        write_json(
            directory / "test.json",
            {
                "checkpoint": str(output),
                "sha256": digest(output),
                "epoch": best_epoch,
                "provenance": identity,
                **_heldout(settings, policy, forward, test, device),
            },
        )
    write_json(settings.output_dir / "run-status.json", {"status": "complete", "pid": os.getpid()})
    write_json(
        settings.output_dir / "training-report.json",
        {
            "schema_version": "spatial-contract-bc",
            "best_epoch": best_epoch,
            "training_span": {"target_epoch": settings.bc.epochs},
            "source_revision": identity["revision"],
            "checkpoint": str(output),
        },
    )
    return output


def train(settings: Settings) -> Path:
    """Publish failure status even when initialization or the first optimizer step fails."""
    try:
        manifest = json.loads(prepare(settings).read_text())
        widths = {settings.bc.batch_rows} | {
            remainder
            for shard in manifest["shards"]
            if (remainder := shard["rows"] % settings.bc.batch_rows)
        }
        # Teacher-forced forward has separate gradient and no-gradient variants.
        # Admit exactly the finite widths present in these compact shards.
        limit = max(int(torch.compiler.config.recompile_limit), 2 * len(widths))
        with torch.compiler.config.patch(recompile_limit=limit):  # type: ignore[attr-defined]
            return _train(settings)
    except BaseException:
        write_json(
            settings.output_dir / "run-status.json", {"status": "failed", "pid": os.getpid()}
        )
        raise
