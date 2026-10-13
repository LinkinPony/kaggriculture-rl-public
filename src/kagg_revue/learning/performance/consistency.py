"""Compare sampled likelihoods with eager and compiled full-model teacher forcing."""

from pathlib import Path
from typing import Any

import hydra
import orjson
import torch
from omegaconf import DictConfig

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.league.config import League
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import log_probabilities


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="attention_consistency"
)
def main(config: DictConfig) -> None:
    """Exercise real trained weights and nonempty native observations at both batch sizes."""
    torch.set_num_threads(2)
    torch.backends.cuda.enable_cudnn_sdp(False)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    root = Path(config.run)
    state = orjson.loads((root / "league.json").read_bytes())
    protocol = League.model_validate(state["protocol"])
    settings = runtime_settings(protocol.experiment)
    endpoint = root / "a" / state["members"]["a"]["bc_path"]
    actor, _ = load_policy(endpoint, torch.device("cuda:0"))
    checkpoint = root / state["latest"]
    if digest(checkpoint) != state["checkpoints"][state["latest"]]:
        raise ValueError("diagnostic checkpoint changed")
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    actor.load_state_dict(payload["models"]["a"]["actor"])
    runtime = ActorRuntime(
        actor, 64, sample=True, compile_inference=True, bf16_reduced_precision_reduction=False
    )
    batch = create_selfplay_batch(settings, list(range(74000, 74032)))
    batch.observe_selfplay_into(runtime.host.numpy())
    actions, behavior = runtime.act(0)
    observations = runtime.observations
    steps = runtime.steps
    if config.sample_path:
        sample = torch.load(config.sample_path, map_location="cuda:0", weights_only=True)
        observations, actions, steps, behavior = (
            sample[name] for name in ("observations", "actions", "steps", "log_probabilities")
        )
    compiled = torch.compile(actor, fullgraph=True, dynamic=False)
    report: list[dict[str, Any]] = []
    for count in (64, 2880):
        indices = torch.arange(count, device="cuda:0") % len(steps)
        obs, act, turns, old = (
            observations[indices],
            actions[indices].long(),
            steps[indices],
            behavior[indices],
        )
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
            eager = actor(obs, turns, act)
            actual = compiled(obs, turns, act)
            fields = actor.field_weights(act, turns, obs)
            expected_lp, actual_lp = log_probabilities(eager, act), log_probabilities(actual, act)
            row = {
                "rows": count,
                "compiled_finite": bool(actual.isfinite().all()),
                "maximum_logit_difference": float((actual - eager).abs().max()),
                "maximum_logprob_difference": float(
                    ((actual_lp - expected_lp) * fields).abs().max()
                ),
                "eager_vs_behavior_maximum": float(((expected_lp - old) * fields).abs().max()),
                "compiled_vs_behavior_maximum": float(((actual_lp - old) * fields).abs().max()),
            }
        report.append(row)
        write_json(Path(config.output), report)
        print(orjson.dumps(row).decode(), flush=True)


if __name__ == "__main__":
    main()
