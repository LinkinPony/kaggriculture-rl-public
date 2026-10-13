"""Package an exact research controller as a standalone, attributed Python agent."""

import ast
import inspect
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, ConfigDict

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.opponents.public import (
    PublicAgentRecord,
    load_public_agent_manifest,
    resolve_public_agent_path,
)
from kagg_revue.opponents.research import market
from kagg_revue.opponents.research.settings import Variant


class _Names(ast.NodeTransformer):
    """Keep new helpers distinct from the upstream module's global symbols."""

    replacements = {
        "apply_market": "_research_market",
        "_priority": "_research_priority",
        "_INPUTS": "_RESEARCH_INPUTS",
    }

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Rename helper references while retaining all expression semantics."""
        node.id = self.replacements.get(node.id, node.id)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Rename only the new controller definitions."""
        node.name = self.replacements.get(node.name, node.name)
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.Assign:
        """Omit local type hints, which have no runtime effect, for the C++ compiler."""
        if node.value is None:
            raise ValueError("exported local declaration requires an initializer")
        return ast.copy_location(ast.Assign(targets=[node.target], value=node.value), node)


def source(record: PublicAgentRecord, variant: Variant) -> str:
    """Retain upstream source and append the exact new controller definitions."""
    base = resolve_public_agent_path(record, Path.cwd()).read_text()
    helper_sources = [inspect.getsource(market.apply_market), inspect.getsource(market._priority)]
    helpers = _Names().visit(ast.parse("\n".join(helper_sources)))
    ast.fix_missing_locations(helpers)
    lines = [
        base,
        "# Original local research: scheduled-sale advancement and market queue priority.",
        "# Upstream source and its attribution are retained above without strategy edits.",
        f"# Parent source SHA-256: {record.sha256}",
        "_RESEARCH_INPUTS = {'WHEAT', 'FERTILIZER'}",
        ast.unparse(helpers),
        "class _ResearchSettings:",
    ]
    lines.extend(f"    {name} = {value!r}" for name, value in variant.model_dump().items())
    lines.extend(f"{name} = {value!r}" for name, value in variant.globals.items())
    if variant.opening is not None:
        first, second, sale = variant.opening
        opening = [
            ["BUY_PRODUCT", "WHEAT", first],
            ["BUY_PRODUCT", "WHEAT", second],
            ["SELL", "WHEAT", sale],
        ]
        lines.extend(
            [
                f"_R42_OPENING = {opening!r}",
                "for _research_tape in _IMPL.chassis.routes.values():",
                "    _research_tape[0] = dict(_research_tape[0], "
                "market=[list(o) for o in _R42_OPENING])",
            ]
        )
    lines.extend(
        [
            "_RESEARCH_PARENT = agent",
            "_RESEARCH_COUNTERS = {}",
            "def agent(observation, configuration=None):",
            "    if int(observation['step']) == 0: _RESEARCH_COUNTERS.clear()",
            "    action = _RESEARCH_PARENT(observation, configuration)",
            "    return _research_market(observation, action, globals(), "
            "_ResearchSettings, _RESEARCH_COUNTERS)",
            "agent.telemetry = _RESEARCH_COUNTERS",
        ]
    )
    result = "\n\n".join(lines[:6]) + "\n" + "\n".join(lines[6:]) + "\n"
    ast.parse(result)
    return result


def export(record: PublicAgentRecord, variant: Variant, directory: Path) -> Path:
    """Write immutable source and provenance into a new local research artifact."""
    if not directory.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("research exports must remain under outputs")
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "main.py"
    path.write_text(source(record, variant))
    license_path = Path("src/kagg_revue/opponents/portfolios/LICENSE")
    (directory / "LICENSE").write_bytes(license_path.read_bytes())
    write_json(
        directory / "provenance.json",
        {
            "variant": variant.model_dump(mode="json"),
            "parent": record.model_dump(mode="json"),
            "main_sha256": digest(path),
            "controller_sha256": digest(Path(market.__file__)),
            "exporter_sha256": digest(Path(__file__)),
            "license_sha256": digest(license_path),
        },
    )
    return path


class Export(BaseModel):
    """Reproduce a standalone candidate from its authenticated parent and recipe."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest: Path
    variant: Variant
    directory: Path


@hydra.main(version_base=None, config_path="../../../../configs", config_name="script_export")
def main(configuration: DictConfig) -> None:
    """Export a fresh artifact while retaining the frozen incumbent bytes."""
    config = Export.model_validate(OmegaConf.to_container(configuration.export, resolve=True))
    record = load_public_agent_manifest(config.manifest).by_id()[config.variant.base]
    print(export(record, config.variant, config.directory))


if __name__ == "__main__":
    main()
