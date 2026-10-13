"""Lexical scopes and deterministic C++ translation units."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from typing import Any


def quoted(value: str) -> str:
    """Encode a C++ UTF-8 string literal without universal surrogate escapes."""
    return json.dumps(value, ensure_ascii=False)


def bindings(nodes: list[ast.stmt], arguments: ast.arguments | None = None) -> set[str]:
    """Find function-local names without descending into nested lexical scopes."""
    found: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                found.add(node.id)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            found.add(node.name)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            found.add(node.name)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            pass

        def visit_ListComp(self, node: ast.AST) -> None:
            pass

        visit_SetComp = visit_ListComp
        visit_DictComp = visit_ListComp
        visit_GeneratorExp = visit_ListComp

        def visit_Import(self, node: ast.Import) -> None:
            found.update(item.asname or item.name for item in node.names)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module != "__future__":
                found.update(item.asname or item.name for item in node.names)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name is not None:
                found.add(node.name)
            self.generic_visit(node)

    visitor = Visitor()
    for statement in nodes:
        visitor.visit(statement)
    if arguments is not None:
        found.update(
            arg.arg for arg in [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
        )
        found.update(arg.arg for arg in [arguments.vararg, arguments.kwarg] if arg is not None)
    return found


@dataclass
class Lexical:
    """Describe Python name resolution independently of runtime container lookup."""

    local: set[str] = field(default_factory=set)
    captured: set[str] = field(default_factory=set)
    global_names: set[str] = field(default_factory=set)
    module: bool = False
    class_name: str | None = None
    class_body: bool = False
    cpp_scope: str = "s"
    slotted: bool = False

    def slots(self) -> list[str]:
        """Use a stable native offset for each lexically declared local."""
        return sorted(self.local - self.global_names)

    def prepare(self) -> list[str]:
        """Initialize argument slots once before executing the function body."""
        if not self.slotted or not self.slots():
            return []
        names = ", ".join(quoted(name) for name in self.slots())
        return [
            f"static constexpr const char* {self.cpp_scope}_names[] = {{{names}}};",
            f"{self.cpp_scope}->PrepareSlots({self.cpp_scope}_names);",
        ]

    def read(self, name: str) -> str:
        """Select local, captured or global name resolution."""
        method = "Global"
        if not self.module and name not in self.global_names:
            if name in self.local:
                if self.slotted:
                    return f"{self.cpp_scope}->LocalAt({self.slots().index(name)})"
                method = "Local"
            elif name in self.captured:
                method = "Captured"
        return f"{self.cpp_scope}->{method}({quoted(name)})"

    def write(self, name: str, value: str) -> str:
        """Emit an assignment to the owning namespace."""
        if name in self.global_names:
            return f"Put({self.cpp_scope}->globals, {quoted(name)}, {value});"
        if self.slotted:
            return f"{self.cpp_scope}->SetAt({self.slots().index(name)}, {value});"
        return f"{self.cpp_scope}->Set({quoted(name)}, {value});"


@dataclass
class Program:
    """Collect only static data and native C++ bodies, never runtime Python code."""

    constants: list[Any] = field(default_factory=list)
    functions: dict[str, str] = field(default_factory=dict)
    declarations: set[str] = field(default_factory=set)
    counter: int = 0

    def temporary(self, prefix: str = "v") -> str:
        """Allocate a deterministic C++ temporary name."""
        self.counter += 1
        return f"{prefix}{self.counter}"

    def constant(self, value: Any) -> str:
        """Extract immutable source data into the portfolio asset."""
        index = len(self.constants)
        self.constants.append(
            {"__native_bytes__": value.hex()} if isinstance(value, bytes) else value
        )
        return f"c.constants.at({index})"
