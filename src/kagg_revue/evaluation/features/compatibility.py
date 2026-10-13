"""Test proposed feature insertion using real v4 weights and replay observations."""

import gzip
import importlib.util
import json
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from torch import Tensor, nn

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.features.residual import ResidualProbe
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.grounded.encoder import ContextEncoder
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.memory.temporal import MemoryState


class Audit(FrozenSettings):
    """Pin offline inputs and bound CPU usage independently of the live learner."""

    checkpoint: Path
    checkpoint_sha256: str
    native: Path
    native_sha256: str
    replay: Path
    replay_sha256: str
    output: Path
    starts: list[int]
    length: int = 8
    threads: int = 2


def observations(config: Audit, features: int, units: int) -> dict[int, Tensor]:
    """Replay public history from turn zero through the certified native encoder."""
    spec = importlib.util.spec_from_file_location("_revue_observation", config.native)
    if spec is None or spec.loader is None:
        raise ValueError("native observation extension cannot be loaded")
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    replay = json.loads(gzip.decompress(config.replay.read_bytes()))
    session = native.ContractSession(replay["configuration"], units)
    wanted = {turn for start in config.starts for turn in range(start, start + config.length)}
    rows = {}
    for turn in range(max(wanted) + 1):
        session.update(replay["steps"][turn][0]["observation"])
        if turn in wanted:
            row = np.empty((1, features), dtype=np.float16)
            session.observe_into(row)
            rows[turn] = torch.from_numpy(row.copy())
    return rows


def same_memory(left: MemoryState, right: MemoryState) -> bool:
    """Compare the complete recurrent state, including retained turn identifiers."""
    return torch.equal(left.turns, right.turns) and all(
        torch.equal(a, b) for a, b in zip(left.layers, right.layers, strict=True)
    )


