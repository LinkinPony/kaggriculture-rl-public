"""Compare BF16 online sampling and teacher-forced replay across memory eviction."""

import json
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.learning.optimization.prefix import prefix_surrogate
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.spatial.model import log_probabilities


@torch.no_grad()
def verify(
    config: Experiment,
    *,
    checkpoint: Path | None = None,
    compiled: bool = False,
    output: Path = Path("outputs/analysis/gtrxl-20260916/full-season-consistency.json"),
) -> dict[str, Any]:
    """Check full-season stored behavior likelihoods and episode cache reset."""
    assert config.demonstrations is not None
    torch.set_num_threads(2)
    device = torch.device(config.device)
    torch.cuda.set_device(device)
    settings = runtime_settings(config)
    actor = (
        load_policy(checkpoint, device)[0]
        if checkpoint is not None
        else random_policy(ContractLayout.resolve(settings), config.seed, config.exploration).to(
            device
        )
    )
    assert isinstance(actor, MemoryPolicy)
    if compiled:
        from kagg_revue.policy.memory.compilation import compile_actor

        compile_actor(actor)
    root = config.demonstrations.manifest.parent
    manifest = json.loads(config.demonstrations.manifest.read_text())
    record = manifest["shards"][0]
    observations = torch.from_numpy(np.load(root / record["observations"])[:, :1].copy()).to(device)
    runtime = ActorRuntime(actor, 1, sample=True, precision="bf16", compile_inference=False)
    actions, probabilities = [], []
    for turn in range(len(observations)):
        runtime.host.copy_(observations[turn].cpu())
        chosen, likelihood = runtime.act(turn)
        actions.append(chosen.clone())
        probabilities.append(likelihood.clone())
    selected = torch.stack(actions)
    behavior = torch.stack(probabilities)
    replayed = []
    state = actor.memory.temporal.empty(1, device)
    with torch.autocast(device.type, dtype=torch.bfloat16):
        for start in range(0, len(observations), config.sequence_chunk_turns):
            end = min(start + config.sequence_chunk_turns, len(observations))
            _, logits, state = actor.sequence(
                observations[start:end],
                torch.arange(start, end, device=device),
                state,
                selected[start:end],
            )
            replayed.append(log_probabilities(logits[:, 0], selected[start:end, 0]))
    actual = torch.cat(replayed)
    turns = torch.arange(len(observations), device=device)
    fields = actor.field_weights(selected[:, 0], turns, observations[:, 0])
    difference = (actual - behavior[:, 0]) * fields
    _, kl = prefix_surrogate(difference, fields, torch.zeros_like(difference), 0.1)
    if not bool(torch.isfinite(kl).all()) or float(kl.mean()) > 0.001:
        raise ValueError(
            f"unchanged recurrent policy has excessive numerical KL: {float(kl.mean())}"
        )
    assert runtime.memory is not None
    expected = torch.arange(
        len(observations) - 384, len(observations), device=device
    ).repeat_interleave(4)
    assert torch.equal(runtime.memory.state.turns, expected)
    runtime.host.copy_(observations[0].cpu())
    runtime.act(0)
    assert (runtime.memory.state.turns[:-4] == -1).all()
    assert (runtime.memory.state.turns[-4:] == 0).all()
    try:
        runtime.act(2)
    except ValueError:
        pass
    else:
        raise AssertionError("recurrent runtime accepted a missing context frame")
    result = {
        "turns": len(observations),
        "precision": "bf16",
        "mean_unchanged_policy_prefix_kl": float(kl.mean()),
        "maximum_prefix_kl": float(kl.max()),
        "maximum_active_field_logprob_difference": float(difference.abs().max()),
        "384_turn_eviction_checked": True,
        "episode_reset_checked": True,
        "compiled_components": compiled,
        "checkpoint_sha256": digest(checkpoint) if checkpoint is not None else None,
        "cache_dtype": str(runtime.memory.state.keys[0].dtype),
    }
    write_json(output, result)
    return result


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="learning_gtrxl_20260916"
)
def main(configuration: DictConfig) -> None:
    """Exercise the exact final memory capacity without training any candidate."""
    config = Experiment.model_validate(
        OmegaConf.to_container(configuration.experiment, resolve=True)
    )
    options: dict[str, Any] = {}
    if configuration.get("checkpoint"):
        options["checkpoint"] = Path(configuration.checkpoint)
    if configuration.get("output"):
        options["output"] = Path(configuration.output)
    print(
        json.dumps(verify(config, compiled=bool(configuration.get("compiled")), **options)),
        flush=True,
    )


if __name__ == "__main__":
    main()
