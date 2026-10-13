"""Compatibility imports for shared learning optimization.

Implementation lives in kagg_revue.learning.optimization.learner.
"""

from kagg_revue.learning.optimization.learner import (
    Learner,
    advantage_moments,
    average_gradients,
    global_mean,
    weighted_mean,
)

__all__ = ["average_gradients", "global_mean", "weighted_mean", "advantage_moments", "Learner"]
