"""Reproducible ahead-of-time source translation and authenticated asset output."""

import ast
import hashlib
import json
import re
import zlib
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.opponents.compilation.compiler import Compiler
from kagg_revue.opponents.compilation.model import Lexical, Program
from kagg_revue.opponents.compilation.normalization import normalize
from kagg_revue.opponents.compilation.sources import CANDIDATES, ExtraSource
from kagg_revue.opponents.public import load_public_agent_manifest, resolve_public_agent_path

_PREFIX = (
    "// Generated from authenticated public notebook source; do not edit.\n"
    '#include "opponents/compiled/generated/declarations.hpp"\n'
    "\nnamespace kagg::opponents::compiled {\n"
)


def _write(path: Path, text: str) -> None:
    """Leave identical translation units untouched for incremental native builds."""
    if not path.exists() or path.read_text() != text:
        path.write_text(text)


def generate(
    manifest: Path,
    destination: Path,
    assets: Path,
    additions: dict[str, ExtraSource] | None = None,
) -> dict[str, Any]:
    """Share identical function bodies while preserving every candidate's globals."""
    records = load_public_agent_manifest(manifest).by_id()
    program = Program()
    compiler = Compiler(program, Lexical(module=True))
    entries: dict[str, str] = {}
    data_indices: dict[str, range] = {}
    source_hashes: dict[str, str] = {}
    normalizations: dict[str, dict[str, str]] = {}
    for candidate in CANDIDATES:
        record = records.get(candidate.agent_id) or records[candidate.survey_id]
        first_constant = len(program.constants)
        if record.sha256 != candidate.sha256:
            raise ValueError(f"unreviewed source for {candidate.agent_id}")
        expected_entrypoint = "agent" if candidate.entrypoint == "agent" else "last_callable"
        if record.entrypoint != expected_entrypoint:
            raise ValueError(f"unreviewed entrypoint for {candidate.agent_id}")
        path = resolve_public_agent_path(record, Path.cwd())
        tree = normalize(ast.parse(path.read_text()), candidate.normalization)
        if candidate.entrypoint != "agent":
            tree.body.extend(ast.parse(f"_native_entrypoint = {candidate.entrypoint}").body)
        entries[candidate.agent_id] = compiler.module_code(tree, candidate.agent_id)
        data_indices[candidate.agent_id] = range(first_constant, len(program.constants))
        source_hashes[candidate.agent_id] = candidate.sha256
        if candidate.normalization != "none":
            normalizations[candidate.agent_id] = {
                "mode": candidate.normalization,
                "normalized_ast_sha256": hashlib.sha256(
                    ast.dump(tree, include_attributes=False).encode()
                ).hexdigest(),
            }
    public_constants = len(program.constants)
    public_ids = set(entries)
    for name, extra in (additions or {}).items():
        if (
            name in entries
            or not name
            or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_" for c in name)
        ):
            raise ValueError(f"invalid or duplicated extra strategy identity: {name}")
        path = extra.path.resolve()
        allowed = [(Path.cwd() / directory).resolve() for directory in ("src", "outputs")]
        if not any(path.is_relative_to(root) for root in allowed) or digest(path) != extra.sha256:
            raise ValueError(f"unverified local research source: {name}")
        first_constant = len(program.constants)
        tree = normalize(ast.parse(path.read_text()), extra.normalization)
        entries[name] = compiler.module_code(tree, name)
        data_indices[name] = range(first_constant, len(program.constants))
        source_hashes[name] = extra.sha256
        normalizations[name] = {
            "mode": extra.normalization,
            "normalized_ast_sha256": hashlib.sha256(
                ast.dump(tree, include_attributes=False).encode()
            ).hexdigest(),
        }
    destination.mkdir(parents=True, exist_ok=True)
    expected: set[str] = {"declarations.hpp", "entry.cpp"}
    for name, body in sorted(program.functions.items()):
        filename = f"{name.lower()}.cpp"
        expected.add(filename)
        _write(
            destination / filename,
            ('#include "opponents/compiled/forecast.hpp"\n' if "Forecast(c, s)" in body else "")
            + ('#include "opponents/compiled/typed.hpp"\n' if "Typed" in body else "")
            + _PREFIX
            + body
            + "}  // namespace kagg::opponents::compiled\n",
        )
    for old in destination.glob("*.cpp"):
        if old.name not in expected:
            old.unlink()
    declarations = [
        "// Generated native policy function declarations.\n#pragma once\n"
        '#include "opponents/compiled/runtime.hpp"\n'
        '#include "opponents/compiled/inputs.hpp"\nnamespace kagg::opponents::compiled {'
    ]
    declarations.extend(
        f"Value {name}(Context&, const ScopePtr&);" for name in sorted(program.declarations)
    )
    declarations.extend(["Value Initialize(const std::string&, Context&, Value);", "}\n"])
    _write(destination / "declarations.hpp", "\n".join(declarations))
    entry = [
        "Value Initialize(const std::string& kind, Context& c, Value globals) {",
        "auto scope = Module(globals);",
    ]
    entry.extend(
        f'if (kind == "{name}") return {code}(c, scope);' for name, code in entries.items()
    )
    entry.extend(['throw PortError("unknown compiled policy");', "}"])
    _write(destination / "entry.cpp", _PREFIX + "\n".join(entry) + "\n}\n")
    assets.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, source_sha256 in source_hashes.items():
        # Keep every existing public asset byte-identical when appending research.
        # The original five portfolios share the original constant prefix. Keep
        # their archived bytes stable when new public strategies are appended.
        original_ids = {candidate.agent_id for candidate in CANDIDATES[:5]}
        original_count = data_indices[CANDIDATES[4].agent_id].stop
        count = (
            original_count
            if name in original_ids
            else public_constants
            if name in public_ids
            else len(program.constants)
        )
        pending = [entries[name]]
        visited: set[str] = set()
        needed: set[int] = set()
        while pending:
            function = pending.pop()
            if function in visited:
                continue
            visited.add(function)
            body = program.functions[function]
            needed.update(map(int, re.findall(r"c\.constants\.at\((\d+)\)", body)))
            pending.extend(re.findall(r"\b(?:Code|Init)_[0-9a-f]{20}\b", body))
        payload = {
            "agent_id": name,
            "source_sha256": source_sha256,
            "constants": [
                value if i in needed else None for i, value in enumerate(program.constants[:count])
            ],
            "routes": [],
        }
        packed = zlib.compress(json.dumps(payload, separators=(",", ":")).encode(), 9)
        (assets / f"{name}.json.zlib").write_bytes(packed)
        hashes[name] = hashlib.sha256(packed).hexdigest()
    return {
        "functions": len(program.functions),
        "constants": len(program.constants),
        "asset_sha256": hashes,
        "source_sha256": source_hashes,
        "normalizations": normalizations,
    }
