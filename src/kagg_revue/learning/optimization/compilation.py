"""Shared compilation choices for production PPO and throughput measurements."""

from typing import TYPE_CHECKING, Any

import torch

from kagg_revue.policy.compilation import options
from kagg_revue.policy.grounded.typed import TypedGroundedPolicy
from kagg_revue.policy.memory.compilation import compile_actor
from kagg_revue.policy.memory.policy import MemoryPolicy

if TYPE_CHECKING:
    from kagg_revue.learning.optimization.learner import Learner


def compile_learner(learner: "Learner") -> None:
    """Use bounded scene/decoder graphs and Hopper layouts for stateless typed actors."""
    actor = learner.policy
    typed = isinstance(actor, TypedGroundedPolicy) and not isinstance(actor, MemoryPolicy)
    controls: dict[str, Any] = options(learner.device) if typed else {}
    if typed:
        assert isinstance(actor, TypedGroundedPolicy)
        compile_actor(actor)
        learner.forward = actor
    else:
        learner.forward = torch.compile(actor, fullgraph=True, dynamic=False, options=controls)
    learner.value = torch.compile(learner.critic, fullgraph=True, dynamic=False, options=controls)
    if learner.prefix_value is not None:
        learner.prefix_value = torch.compile(
            learner.prefix_value, fullgraph=True, dynamic=False, options=controls
        )
    if learner.losses is not None:
        for name in ("actor", "value", "divergence"):
            setattr(
                learner.losses,
                name,
                torch.compile(
                    getattr(learner.losses, name), fullgraph=True, dynamic=False, options=controls
                ),
            )
