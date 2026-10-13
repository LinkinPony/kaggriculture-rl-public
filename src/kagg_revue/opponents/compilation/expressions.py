"""Translate the frozen policies' expression subset into C++ expressions."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from kagg_revue.opponents.compilation.model import Lexical, bindings, quoted

if TYPE_CHECKING:
    from kagg_revue.opponents.compilation.compiler import Compiler


def expression(c: Compiler, node: ast.expr) -> str:
    """Emit native expressions and reject unsupported syntax during generation."""
    e = c.expression
    if isinstance(node, ast.Constant):
        literal = node.value
        if literal is None:
            return "Value{}"
        if isinstance(literal, bool):
            return f"Value({'true' if literal else 'false'})"
        if isinstance(literal, int):
            return f"Value(int64_t{{{literal}}})"
        if isinstance(literal, float):
            return f"Value({literal!r})"
        if isinstance(literal, str):
            return f"Value({quoted(literal)})"
        raise TypeError(f"unsupported constant: {literal!r}")
    if isinstance(node, ast.Name):
        return c.lexical.read(node.id)
    if isinstance(node, ast.Attribute):
        return f"Attribute({e(node.value)}, {quoted(node.attr)})"
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Slice):
            parts = [
                e(x) if x is not None else "Value{}"
                for x in (node.slice.lower, node.slice.upper, node.slice.step)
            ]
            return f"Slice({e(node.value)}, {', '.join(parts)})"
        return f"Get({e(node.value)}, {e(node.slice)})"
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        kind = {ast.List: "List", ast.Tuple: "Tuple", ast.Set: "Set"}[type(node)]
        if not any(isinstance(x, ast.Starred) for x in node.elts):
            return f"{kind}({{{', '.join(e(x) for x in node.elts)}}})"
        temporary = c.program.temporary("args")
        statements = [f"Arguments {temporary};"]
        for value in node.elts:
            content = value.value if isinstance(value, ast.Starred) else value
            flag = "true" if isinstance(value, ast.Starred) else "false"
            statements.append(f"{temporary}.Add({e(content)}, {flag});")
        return (
            "([&]() -> Value { "
            + " ".join(statements)
            + f" return {kind}(std::move({temporary}.positional)); }}())"
        )
    if isinstance(node, ast.Dict):
        result = c.program.temporary("dict")
        statements = [f"auto {result} = Dict();"]
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                statements.append(f"Merge({result}, {e(value)});")
            else:
                k = c.program.temporary("key")
                statements.extend([f"auto {k} = {e(key)};", f"Put({result}, {k}, {e(value)});"])
        return "([&]() -> Value { " + " ".join(statements) + f" return {result}; }}())"
    if isinstance(node, ast.BinOp):
        left = c.program.temporary()
        return (
            f"([&]() -> Value {{ auto {left} = {e(node.left)}; "
            f"return Binary({quoted(type(node.op).__name__)}, {left}, {e(node.right)}); }}())"
        )
    if isinstance(node, ast.UnaryOp):
        return f"Unary({quoted(type(node.op).__name__)}, {e(node.operand)})"
    if isinstance(node, ast.BoolOp):
        temporary_value = c.program.temporary()
        statements = [f"auto {temporary_value} = {e(node.values[0])};"]
        for item in node.values[1:]:
            test = f"static_cast<bool>({temporary_value})"
            if isinstance(node.op, ast.And):
                test = "!" + test
            statements.extend(
                [f"if ({test}) return {temporary_value};", f"{temporary_value} = {e(item)};"]
            )
        return "([&]() -> Value { " + " ".join(statements) + f" return {temporary_value}; }}())"
    if isinstance(node, ast.Compare):
        left, right = c.program.temporary(), c.program.temporary()
        statements = [f"auto {left} = {e(node.left)};", f"Value {right};"]
        for op, item in zip(node.ops, node.comparators, strict=True):
            statements.extend(
                [
                    f"{right} = {e(item)};",
                    f"if (!static_cast<bool>(Binary({quoted(type(op).__name__)}, "
                    f"{left}, {right}))) return Value(false);",
                    f"{left} = {right};",
                ]
            )
        return "([&]() -> Value { " + " ".join(statements) + " return Value(true); }())"
    if isinstance(node, ast.IfExp):
        return f"(static_cast<bool>({e(node.test)}) ? {e(node.body)} : {e(node.orelse)})"
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
        return comprehension(c, node)
    if isinstance(node, ast.Lambda):
        return c.function(node)
    if isinstance(node, ast.JoinedStr):
        parts = [
            e(value)
            if not isinstance(value, ast.FormattedValue)
            else f"Value(Repr({e(value.value)}))"
            for value in node.values
        ]
        return "Value(" + " + ".join(f"{part}.string()" for part in parts) + ")"
    if isinstance(node, ast.Call):
        name = ast.unparse(node.func)
        if c.data.canonical(node.func) in {"json.loads", "zlib.decompress"}:
            return c.program.constant(c.data.value(node))
        if name == "globals" and not node.args:
            return f"{c.lexical.cpp_scope}->globals"
        if name == "super" and not node.args:
            if c.lexical.class_name is None:
                raise ValueError("super() outside a compiled class")
            return f"MakeSuper({c.lexical.read(c.lexical.class_name)}, {c.lexical.read('self')})"
        if (
            name in {"any", "all", "next"}
            and node.args
            and isinstance(node.args[0], ast.GeneratorExp)
        ):
            return comprehension(
                c,
                node.args[0],
                reduction=name,
                fallback=node.args[1] if len(node.args) == 2 else None,
            )
        function, arguments = c.program.temporary("fn"), c.program.temporary("args")
        dictionary_get = isinstance(node.func, ast.Attribute) and node.func.attr == "get"
        target = (
            f"PrepareDictionaryGet({e(node.func.value)})"
            if isinstance(node.func, ast.Attribute) and dictionary_get
            else e(node.func)
        )
        statements = [f"auto {function} = {target};", f"Arguments {arguments};"]
        if len(node.args) > 1:
            statements.append(f"{arguments}.positional.reserve({len(node.args)});")
        for item in node.args:
            content = item.value if isinstance(item, ast.Starred) else item
            flag = "true" if isinstance(item, ast.Starred) else "false"
            statements.append(f"{arguments}.Add({e(content)}, {flag});")
        for keyword in node.keywords:
            if keyword.arg is None:
                statements.append(f"{arguments}.ExpandKeywords({e(keyword.value)});")
            else:
                statements.append(
                    f"{arguments}.Keyword({quoted(keyword.arg)}, {e(keyword.value)});"
                )
        invoke = "CallDictionaryGet" if dictionary_get else "Call"
        return (
            "([&]() -> Value { "
            + " ".join(statements)
            + f" return {invoke}(c, {function}, std::move({arguments})); }}())"
        )
    raise TypeError(f"unsupported expression: {ast.dump(node)[:200]}")


def comprehension(
    c: Compiler,
    node: ast.ListComp | ast.SetComp | ast.DictComp | ast.GeneratorExp,
    *,
    reduction: str | None = None,
    fallback: ast.expr | None = None,
) -> str:
    """Compile generator short-circuiting as C++ loops, including next's fallback."""
    scope = c.program.temporary("comp")
    targets: list[ast.stmt] = [
        ast.Assign(targets=[g.target], value=ast.Constant(None)) for g in node.generators
    ]
    captured = c.lexical.captured | (set() if c.lexical.module else c.lexical.local)
    child = c.child(
        Lexical(local=bindings(targets), captured=captured, cpp_scope=scope, slotted=True)
    )
    result = c.program.temporary("result")
    initial = "Dict()" if isinstance(node, ast.DictComp) else "List()"
    statements = [
        f"auto {scope} = std::make_shared<Scope>();",
        f"{scope}->globals = {c.lexical.cpp_scope}->globals;",
        f"{scope}->parent = {c.lexical.cpp_scope};",
        *child.lexical.prepare(),
        f"auto {result} = {initial};",
    ]
    if fallback is not None:
        statements.append(f"auto fallback = {c.expression(fallback)};")
    for index, generator in enumerate(node.generators):
        if generator.is_async:
            raise TypeError("asynchronous policy comprehensions are unsupported")
        value = c.program.temporary("item")
        iterable = c.expression(generator.iter) if index == 0 else child.expression(generator.iter)
        statements.append(f"for (const auto& {value} : Iterate({iterable})) {{")
        statements.extend(child.assign(generator.target, value))
        for filter_node in generator.ifs:
            statements.append(f"if (!static_cast<bool>({child.expression(filter_node)})) continue;")
    if isinstance(node, ast.DictComp):
        statements.append(
            f"Put({result}, {child.expression(node.key)}, {child.expression(node.value)});"
        )
    else:
        element = child.expression(node.elt)
        if reduction == "next":
            statements.append(f"return {element};")
        elif reduction in {"any", "all"}:
            condition = f"static_cast<bool>({element})"
            if reduction == "all":
                condition = "!" + condition
            statements.append(
                f"if ({condition}) return Value({'true' if reduction == 'any' else 'false'});"
            )
        else:
            statements.append(f"{result}.node()->sequence.push_back({element});")
    statements.extend("}" for _ in node.generators)
    if reduction == "next":
        statements.append(
            "return fallback;"
            if fallback is not None
            else 'throw Error("StopIteration", "generator exhausted");'
        )
    elif reduction in {"any", "all"}:
        statements.append(f"return Value({'true' if reduction == 'all' else 'false'});")
    elif isinstance(node, ast.SetComp):
        statements.append(f"return Set({result}.node()->sequence);")
    else:
        statements.append(f"return {result};")
    return "([&]() -> Value { " + " ".join(statements) + " }())"
