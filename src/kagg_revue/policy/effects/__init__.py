"""Atomic-effect policy contract and recurrent pointer model."""

from kagg_revue.policy.effects.contract import NativeEffectContract
from kagg_revue.policy.effects.data import EffectTensorState, tensor_state_from_native
from kagg_revue.policy.effects.model import EffectActorCritic, EffectPolicy
from kagg_revue.policy.effects.schema import (
    EffectArchitecture,
    EffectPolicyOutput,
    EffectSelection,
)

__all__ = [
    "EffectArchitecture",
    "EffectActorCritic",
    "EffectPolicy",
    "EffectPolicyOutput",
    "EffectSelection",
    "EffectTensorState",
    "NativeEffectContract",
    "tensor_state_from_native",
]
