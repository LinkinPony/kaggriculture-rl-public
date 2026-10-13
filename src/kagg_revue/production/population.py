"""Compatibility imports for shared complete-game collection."""

from kagg_revue.learning.collection.population import (
    TrainingBatch,
    create_training_batch,
    episode_weights,
    historical_games,
    outcomes,
    policy_rows,
    script_games,
)

__all__ = [
    "TrainingBatch",
    "create_training_batch",
    "episode_weights",
    "historical_games",
    "policy_rows",
    "script_games",
    "outcomes",
]
