"""Hydra command for frozen actor extraction, packaging, and validation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.submission.config import SubmissionAppSettings, SubmissionSettings
from kagg_revue.submission.evaluate import evaluate_submission
from kagg_revue.submission.package import build_submission


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[3]


def _settings(overrides: list[str]) -> SubmissionSettings:
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="submission_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return SubmissionAppSettings.model_validate(cast(dict[str, Any], value)).submission


def _path(path: Path, root: Path) -> Path:
    return (path if path.is_absolute() else root / path).resolve()


def _validate(settings: SubmissionSettings, root: Path) -> dict[str, object]:
    output_dir = _path(settings.output_dir, root)
    validation_dir = output_dir / "local-validation"
    if validation_dir.exists():
        raise FileExistsError(f"local submission validation already exists: {validation_dir}")
    temporary_root = root / "tmp"
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="submission-validation-", dir=temporary_root) as raw:
        subprocess.run(
            [
                sys.executable,
                str(output_dir / "kaggle-validation.py"),
                "--archive",
                str(output_dir / "submission.tar.gz"),
                "--output-dir",
                str(validation_dir),
                "--work-dir",
                str(Path(raw) / "work"),
                "--seed",
                str(settings.smoke.seed),
                "--act-timeout",
                str(settings.smoke.act_timeout_seconds),
                "--remaining-overage",
                str(settings.smoke.remaining_overage_seconds),
                "--run-timeout",
                str(settings.smoke.run_timeout_seconds),
            ],
            cwd=root,
            check=True,
        )
    value = json.loads(
        (validation_dir / "submission-validation-report.json").read_text(encoding="utf-8")
    )
    if not isinstance(value, dict):
        raise TypeError("local submission validation report must be a mapping")
    return cast(dict[str, object], value)


def main() -> None:
    """Build, validate, or evaluate one immutable Kaggle submission candidate."""
    parser = argparse.ArgumentParser(prog="kagg-revue-submission")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=("run", "build", "validate", "evaluate"),
    )
    arguments, overrides = parser.parse_known_args()
    settings = _settings(overrides)
    root = repository_root()
    if arguments.command == "build":
        result = build_submission(settings, root)
    elif arguments.command == "validate":
        result = _validate(settings, root)
    elif arguments.command == "evaluate":
        result = evaluate_submission(
            _path(settings.training_run, root),
            _path(settings.output_dir, root),
            root,
        )
    else:
        result = build_submission(settings, root)
        result = {"build": result, "validation": _validate(settings, root)}
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
