"""Reproduce compiled numerical defects from an authenticated BC checkpoint."""

import json
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.strata.loading import ResidentDataset
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.spatial.model import log_probabilities


@hydra.main(version_base=None, config_path="../../../../configs", config_name="league_diagnosis")
def main(config: DictConfig) -> None:
    """Compare traced eager and compiled kernels without modifying training state."""
    torch.set_num_threads(2)
    device = torch.device(config.device)
    torch.cuda.set_device(device)
    torch.backends.cuda.enable_cudnn_sdp(False)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    directory = Path(config.run) / "bc"
    state = json.loads((directory / "state.json").read_text())
    checkpoint = directory / state["latest"]
    actor, payload = load_policy(checkpoint, device)
    source = state["protocol"]["demonstrations"]
    manifest = Path(source["manifest"])
    if digest(manifest) != source["sha256"]:
        raise ValueError("modified diagnostic manifest")
    dataset = object.__new__(ResidentDataset)
    dataset.directory = manifest.parent.resolve()
    dataset.manifest = json.loads(manifest.read_text())
    dataset.shards = dataset.manifest["shards"]
    dataset.layout = actor.layout
    record = dataset.shards[config.shard]
    for name, expected in record["hashes"].items():
        if digest(dataset.path(record[name])) != expected:
            raise ValueError("modified diagnostic shard")
    observations, actions, turns, _ = next(
        dataset.batches(config.shard, 1024, device, (63001, 3, config.shard), rank=0, world=2)
    )
    captured: list[tuple[str, torch.Tensor, torch.Tensor]] = []

    def hook(name: str) -> Any:
        def capture(module: Any, inputs: tuple[torch.Tensor, ...], output: torch.Tensor) -> None:
            captured.append((name, inputs[0].detach().clone(), output.detach().clone()))

        return capture

    if config.trace:
        for name, module in actor.named_modules():
            if name.startswith("condition.") or name == "encoder":
                module.register_forward_hook(hook(name))
    options = dict(config.options)
    compiled = torch.compile(actor, dynamic=False, options=options)
    report: dict[str, Any] = {"checkpoint": digest(checkpoint), "options": options, "cases": []}
    for mode in config.modes:
        if mode == "poison":
            from kagg_revue.learning.league.poison import install

            install(Path(config.output).with_suffix(".pt"))
        captured.clear()
        actor.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits = (actor if mode == "eager" else compiled)(observations, turns, actions)
            weights = actor.field_weights(actions, turns, observations)
            loss = (
                -(log_probabilities(logits, actions) * weights)
                .sum(-1)
                .div(weights.sum(-1).clamp_min(1))
                .mean()
            )
        case: dict[str, Any] = {"mode": mode, "loss": loss.item(), "nodes": []}
        for name, before, after in captured:
            row = {
                "name": name,
                "input_finite": bool(before.isfinite().all()),
                "output_finite": bool(after.isfinite().all()),
                "input_max": before.abs().max().item(),
                "output_max": after.abs().max().item(),
            }
            case["nodes"].append(row)
            if row["input_finite"] and not row["output_finite"]:
                target = Path(config.output).with_suffix(".pt")
                torch.save(
                    {
                        "name": name,
                        "input": before,
                        "output": after,
                        "state": actor.get_submodule(name).state_dict(),
                    },
                    target,
                )
                break
        if bool(loss.isfinite()) and config.backward:
            loss.backward()  # type: ignore[no-untyped-call]
            case["gradients_finite"] = all(
                p.grad is None or bool(p.grad.isfinite().all()) for p in actor.parameters()
            )
        report["cases"].append(case)
        write_json(Path(config.output), report)
        print(json.dumps({k: v for k, v in case.items() if k != "nodes"}), flush=True)
    if config.scan:
        for rank in (0, 1):
            batches = dataset.batches(
                config.shard, 1024, device, (63001, 3, config.shard), rank=rank, world=2
            )
            for batch, (observations, actions, turns, _) in enumerate(batches):
                actor.zero_grad(set_to_none=True)
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    logits = compiled(observations, turns, actions)
                    weights = actor.field_weights(actions, turns, observations)
                    loss = (
                        -(log_probabilities(logits, actions) * weights)
                        .sum(-1)
                        .div(weights.sum(-1).clamp_min(1))
                        .mean()
                    )
                loss.backward()  # type: ignore[no-untyped-call]
                norm = torch.nn.utils.clip_grad_norm_(
                    actor.parameters(), 1.0, error_if_nonfinite=True
                )
                if not bool(loss.isfinite()):
                    raise ValueError(f"nonfinite scanned batch {rank}/{batch}")
                report["cases"].append(
                    {
                        "mode": "scan",
                        "rank": rank,
                        "batch": batch,
                        "loss": loss.item(),
                        "gradient_norm": norm.item(),
                    }
                )
                write_json(Path(config.output), report)
        print(json.dumps({"phase": "scan_complete", "batches": 2 * (batch + 1)}), flush=True)


if __name__ == "__main__":
    main()
