"""Fast paths require exact source operations and retain lexical fallback semantics."""

import ast

from kagg_revue.opponents.compilation.specialization import specialization


def test_specializations_match_operations_and_reject_changed_semantics() -> None:
    """Renaming is safe; casts, defaults, closures and branch changes remain checked."""
    source = """
def number(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
def field(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)
"""
    functions = ast.parse(source).body
    for node, expected in zip(functions, ("kInteger", "kDictGet"), strict=True):
        assert isinstance(node, ast.FunctionDef)
        assert specialization(node, capture=False) == expected
        assert specialization(node, capture=True) == "kNone"
    for altered in (
        source.replace("int(value)", "float(value)"),
        source.replace("value.get(key, default)", "value.get(key)"),
    ):
        nodes = ast.parse(altered).body
        assert (
            sum(
                specialization(n, capture=False) != "kNone"
                for n in nodes
                if isinstance(n, ast.FunctionDef)
            )
            == 1
        )
