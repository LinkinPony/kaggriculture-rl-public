"""Finite-gradient and temporal consistency checks on the final-size architecture."""

import json
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.spatial.model import log_probabilities


def qualify(config: Experiment) -> dict[str, Any]:
    """Check final-size policy, recurrent inference, history eviction and gradients."""
    assert config.demonstrations is not None
    torch.set_num_threads(4)
    device = torch.device(config.device)
    torch.cuda.set_device(device)
    settings = runtime_settings(config)
    actor = random_policy(ContractLayout.resolve(settings), config.seed, config.exploration).to(
        device
    )
    assert isinstance(actor, MemoryPolicy)
    critic = MemoryCritic(actor.layout).to(device)
    manifest = json.loads(config.demonstrations.manifest.read_text())
    record = manifest["shards"][0]
    root = config.demonstrations.manifest.parent
    observations = torch.from_numpy(np.load(root / record["observations"])[:, :1].copy()).to(device)
    actions = torch.from_numpy(np.load(root / record["actions"])[:, :1].astype(np.int64)).to(device)
    clock = torch.arange(16, device=device)
    with torch.no_grad():
        state = actor.memory.temporal.empty(1, device)
        _, reference, _ = actor.sequence(observations[:16], clock, state, actions[:16])
        state = actor.memory.temporal.empty(1, device)
        pieces = []
        for turn in range(16):
            _, step_logits, state = actor.sequence(
                observations[turn : turn + 1],
                clock[turn : turn + 1],
                state,
                actions[turn : turn + 1],
            )
            pieces.append(step_logits)
        actual = torch.cat(pieces)
        torch.testing.assert_close(actual, reference, atol=2e-4, rtol=2e-4)
        fields = actor.field_weights(
            actions[:16].flatten(0, 1), clock, observations[:16].flatten(0, 1)
        )
        difference = (
            log_probabilities(actual[:, 0], actions[:16, 0])
            - log_probabilities(reference[:, 0], actions[:16, 0])
        ) * fields
        max_difference = float(difference.abs().max())
    runtime = ActorRuntime(actor, 1, sample=False, precision="fp32", compile_inference=False)
    sampled, probabilities = [], []
    for turn in range(16):
        runtime.host.copy_(observations[turn].cpu())
        chosen, likelihood = runtime.act(turn)
        sampled.append(chosen.clone())
        probabilities.append(likelihood.clone())
    with torch.no_grad():
        _, logits, _ = actor.sequence(
            observations[:16], clock, actor.memory.temporal.empty(1, device), torch.stack(sampled)
        )
        likelihood = log_probabilities(logits[:, 0], torch.stack(sampled)[:, 0])
        torch.testing.assert_close(likelihood, torch.cat(probabilities), atol=3e-4, rtol=3e-4)
    fields = actor.field_weights(actions[:16].flatten(0, 1), clock, observations[:16].flatten(0, 1))
    actor.zero_grad(set_to_none=True)
    _, logits, _ = actor.sequence(
        observations[:16], clock, actor.memory.temporal.empty(1, device), actions[:16]
    )
    loss = -(log_probabilities(logits[:, 0], actions[:16, 0]) * fields).sum() / fields.sum()
    loss.backward()  # type: ignore[no-untyped-call]
    gradients = {
        name: float(parameter.grad.abs().sum())
        for name, parameter in actor.named_parameters()
        if parameter.grad is not None
    }
    assert all(torch.isfinite(p.grad).all() for p in actor.parameters() if p.grad is not None)
    assert any(v > 0 for k, v in gradients.items() if k.startswith("memory.temporal"))
    assert any(v > 0 for k, v in gradients.items() if "attention_gate" in k)
    value, prefixes, _ = critic.sequence(
        observations[:16],
        clock,
        critic.memory.temporal.empty(1, device),
        actions[:16],
        fields[:, None],
    )
    (value.square().mean() + prefixes.square().mean()).backward()  # type: ignore[no-untyped-call]
    assert all(torch.isfinite(p.grad).all() for p in critic.parameters() if p.grad is not None)
    result = {
        "actor_parameters": sum(p.numel() for p in actor.parameters()),
        "critic_parameters": sum(p.numel() for p in critic.parameters()),
        "memory_turns": config.memory_turns,
        "memory_slots_per_layer": 4 * config.memory_turns,
        "chunk_step_likelihood_max_difference": max_difference,
        "cuda_graph_matches_sequence": True,
        "finite_actor_critic_gradients": True,
        "memory_and_gates_receive_gradients": True,
        "bc_probe_loss": float(loss.detach()),
    }
    write_json(Path("outputs/analysis/gtrxl-20260916/components.json"), result)
    return result


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="learning_gtrxl_20260916"
)
def main(configuration: DictConfig) -> None:
    """Run component qualification without touching any training run."""
    config = Experiment.model_validate(
        OmegaConf.to_container(configuration.experiment, resolve=True)
    )
    print(json.dumps(qualify(config)), flush=True)


if __name__ == "__main__":
    main()
