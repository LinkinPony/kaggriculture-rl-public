"""Probe frozen actors on complete native self-play histories without optimizer steps."""

import gc
import json
import time
from pathlib import Path
from typing import Any, Literal

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, Field
from torch import Tensor

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.divergence.statistics import summarize
from kagg_revue.learning.collection.sampling import collect
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.memory.policy import MemoryPolicy


class Options(BaseModel):
    """Hydra overrides for a bounded diagnostic, independent of the training ledger."""

    output: Path
    games: int = Field(default=8, gt=0)
    seed: int = 92515001
    device: str = "cuda:0"
    chunk_turns: int = Field(default=48, gt=0)
    replay_trajectories: int = Field(default=4, gt=0)
    precision: Literal["bf16", "fp32"] = "bf16"
    collect: bool = True


@torch.no_grad()
def replay(
    before: MemoryPolicy,
    after: MemoryPolicy,
    tape: dict[str, Tensor],
    options: Options,
) -> dict[str, Tensor]:
    """Integrate categorical KL exactly, conditional on sampled old-policy prefixes."""
    device = next(before.parameters()).device
    observations, actions = tape["observations"], tape["actions"].long()
    turns, count = observations.shape[:2]
    saved: dict[str, list[Tensor]] = {}
    for offset in range(0, count, options.replay_trajectories):
        stop = min(offset + options.replay_trajectories, count)
        states = [actor.memory.temporal.empty(stop - offset, device) for actor in (before, after)]
        pieces: dict[str, list[Tensor]] = {}
        for start in range(0, turns, options.chunk_turns):
            end = min(start + options.chunk_turns, turns)
            obs = observations[start:end, offset:stop].to(device)
            chosen = actions[start:end, offset:stop].to(device)
            steps = torch.arange(start, end, device=device)
            logs = []
            with torch.autocast(
                device.type, dtype=torch.bfloat16, enabled=options.precision == "bf16"
            ):
                for index, actor in enumerate((before, after)):
                    _, logits, states[index] = actor.sequence(obs, steps, states[index], chosen)
                    logs.append(logits.float().log_softmax(-1))
            old_log, new_log = logs
            old, new = old_log.exp(), new_log.exp()
            fields = before.field_weights(
                chosen.flatten(0, 1),
                steps.repeat_interleave(stop - offset),
                obs.flatten(0, 1),
            ).reshape_as(chosen)
            old_selected = old_log.gather(-1, chosen[..., None]).squeeze(-1)
            new_selected = new_log.gather(-1, chosen[..., None]).squeeze(-1)
            current = {
                "fields": fields,
                "exact_kl": (old * (old_log - new_log)).sum(-1).clamp_min(0),
                "log_ratio": new_selected - old_selected,
                "unchanged_log_ratio": old_selected
                - tape["behavior"][start:end, offset:stop].to(device),
                "entropy_before": -(old * old_log).sum(-1),
                "entropy_after": -(new * new_log).sum(-1),
                "tv": 0.5 * (old - new).abs().sum(-1),
                "greedy_changed": old_log.argmax(-1) != new_log.argmax(-1),
                "support_size": (old_log > -1e8).sum(-1),
                "maximum_probability": old.max(-1).values,
            }
            for key, value in current.items():
                pieces.setdefault(key, []).append(value.cpu())
        for key, values in pieces.items():
            saved.setdefault(key, []).append(torch.cat(values))
        print(
            json.dumps({"replayed_trajectories": stop, "precision": options.precision}), flush=True
        )
    return {key: torch.cat(values, dim=1) for key, values in saved.items()}


def diagnose(options: Options) -> dict[str, Any]:
    """Save distribution diagnostics and provenance without touching the source run."""
    started = time.perf_counter()
    torch.set_num_threads(2)
    torch.manual_seed(options.seed)
    device = torch.device(options.device)
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.set_per_process_memory_fraction(0.08, device)
    before, payload = load_policy(options.output / "before.pt", device)
    assert isinstance(before, MemoryPolicy)
    before.eval()
    settings = RuntimeSettings.model_validate(payload["settings"])
    del payload
    tape_path = options.output / "rollout.pt"
    if options.collect:
        settings = settings.model_copy(
            update={
                "workers": 2,
                "devices": (options.device,),
                "compile": False,
                "script_population": None,
                "ppo": settings.ppo.model_copy(
                    update={"history": None, "script_fraction": 0, "script_opponents": ()}
                ),
            }
        )
        runtime = ActorRuntime(before, 2 * options.games, sample=True, precision="bf16")
        with torch.no_grad():
            rollout = collect(
                settings, before, runtime, list(range(options.seed, options.seed + options.games))
            )
        count = 2 * options.games
        tape = {
            "observations": rollout.observations.reshape(
                -1, count, before.layout.observation.features
            ).cpu(),
            "actions": rollout.actions.reshape(-1, count, before.layout.factors).cpu(),
            "behavior": rollout.log_probabilities.reshape(-1, count, before.layout.factors).cpu(),
        }
        torch.save(tape, tape_path)
        write_json(
            options.output / "collection.json", {"cash": rollout.cash.tolist(), **rollout.timing}
        )
        del rollout, runtime
        gc.collect()
        if device.type == "cuda":
            torch.cuda.empty_cache()
        print(
            json.dumps({"collection_complete": True, "seconds": time.perf_counter() - started}),
            flush=True,
        )
    else:
        tape = torch.load(tape_path, map_location="cpu", weights_only=True)
    after, payload = load_policy(options.output / "after.pt", device)
    assert isinstance(after, MemoryPolicy)
    after.eval()
    del payload
    data = replay(before, after, tape, options)
    result = {
        "options": options.model_dump(mode="json"),
        "snapshot": json.loads((options.output / "snapshot.json").read_text()),
        "semantics": "Old-policy self-play histories; full conditional categorical KL at sampled "
        "prefixes. Uncompiled replay; BF16 graph collection. Frozen checkpoints span multiple "
        "training updates. This is a diagnostic sample, not a strength evaluation.",
        "summary": summarize(data, before.layout.work_factors),
        "seconds": time.perf_counter() - started,
    }
    torch.save(data, options.output / f"fields-{options.precision}.pt")
    write_json(options.output / f"report-{options.precision}.json", result)
    return result


@hydra.main(version_base=None, config_path=None, config_name=None)
def main(config: DictConfig) -> None:
    """Run a configured read-only policy diagnostic."""
    options = Options.model_validate(OmegaConf.to_container(config, resolve=True))
    result = diagnose(options)
    print(json.dumps({"seconds": result["seconds"], "report": str(options.output)}), flush=True)


if __name__ == "__main__":
    main()
