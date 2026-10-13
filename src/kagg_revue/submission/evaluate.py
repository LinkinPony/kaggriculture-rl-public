"""Closed-loop promotion evaluation for one frozen submission actor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.rl.config import RlSettings
from kagg_revue.rl.evaluate import evaluate_actor_critic


def evaluate_submission(
    training_run: Path,
    submission_dir: Path,
    repository_root: Path,
) -> dict[str, object]:
    """Evaluate the frozen actor against its initial actor and notebook ladder."""
    repository_root = repository_root.resolve()
    training_run = training_run.resolve()
    submission_dir = submission_dir.resolve()
    evaluation_dir = submission_dir / "evaluation"
    if evaluation_dir.exists():
        raise FileExistsError(f"submission evaluation already exists: {evaluation_dir}")
    build_report_path = submission_dir / "build-report.json"
    build_report = json.loads(build_report_path.read_text(encoding="utf-8"))
    if not isinstance(build_report, dict):
        raise TypeError("submission build report must be a mapping")
    current_source = source_identity(repository_root)
    build_source = build_report.get("source")
    if build_source != current_source or current_source["worktree_dirty"]:
        raise ValueError("submission evaluation source differs from its clean build revision")
    snapshot = build_report.get("snapshot")
    if not isinstance(snapshot, dict):
        raise TypeError("submission build report lacks its actor snapshot")
    initial_actor = snapshot.get("initial_actor")
    if not isinstance(initial_actor, dict):
        raise TypeError("submission build report lacks its initial actor identity")
    actor_path = submission_dir / "actor.pt"
    if not actor_path.is_file():
        raise FileNotFoundError(f"submission actor snapshot does not exist: {actor_path}")
    actor_sha256 = sha256_file(actor_path)
    if actor_sha256 != snapshot.get("sha256"):
        raise ValueError("submission actor snapshot differs from its build report")

    resolved = json.loads((training_run / "resolved-settings.json").read_text(encoding="utf-8"))
    if not isinstance(resolved, dict) or not isinstance(resolved.get("rl"), dict):
        raise TypeError("training run lacks resolved RL settings")
    settings = RlSettings.model_validate(cast(dict[str, Any], resolved["rl"]))
    settings = settings.model_copy(update={"output_dir": evaluation_dir})
    evaluation_dir.mkdir()
    training_report: dict[str, object] = {
        "source": build_source,
        "actor_artifact": {
            "path": str(actor_path),
            "sha256": actor_sha256,
            "size_bytes": actor_path.stat().st_size,
        },
        "initial_actor": initial_actor,
    }
    return evaluate_actor_critic(
        settings,
        load_backend(repository_root),
        training_report,
        repository_root,
    )


__all__ = ["evaluate_submission"]
