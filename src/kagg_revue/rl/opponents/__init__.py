"""Immutable actor opponents for terminal-outcome training."""

from kagg_revue.rl.opponents.checkpoint import (
    FrozenActorOpponent,
    load_frozen_actor_opponent,
)

__all__ = ["FrozenActorOpponent", "load_frozen_actor_opponent"]
