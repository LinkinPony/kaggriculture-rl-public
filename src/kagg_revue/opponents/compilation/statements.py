"""Emit native control flow and preserve source assignment order."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from kagg_revue.opponents.compilation.model import Lexical, bindings, quoted

if TYPE_CHECKING:
    from kagg_revue.opponents.compilation.compiler import Compiler


def assign(c: Compiler, target: ast.expr, value: str) -> list[str]:
    """Assign an evaluated RHS, preserving aliases and nested unpacking."""
    e = c.expression
    if isinstance(target, ast.Name):
        return [c.lexical.write(target.id, value)]
    if isinstance(target, ast.Attribute):
        return [f"SetAttribute({e(target.value)}, {quoted(target.attr)}, {value});"]
    if isinstance(target, ast.Subscript):
        if isinstance(target.slice, ast.Slice):
            parts = [
                e(x) if x is not None else "Value{}"
                for x in (target.slice.lower, target.slice.upper, target.slice.step)
            ]
            return [f"PutSlice({e(target.value)}, {', '.join(parts)}, {value});"]
        return [f"Put({e(target.value)}, {e(target.slice)}, {value});"]
    if isinstance(target, (ast.Tuple, ast.List)):
        values = c.program.temporary("unpack")
        stars = [i for i, item in enumerate(target.elts) if isinstance(item, ast.Starred)]
        if len(stars) > 1:
            raise ValueError("multiple starred assignment targets")
        statements = [
            f"auto {values} = Iterate({value});",
            f"ValidateUnpack({values}, {len(target.elts) - len(stars)}, "
            f"{'true' if stars else 'false'});",
        ]
        for index, item in enumerate(target.elts):
            if isinstance(item, ast.Starred):
                tail = len(target.elts) - index - 1
                rhs = f"List(Values({values}.begin() + {index}, {values}.end() - {tail}))"
                statements.extend(assign(c, item.value, rhs))
            else:
                offset = (
                    str(index)
                    if not stars or index < stars[0]
                    else f"{values}.size() - {len(target.elts) - index}"
                )
                statements.extend(assign(c, item, f"{values}.at({offset})"))
        return statements
    raise TypeError(f"unsupported assignment target: {ast.dump(target)}")


def statement(c: Compiler, node: ast.stmt) -> list[str]:
    """Translate only constructs present in authenticated policy sources."""
    e = c.expression
    scope = c.lexical.cpp_scope
    if isinstance(node, ast.Expr):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return []
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "exec"
        ):
            call = node.value
            if (
                len(call.args) != 2
                or not isinstance(call.args[0], ast.Constant)
                or not isinstance(call.args[0].value, str)
            ):
                raise ValueError("only literal embedded source namespaces may be compiled")
            code = c.module_code(ast.parse(call.args[0].value), "embedded")
            return [f"{code}(c, Module({e(call.args[1])}));"]
        return [f"(void){e(node.value)};"]
    if isinstance(node, ast.Assign):
        rhs = c.program.temporary()
        result = [f"auto {rhs} = {e(node.value)};"]
        for target in node.targets:
            result.extend(assign(c, target, rhs))
        return result
    if isinstance(node, ast.AugAssign):
        target = node.target
        op = quoted(type(node.op).__name__)
        if isinstance(target, ast.Subscript) and not isinstance(target.slice, ast.Slice):
            base, key, old = (c.program.temporary() for _ in range(3))
            return [
                f"auto {base} = {e(target.value)};",
                f"auto {key} = {e(target.slice)};",
                f"auto {old} = Get({base}, {key});",
                f"Put({base}, {key}, Inplace({op}, {old}, {e(node.value)}));",
            ]
        if isinstance(target, ast.Attribute):
            base, old = c.program.temporary(), c.program.temporary()
            return [
                f"auto {base} = {e(target.value)};",
                f"auto {old} = Attribute({base}, {quoted(target.attr)});",
                f"SetAttribute({base}, {quoted(target.attr)}, "
                f"Inplace({op}, {old}, {e(node.value)}));",
            ]
        old = c.program.temporary()
        return [
            f"auto {old} = {e(target)};",
            *assign(c, target, f"Inplace({op}, {old}, {e(node.value)})"),
        ]
    if isinstance(node, ast.Return):
        return [f"return {e(node.value) if node.value is not None else 'Value{}'};"]
    if isinstance(node, ast.If):
        # Imported public scripts never execute their packaging-only main guard.
        if ast.unparse(node.test) in {"__name__ == '__main__'", '__name__ == "__main__"'}:
            return c.block(node.orelse)
        result = [f"if (static_cast<bool>({e(node.test)})) {{", *c.block(node.body), "}"]
        if node.orelse:
            result.extend(["else {", *c.block(node.orelse), "}"])
        return result
    if isinstance(node, ast.For | ast.While):
        exhausted = c.program.temporary("exhausted") if node.orelse else None
        result = [f"bool {exhausted} = true;"] if exhausted else []
        if isinstance(node, ast.For):
            item = c.program.temporary("item")
            result.extend(
                [
                    f"for (const auto& {item} : Iterate({e(node.iter)})) {{",
                    *assign(c, node.target, item),
                ]
            )
        else:
            result.append(f"while (static_cast<bool>({e(node.test)})) {{")
        c.loop_flags.append(exhausted)
        try:
            result.extend(c.block(node.body))
        finally:
            c.loop_flags.pop()
        result.append("}")
        if exhausted:
            result.extend([f"if ({exhausted}) {{", *c.block(node.orelse), "}"])
        return result
    if isinstance(node, ast.Break):
        flag = c.loop_flags[-1]
        return [*([f"{flag} = false;"] if flag else []), "break;"]
    if isinstance(node, ast.Continue):
        return ["continue;"]
    if isinstance(node, ast.Pass):
        return []
    if isinstance(node, ast.Try):
        if node.finalbody:
            if (
                node.handlers
                or node.orelse
                or len(node.body) != 1
                or not isinstance(node.body[0], ast.Return)
            ):
                raise TypeError("native finally requires a single try-return without handlers")
            returned = c.program.temporary("returned")
            value = e(node.body[0].value) if node.body[0].value is not None else "Value()"
            # Evaluate once, then restore the temporary policy setting on both
            # success and failure. Cleanup may itself override the pending return
            # or exception, matching Python without a throwing C++ destructor.
            return [
                "{",
                f"Value {returned};",
                "try {",
                f"{returned} = {value};",
                "} catch (...) {",
                *c.block(node.finalbody),
                "throw;",
                "}",
                *c.block(node.finalbody),
                f"return {returned};",
                "}",
            ]
        if node.orelse:
            raise TypeError("try else is outside the frozen subset")
        error = c.program.temporary("error")
        result = ["try {", *c.block(node.body), f"}} catch (const Error& {error}) {{"]
        for index, handler in enumerate(node.handlers):
            test = "true" if handler.type is None else f"Matches({error}, {e(handler.type)})"
            result.append(f"{'if' if index == 0 else 'else if'} ({test}) {{")
            if handler.name:
                result.append(c.lexical.write(handler.name, f"Value({error}.what())"))
            result.extend([*c.block(handler.body), "}"])
        result.extend(["else { throw; }", "}"])
        return result
    if isinstance(node, ast.Raise):
        return ["throw;"] if node.exc is None else [f"Raise({e(node.exc)});"]
    if isinstance(node, ast.Assert):
        message = quoted(ast.unparse(node.msg)) if node.msg is not None else '"assertion failed"'
        return [
            f'if (!static_cast<bool>({e(node.test)})) throw Error("AssertionError", {message});'
        ]
    if isinstance(node, ast.Delete):
        result = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                if c.lexical.slotted and target.id not in c.lexical.global_names:
                    result.append(f"{scope}->EraseAt({c.lexical.slots().index(target.id)});")
                    continue
                location = (
                    "globals"
                    if c.lexical.module or target.id in c.lexical.global_names
                    else "locals"
                )
                result.append(f"Erase({scope}->{location}, {quoted(target.id)});")
            elif isinstance(target, ast.Subscript) and not isinstance(target.slice, ast.Slice):
                result.append(f"Erase({e(target.value)}, {e(target.slice)});")
            else:
                raise TypeError("unsupported native delete")
        return result
    if isinstance(node, ast.Global):
        return []
    if isinstance(node, ast.Import):
        return [
            c.lexical.write(item.asname or item.name, f"Builtin({quoted(item.name)})")
            for item in node.names
        ]
    if isinstance(node, ast.ImportFrom):
        if node.module == "__future__":
            return []
        assert node.module is not None
        names = {
            ("copy", "deepcopy"): "copy.deepcopy",
            ("time", "perf_counter"): "perf_counter",
            ("itertools", "permutations"): "permutations",
        }
        return [
            c.lexical.write(
                item.asname or item.name, f"Builtin({quoted(names[(node.module, item.name)])})"
            )
            for item in node.names
        ]
    if isinstance(node, ast.FunctionDef):
        value = c.function(node)
        for decorator in reversed(node.decorator_list):
            value = f"Call(c, {e(decorator)}, Arguments{{{{{value}}}, {{}}}})"
        result = [c.lexical.write(node.name, value)]
        if not c.lexical.module and not c.lexical.class_body:
            result.append(f"{scope}->definitions.push_back({quoted(node.name)});")
        return result
    if isinstance(node, ast.ClassDef):
        if len(node.bases) > 1 or node.keywords or node.decorator_list:
            raise TypeError("unsupported native class declaration")
        child_scope = c.program.temporary("cls")
        child = c.child(
            Lexical(
                local=bindings(node.body),
                captured=c.lexical.captured,
                class_name=node.name,
                class_body=True,
                cpp_scope=child_scope,
            )
        )
        base = e(node.bases[0]) if node.bases else "Value{}"
        return [
            f"auto {child_scope} = std::make_shared<Scope>();",
            f"{child_scope}->globals = {scope}->globals;",
            *child.block(node.body),
            c.lexical.write(
                node.name, f"Class({quoted(node.name)}, {base}, {child_scope}->locals)"
            ),
        ]
    raise TypeError(f"unsupported statement at {node.lineno}: {ast.dump(node)[:200]}")
