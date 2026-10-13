"""Export an independently authored, standard-library-only executable opponent."""

import ast
import json
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, ConfigDict

from kagg_revue.artifacts.io import digest, write_json


class Export(BaseModel):
    """Bind one standalone source to a frozen independent controller recipe."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    incumbent: Path
    directory: Path


def source(settings: dict[str, Any], configuration: dict[str, Any]) -> tuple[str, dict[str, str]]:
    """Inline only our own rule model, finance, task and scheduling implementations."""
    root = Path(__file__).parent
    hashes = {}
    parts = ["# Enterprise P1: independently authored economic farm director."]
    for name in ("economy", "tasks", "territories", "finance", "agent"):
        path = root / f"{name}.py"
        hashes[name] = digest(path)
        tree = ast.parse(path.read_text())
        tree.body = [
            node
            for node in tree.body
            if not (
                isinstance(node, ast.ImportFrom) and (node.module or "").startswith("kagg_revue")
            )
        ]
        parts.append(ast.unparse(tree))
    parts.extend(
        [
            f"_ENTERPRISE_SETTINGS = {settings!r}",
            f"_ENTERPRISE_CONFIGURATION = {configuration!r}",
            "_ENTERPRISE_POLICIES = {}",
            "def agent(observation, configuration=None):",
            "    player = observation['player']",
            "    if observation['step'] == 0 or player not in _ENTERPRISE_POLICIES:",
            "        _ENTERPRISE_POLICIES[player] = Director("
            "dict(configuration or _ENTERPRISE_CONFIGURATION), _ENTERPRISE_SETTINGS)",
            "    return _ENTERPRISE_POLICIES[player].act(observation)",
        ]
    )
    result = "\n\n".join(parts[:6]) + "\n" + "\n".join(parts[6:]) + "\n"
    ast.parse(result)
    return result, hashes


def export(config: Export) -> Path:
    """Freeze an exact recipe and its complete original source in a new output directory."""
    from kagg_revue.native import _revue_native as native

    if not config.directory.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("independent research exports must remain under outputs")
    settings = json.loads(config.incumbent.read_text())["settings"]
    program, hashes = source(settings, dict(native.Engine(1, {}).configuration))
    config.directory.mkdir(parents=True, exist_ok=False)
    path = config.directory / "main.py"
    path.write_text(program)
    write_json(
        config.directory / "provenance.json",
        {
            "name": "enterprise_p1",
            "settings": settings,
            "source_sha256": hashes,
            "main_sha256": digest(path),
            "notebook_parent": None,
            "incumbent": str(config.incumbent),
            "incumbent_sha256": digest(config.incumbent),
            "scope": "Independent Python prototype; standard 10x10, 30-day contest environment.",
        },
    )
    return path


@hydra.main(version_base=None, config_path="../../../../configs", config_name="enterprise_export")
def main(configuration: DictConfig) -> None:
    """Produce a fresh standalone artifact from a declared research incumbent."""
    config = Export.model_validate(OmegaConf.to_container(configuration.export, resolve=True))
    print(export(config))


if __name__ == "__main__":
    main()
