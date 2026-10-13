"""End-to-end behavior-cloning orchestration and provenance."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from kagg_revue.bc.config import ExperimentSettings, ModelSettings
from kagg_revue.bc.dataset import SequenceDataset, sha256_file, write_dataset_identity
from kagg_revue.bc.evaluate import evaluate_policy
from kagg_revue.bc.train import train_policy
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity

Command = Literal["run", "train", "evaluate"]


def _resolve(root: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def resolve_paths(settings: ExperimentSettings, root: Path) -> ExperimentSettings:
    """Resolve operational paths against the repository."""
    return settings.model_copy(
        update={
            "dataset_dir": _resolve(root, settings.dataset_dir),
            "public_agent_manifest": _resolve(root, settings.public_agent_manifest),
            "output_dir": _resolve(root, settings.output_dir),
            "resume_checkpoint": (
                None
                if settings.resume_checkpoint is None
                else _resolve(root, settings.resume_checkpoint)
            ),
            "initial_actor": (
                None
                if settings.initial_actor is None
                else _resolve(root, settings.initial_actor)
            ),
        }
    )


def _prepare_output(settings: ExperimentSettings, root: Path) -> None:
    output_root = (root / "outputs").resolve()
    if not settings.output_dir.is_relative_to(output_root):
        raise ValueError(f"experiment output must be under {output_root}")
    if settings.output_dir.exists():
        raise FileExistsError(f"experiment output already exists: {settings.output_dir}")
    settings.output_dir.mkdir(parents=True)


def _load_training_report(output_dir: Path) -> dict[str, object]:
    value = json.loads((output_dir / "training-report.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("training report is not a mapping")
    return cast(dict[str, object], value)


def _validate_dataset_abi(
    dataset: SequenceDataset,
    backend: BackendApi,
    settings: ExperimentSettings,
) -> None:
    manifest = dataset.manifest
    encoder = backend.actor_encoder_spec()
    if manifest.actor_encoder_version != str(encoder["version"]):
        raise ValueError("dataset and native observation encoder versions differ")
    if (
        manifest.board_shape[1] != int(encoder["board_channels"])
        or manifest.unit_shape[2] != int(encoder["unit_feat"])
        or manifest.global_features != int(encoder["global_feat"])
    ):
        raise ValueError("dataset and native observation tensor shapes differ")
    native_keys = tuple(str(key) for key in backend.action_codec_spec()["keys"])
    dataset_keys = (*manifest.unit_candidate_keys, *manifest.market_candidate_keys)
    if dataset_keys != native_keys:
        raise ValueError("dataset and native action codec vocabularies differ")
    fact_spec = backend.derived_fact_spec()
    dataset_fact_contract = (
        manifest.derived_fact_version,
        manifest.turn_fact_features,
        manifest.prefix_fact_features,
        manifest.candidate_fact_features,
    )
    native_fact_contract = (
        str(fact_spec["version"]),
        int(fact_spec["turn_features"]),
        int(fact_spec["prefix_features"]),
        int(fact_spec["candidate_features"]),
    )
    if manifest.derived_fact_version is not None and (
        dataset_fact_contract != native_fact_contract
    ):
        raise ValueError("dataset and native derived-fact contracts differ")
    if manifest.unit_limit != settings.unit_limit:
        raise ValueError("dataset and experiment unit limits differ")
    resolved = backend.engine(seed=0, configuration=dict(settings.environment)).configuration
    board_size = int(resolved["boardSize"])
    if manifest.board_shape[2:] != (board_size, board_size):
        raise ValueError("dataset and resolved environment board shapes differ")


def _validate_training_profile(training: dict[str, object], model_settings: ModelSettings) -> None:
    architecture = training.get("architecture")
    if not isinstance(architecture, dict):
        raise ValueError("training report lacks the resolved actor architecture")
    for name, expected in model_settings.model_dump(mode="json").items():
        if architecture.get(name) != expected:
            raise ValueError(f"evaluation model setting differs from the actor artifact: {name}")


def _decision(evaluation: dict[str, object]) -> dict[str, object]:
    """Expose direct evidence without automatically promoting a checkpoint."""
    selection = evaluation.get("selection")
    if not isinstance(selection, dict):
        raise ValueError("evaluation report lacks selection results")
    candidate = selection.get("turn_policy")
    if not isinstance(candidate, dict):
        raise ValueError("selection result lacks the turn policy")
    return {
        "status": "review",
        "selection_wins": candidate["wins"],
        "selection_ties": candidate["ties"],
        "selection_losses": candidate["losses"],
        "promotion_authority": False,
        "reason": "a clean revision and frozen confirmation decision are still required",
    }


def run_experiment(
    model_settings: ModelSettings,
    settings: ExperimentSettings,
    repository_root: Path,
    command: Command,
) -> dict[str, object]:
    """Train and/or evaluate one immutable experiment directory."""
    settings = resolve_paths(settings, repository_root)
    backend = load_backend(repository_root)
    if command in {"run", "train"}:
        dataset = SequenceDataset(
            settings.dataset_dir,
            settings.split_seed,
            settings.train_fraction,
            settings.validation_fraction,
        )
        _validate_dataset_abi(dataset, backend, settings)
        _prepare_output(settings, repository_root)
        source = source_identity(repository_root)
        resolved = {
            "source": source,
            "model": model_settings.model_dump(mode="json"),
            "experiment": settings.model_dump(mode="json"),
        }
        (settings.output_dir / "resolved-settings.json").write_text(
            json.dumps(resolved, indent=2, sort_keys=True), encoding="utf-8"
        )
        write_dataset_identity(dataset, settings.output_dir / "dataset-identity.json")
        training = train_policy(
            model_settings,
            settings,
            dataset,
            settings.output_dir,
            source,
        )
        if command == "train":
            return training
    else:
        if not settings.output_dir.is_dir():
            raise FileNotFoundError(f"experiment output does not exist: {settings.output_dir}")
        training = _load_training_report(settings.output_dir)

    _validate_training_profile(training, model_settings)

    evaluation = evaluate_policy(settings, backend, training, settings.output_dir)
    report: dict[str, object] = {
        "schema_version": "turn-policy-experiment-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": source_identity(repository_root),
        "resolved_settings": {
            "model": model_settings.model_dump(mode="json"),
            "experiment": settings.model_dump(mode="json"),
        },
        "training_report": {
            "path": str(settings.output_dir / "training-report.json"),
            "sha256": sha256_file(settings.output_dir / "training-report.json"),
        },
        "evaluation_report": {
            "path": str(settings.output_dir / "evaluation-report.json"),
            "sha256": sha256_file(settings.output_dir / "evaluation-report.json"),
        },
        "decision": _decision(evaluation),
    }
    (settings.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


__all__ = ["Command", "resolve_paths", "run_experiment", "source_identity"]
