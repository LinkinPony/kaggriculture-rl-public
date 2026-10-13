"""Load unmodified official runner modules without importing unrelated environments."""

import hashlib
import importlib
import json
import sys
import types
import zipfile
from pathlib import Path
from typing import Any

FRAMEWORK_FILES = (
    "agent.py",
    "core.py",
    "errors.py",
    "utils.py",
    "schemas.json",
    "status_codes.json",
    "envs/kaggriculture/kaggriculture.py",
    "envs/kaggriculture/kaggriculture.json",
)


def prepare_framework(reference: Path, destination: Path) -> dict[str, Any]:
    """Authenticate the original wheel and extract only explicitly named modules."""
    manifest = json.loads((reference / "manifest.json").read_text())
    wheel = reference / manifest["wheel"]
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != manifest["wheel_sha256"]:
        raise ValueError("official framework wheel identity differs")
    files = {}
    with zipfile.ZipFile(wheel) as archive:
        for name in FRAMEWORK_FILES:
            content = archive.read(f"kaggle_environments/{name}")
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            files[name] = hashlib.sha256(content).hexdigest()
    return {
        "version": manifest["version"],
        "wheel_sha256": manifest["wheel_sha256"],
        "files": files,
    }


def load_framework(directory: Path, version: str) -> Any:
    """Load the exact Agent and Environment implementations with a minimal registry."""
    if any(
        name == "kaggle_environments" or name.startswith("kaggle_environments.")
        for name in sys.modules
    ):
        raise RuntimeError("official framework must load into a fresh module namespace")
    package = types.ModuleType("kaggle_environments")
    package.__path__ = [str(directory)]
    package.__dict__["__version__"] = version
    sys.modules[package.__name__] = package
    core = importlib.import_module("kaggle_environments.core")
    environment = importlib.import_module("kaggle_environments.envs.kaggriculture.kaggriculture")
    core.register(
        "kaggriculture",
        {
            "interpreter": environment.interpreter,
            "renderer": environment.renderer,
            "html_renderer": environment.html_renderer,
            "specification": environment.specification,
            "agents": environment.agents,
        },
    )
    return core
