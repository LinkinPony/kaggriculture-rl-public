"""Validated settings for atomic-effect teacher data and behavior cloning."""

from __future__ import annotations

import re
from pathlib import Path

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.rl.effects.config import EffectModelSettings
from kagg_revue.teacher.config import SubmissionArtifactSettings


def _repository_path(path: Path, root: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != root:
        raise ValueError(f"{name} must be repository-relative under {root}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


def _validate_environment(environment: dict[str, object], name: str) -> None:
    for field, minimum in {
        "boardSize": 1,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 1,
    }.items():
        value = environment.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            raise ValueError(f"{name} environment {field} is invalid")


class EffectTeacherDataSettings(BaseModel):
    """One provenance-bound atomic-effect demonstration dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    teacher: SubmissionArtifactSettings
    submission_record_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    output_dir: Path
    report_dir: Path
    seed_start: int = Field(ge=0)
    games: int = Field(gt=0)
    games_per_shard: int = Field(gt=0)
    process_workers: int = Field(gt=0)
    native_workers: int = Field(gt=0)
    compression_level: int = Field(ge=0, le=9)
    unit_limit: int = Field(gt=0, le=255)
    maximum_quantity: int = Field(gt=0)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_generation(self) -> EffectTeacherDataSettings:
        """Reject escaped outputs and values outside native integer bounds."""
        _repository_path(self.output_dir, "data", "effect teacher dataset")
        if self.output_dir.parts[:2] != ("data", "external"):
            raise ValueError("effect teacher dataset must be under data/external/")
        _repository_path(self.report_dir, "outputs", "effect teacher report")
        if self.seed_start + self.games - 1 > 2**63 - 1:
            raise ValueError("effect teacher seed range exceeds the native int64 ABI")
        if self.games_per_shard > self.games:
            raise ValueError("effect teacher shard cannot contain more games than the dataset")
        _validate_environment(self.environment, "effect teacher")
        return self


class EffectTeacherDataAppSettings(BaseModel):
    """Hydra root for atomic-effect teacher data generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    effect_teacher_data: EffectTeacherDataSettings


class EffectCorrectionDataSettings(BaseModel):
    """Rank8 labels on complete rollouts from one frozen effect student."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    teacher: SubmissionArtifactSettings
    submission_record_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    student_checkpoint: Path
    public_agent_manifest: Path
    opponents: tuple[str, ...] = Field(min_length=1)
    output_dir: Path
    report_dir: Path
    seed_start: int = Field(ge=0)
    seeds: int = Field(gt=0)
    batch_seeds: int = Field(gt=0)
    cpu_workers: int = Field(gt=0)
    compression_level: int = Field(ge=0, le=9)
    unit_limit: int = Field(gt=0, le=255)
    device: str
    maximum_graph_variants: int = Field(gt=0)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_correction(self) -> EffectCorrectionDataSettings:
        """Keep correction inputs authenticated and outputs in declared roots."""
        _repository_path(
            self.teacher.archive_path,
            "data",
            "effect correction teacher archive",
        )
        if self.teacher.archive_path.parts[:2] != ("data", "external"):
            raise ValueError("effect correction teacher must be under data/external/")
        _repository_path(
            self.student_checkpoint,
            "outputs",
            "effect correction student checkpoint",
        )
        _repository_path(
            self.public_agent_manifest,
            "data",
            "effect correction public agent manifest",
        )
        if self.public_agent_manifest.parts[:2] != ("data", "external"):
            raise ValueError("effect correction manifest must be under data/external/")
        _repository_path(self.output_dir, "data", "effect correction dataset")
        if self.output_dir.parts[:2] != ("data", "external"):
            raise ValueError("effect correction dataset must be under data/external/")
        _repository_path(self.report_dir, "outputs", "effect correction report")
        if len(set(self.opponents)) != len(self.opponents):
            raise ValueError("effect correction opponents must be unique")
        if any(not opponent or opponent == "self_play" for opponent in self.opponents):
            raise ValueError("effect correction requires named frozen opponents")
        if self.seed_start + self.seeds - 1 > 2**63 - 1:
            raise ValueError("effect correction seed range exceeds the native int64 ABI")
        if self.seeds % self.batch_seeds:
            raise ValueError("effect correction seeds must divide into complete batches")
        try:
            device = torch.device(self.device)
        except (RuntimeError, ValueError) as error:
            raise ValueError("effect correction device is invalid") from error
        if device.type not in {"cpu", "cuda"}:
            raise ValueError("effect correction device must be CPU or CUDA")
        if device.type == "cuda" and device.index is None:
            raise ValueError("effect correction CUDA requires an indexed device")
        _validate_environment(self.environment, "effect correction")
        return self


class EffectCorrectionDataAppSettings(BaseModel):
    """Hydra root for student-state Rank8 correction data."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    effect_correction_data: EffectCorrectionDataSettings


class EffectAggregateComponentSettings(BaseModel):
    """One authenticated effect dataset and its local held-out split sizes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest: Path
    validation_games: int = Field(gt=0)
    test_games: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_manifest(self) -> EffectAggregateComponentSettings:
        """Require a repository-relative external dataset manifest."""
        _repository_path(self.manifest, "data", "effect aggregate component")
        if self.manifest.parts[:2] != ("data", "external") or self.manifest.name != (
            "manifest.json"
        ):
            raise ValueError(
                "effect aggregate component must be a manifest under data/external/"
            )
        return self


class EffectAggregateDataSettings(BaseModel):
    """Immutable union of demonstration and student-state effect datasets."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    components: dict[str, EffectAggregateComponentSettings]
    output_dir: Path
    report_dir: Path

    @model_validator(mode="after")
    def validate_aggregate(self) -> EffectAggregateDataSettings:
        """Require stable component names and external-data output paths."""
        if len(self.components) < 2:
            raise ValueError("effect aggregate requires at least two components")
        if any(
            re.fullmatch(r"[a-z][a-z0-9_]*", name) is None
            for name in self.components
        ):
            raise ValueError("effect aggregate component names must be stable identifiers")
        _repository_path(self.output_dir, "data", "effect aggregate dataset")
        if self.output_dir.parts[:2] != ("data", "external"):
            raise ValueError("effect aggregate dataset must be under data/external/")
        _repository_path(self.report_dir, "outputs", "effect aggregate report")
        return self


class EffectAggregateDataAppSettings(BaseModel):
    """Hydra root for immutable effect dataset aggregation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    effect_aggregate_data: EffectAggregateDataSettings


class EffectBcOptimizationSettings(BaseModel):
    """Streaming optimization settings for atomic-effect imitation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    epochs: int = Field(gt=0)
    games_per_batch: int = Field(gt=0)
    learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    weight_decay: float = Field(ge=0.0, allow_inf_nan=False)
    outcome_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    gradient_clip: float = Field(gt=0.0, allow_inf_nan=False)
    seed: int = Field(ge=0)
    device: str
    cpu_threads: int = Field(gt=0)
    loader_workers: int = Field(gt=0)
    prefetch_batches: int = Field(gt=0)
    candidate_elements_per_chunk: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_device(self) -> EffectBcOptimizationSettings:
        """Accept CPU or an explicitly indexed CUDA device."""
        try:
            device = torch.device(self.device)
        except (RuntimeError, ValueError) as error:
            raise ValueError("effect BC training device is invalid") from error
        if device.type not in {"cpu", "cuda"}:
            raise ValueError("effect BC training device must be CPU or CUDA")
        if device.type == "cuda" and device.index is None:
            raise ValueError("effect BC CUDA training requires an indexed device")
        return self


class EffectBcSettings(BaseModel):
    """One provenance-bound atomic-effect behavior-cloning run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_dir: Path
    dataset_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_dir: Path
    initial_actor: Path
    initial_checkpoint: Path | None = None
    validation_games: int = Field(gt=0)
    test_games: int = Field(gt=0)
    unit_limit: int = Field(gt=0)
    model: EffectModelSettings
    optimization: EffectBcOptimizationSettings
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_training(self) -> EffectBcSettings:
        """Keep source and output artifacts within their repository namespaces."""
        _repository_path(self.dataset_dir, "data", "effect BC dataset")
        if self.dataset_dir.parts[:2] != ("data", "external"):
            raise ValueError("effect BC dataset must be under data/external/")
        _repository_path(self.output_dir, "outputs", "effect BC output")
        _repository_path(self.initial_actor, "outputs", "effect BC initial actor")
        if self.initial_checkpoint is not None:
            _repository_path(
                self.initial_checkpoint,
                "outputs",
                "effect BC initial checkpoint",
            )
        _validate_environment(self.environment, "effect BC")
        return self


class EffectBcAppSettings(BaseModel):
    """Hydra root for atomic-effect behavior cloning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    effect_bc: EffectBcSettings


__all__ = [
    "EffectAggregateComponentSettings",
    "EffectAggregateDataAppSettings",
    "EffectAggregateDataSettings",
    "EffectBcAppSettings",
    "EffectBcOptimizationSettings",
    "EffectBcSettings",
    "EffectCorrectionDataAppSettings",
    "EffectCorrectionDataSettings",
    "EffectTeacherDataAppSettings",
    "EffectTeacherDataSettings",
]
