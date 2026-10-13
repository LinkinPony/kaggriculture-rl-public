"""Check compiled sampling likelihoods and live weight refresh against eager teacher forcing."""

import json
from pathlib import Path

import torch

from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import log_probabilities


def inference(directory: Path) -> dict[str, float | bool]:
    """Verify fresh sampled actions before and after an in-place actor parameter change."""
    state = json.loads((directory / "state.json").read_text())
    config = Experiment.model_validate(state["protocol"])
    device = torch.device(config.device)
    torch.cuda.set_device(device)
    torch.set_num_threads(2)
    policy, _ = artifacts.load_member(config, state, state["latest"], device)
    runtime = ActorRuntime(
        policy,
        96,
        sample=True,
        precision="bf16",
        compile_inference=True,
        bf16_reduced_precision_reduction=False,
    )
    settings = runtime_settings(config)
    batch = create_selfplay_batch(settings, list(range(48)))
    batch.observe_selfplay_into(runtime.host.numpy())
    errors = []
    for iteration in range(2):
        if iteration:
            with torch.no_grad():
                # A large parameter change makes a stale graph unambiguously wrong.
                policy.get_parameter("jobs.0.3.bias")[0].add_(4)
                policy.get_parameter("market_heads.0.3.bias")[0].add_(4)
        actions, likelihood = runtime.act(iteration)
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16, cache_enabled=False):
            logits = policy(runtime.observations, runtime.steps, actions)
            expected = log_probabilities(logits, actions)
        error = float((expected - likelihood).abs().max())
        if not torch.isfinite(expected).all() or error > 0.05:
            raise RuntimeError(
                f"compiled inference likelihood or live weights differ at {iteration}: {error}"
            )
        errors.append(error)
    return {
        "passed": True,
        "maximum_log_probability_error": max(errors),
        "live_weight_refresh": True,
        "bf16_absolute_tolerance": 0.05,
    }
