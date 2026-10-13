"""Validated settings for conditional-program behavior cloning."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.bc.data_config import ReplayContract
from kagg_revue.rl.programs.config import ProgramAbiSettings, ProgramModelSettings


def _repository_path(path: Path, root: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != root:
        raise ValueError(f"{name} must be repository-relative under {root}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class ProgramBcSourceSettings(BaseModel):
    """Authenticated daily archives and stable episode partitions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    index_archive: Path
    source_archives: tuple[Path, ...]
    days: int = Field(gt=0)
    validation_fraction: float = Field(gt=0.0, lt=0.5)
    test_fraction: float = Field(gt=0.0, lt=0.5)
    workers: int = Field(gt=0)
    worker_cpu_threads: int = Field(gt=0)
    maximum_rejection_fraction: float = Field(ge=0.0, lt=1.0)
    contract: ReplayContract

    @model_validator(mode="after")
    def validate_archives(self) -> ProgramBcSourceSettings:
        """Require one archive per day and a nonempty training partition."""
        if len(self.source_archives) != self.days:
            raise ValueError("program BC source archive count must equal days")
        if len(set(self.source_archives)) != len(self.source_archives):
            raise ValueError("program BC source archives must be unique")
        if self.validation_fraction + self.test_fraction >= 1.0:
            raise ValueError("program BC validation and test fractions leave no training data")
        return self


class ProgramDemonstrationSourceSettings(BaseModel):
    """Paired native matches from one authenticated frozen teacher."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    teacher: str = Field(min_length=1)
    opponent: str = Field(min_length=1)
    public_agent_manifest: Path
    seed_start: int = Field(ge=0)
    seeds: int = Field(gt=0)
    workers: int = Field(gt=0)
    validation_fraction: float = Field(gt=0.0, lt=0.5)
    test_fraction: float = Field(gt=0.0, lt=0.5)

    @model_validator(mode="after")
    def validate_population(self) -> ProgramDemonstrationSourceSettings:
        """Require distinct lineages and nonempty room for training examples."""
        if self.teacher == self.opponent:
            raise ValueError("program demonstration teacher and opponent must differ")
        if self.validation_fraction + self.test_fraction >= 1.0:
            raise ValueError("program demonstration partitions leave no training data")
        _repository_path(
            self.public_agent_manifest,
            "data",
            "demonstration public_agent_manifest",
        )
        if self.public_agent_manifest.parts[:2] != ("data", "external"):
            raise ValueError("demonstration manifest must remain under data/external/")
        return self


class ProgramCorrectionSourceSettings(BaseModel):
    """Teacher labels on states visited by one frozen student checkpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    teacher: str = Field(min_length=1)
    opponent: str = Field(min_length=1)
    student_checkpoint: Path
    public_agent_manifest: Path
    seed_start: int = Field(ge=0)
    seeds: int = Field(gt=0)
    batch_seeds: int = Field(gt=0)
    workers: int = Field(gt=0)
    actor_streams: int = Field(default=1, gt=0)
    shard_workers: int = Field(default=1, gt=0)
    device: str
    host_memory_limit_gib: float = Field(gt=0.0, allow_inf_nan=False)
    use_cuda_graphs: bool = False
    use_full_turn_graph: bool = False
    fuse_teacher: bool = False
    teacher_workers: int | None = Field(default=None, gt=0)
    validation_fraction: float = Field(gt=0.0, lt=0.5)
    test_fraction: float = Field(gt=0.0, lt=0.5)

    @model_validator(mode="after")
    def validate_correction(self) -> ProgramCorrectionSourceSettings:
        """Bind the first correction pass to the authenticated native teacher."""
        if self.teacher != "kaito_v48":
            raise ValueError("program correction currently requires the Kaito v48 teacher")
        if self.teacher == self.opponent:
            raise ValueError("program correction teacher and opponent must differ")
        if self.validation_fraction + self.test_fraction >= 1.0:
            raise ValueError("program correction partitions leave no training data")
        if self.seeds % self.batch_seeds:
            raise ValueError("program correction seeds must divide into rollout batches")
        if self.batch_seeds % self.actor_streams:
            raise ValueError("program correction batch must divide across actor streams")
        if self.teacher_workers is not None and not self.fuse_teacher:
            raise ValueError("teacher_workers requires fused correction generation")
        if self.use_full_turn_graph and not self.use_cuda_graphs:
            raise ValueError("full-turn graph requires CUDA graph correction generation")
        _repository_path(
            self.student_checkpoint,
            "outputs",
            "correction student_checkpoint",
        )
        _repository_path(
            self.public_agent_manifest,
            "data",
            "correction public_agent_manifest",
        )
        if self.public_agent_manifest.parts[:2] != ("data", "external"):
            raise ValueError("correction manifest must remain under data/external/")
        parts = self.device.split(":", maxsplit=1)
        if (
            parts[0] not in {"cpu", "cuda"}
            or (parts[0] == "cpu" and len(parts) != 1)
            or (len(parts) == 2 and not parts[1].isdigit())
        ):
            raise ValueError("program correction device must be CPU or CUDA")
        return self


