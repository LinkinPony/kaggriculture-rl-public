"""Authenticated official interpreter for independent native and replay audits."""

import ast
import importlib.util
import json
import random
import sys
import types
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest


class Record(dict[str, Any]):
    """Minimal mapping/attribute protocol used by the official interpreter."""

    def __getattr__(self, name: str) -> Any:
        """Expose mapping keys as framework fields."""
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def __setattr__(self, name: str, value: Any) -> None:
        """Store mutations in the shared observation mapping."""
        self[name] = value


def load_reference(directory: Path) -> Any:
    """Load and authenticate the pinned interpreter and its minimal framework helper."""
    manifest = json.loads((directory / "manifest.json").read_text())
    wheel = directory / manifest["wheel"]
    if digest(wheel) != manifest["wheel_sha256"]:
        raise ValueError("official reference wheel fingerprint changed")
    with zipfile.ZipFile(wheel) as archive:
        source = archive.read("kaggle_environments/utils.py").decode()
        node = next(
            node
            for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef) and node.name == "resolve_episode_seed"
        )
        helper = types.ModuleType("kaggle_environments.utils")
        helper.__dict__.update({"Any": Any, "Callable": Callable, "random": random})
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(wheel), "exec"), helper.__dict__)
        sys.modules["kaggle_environments.utils"] = helper
        for filename in ("kaggriculture.py", "kaggriculture.json"):
            content = archive.read(f"kaggle_environments/envs/kaggriculture/{filename}")
            target = directory / filename
            if not target.exists():
                target.write_bytes(content)
            elif target.read_bytes() != content:
                raise ValueError("extracted official reference changed")
    spec = importlib.util.spec_from_file_location(
        "production_official_reference", directory / "kaggriculture.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen official interpreter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OfficialGame:
    """Run the pinned interpreter with an explicit framework step counter."""

    def __init__(self, module: Any, configuration: dict[str, Any], seed: int) -> None:
        """Initialize both public and private seats from the declared official seed."""
        self.module = module
        self.step_index = 0
        self.state = [
            Record(observation=Record(player=seat, step=0), status="ACTIVE", action={})
            for seat in (0, 1)
        ]
        self.environment = Record(
            configuration=Record(**{**configuration, "seed": seed}), info={}, done=False
        )
        module.interpreter(self.state, self.environment)

    def step(self, actions: list[Any]) -> None:
        """Apply one simultaneous official action pair and advance the frame clock."""
        for state, action in zip(self.state, actions, strict=True):
            state.action = action
            state.observation.step = self.step_index
        self.module.interpreter(self.state, self.environment)
        self.step_index += 1
        for state in self.state:
            state.observation.step = self.step_index

    def observation(self, seat: int) -> dict[str, Any]:
        """Return a top-level view whose inventory mappings retain live engine order."""
        return dict(self.state[seat].observation)
