"""Compatibility imports for shared learning optimization.

Implementation lives in kagg_revue.learning.optimization.objectives.
"""

from kagg_revue.learning.optimization.objectives import (
    surrogate_rows,
    terminal_rewards,
)

__all__ = ["terminal_rewards", "surrogate_rows"]
