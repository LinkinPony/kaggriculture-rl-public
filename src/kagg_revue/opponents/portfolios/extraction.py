"""Extract literal route data without executing downloaded Python code."""

import ast
import base64
import hashlib
import json
import zlib
from pathlib import Path
from typing import Any

from kagg_revue.opponents.portfolios.catalog import LEGACY_SOURCES
from kagg_revue.opponents.public import load_public_agent_manifest, resolve_public_agent_path


class Literals:
    """Evaluate only data literals, aliases, and explicit decoding operations."""

    def __init__(self, source: str) -> None:
        """Index assignments, retaining the original Python expressions."""
        self.assignments: dict[str, ast.expr] = {}
        for node in ast.parse(source).body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.assignments[target.id] = node.value

    def named(self, name: str) -> Any:
        """Decode one named constant."""
        return self.value(self.assignments[name])

    def value(self, node: ast.expr) -> Any:
        """Reject every operation other than the bounded data-only allowlist."""
        if isinstance(node, ast.Name):
            return self.named(node.id)
        if isinstance(node, (ast.List, ast.Tuple)):
            return [self.value(element) for element in node.elts]
        if isinstance(node, ast.Call) and not node.keywords:
            name = ast.unparse(node.func)
            if len(node.args) == 1:
                argument = self.value(node.args[0])
                if name == "base64.b85decode":
                    return base64.b85decode(argument)
                if name == "base64.b64decode":
                    return base64.b64decode(argument, validate=True)
                if name == "zlib.decompress":
                    return zlib.decompress(argument)
                if name == "json.loads":
                    return json.loads(argument)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "decode":
                encoding = ast.literal_eval(node.args[0]) if node.args else "utf-8"
                return self.value(node.func.value).decode(encoding)
        return ast.literal_eval(node)


def _extract(agent_id: str, source: str, directory: Path) -> dict[str, Any]:
    if agent_id == "shop_router_0909":
        routes = json.loads((directory / "actions.json").read_text())
        if len(routes) != 13 or any(len(route) != 719 for route in routes):
            raise ValueError("Shop Router 0909 requires 13 complete action tapes")
        return {"routes": routes}
    if agent_id == "shop_router_0908":
        from kagg_revue.opponents.portfolios.shop import extract_shop_router

        return extract_shop_router(directory)
    literals = Literals(source)
    if agent_id == "router_95":
        assignment = next(
            node
            for node in ast.parse(source).body
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Tuple)
        )
        routes, policy = literals.value(assignment.value)
        return {"routes": routes, "policy": policy}
    if agent_id == "boatlee_v29":
        return {"routes": [literals.named("_ACTIONS")]}
    if agent_id == "farming_v4":
        blob = json.loads(zlib.decompress(base64.b64decode(literals.named("_BLOB"))))
        routes = {blob["main"]: blob["full"]}
        for tail in blob["tails"]:
            routes[tail["h"]] = routes[tail["parent"]][: tail["at"]] + tail["suffix"]
        names = [literals.named(name) for name in ("MAIN", "YARN", "YARN_CARROT", "MILK_GLUT")]
        result = [routes[name] for name in names]
        prefixes = [
            [
                next(
                    (i for i, (a, b) in enumerate(zip(left, right, strict=True)) if a != b),
                    len(left),
                )
                for right in result
            ]
            for left in result
        ]
        return {"routes": result, "prefixes": prefixes}
    if agent_id == "kaito_v58":
        pairs = literals.named("_V58_POLICY_ROUTES")
        return {"routes": [route for _, route in pairs], "names": [name for name, _ in pairs]}
    raise ValueError(f"unknown source: {agent_id}")


def extract(manifest: Path, destination: Path) -> dict[str, str]:
    """Write reproducible compressed route assets bound to reviewed source hashes."""
    records = load_public_agent_manifest(manifest).by_id()
    destination.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for spec in LEGACY_SOURCES:
        if spec.agent_id not in records:
            continue  # Historical four-opponent manifests remain extractable.
        record = records[spec.agent_id]
        if (record.sha256, record.notebook_ref, record.files) != (
            spec.sha256,
            spec.notebook_ref,
            dict(spec.files),
        ):
            raise ValueError(f"unexpected source identity for {spec.agent_id}")
        path = resolve_public_agent_path(record, Path.cwd())
        data = _extract(spec.agent_id, path.read_text(), path.parent)
        data.update(agent_id=spec.agent_id, source_sha256=spec.sha256)
        raw = json.dumps(data, separators=(",", ":"), sort_keys=True).encode()
        packed = zlib.compress(raw, 9)
        (destination / f"{spec.agent_id}.json.zlib").write_bytes(packed)
        hashes[spec.agent_id] = hashlib.sha256(packed).hexdigest()
    return hashes
