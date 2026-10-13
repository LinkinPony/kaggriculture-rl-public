"""Resolved controls for a bounded model-generated trajectory search."""

from pathlib import Path

from pydantic import Field, model_validator

from kagg_revue.production.config import FrozenSettings, Settings


class Proposal(FrozenSettings):
    """An exploration horizon and temperature, without prescribed game actions."""

    decisions: int = Field(gt=0)
    temperature: float = Field(gt=0)


class ExpertSettings(FrozenSettings):
    """Separate search and supervised optimization from the PPO experiment."""

    production: Settings
    proposals: tuple[Proposal, ...]
    iterations: int = Field(gt=0)
    learning_rate: float = Field(gt=0)
    retention_weight: float = Field(gt=0)
    learner_rows: int = Field(gt=0)
    microbatch_rows: int = Field(gt=0)
    maximum_plan_kl: float = Field(gt=0)
    backtrack_attempts: int = Field(gt=0)
    evaluation_interval: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_experiment(self) -> "ExpertSettings":
        """Require an explicit neural baseline and fixed synchronized batch geometry."""
        p = self.production
        if p.checkpoint is None or p.model.time_prior or p.model.architecture != "work-v1":
            raise ValueError("expert iteration requires an explicit no-table work checkpoint")
        if (
            not self.proposals
            or max(v.decisions for v in self.proposals) > p.turns // p.decision_interval
        ):
            raise ValueError("search windows must fit in a complete game")
        if self.learner_rows % (2 * len(p.devices)) or self.microbatch_rows % len(p.devices):
            raise ValueError("global learner and microbatch rows must divide across ranks")
        if self.iterations > p.ppo.updates:
            raise ValueError("search must fit in the reserved training seed range")
        return self


class EvolutionSettings(FrozenSettings):
    """Whole-policy search with a rolling opponent and a frozen quality reference."""

    production: Settings
    reference: Path
    generations: int = Field(gt=0)
    directions: int = Field(gt=0)
    scales: tuple[float, ...]
    mutation_seed: int = Field(ge=0)
    finalists: int = Field(gt=0)
    retain_generations: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_evolution(self) -> "EvolutionSettings":
        """Keep all neural semantics and reserve disjoint evolving seed panels."""
        p = self.production
        if p.checkpoint is None or p.model.time_prior or p.model.architecture != "work-v1":
            raise ValueError("policy search requires an explicit no-table work checkpoint")
        if any(not device.startswith("cuda:") for device in p.devices):
            raise ValueError("production policy search requires CUDA actor shards")
        if not self.scales or any(value <= 0 for value in self.scales):
            raise ValueError("mutation scales must be positive")
        if self.generations > p.ppo.updates:
            raise ValueError("generations exceed the reserved training seed range")
        ranges = sorted(
            (start, start + self.generations * p.evaluation_games // 2)
            for start in (p.ppo.seed_start, p.evaluation_seed, p.confirmation_seed)
        )
        if any(left[1] > right[0] for left, right in zip(ranges, ranges[1:], strict=False)):
            raise ValueError("search, selection and confirmation ranges overlap")
        return self


class ApprenticeSettings(EvolutionSettings):
    """Search experts and fit their conditional policies on apprentice-visited states."""

    teacher: Path
    collection_seed: int = Field(ge=0)
    validation_seed: int = Field(ge=0)
    learning_rate: float = Field(gt=0)
    temperature: float = Field(gt=0)
    learner_steps: int = Field(gt=0)
    learner_rows: int = Field(gt=0)
    microbatch_rows: int = Field(gt=0)
    observations_per_trajectory: int = Field(gt=0)
    search_interval: int = Field(gt=0)
    bootstrap_updates: int = Field(ge=0)
    evaluation_interval: int = Field(gt=0)
    fits_per_expert: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_apprentice(self) -> "ApprenticeSettings":
        """Reserve independent data/search/selection bands and fixed learner graph shapes."""
        p = self.production
        world = len(p.devices)
        if world != 2:
            raise ValueError("apprentice assessment requires two population shards")
        if self.learner_rows % world or self.microbatch_rows % world:
            raise ValueError("global learner rows must divide into synchronized microbatches")
        if self.observations_per_trajectory > p.turns // p.decision_interval:
            raise ValueError("observation samples must fit within complete episodes")
        ranges = sorted(
            [
                (
                    self.collection_seed,
                    self.collection_seed + self.generations * p.ppo.games_per_update,
                ),
                *[
                    (seed, seed + self.generations * p.evaluation_games // 2)
                    for seed in (
                        p.ppo.seed_start,
                        p.evaluation_seed,
                        self.validation_seed,
                        p.confirmation_seed,
                    )
                ],
            ]
        )
        if any(left[1] > right[0] for left, right in zip(ranges, ranges[1:], strict=False)):
            raise ValueError("apprentice data and evaluation seed bands overlap")
        return self
