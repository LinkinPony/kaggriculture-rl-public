"""Measure effect rollout and learner hot paths with a resolved training profile."""

from __future__ import annotations

import argparse
import gc
import json
import os
import random
import time
from pathlib import Path
from typing import Any, cast

import torch

from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.rl.effects.checkpoint import load_checkpoint, restore_rng
from kagg_revue.rl.effects.chunked import backward_sharded_ppo, evaluate_sharded_behavior
from kagg_revue.rl.effects.cli import load_settings, repository_root
from kagg_revue.rl.effects.fleet import EffectRolloutFleet
from kagg_revue.rl.effects.initialization import configure_effect_trainable
from kagg_revue.rl.effects.replay import _enable_trainable_recurrent_backends, _prefetched_subsets
from kagg_revue.rl.effects.runtime import native_contract
from kagg_revue.rl.rollout.population import weighted_rollout_jobs


def main() -> None:
    """Collect a production rank and profile one real learner microbatch."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch", type=Path)
    parser.add_argument("--audit-resume", action="store_true")
    arguments, overrides = parser.parse_known_args()
    root = repository_root()
    settings = load_settings(overrides)
    output = arguments.output
    output.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TORCHINDUCTOR_CACHE_DIR", str(root / "tmp" / "torchinductor"))
    device = torch.device(settings.device)
    torch.cuda.set_device(device)
    torch.set_num_threads(settings.cpu_threads)
    torch.manual_seed(settings.seed)
    backend = load_backend(root)
    contract = native_contract(backend, settings.environment)
    model, metadata = load_checkpoint(arguments.checkpoint, contract, device)
    configure_effect_trainable(model, train_turn_encoder=settings.model.train_turn_encoder)
    report: dict[str, object] = {
        "source": source_identity(root),
        "resolved_config": settings.model_dump(mode="json"),
        "checkpoint": str(arguments.checkpoint),
        "checkpoint_update": metadata["update"],
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
    }
    if arguments.batch is None:
        generators = tuple(
            torch.Generator(device=device).manual_seed(settings.seed + 1 + index)
            for index in range(settings.rollout.actor_streams_per_device)
        )
        update = int(cast(int, metadata["update"])) + 1 if arguments.audit_resume else 1
        if arguments.audit_resume:
            restore_rng(
                cast(dict[str, Any], metadata["rng_state"])["rank_states"][0],
                random.Random(settings.seed),
                generators,
                (device,) * len(generators),
            )
        seed_start = settings.rollout_seed_start + (update - 1) * settings.rollout.seeds_per_update
        seeds = tuple(
            range(
                seed_start,
                seed_start + settings.rollout.seeds_per_update,
            )
        )
        jobs = weighted_rollout_jobs(
            seeds,
            settings.population.weights,
            rank=0,
            world_size=len(settings.rollout.devices or (settings.device,)),
            sampling_seed=settings.seed + update * 1_000_003,
        )
        fleet = EffectRolloutFleet(
            backend,
            model,
            contract,
            settings.environment,
            unit_limit=settings.unit_limit,
            cpu_workers=settings.rollout.cpu_workers,
            device=device,
            action_generators=generators,
            maximum_graph_variants=settings.rollout.maximum_graph_variants,
        )
        rollout_reports = []
        model.eval()
        try:
            for iteration in range(2):
                torch.cuda.reset_peak_memory_stats(device)
                with torch.inference_mode():
                    result = fleet.collect_jobs(jobs)
                rollout_reports.append(result.diagnostics)
                print(json.dumps({"rollout": iteration, **result.diagnostics}), flush=True)
                if arguments.audit_resume:
                    audited = tuple(index * result.batch.episode_count // 32 for index in range(32))
                    groups = tuple(
                        audited[start : start + 4] for start in range(0, len(audited), 4)
                    )
                    for group, (batch, _, _) in zip(
                        groups,
                        _prefetched_subsets(
                            result.batch,
                            groups,
                            device,
                            critic_only=False,
                        ),
                        strict=True,
                    ):
                        with torch.inference_mode():
                            errors = evaluate_sharded_behavior(
                                model,
                                batch,
                                candidate_elements_per_chunk=(
                                    settings.optimization.candidate_elements_per_chunk
                                ),
                            )
                        print(f"audit {group}: {errors}", flush=True)
                        if errors.maximum_log_error > 0.1:
                            torch.save(batch, output / "failed-microbatch.pt")
                            return
                    return
                if iteration == 0:
                    batch = result.batch.subset(
                        tuple(range(settings.optimization.effective_episodes_per_microbatch)),
                        torch.device("cpu"),
                    )
                    torch.save(batch, output / "microbatch.pt")
                del result
                gc.collect()
        finally:
            fleet.close()
        report["rollouts"] = rollout_reports
        batch_path = output / "microbatch.pt"
    else:
        batch_path = arguments.batch
    # Use precisely the same persisted, real rows for implementation comparisons.
    batch = torch.load(batch_path, weights_only=False, map_location=device)
    report["microbatch"] = {
        "episodes": batch.episode_count,
        "factors": batch.factor_count,
        "shards": [
            {
                "rows": shard.row_count,
                "candidates": shard.state.candidate_fields.shape[1],
                "entities": 1
                + sum(
                    getattr(shard.state, name).shape[1]
                    for name in ("jobs", "work_prefix", "market_prefix", "previous_action")
                ),
                "legal_candidates": int(shard.state.candidate_mask.sum()),
            }
            for shard in batch.decision_shards
        ],
    }
    model.train()
    model.actor.eval()
    _enable_trainable_recurrent_backends(model)
    advantages = batch.outcomes[batch.episode_index]
    scale = torch.ones((), device=device)

    def run() -> None:
        model.zero_grad(set_to_none=True)
        backward_sharded_ppo(
            model,
            batch,
            advantages,
            settings.optimization,
            value_scale=scale,
            policy_scale=scale,
            critic_actor_gradient=settings.optimization.critic_actor_gradient,
            validate=False,
        )

    torch.cuda.empty_cache()
    times = []
    for iteration in range(3):
        torch.cuda.synchronize(device)
        started = time.perf_counter()
        run()
        torch.cuda.synchronize(device)
        times.append(time.perf_counter() - started)
        print(json.dumps({"learner": iteration, "seconds": times[-1]}), flush=True)
    report["learner_seconds"] = times
    with torch.profiler.profile(
        activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
        record_shapes=True,
    ) as profiler:
        run()
        torch.cuda.synchronize(device)
    profiler.export_chrome_trace(str(output / "learner-trace.json.gz"))
    (output / "learner-kernels.txt").write_text(
        profiler.key_averages(group_by_input_shape=True).table(
            sort_by="self_cuda_time_total",
            row_limit=50,
        ),
        encoding="utf-8",
    )
    report["peak_allocated_bytes"] = torch.cuda.max_memory_allocated(device)
    report["peak_reserved_bytes"] = torch.cuda.max_memory_reserved(device)
    (output / "performance.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