class ProgramAggregateSourceSettings(BaseModel):
    """Immutable union of previously authenticated program datasets."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    components: dict[str, Path]

    @model_validator(mode="after")
    def validate_components(self) -> ProgramAggregateSourceSettings:
        """Require two or more named external dataset manifests."""
        if len(self.components) < 2:
            raise ValueError("program aggregate requires at least two components")
        for name, path in self.components.items():
            if re.fullmatch(r"[a-z][a-z0-9_]*", name) is None:
                raise ValueError("program aggregate component names must be stable identifiers")
            _repository_path(path, "data", f"aggregate component {name}")
            if path.parts[:2] != ("data", "external") or path.name != "manifest.json":
                raise ValueError(
                    "program aggregate components must be manifests under data/external/"
                )
        return self


class ProgramBcOptimizationSettings(BaseModel):
    """End-to-end actor/program imitation optimization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    epochs: int = Field(gt=0)
    batch_sequences: int = Field(gt=0)
    learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    weight_decay: float = Field(ge=0.0, allow_inf_nan=False)
    outcome_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    gradient_clip: float = Field(gt=0.0, allow_inf_nan=False)
    seed: int = Field(ge=0)
    device: str
    cpu_threads: int = Field(gt=0)
    loader_workers: int = Field(gt=0)
    prefetch_shards: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_device(self) -> ProgramBcOptimizationSettings:
        """Accept an explicit CPU or indexed CUDA training device."""
        parts = self.device.split(":", maxsplit=1)
        if (
            parts[0] not in {"cpu", "cuda"}
            or (parts[0] == "cpu" and len(parts) != 1)
            or (len(parts) == 2 and not parts[1].isdigit())
        ):
            raise ValueError("program BC device must be CPU or CUDA")
        return self


class ProgramBcSettings(BaseModel):
    """One immutable daily-data conditional-program BC run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_dir: Path
    output_dir: Path
    initial_actor: Path
    initial_checkpoint: Path | None = None
    initialization: Literal["pretrained", "random"] = "pretrained"
    translation: Literal["raw", "semantic"] = "raw"
    source: ProgramBcSourceSettings | None = None
    demonstration_source: ProgramDemonstrationSourceSettings | None = None
    correction_source: ProgramCorrectionSourceSettings | None = None
    aggregate_source: ProgramAggregateSourceSettings | None = None
    abi: ProgramAbiSettings
    model: ProgramModelSettings
    optimization: ProgramBcOptimizationSettings
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_paths(self) -> ProgramBcSettings:
        """Keep raw, compact, and generated artifacts in their declared roots."""
        _repository_path(self.dataset_dir, "data", "dataset_dir")
        if self.dataset_dir.parts[:2] != ("data", "external"):
            raise ValueError("program BC dataset must remain under data/external/")
        _repository_path(self.output_dir, "outputs", "output_dir")
        _repository_path(self.initial_actor, "outputs", "initial_actor")
        if self.initial_checkpoint is not None:
            _repository_path(
                self.initial_checkpoint,
                "outputs",
                "initial_checkpoint",
            )
        if self.initialization == "random" and self.initial_checkpoint is not None:
            raise ValueError("random program BC initialization cannot resume a checkpoint")
        sources = (
            self.source,
            self.demonstration_source,
            self.correction_source,
            self.aggregate_source,
        )
        if sum(value is not None for value in sources) != 1:
            raise ValueError(
                "program BC requires exactly one replay, demonstration, correction, or "
                "aggregate source"
            )
        return self


class ProgramBcAppSettings(BaseModel):
    """Hydra root for conditional-program behavior cloning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    conditional_program_bc: ProgramBcSettings


__all__ = [
    "ProgramBcAppSettings",
    "ProgramAggregateSourceSettings",
    "ProgramCorrectionSourceSettings",
    "ProgramBcOptimizationSettings",
    "ProgramBcSettings",
    "ProgramBcSourceSettings",
    "ProgramDemonstrationSourceSettings",
]
