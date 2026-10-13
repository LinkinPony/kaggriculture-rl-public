"""Explicit production controls for counterfactual program policy iteration."""

from pathlib import Path

from pydantic import Field, model_validator

from kagg_revue.production.config import FrozenSettings, Settings


class BranchSettings(FrozenSettings):
    """Keep proposal, complete-game evaluation and gradient budgets independently visible."""

    production: Settings
    continuation: Path
    reference: Path
    updates: int = Field(gt=0)
    root_groups: int = Field(gt=0)
    candidates: int = Field(gt=1)
    pivots: int = Field(gt=0)
    alternatives: int = Field(gt=0)
    learning_rate: float = Field(gt=0)
    learner_steps: int = Field(gt=0)
    microbatch_rows: int = Field(gt=0)
    preference_beta: float = Field(gt=0)
    evaluation_interval: int = Field(gt=0)
    retain_checkpoints: int = Field(gt=0)
    root_seed: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_shapes(self) -> "BranchSettings":
        """Resolve one persistent branch shape and disjoint complete-match seed bands."""
        p = self.production
        world = len(p.devices)
        if world != 2 or any(not d.startswith("cuda:") for d in p.devices):
            raise ValueError("state-branch production requires two CUDA ranks")
        if p.checkpoint is None or p.model.architecture != "work-v1" or p.model.time_prior:
            raise ValueError("state-branch training requires an explicit no-table work actor")
        local = p.ppo.games_per_update // world
        scripts = int(local * p.ppo.script_fraction)
        if min(scripts, local - scripts) == 0 or any(
            count % (2 * self.root_groups) for count in (scripts, local - scripts)
        ):
            raise ValueError("each root group must retain paired seats in both populations")
        if self.microbatch_rows % world or self.root_groups > p.turns // p.decision_interval:
            raise ValueError("invalid learner shard width or number of root groups")
        if (self.microbatch_rows // world) % self.candidates:
            raise ValueError("learner microbatches must preserve complete candidate sets")
        if self.updates > p.ppo.updates:
            raise ValueError("updates exceed the reserved rollout seed band")
        ranges = sorted(
            (
                (p.ppo.seed_start, p.ppo.seed_start + self.updates * p.ppo.games_per_update),
                (p.evaluation_seed, p.evaluation_seed + self.updates * p.evaluation_games // 2),
                (p.confirmation_seed, p.confirmation_seed + p.evaluation_games // 2),
            )
        )
        if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:], strict=False)):
            raise ValueError("training, selection and confirmation seeds overlap")
        return self
