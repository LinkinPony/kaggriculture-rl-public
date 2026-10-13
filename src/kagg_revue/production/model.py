"""Compatibility imports for shared policy definitions."""

from kagg_revue.policy.spatial.model import (
    AttentionBlock,
    Critic,
    Policy,
    imitation_loss,
    log_probabilities,
    sample_categorical,
    scale_logits,
)

__all__ = [
    "AttentionBlock",
    "Policy",
    "Critic",
    "scale_logits",
    "sample_categorical",
    "log_probabilities",
    "imitation_loss",
]
