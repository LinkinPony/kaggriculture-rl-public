"""Legacy workflow provenance and shared artifact compatibility imports."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.production.config import Settings

__all__ = ["digest", "write_json", "load_policy", "save_policy", "provenance"]


def provenance(settings: Settings) -> dict[str, Any]:
    """Bind source, native binary, resolved profile and source-authenticated opponents."""
    from kagg_revue.native import _revue_native

    source_root = Path(__file__).resolve().parents[3]
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source_root, text=True
    ).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=source_root, text=True)
    patch = subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=source_root)
    manifest_path = Path("data/external/kaggriculture-public-notebooks-2026-08-28/manifest.json")
    names = {*settings.opponents, *settings.ppo.script_opponents} - {"pass"}
    if settings.bc.source_kind == "teacher" and (
        settings.mode in {"generate", "audit", "bc"} or settings.checkpoint is None
    ):
        names.add("kaito_v48")
    # Neural-only runs have no dependency on a notebook manifest or teacher bytes.
    manifest = json.loads(manifest_path.read_text()) if names else {"agents": []}
    identities = [record for record in manifest["agents"] if record["agent_id"] in names]
    for record in identities:
        path = Path(record["main_path"])
        if digest(path) != record["sha256"]:
            raise ValueError(f"opponent source fingerprint changed: {path}")
    return {
        "revision": revision,
        "clean": not bool(status),
        "status": status,
        "tracked_diff_sha256": hashlib.sha256(patch).hexdigest(),
        "native_sha256": digest(Path(_revue_native.__file__)),
        "historical_opponent": {
            "path": str(settings.ppo.history.checkpoint),
            "sha256": digest(settings.ppo.history.checkpoint),
        }
        if settings.ppo.history is not None
        else None,
        "evaluation_policies": [
            {"path": str(path), "sha256": digest(path)} for path in settings.evaluation_policies
        ],
        "profile": settings.model_dump(mode="json"),
        "opponents": identities,
    }
