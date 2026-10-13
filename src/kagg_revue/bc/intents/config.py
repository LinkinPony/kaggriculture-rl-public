"""Validated settings for canonical-intent teacher data generation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.rl.intents.config import IntentModelSettings
from kagg_revue.teacher.config import SubmissionArtifactSettings


def _repository_path(path: Path, root: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != root:
        raise ValueError(f"{name} must be repository-relative under {root}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class IntentTeacherDataSettings(BaseModel):
    """One provenance-bound canonical-intent teacher dataset."""

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
    max_transaction_steps: int = Field(gt=1)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_generation(self) -> IntentTeacherDataSettings:
        """Reject escaped artifacts and environments outside the actor ABI."""
        _repository_path(self.output_dir, "data", "intent teacher dataset")
        if self.output_dir.parts[:2] != ("data", "external"):
            raise ValueError("intent teacher dataset must be under data/external/")
        _repository_path(self.report_dir, "outputs", "intent teacher report")
        if self.seed_start + self.games - 1 > 2**63 - 1:
            raise ValueError("intent teacher seed range exceeds the native int64 ABI")
        if self.games_per_shard > self.games:
            raise ValueError("intent teacher shard cannot contain more games than the dataset")
        for name, minimum in {
            "boardSize": 1,
            "episodeSteps": 2,
            "turnsPerDay": 1,
            "maxMarketOrdersPerTurn": 1,
        }.items():
            value = self.environment.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
                raise ValueError(f"intent teacher environment {name} is invalid")
        return self


class IntentTeacherDataAppSettings(BaseModel):
    """Hydra root for canonical-intent teacher data generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_teacher_data: IntentTeacherDataSettings


class IntentBcOptimizationSettings(BaseModel):
    """Streaming end-to-end optimization for canonical-intent imitation."""

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

    @model_validator(mode="after")
    def validate_device(self) -> IntentBcOptimizationSettings:
        """Accept CPU or an explicitly indexed CUDA device."""
        try:
            device = __import__("torch").device(self.device)
        except (RuntimeError, ValueError) as error:
            raise ValueError("intent BC training device is invalid") from error
        if device.type not in {"cpu", "cuda"}:
            raise ValueError("intent BC training device must be CPU or CUDA")
        if device.type == "cuda" and device.index is None:
            raise ValueError("intent BC CUDA training requires an indexed device")
        return self


class IntentBcSettings(BaseModel):
    """One provenance-bound random-initialized intent BC run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_dir: Path
    dataset_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_dir: Path
    architecture_actor: Path
    initialization: Literal["random"]
    validation_games: int = Field(gt=0)
    test_games: int = Field(gt=0)
    unit_limit: int = Field(gt=0)
    model: IntentModelSettings
    optimization: IntentBcOptimizationSettings
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_training(self) -> IntentBcSettings:
        """Keep artifacts scoped and reject a frozen random turn encoder."""
        _repository_path(self.dataset_dir, "data", "intent BC dataset")
        if self.dataset_dir.parts[:2] != ("data", "external"):
            raise ValueError("intent BC dataset must be under data/external/")
        _repository_path(self.output_dir, "outputs", "intent BC output")
        _repository_path(
            self.architecture_actor,
            "outputs",
            "intent BC architecture_actor",
        )
        if not self.model.train_turn_encoder:
            raise ValueError("random intent BC must train the causal turn encoder")
        for name, minimum in {
            "boardSize": 1,
            "episodeSteps": 2,
            "turnsPerDay": 1,
            "maxMarketOrdersPerTurn": 1,
        }.items():
            value = self.environment.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
                raise ValueError(f"intent BC environment {name} is invalid")
        return self


class IntentBcAppSettings(BaseModel):
    """Hydra root for canonical-intent behavior cloning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_bc: IntentBcSettings


__all__ = [
    "IntentBcAppSettings",
    "IntentBcOptimizationSettings",
    "IntentBcSettings",
    "IntentTeacherDataAppSettings",
    "IntentTeacherDataSettings",
]
