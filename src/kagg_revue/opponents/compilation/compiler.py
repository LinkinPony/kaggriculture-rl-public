"""Compile policy functions into shared, deterministic C++ translation units."""

from __future__ import annotations

import ast
import hashlib
import json

from kagg_revue.opponents.compilation.data import StaticData
from kagg_revue.opponents.compilation.expressions import expression
from kagg_revue.opponents.compilation.model import Lexical, Program, bindings, quoted
from kagg_revue.opponents.compilation.specialization import specialization
from kagg_revue.opponents.compilation.statements import assign, statement
from kagg_revue.opponents.compilation.typed import FUNCTIONS


class Compiler:
    """Emit control flow ahead of time; no AST or bytecode is used in training."""

    def __init__(self, program: Program, lexical: Lexical) -> None:
        """Attach shared output and the lexical namespace."""
        self.program = program
        self.lexical = lexical
        self.loop_flags: list[str | None] = []
        self.data = StaticData(ast.Module(body=[], type_ignores=[]))

    def child(self, lexical: Lexical) -> Compiler:
        """Share output with another lexical namespace."""
        child = Compiler(self.program, lexical)
        child.data = self.data
        return child

    def expression(self, node: ast.expr) -> str:
        """Translate one expression into native C++."""
        return expression(self, node)

    def assign(self, target: ast.expr, value: str) -> list[str]:
        """Translate assignment while preserving alias semantics."""
        return assign(self, target, value)

    def block(self, nodes: list[ast.stmt]) -> list[str]:
        """Translate statements in their original execution order."""
        return [line for node in nodes for line in statement(self, node)]

    def function(self, node: ast.FunctionDef | ast.Lambda) -> str:
        """Bind a deduplicated native function to its definition scope."""
        capture = not self.lexical.module and not self.lexical.class_body
        captured = self.lexical.local | self.lexical.captured if capture else set()
        body: list[ast.stmt] = (
            node.body if isinstance(node, ast.FunctionDef) else [ast.Return(node.body)]
        )
        globals_ = {
            name
            for item in body
            for decl in ast.walk(item)
            if isinstance(decl, ast.Global)
            for name in decl.names
        }
        lexical = Lexical(
            local=bindings(body, node.args),
            captured=captured,
            global_names=globals_,
            class_name=self.lexical.class_name,
            slotted=True,
        )
        identity = ast.dump(node, include_attributes=False) + json.dumps(
            [sorted(captured), self.lexical.class_name]
        )
        folded = [
            self.data.value(call)
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
            and self.data.canonical(call.func) in {"json.loads", "zlib.decompress"}
        ]
        if folded:
            identity += json.dumps(folded, default=lambda value: {"bytes": value.hex()})
        code = "Code_" + hashlib.sha256(identity.encode()).hexdigest()[:20]
        self.program.declarations.add(code)
        if code not in self.program.functions:
            self.program.functions[code] = ""
            prefix = []
            native = FUNCTIONS.get(
                hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
            )
            if native:
                prefix.append(f"if (auto result = {native}(c, s)) return *result;")
            if hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest() == (
                "fe641aabf5433767faed1d7c324639f6ae682f75c6bf360b938d7f14c004bdde"
            ):
                prefix.append("if (auto result = Forecast(c, s)) return *result;")
            if code == "Code_0fb13b0638d196e5f1f0":
                # Exact AST/lexical identity of the frozen finite input tour.
                # Unsupported inputs retain the generated source implementation.
                prefix.append("if (auto result = InputPath(c, s)) return *result;")
            lines = self.child(lexical).block(body)
            self.program.functions[code] = (
                f"Value {code}(Context& c, const ScopePtr& s) {{\n"
                + "\n".join([*prefix, *lexical.prepare(), *lines])
                + "\nreturn {};\n}\n"
            )
        args = node.args

        def names(items: list[ast.arg]) -> str:
            return "{" + ", ".join(quoted(arg.arg) for arg in items) + "}"

        defaults = "{" + ", ".join(self.expression(value) for value in args.defaults) + "}"
        keyword_defaults = (
            "{"
            + ", ".join(
                self.expression(value) if value is not None else 'Builtin("missing")'
                for value in args.kw_defaults
            )
            + "}"
        )
        signature = (
            "Signature{"
            + ", ".join(
                [
                    names([*args.posonlyargs, *args.args]),
                    defaults,
                    names(args.kwonlyargs),
                    keyword_defaults,
                    quoted(args.vararg.arg if args.vararg else ""),
                    quoted(args.kwarg.arg if args.kwarg else ""),
                    (
                        "([]() -> std::span<const char* const> { static constexpr const char* "
                        "names[] = {"
                        + ", ".join(quoted(name) for name in lexical.slots())
                        + "}; return names; }())"
                    )
                    if lexical.slots()
                    else "{}",
                ]
            )
            + "}"
        )
        name = node.name if isinstance(node, ast.FunctionDef) else "<lambda>"
        captured_flag = "true" if capture else "false"
        fast = specialization(node, capture=capture)
        suffix = f", Specialization::{fast}" if fast != "kNone" else ""
        return (
            f"Define(&{code}, {self.lexical.cpp_scope}, {signature}, "
            f"{captured_flag}, {quoted(name)}{suffix})"
        )

    def module_code(self, node: ast.Module, label: str) -> str:
        """Compile a frozen module initializer without executing its source."""
        identity = label + ast.dump(node, include_attributes=False)
        code = "Init_" + hashlib.sha256(identity.encode()).hexdigest()[:20]
        self.program.declarations.add(code)
        if code not in self.program.functions:
            self.program.functions[code] = ""
            child = self.child(Lexical(module=True))
            child.data = StaticData(node)
            lines = child.block(node.body)
            self.program.functions[code] = (
                f"Value {code}(Context& c, const ScopePtr& s) {{\n"
                + "\n".join(lines)
                + "\nreturn {};\n}\n"
            )
        return code
