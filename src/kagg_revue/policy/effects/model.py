"""Public model interface for effect policies and their independent critic."""

from kagg_revue.policy.effects.actor_critic import EffectActorCritic
from kagg_revue.policy.effects.pointer import EffectPolicy

__all__ = ["EffectActorCritic", "EffectPolicy"]
