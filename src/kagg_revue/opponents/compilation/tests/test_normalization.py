"""Keep native normalization bound to the reviewed Python performance adapter."""

import ast
from pathlib import Path

import pytest

from kagg_revue.opponents.compilation.normalization import normalize
from kagg_revue.opponents.public import load_public_agent_manifest, resolve_public_agent_path


@pytest.mark.parametrize("version", [43, 45])
def test_normalization_accepts_exact_adapter_and_rejects_modified_source(version: int) -> None:
    """Remove only the reviewed copier; retain the strategy and fail on adapter drift."""
    day = 15 if version == 43 else 16
    manifest = Path(f"data/external/kaggriculture-notebook-survey-202609{day}/manifest.json")
    record = load_public_agent_manifest(manifest).by_id()[f"ahmed_v{version}"]
    source = resolve_public_agent_path(record, Path.cwd()).read_text()
    tree = ast.parse(source)
    assert normalize(tree, "none") is tree
    old = [ast.dump(node) for node in tree.body]
    normalized = normalize(tree, "v43-container-copy")
    retained = [ast.dump(node) for node in normalized.body]
    assert len(old) - len(retained) == 7
    assert all(node in old for node in retained)
    changed = ast.parse(source)
    assignment = next(
        node
        for node in changed.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "_R149_MISSING"
    )
    assignment.value = ast.Constant(value=None)
    with pytest.raises(ValueError, match="differs"):
        normalize(changed, "v43-container-copy")
    with pytest.raises(ValueError, match="absent"):
        normalize(ast.parse("agent = None"), "v43-container-copy")
