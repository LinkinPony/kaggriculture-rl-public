"""Recognize guarded fast paths while retaining every original function body."""

import ast


def specialization(node: ast.FunctionDef | ast.Lambda, *, capture: bool) -> str:
    """Match exact AST operations; names alone never select an implementation."""
    if capture or not isinstance(node, ast.FunctionDef):
        return "kNone"
    args = node.args
    if args.vararg or args.kwarg or args.kwonlyargs or args.posonlyargs:
        return "kNone"
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    names = [arg.arg for arg in args.args]
    if len(names) == 3 and len(args.defaults) == 1:
        value, key, default = names
        expected = ast.parse(
            f"if isinstance({value}, dict):\n    return {value}.get({key}, {default})"
        ).body[0]
        if body and ast.dump(body[0]) == ast.dump(expected):
            return "kDictGet"
    if len(names) == 2 and len(args.defaults) == 1:
        value, default = names
        expected_body = ast.parse(
            f"try:\n    return int({value})\nexcept (TypeError, ValueError):\n    return {default}"
        ).body
        if [ast.dump(item) for item in body] == [ast.dump(item) for item in expected_body]:
            return "kInteger"
    return "kNone"
