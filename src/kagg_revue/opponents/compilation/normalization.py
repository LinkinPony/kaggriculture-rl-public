"""Explicit, hash-bound normalization of Python-only container-copy optimizations."""

import ast
import hashlib
from typing import Literal

Normalization = Literal["none", "v43-container-copy"]
_COPY_AST_SHA256 = "3776ed1eae1f12cb21c38b6e634d538cb97b69d48b20c2ceeb38b30eb6c6cd9b"


def normalize(tree: ast.Module, mode: Normalization) -> ast.Module:
    """Use the native graph copier in place of the exact V43 Python speed adapter."""
    if mode == "none":
        return tree
    starts = [
        index
        for index, node in enumerate(tree.body)
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "_R149_COPY"
    ]
    if len(starts) != 1:
        raise ValueError("the declared V43 copy adapter is absent or ambiguous")
    start = starts[0]
    adapter = ast.Module(body=tree.body[start : start + 7], type_ignores=[])
    actual = hashlib.sha256(ast.dump(adapter, include_attributes=False).encode()).hexdigest()
    if actual != _COPY_AST_SHA256:
        raise ValueError("V43 copy adapter differs from the reviewed performance-only code")
    # The retained copy module and planner deepcopy already map to native DeepCopy.
    # Selection policy, overflow recovery and the optimized route planner remain.
    tree.body[start : start + 7] = []
    return tree
