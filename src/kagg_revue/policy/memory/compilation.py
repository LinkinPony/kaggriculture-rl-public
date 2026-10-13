"""Bound recurrent compilation without changing state-dict names or math."""

from typing import TYPE_CHECKING

import torch

from kagg_revue.policy.compilation import options as compilation_options
from kagg_revue.policy.grounded.encoder import ContextEncoder

if TYPE_CHECKING:
    from kagg_revue.learning.sequences.critic import MemoryCritic
    from kagg_revue.policy.grounded.typed import TypedGroundedPolicy


def compile_actor(actor: "TypedGroundedPolicy") -> None:
    """Compile scene, temporal and decoder graphs at explicit tensor boundaries."""
    from kagg_revue.policy.memory.policy import MemoryPolicy

    _allow_shapes()
    options = compilation_options(next(actor.parameters()).device)
    assert isinstance(actor.encoder, ContextEncoder)
    actor.encoder.tokens = torch.compile(  # type: ignore[method-assign]
        actor.encoder.tokens, fullgraph=True, dynamic=False, options=options
    )
    if isinstance(actor, MemoryPolicy):
        actor.memory.compile(fullgraph=True, dynamic=False, options=options)
        actor.memory.step = torch.compile(  # type: ignore[method-assign]
            actor.memory.step, fullgraph=True, dynamic=False, options=options
        )
    actor.decode_encoded = torch.compile(  # type: ignore[method-assign]
        actor.decode_encoded, fullgraph=True, dynamic=False, options=options
    )


def compile_critic(critic: "MemoryCritic") -> None:
    """Keep prefix-value and temporal backward graphs bounded independently."""
    _allow_shapes()
    assert isinstance(critic.entity_encoder, ContextEncoder)
    options = compilation_options(next(critic.parameters()).device)
    critic.entity_encoder.tokens = torch.compile(  # type: ignore[method-assign]
        critic.entity_encoder.tokens, fullgraph=True, dynamic=False, options=options
    )
    critic.memory.compile(fullgraph=True, dynamic=False, options=options)
    critic.prefixes_encoded = torch.compile(  # type: ignore[method-assign]
        critic.prefixes_encoded, fullgraph=True, dynamic=False, options=options
    )


def _allow_shapes() -> None:
    """Budget static graphs for both widths, tail chunks, grad modes and inference."""
    # Actor and critic share Python code objects. Their finite set of recurrent
    # shapes exceeds Dynamo's default eight variants even within the first update.
    torch.compiler.config.recompile_limit = max(64, int(torch.compiler.config.recompile_limit))
