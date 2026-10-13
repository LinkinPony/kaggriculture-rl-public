"""Compatibility imports for shared learning optimization.

Implementation lives in kagg_revue.learning.optimization.protection.
"""

from kagg_revue.learning.optimization.protection import (
    StepResult,
    guarded_step,
    has_return_variation,
)

__all__ = ["has_return_variation", "StepResult", "guarded_step"]
