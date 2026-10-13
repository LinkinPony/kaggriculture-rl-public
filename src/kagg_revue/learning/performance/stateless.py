"""Profile warmed stateless actor and critic work outside throughput measurements."""

from pathlib import Path

import torch

from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.optimization.learner import Learner


def profile_microbatch(learner: Learner, rollout: Rollout, output: Path) -> None:
    """Trace one real-sized forward/backward microbatch without applying an update."""
    losses = learner.losses
    if losses is None:
        raise ValueError("stateless profiling requires fused prefix objectives")
    count = min(len(rollout.steps), learner.settings.ppo.microbatch_rows)
    section = slice(0, count)
    observations = rollout.observations[section]
    actions = rollout.actions[section].long()
    steps, behavior = rollout.steps[section], rollout.log_probabilities[section]
    weights, returns = rollout.weights[section], rollout.returns[section]
    mass = weights.sum()
    # Timing-only gradients; the full PPO measurement already used real credits.
    credits = torch.ones_like(behavior)

    def operation() -> None:
        learner.actor_optimizer.zero_grad(set_to_none=True)
        learner.critic_optimizer.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            with torch.profiler.record_function("actor_forward"):
                loss, _ = losses.actor(
                    observations, steps, actions, behavior, credits, weights, mass, 1.0
                )
            with torch.profiler.record_function("critic_forward"):
                value, _, _ = losses.value(observations, steps, actions, returns, weights, mass)
        with torch.profiler.record_function("actor_backward"):
            loss.backward()  # type: ignore[no-untyped-call]
        with torch.profiler.record_function("critic_backward"):
            value.backward()  # type: ignore[no-untyped-call]

    operation()
    torch.cuda.synchronize()
    with torch.profiler.profile(
        activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
        record_shapes=False,
    ) as profile:
        operation()
        torch.cuda.synchronize()
    profile.export_chrome_trace(str(output.with_suffix(".trace.json")))
    output.with_suffix(".profile.txt").write_text(
        profile.key_averages().table(sort_by="self_device_time_total", row_limit=60)
    )
