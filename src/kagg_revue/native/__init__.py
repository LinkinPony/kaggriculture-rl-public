"""Official rules, self-play batches and observation execution.

Build the CPU training core with ``python -m kagg_revue.native.build``.
The older ``native.engine`` adapter uses the explicit ``build.target=legacy``
target. Explicit script populations reuse that extension's C++ opponents;
neural self-play continues to use the smaller core.
"""
