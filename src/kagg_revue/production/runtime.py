"""Compatibility imports for policy inference and complete-game collection."""

from kagg_revue.learning.collection.sampling import Rollout, collect
from kagg_revue.policy.inference import ActorRuntime

__all__ = ["ActorRuntime", "Rollout", "collect"]