def run(config: Audit) -> dict[str, Any]:
    """Measure identity and gradients without updating or saving trained weights."""
    for name in ("checkpoint", "native", "replay"):
        if digest(getattr(config, name)) != getattr(config, f"{name}_sha256"):
            raise ValueError(f"{name} differs from the pinned artifact")
    torch.set_num_threads(config.threads)
    device = torch.device("cpu")
    actor, payload = load_policy(config.checkpoint, device)
    assert isinstance(actor, MemoryPolicy)
    assert isinstance(actor.encoder, ContextEncoder)
    critic = MemoryCritic(actor.layout)
    critic.load_state_dict(payload["critic"], strict=True)
    assert isinstance(critic.entity_encoder, ContextEncoder)
    actor.eval().requires_grad_(False)
    critic.eval().requires_grad_(False)
    base = actor.layout.observation
    if (base.version, actor.layout.cells, base.units) != (
        "grounded-production-context-v4",
        100,
        32,
    ):
        raise ValueError("this proposal audit is scoped to the current v4 geometry")
    actor_probe = ResidualProbe(base.width, actor.layout.cells, base.units)
    critic_probe = ResidualProbe(actor.layout.network.critic_width, actor.layout.cells, base.units)
    rows = observations(config, base.features, base.units)
    generator = torch.Generator().manual_seed(5912)
    records = []
    gradient_norms = {}
    prefix = base.features - base.support_features
    for start in config.starts:
        old = torch.stack([rows[turn] for turn in range(start, start + config.length)])
        steps = torch.arange(start, start + config.length)
        state = actor.memory.temporal.empty(1, device)
        critic_state = critic.memory.temporal.empty(1, device)
        with torch.no_grad():
            actions, logits, memory = actor.sequence(old, steps, state)
            fields = actor.field_weights(actions.flatten(0, 1), steps, old.flatten(0, 1))[:, None]
            values, prefixes, critic_memory = critic.sequence(
                old, steps, critic_state, actions, fields
            )
        extra = torch.randn(config.length, 1, actor_probe.features, generator=generator).to(
            old.dtype
        )
        extended = torch.cat((old[..., :prefix], extra, old[..., prefix:]), -1)
        actor_probe.values = extra.flatten(0, 1)
        critic_probe.values = actor_probe.values
        actor_hook = actor.encoder.blocks[0].register_forward_pre_hook(actor_probe.hook)
        critic_hook = critic.entity_encoder.blocks[0].register_forward_pre_hook(critic_probe.hook)
        try:
            with torch.no_grad():
                selected, new_logits, new_memory = actor.sequence(extended, steps, state)
                new_fields = actor.field_weights(
                    actions.flatten(0, 1), steps, extended.flatten(0, 1)
                )[:, None]
                new_values, new_prefixes, new_critic_memory = critic.sequence(
                    extended, steps, critic_state, actions, new_fields
                )
            record = {
                "start": start,
                "length": config.length,
                "legacy_projection_equal": torch.equal(
                    torch.cat(
                        (extended[..., :prefix], extended[..., -base.support_features :]), -1
                    ),
                    old,
                ),
                "logits_equal": torch.equal(logits, new_logits),
                "max_logit_difference": float((logits - new_logits).abs().max()),
                "greedy_actions_equal": torch.equal(actions, selected),
                "recurrent_state_equal": same_memory(memory, new_memory),
                "critic_values_equal": torch.equal(values, new_values),
                "critic_prefixes_equal": torch.equal(prefixes, new_prefixes),
                "critic_memory_equal": same_memory(critic_memory, new_critic_memory),
                "field_weights_equal": torch.equal(fields, new_fields),
                "max_critic_difference": float((values - new_values).abs().max()),
            }
            records.append(record)
            if start == config.starts[-1]:
                actor_probe.values = extra[:1].flatten(0, 1)
                _, differentiable, _ = actor.sequence(extended[:1], steps[:1], state, actions[:1])
                loss = -differentiable.log_softmax(-1).gather(-1, actions[:1, ..., None]).mean()
                loss.backward()  # type: ignore[no-untyped-call]
                for name, layer in actor_probe.projections.items():
                    assert isinstance(layer, nn.Linear)
                    if layer.weight.grad is None:
                        raise ValueError(f"new projection has no gradient: {name}")
                    gradient_norms[name] = float(layer.weight.grad.norm())
        finally:
            actor_hook.remove()
            critic_hook.remove()
    actor_unchanged = all(
        torch.equal(value, payload["model"][name]) for name, value in actor.state_dict().items()
    )
    critic_unchanged = all(
        torch.equal(value, payload["critic"][name]) for name, value in critic.state_dict().items()
    )
    passed = (
        actor_unchanged
        and critic_unchanged
        and all(
            all(
                row[key]
                for key in (
                    "legacy_projection_equal",
                    "logits_equal",
                    "greedy_actions_equal",
                    "recurrent_state_equal",
                    "critic_values_equal",
                    "critic_prefixes_equal",
                    "critic_memory_equal",
                    "field_weights_equal",
                )
            )
            for row in records
        )
        and all(np.isfinite(value) and value > 0 for value in gradient_norms.values())
    )
    report = {
        "passed": bool(passed),
        "scope": "CPU FP32 residual-insertion prototype with synthetic supplementary values; "
        "not a v5 native encoder, production loader, complete 384-turn-history qualification, "
        "optimizer migration, or evidence of improved playing strength",
        "inputs": config.model_dump(mode="json"),
        "source_sha256": {
            str(path): digest(path)
            for path in (Path(__file__), Path(__file__).with_name("residual.py"))
        },
        "torch_version": torch.__version__,
        "observation_dtype": "float16",
        "compute_dtype": "float32",
        "checkpoint_update": payload["update"],
        "legacy_observation_features": base.features,
        "supplementary_features": actor_probe.features,
        "packed_observation_features": base.features + actor_probe.features,
        "support_prefix_offset": prefix,
        "new_actor_parameters": sum(p.numel() for p in actor_probe.parameters()),
        "new_critic_parameters": sum(p.numel() for p in critic_probe.parameters()),
        "old_actor_tensors": len(payload["model"]),
        "old_critic_tensors": len(payload["critic"]),
        "old_actor_tensors_unchanged": actor_unchanged,
        "old_critic_tensors_unchanged": critic_unchanged,
        "windows": records,
        "actor_supplement_gradient_norms": gradient_norms,
    }
    write_json(config.output, report)
    if not passed:
        raise ValueError("feature insertion identity or gradient check failed")
    return report


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="features_compatibility_20260925",
)
def main(config: DictConfig) -> None:
    """Run a CPU-only design experiment from a resolved Hydra configuration."""
    settings = Audit.model_validate(OmegaConf.to_container(config, resolve=True))
    result = run(settings)
    print(json.dumps({"passed": result["passed"], "output": str(settings.output)}))


if __name__ == "__main__":
    main()
