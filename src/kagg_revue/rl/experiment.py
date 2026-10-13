"""Training and evaluation orchestration for terminal-outcome RL."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.rl.config import RlSettings
from kagg_revue.rl.evaluate import evaluate_actor_critic
from kagg_revue.rl.train import resolve_rl_paths, train_actor_critic

RlCommand = Literal["run", "train", "evaluate"]


def _training_report(output_dir: Path) -> dict[str, object]:
    path = output_dir / "training-report.json"
    if not path.is_file():
        raise FileNotFoundError(f"RL training report does not exist: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("RL training report is not a mapping")
    return cast(dict[str, object], value)


def run_rl_experiment(
    raw_settings: RlSettings, repository_root: Path, command: RlCommand
) -> dict[str, object]:
    """Run an immutable RL training phase and/or its held-out evaluation."""
    settings = resolve_rl_paths(raw_settings, repository_root)
    if command in {"run", "train"}:
        training = train_actor_critic(settings, repository_root)
        if command == "train":
            return training
    else:
        if not settings.output_dir.is_dir():
            raise FileNotFoundError(f"RL run directory does not exist: {settings.output_dir}")
        training = _training_report(settings.output_dir)

    backend = load_backend(repository_root)
    evaluation = evaluate_actor_critic(settings, backend, training, repository_root)
    report_path = settings.output_dir / "report.json"
    if report_path.exists():
        raise FileExistsError(f"RL experiment report already exists: {report_path}")
    report: dict[str, object] = {
        "schema_version": "terminal-wdl-experiment-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": source_identity(repository_root),
        "resolved_settings": settings.model_dump(mode="json"),
        "training_report": {
            "path": str(settings.output_dir / "training-report.json"),
            "sha256": sha256_file(settings.output_dir / "training-report.json"),
        },
        "evaluation_report": {
            "path": str(settings.output_dir / "evaluation-report.json"),
            "sha256": sha256_file(settings.output_dir / "evaluation-report.json"),
        },
        "decision": evaluation["decision"],
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


__all__ = ["RlCommand", "run_rl_experiment"]
