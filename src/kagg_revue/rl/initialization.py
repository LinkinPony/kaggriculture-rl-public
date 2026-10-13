"""Training-time actor initialization independent of behavior weights."""

from __future__ import annotations

import torch

from kagg_revue.policy.model import TurnPolicyNet


def initialize_training_actor(
    architecture_source: TurnPolicyNet,
    mode: str,
    device: torch.device,
) -> TurnPolicyNet:
    """Return artifact weights or a fresh actor with only the same architecture."""
    if mode == "artifact":
        return architecture_source
    if mode != "random":
        raise ValueError(f"unsupported actor initialization mode: {mode}")
    actor = TurnPolicyNet(architecture_source.architecture).to(device)
    actor.train(architecture_source.training)
    return actor


__all__ = ["initialize_training_actor"]
