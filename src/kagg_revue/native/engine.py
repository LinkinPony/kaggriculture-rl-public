"""Loader for the native engine extension.

The extension is built in-place (gitignored ``.so`` next to this file) by
``python -m kagg_revue.native.build build.target=legacy``.
"""

from kagg_revue.native._revue_native import Engine, EngineBatch, PyRandom

__all__ = ["Engine", "EngineBatch", "PyRandom"]
