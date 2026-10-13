"""Compatibility imports for shared learning optimization.

Implementation lives in kagg_revue.learning.optimization.prefix.
"""

from kagg_revue.learning.optimization.prefix import (
    PrefixCritic,
    prefix_credit,
    prefix_surrogate,
    prefix_value_rows,
)

__all__ = ["PrefixCritic", "prefix_credit", "prefix_surrogate", "prefix_value_rows"]
