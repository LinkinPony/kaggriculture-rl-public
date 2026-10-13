"""Validated neural execution geometry shared by independent learning workflows."""

from typing import Literal

from pydantic import Field, model_validator

from kagg_revue.learning.optimization.settings import OptimizationSettings
from kagg_revue.opponents.settings import PublicPopulation
from kagg_revue.policy.settings import GeometrySettings


class RuntimeSettings(GeometrySettings):
    """Native collection, neural matches and PPO without artifact or BC inputs."""

    devices: tuple[str, ...]
    workers: int = Field(gt=0)
    evaluation_games: int = Field(gt=0)
    compile: bool
    fused_loss: bool = False
    sequence_chunk_turns: int = Field(default=48, gt=0)
    sequence_games_per_rank: int = Field(default=4, gt=0)
    precision: Literal["bf16", "fp32"] = "bf16"
    bf16_reduced_precision_reduction: bool = True
    ppo: OptimizationSettings
    script_population: PublicPopulation | None = None

    @model_validator(mode="after")
    def validate_runtime(self) -> "RuntimeSettings":
        """Keep geometry, population balance, and optimizer shapes consistent."""
        if not self.devices or len(set(self.devices)) != len(self.devices):
            raise ValueError("devices must be nonempty and unique")
        ranks = len(self.devices)
        if (self.ppo.gamma != 1 or self.ppo.gae_lambda != 1) and (
            self.model.memory_turns
            or self.decision_interval != 1
            or self.ppo.ratio_scope != "prefix"
            or self.ppo.prefix_trace_lambda != 1
        ):
            raise ValueError("temporal GAE requires stateless single-turn, full-prefix credit")
        scripts = self.ppo.games_per_update * self.ppo.script_fraction / ranks
        history = self.ppo.history
        if history is not None:
            historical = self.ppo.games_per_update * history.fraction / ranks
            if not historical.is_integer() or int(historical) % 2:
                raise ValueError("historical games must balance both learned seats on every rank")
            if (
                self.model.architecture not in {"work-v1", "grounded-v1", "grounded-v2"}
                or self.ppo.temperature_schedule is not None
            ):
                raise ValueError("historical self-play requires a fixed-temperature work actor")
            if history.fraction + self.ppo.script_fraction > 1:
                raise ValueError("frozen opponent fractions exceed the physical game budget")
        if not scripts.is_integer():
            raise ValueError("script game counts must be integral on every learner rank")
        if self.ppo.population == "self_play":
            if scripts or self.ppo.script_opponents:
                raise ValueError("self-play cannot configure script opponents")
        elif not scripts or not self.ppo.script_opponents:
            raise ValueError("script mixture requires a positive fraction and opponents")
        if scripts and int(scripts) % (2 * len(self.ppo.script_opponents)):
            raise ValueError("script games must balance every opponent and both seats per rank")
        if len(set(self.ppo.script_opponents)) != len(self.ppo.script_opponents):
            raise ValueError("script opponent identities must be unique")
        if self.script_population is not None and (
            self.script_population.fraction != self.ppo.script_fraction
            or self.script_population.agents != self.ppo.script_opponents
            or self.model.architecture not in {"grounded-v1", "grounded-v2"}
            or self.decision_interval != 1
        ):
            raise ValueError("public script identity and runtime population must agree")
        if self.ppo.ratio_scope == "prefix" and (
            self.model.architecture not in {"work-v1", "grounded-v1", "grounded-v2"}
            or not self.model.critic_depth
        ):
            raise ValueError("prefix PPO requires a work policy with an entity critic")
        if self.ppo.prefix_warmup_updates and self.ppo.ratio_scope != "prefix":
            raise ValueError("prefix critic warmup requires prefix PPO")
        schedule = self.ppo.temperature_schedule
        if schedule is not None:
            if not self.ppo.prefix_warmup_updates or self.ppo.ratio_scope != "prefix":
                raise ValueError("temperature ramps require a greedy prefix-critic warmup")
            if not self.ppo.prefix_warmup_updates + 1 < schedule.end_update <= self.ppo.updates:
                raise ValueError(
                    "the temperature ramp must fit warmup and both stochastic endpoints"
                )
            if schedule.start_temperature > self.ppo.temperature:
                raise ValueError("the starting temperature must not exceed the final temperature")
        if self.ppo.bc_rows % ranks:
            raise ValueError("global rehearsal minibatches must divide across learner ranks")
        if self.ppo.games_per_update % ranks or self.ppo.batch_rows % ranks:
            raise ValueError("physical games and global minibatches must divide across ranks")
        if self.ppo.microbatch_rows % ranks:
            raise ValueError("global learner microbatches must divide across ranks")
        if self.ppo.prefix_trace_lambda and self.ppo.ratio_scope != "prefix":
            raise ValueError("prefix traces require prefix PPO")
        return self
