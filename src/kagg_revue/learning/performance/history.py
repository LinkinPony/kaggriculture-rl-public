"""Validate frozen recurrent CUDA graphs against eager conditional likelihoods."""

import json
from pathlib import Path
from typing import Any, cast

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from torch import Tensor

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.collection.archive import PopulationCache
from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.imports import layout_from_payload
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.performance.distributions import Distributions
from kagg_revue.policy.grounded.typed import TypedGroundedPolicy
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.memory.compilation import compile_actor
from kagg_revue.policy.spatial.model import Policy


def verify(runtime: ActorRuntime, rollout: Rollout) -> dict[str, Any]:
    """Check a complete memory window, episode reset and live parameter replacement."""
    policy = runtime.policy
    torch.manual_seed(73001)
    assert isinstance(policy, TypedGroundedPolicy)
    original = {name: value.detach().clone() for name, value in policy.state_dict().items()}
    distributions = Distributions(runtime.device)
    original_decode = policy.decode_encoded
    policy.decode_encoded = distributions.watch("actual", original_decode)  # type: ignore[method-assign]
    runtime = ActorRuntime(
        policy, runtime.host.shape[0], sample=True, bf16_reduced_precision_reduction=False
    )
    reference = Policy.from_layout(policy.layout).to(runtime.device).eval().requires_grad_(False)
    assert isinstance(reference, TypedGroundedPolicy)
    reference.load_state_dict(original)
    decode = reference.decode_encoded

    def teacher(
        encoded: Tensor,
        observations: Tensor,
        actions: Tensor | None,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        return decode(encoded, observations, runtime.actions, False, temperature)

    reference.decode_encoded = distributions.watch("expected", teacher)  # type: ignore[method-assign]
    count = runtime.host.shape[0]
    eager = ActorRuntime(reference, count, sample=True, bf16_reduced_precision_reduction=False)
    frames = rollout.observations.reshape(
        policy.layout.decisions, -1, rollout.observations.shape[-1]
    )
    if frames.shape[-1] != policy.layout.observation.features:
        # Match HistoricalBatch's v4-to-v2 public observation projection.
        support = policy.layout.observation.support_features
        prefix = policy.layout.observation.features - support
        frames = torch.cat((frames[..., :prefix], frames[..., -support:]), -1)
    rows = torch.arange(count, device=frames.device) % frames.shape[1]
    errors = []
    cache_errors = []
    for replacement in (False, True):
        distributions.reset()
        if replacement:
            changed = {name: value.clone() for name, value in original.items()}
            changed["encoder.board.bias"][0] += 0.5
            if "memory.pool_keys.bias" in changed:
                changed["memory.pool_keys.bias"][0] += 0.5
            changed["market_heads.0.1.bias"][0] += 4
            policy.load_state_dict(changed)
            reference.load_state_dict(changed)
        maximum = torch.zeros((), device=runtime.device)
        total = torch.zeros_like(maximum)
        worst = torch.zeros(3, device=runtime.device)
        turns = len(frames) if not replacement else 8
        for turn in range(turns):
            observations = frames[turn, rows].cpu()
            runtime.host.copy_(observations)
            eager.host.copy_(observations)
            _, actual = runtime.act(turn, synchronize=False)
            # Both H2D copies must finish before the next turn reuses pinned hosts.
            _, expected = eager.act(turn, synchronize=True)
            fields = policy.field_weights(runtime.actions, runtime.steps, runtime.observations)
            distributions.update(fields)
            difference = (actual - expected).abs() * fields
            index = difference.flatten().argmax()
            worst = torch.where(
                difference.max() > maximum,
                torch.stack((actual.flatten()[index], expected.flatten()[index], index.float())),
                worst,
            )
            maximum = torch.maximum(maximum, difference.max())
            total += difference.sum() / fields.sum().clamp_min(1)
        torch.cuda.synchronize(runtime.device)
        cache_error = 0.0
        if runtime.memory is not None:
            assert eager.memory is not None
            before, after = eager.memory.state, runtime.memory.state
            if not torch.equal(before.turns, after.turns):
                raise ValueError("compiled historical graph changed the memory clock")
            cache_error = max(
                float((a.float() - b.float()).norm() / a.float().norm().clamp_min(1e-6))
                for a, b in zip(
                    (*before.keys, *before.values), (*after.keys, *after.values), strict=True
                )
            )
        error = {
            "replaced_weights": replacement,
            "turns": turns,
            "maximum_logprob_error": float(maximum),
            "mean_logprob_error": float(total / turns),
            "worst_logprobs_and_flat_index": worst.tolist(),
            "distribution": distributions.report(),
        }
        distribution = distributions.report()
        if (
            not torch.isfinite(maximum)
            or total / turns > 0.005
            or cache_error > 0.03
            or distribution["mean_kl"] > 0.001
            or distribution["mean_total_variation"] > 0.01
            or distribution["changed_legal_support_fields"] != 0
        ):
            raise ValueError(
                f"historical compiled likelihood mismatch: {error}, cache={cache_error}"
            )
        errors.append(error)
        cache_errors.append(cache_error)
    policy.load_state_dict(original)
    policy.decode_encoded = original_decode  # type: ignore[method-assign]
    if runtime.memory is not None:
        runtime.memory.reset()
    return {
        "passed": True,
        "rows": count,
        "errors": errors,
        "cache_relative_l2_errors": cache_errors,
        "live_weight_replacement": True,
        "replaced_parameters": [
            name
            for name in ("encoder.board.bias", "memory.pool_keys.bias", "market_heads.0.1.bias")
            if name in original
        ],
        "recurrent": runtime.memory is not None,
        "episode_reset": True if runtime.memory is not None else None,
        "acceptance": {
            "maximum_logprob_is_diagnostic_only": True,
            "maximum_mean_logprob_error": 0.005,
            "maximum_mean_kl": 0.001,
            "maximum_mean_total_variation": 0.01,
            "maximum_cache_relative_l2_error": 0.03,
            "legal_support_must_match": True,
        },
    }


@hydra.main(version_base=None, config_path="../../../../configs", config_name="hopper_history")
def main(configuration: DictConfig) -> None:
    """Isolate compiler boundaries on an authenticated frozen policy and real tape."""
    options = configuration.benchmark
    identity = artifacts.source_identity()
    state = json.loads((Path(options.run) / "state.json").read_text())
    config = Experiment.model_validate(state["protocol"])
    torch.set_num_threads(2)
    torch.manual_seed(73001)
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    name = (
        options.checkpoint
        or Matchmaker(config, state).select(state["completed_update"] + 1, 1).history
    )
    payload = PopulationCache(config, state)._payload(name)
    policy = Policy.from_layout(layout_from_payload(payload)).to(device)
    policy.load_state_dict(payload["model"])
    assert isinstance(policy, TypedGroundedPolicy)
    policy.eval().requires_grad_(False)
    if options.production:
        compile_actor(policy)
    compiler_options = OmegaConf.to_container(options.compiler, resolve=True)
    assert isinstance(compiler_options, dict)
    target: torch.nn.Module
    for component in [] if options.production else options.components:
        if component == "encoder":
            target, attribute = policy.encoder, "tokens"
        elif component == "memory":
            from kagg_revue.policy.memory.policy import MemoryPolicy

            assert isinstance(policy, MemoryPolicy)
            target, attribute = policy.memory, "step"
        else:
            target, attribute = policy, "decode_encoded"
        setattr(
            target,
            attribute,
            torch.compile(
                getattr(target, attribute),
                fullgraph=True,
                dynamic=False,
                options=cast(dict[str, Any], compiler_options),
            ),
        )
    print(f"capturing {name}: {type(policy).__name__}", flush=True)
    runtime = ActorRuntime(
        policy, options.rows, sample=True, bf16_reduced_precision_reduction=False
    )
    tape = torch.load(options.tape, map_location="cpu", weights_only=False)
    print("verifying", flush=True)
    report = {
        **verify(runtime, tape),
        "source_sha256": identity["source_sha256"],
        "checkpoint": name,
        "checkpoint_sha256": state["members"][name],
        "options": OmegaConf.to_container(options, resolve=True),
    }
    write_json(Path(options.output), report)
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
