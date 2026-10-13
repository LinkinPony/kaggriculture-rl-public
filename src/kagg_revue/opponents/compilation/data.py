"""Decode authenticated literal data with imported aliases at generation time."""

import ast
import copy
from typing import Any

from kagg_revue.opponents.portfolios.extraction import Literals


class StaticData(Literals):
    """Resolve only immutable literal bindings and standard data decoder aliases."""

    def __init__(self, tree: ast.Module) -> None:
        """Index top-level constant strings and unambiguous module imports."""
        super().__init__("")
        self.aliases: dict[str, str] = {}
        for node in tree.body:
            if isinstance(node, ast.Import):
                for item in node.names:
                    self.aliases[item.asname or item.name] = item.name
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value.value, str | bytes):
                        if target.id in self.assignments:
                            raise ValueError(f"ambiguous static data binding: {target.id}")
                        self.assignments[target.id] = node.value

    def canonical(self, node: ast.expr) -> str:
        """Resolve the module portion of a decoder's qualified name."""
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return self.aliases.get(node.value.id, node.value.id) + "." + node.attr
        return ast.unparse(node)

    def value(self, node: ast.expr) -> Any:
        """Use the same bounded decoder allowlist for aliased calls."""
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            canonical = self.canonical(node.func)
            if canonical in {
                "json.loads",
                "zlib.decompress",
                "base64.b85decode",
                "base64.b64decode",
            }:
                node = copy.copy(node)
                node.func = ast.parse(canonical, mode="eval").body
        return super().value(node)
