"""Validated settings for atomic-effect closed-loop evaluation."""

from __future__ import annotations

from pathlib import Path

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator


def _repository_path(path: Path, root: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != root:
        raise ValueError(f"{name} must be repository-relative under {root}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape {root}/")


class EffectEvaluationSettings(BaseModel):
    """One immutable selection and confirmation match panel."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    checkpoint: Path
    training_report: Path
    public_agent_manifest: Path
    output_dir: Path
    opponents: tuple[str, ...] = Field(min_length=1)
    selection_seed_start: int = Field(ge=0)
    selection_seed_count: int = Field(gt=0)
    confirmation_seed_start: int = Field(ge=0)
    confirmation_seed_count: int = Field(gt=0)
    unit_limit: int = Field(gt=0)
    device: str
    cpu_workers: int = Field(gt=0)
    maximum_graph_variants: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_evaluation(self) -> EffectEvaluationSettings:
        """Reject escaped artifacts, repeated opponents, and overlapping panels."""
        _repository_path(self.checkpoint, "outputs", "effect evaluation checkpoint")
        _repository_path(self.training_report, "outputs", "effect BC training report")
        _repository_path(self.public_agent_manifest, "data", "public agent manifest")
        if self.public_agent_manifest.parts[:2] != ("data", "external"):
            raise ValueError("effect evaluation manifest must be under data/external/")
        _repository_path(self.output_dir, "outputs", "effect evaluation output")
        if (
            len(set(self.opponents)) != len(self.opponents)
            or any(not name or name == "self_play" for name in self.opponents)
        ):
            raise ValueError("effect evaluation opponents must be unique external policies")
        selection = range(
            self.selection_seed_start,
            self.selection_seed_start + self.selection_seed_count,
        )
        confirmation = range(
            self.confirmation_seed_start,
            self.confirmation_seed_start + self.confirmation_seed_count,
        )
        if max(selection.start, confirmation.start) < min(selection.stop, confirmation.stop):
            raise ValueError("effect selection and confirmation seeds must be disjoint")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("effect evaluation must record official time-budget semantics")
        try:
            device = torch.device(self.device)
        except (RuntimeError, ValueError) as error:
            raise ValueError("effect evaluation device is invalid") from error
        if device.type not in {"cpu", "cuda"}:
            raise ValueError("effect evaluation device must be CPU or CUDA")
        if device.type == "cuda" and device.index is None:
            raise ValueError("effect evaluation CUDA device must be indexed")
        for name, minimum in {
            "boardSize": 1,
            "episodeSteps": 2,
            "turnsPerDay": 1,
            "maxMarketOrdersPerTurn": 1,
        }.items():
            value = self.environment.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
                raise ValueError(f"effect evaluation environment {name} is invalid")
        return self


class EffectEvaluationAppSettings(BaseModel):
    """Hydra root for one atomic-effect evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    effect_policy_evaluation: EffectEvaluationSettings


__all__ = ["EffectEvaluationAppSettings", "EffectEvaluationSettings"]
