"""Frozen-actor critic training with disjoint physical-seed validation."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import Tensor
from torch.nn import functional as F

from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.rl.effects.checkpoint import load_checkpoint, save_checkpoint
from kagg_revue.rl.effects.cli import load_settings, repository_root
from kagg_revue.rl.effects.initialization import initialize_challenger
from kagg_revue.rl.effects.rollout import EffectRolloutCollector
from kagg_revue.rl.effects.runtime import native_contract

_INPUTS = (
    "board",
    "units",
    "global_features",
    "actions",
    "quantities",
    "turn_mask",
    "decision_mask",
)


def main() -> None:
    """Train only a new critic and test prediction before permitting bootstrap use."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, required=True)
    parser.add_argument("--seeds", type=int, default=96)
    parser.add_argument("--epochs", type=int, default=16)
    args, overrides = parser.parse_known_args()
    if args.seeds < 6 or args.seeds % 6 or args.epochs < 1:
        raise ValueError("critic probe needs positive epochs and six complete seed blocks")
    settings = load_settings(overrides)
    root = repository_root()
    output = (root / args.output).resolve()
    if not output.is_relative_to(root / "outputs"):
        raise ValueError("critic probe output must remain under outputs/")
    source = source_identity(root)
    if source["worktree_dirty"]:
        raise RuntimeError("critic validation requires a clean source revision")
    output.mkdir(parents=True, exist_ok=False)
    if settings.initial_checkpoint is None:
        raise ValueError("critic probe requires a frozen neural checkpoint")
    torch.set_num_threads(settings.cpu_threads)
    torch.manual_seed(settings.seed)
    device = torch.device(settings.device)
    backend = load_backend(root)
    contract = native_contract(backend, settings.environment)
    model, metadata = load_checkpoint(root / settings.initial_checkpoint, contract, device)
    model = initialize_challenger(model, settings.model)
    model.requires_grad_(False)
    critic = model.critic
    if critic is None:
        raise ValueError("critic probe requires the independent critic architecture")
    model.eval()
    collector = EffectRolloutCollector(
        backend,
        model,
        contract,
        settings.environment,
        unit_limit=settings.unit_limit,
        cpu_workers=settings.rollout.cpu_workers,
        device=device,
        action_generator=torch.Generator(device=device).manual_seed(settings.seed),
        maximum_graph_variants=settings.rollout.maximum_graph_variants,
        retain_behavior_distributions=False,
    )
    try:
        rollout = collector.collect_jobs(
            [
                (seed, 0, "self_play")
                for seed in range(args.seed_start, args.seed_start + args.seeds)
            ]
        )
    finally:
        collector.close()
    data = {name: getattr(rollout.batch, name) for name in _INPUTS}
    labels = rollout.batch.outcomes.long() + 1
    games = tuple(asdict(game) for game in rollout.games)
    diagnostics = rollout.diagnostics
    del rollout
    torch.cuda.empty_cache() if device.type == "cuda" else None
    microbatch = settings.optimization.effective_episodes_per_microbatch
    # Persist only reusable critic inputs, never expanded factor/candidate tensors.
    for start in range(0, labels.numel(), microbatch):
        stop = min(start + microbatch, labels.numel())
        np.savez_compressed(
            output / f"episodes-{start:06d}.npz",
            **{name: value[start:stop].numpy() for name, value in data.items()},
            labels=labels[start:stop].numpy(),
        )
    train_end = args.seed_start + 4 * args.seeds // 6
    validation_end = train_end + args.seeds // 6
    splits = {
        "train": [i for i, game in enumerate(games) if int(game["seed"]) < train_end],
        "validation": [
            i for i, game in enumerate(games) if train_end <= int(game["seed"]) < validation_end
        ],
        "confirmation": [i for i, game in enumerate(games) if int(game["seed"]) >= validation_end],
    }
    counts = torch.bincount(labels[splits["train"]], minlength=3).float()
    prior = (counts / counts.sum()).clamp_min(1e-6)
    prior_value = float(prior[2] - prior[0])

    def inputs(rows: list[int]) -> list[Tensor]:
        indices = torch.tensor(rows)
        return [data[name].index_select(0, indices).to(device) for name in _INPUTS]

    @torch.no_grad()
    def score(rows: list[int]) -> dict[str, float]:
        critic.eval()
        totals = torch.zeros(6, device=device)
        for start in range(0, len(rows), microbatch):
            selected = rows[start : start + microbatch]
            target = labels[selected].to(device)
            logits = critic(*inputs(selected))
            horizon = logits.shape[1]
            repeated = target[:, None].expand(-1, horizon)
            losses = F.cross_entropy(logits.flatten(0, 1), repeated.flatten(), reduction="none")
            losses = losses.view(-1, horizon)
            probabilities = logits.softmax(-1)
            value = probabilities[..., 2] - probabilities[..., 0]
            mse = (value - (target.float()[:, None] - 1)).square()
            baseline = ((target.float() - 1) - prior_value).square().mean()
            tail = min(24, horizon)
            totals += torch.stack(
                (
                    losses.mean(),
                    mse.mean(),
                    losses[:, -tail:].mean(),
                    mse[:, -tail:].mean(),
                    -prior.to(device)[target].log().mean(),
                    baseline,
                )
            ) * len(selected)
        values = (totals / len(rows)).cpu().tolist()
        return dict(
            zip(
                ("ce", "mse", "late_ce", "late_mse", "constant_ce", "constant_mse"),
                values,
                strict=True,
            )
        )

    before = score(splits["validation"])
    critic.requires_grad_(True)
    optimizer = torch.optim.AdamW(
        critic.parameters(),
        lr=settings.optimization.critic_learning_rate,
        weight_decay=settings.optimization.weight_decay,
        fused=device.type == "cuda",
    )
    randomizer = np.random.default_rng(settings.seed)
    best = float("inf")
    best_state: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []
    for epoch in range(args.epochs):
        critic.train()
        order = randomizer.permutation(splits["train"]).tolist()
        for start in range(0, len(order), microbatch):
            selected = order[start : start + microbatch]
            optimizer.zero_grad(set_to_none=True)
            logits = critic(*inputs(selected))
            targets = labels[selected].to(device)[:, None].expand(-1, logits.shape[1])
            loss = F.cross_entropy(logits.flatten(0, 1), targets.flatten())
            loss.backward()  # type: ignore[no-untyped-call]
            torch.nn.utils.clip_grad_norm_(critic.parameters(), settings.optimization.gradient_clip)
            optimizer.step()
        validation = score(splits["validation"])
        history.append({"epoch": epoch + 1, **validation})
        if validation["ce"] < best:
            best = validation["ce"]
            best_state = deepcopy(critic.state_dict())
        print(json.dumps(history[-1]), flush=True)
    if best_state is None:
        raise RuntimeError("critic probe failed to select a finite model")
    critic.load_state_dict(best_state)
    confirmation = score(splits["confirmation"])
    report = {
        "source": source,
        "checkpoint": metadata["checkpoint_identity"],
        "resolved_config": settings.model_dump(mode="json"),
        "arguments": vars(args) | {"output": str(args.output)},
        "native_backend": backend.identity,
        "games": games,
        "splits": splits,
        "before_validation": before,
        "epochs": history,
        "confirmation": confirmation,
        "bootstrap_prediction_gate": (
            confirmation["ce"] < confirmation["constant_ce"]
            and confirmation["late_mse"] < confirmation["constant_mse"]
        ),
        "rollout": diagnostics,
        "scope": "Frozen neural actor; critic prediction only, no policy-strength promotion",
    }
    # Initial-checkpoint use resets optimizers; this artifact is not an RL resume.
    identity = save_checkpoint(
        output / "critic-initialized.pt",
        model,
        optimizer,
        update=1,
        contract=contract,
        resolved_config=settings.model_dump(mode="json"),
        source_actor=cast(Mapping[str, object], metadata["source_actor"]),
        source_revision=source,
        opponent_identities={"self_play": metadata["checkpoint_identity"]},
        population_state={"weights": {"self_play": 1.0}},
        rng_state={},
    )
    report["initialized_checkpoint"] = identity
    (output / "report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")


if __name__ == "__main__":
    main()
