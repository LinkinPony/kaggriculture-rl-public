"""Teacher-free experiment controls, resolved through Hydra."""

from math import ceil
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.restarts import RestartSource
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.matchmaking.config import HistoricalSource, Pfsp
from kagg_revue.learning.optimization.settings import CashMargin
from kagg_revue.learning.pretraining.config import Demonstrations, InitialWeights
from kagg_revue.opponents.settings import PublicPopulation


def default_environment() -> dict[str, int | float]:
    """Return the full official season and action geometry for fresh instances."""
    return {
        "boardSize": 10,
        "episodeSteps": 720,
        "turnsPerDay": 24,
        "maxMarketOrdersPerTurn": 10,
    }


class Population(FrozenSettings):
    """A bounded archive of this experiment's frozen policies, optionally using PFSP."""

    fraction: float = Field(default=0.5, ge=0, lt=1)
    snapshot_interval: int = Field(default=4, gt=0)
    capacity: int = Field(default=8, ge=2)
    pfsp: Pfsp | None = None
    sources: tuple[HistoricalSource, ...] = ()
    unified: bool = False

    @property
    def separate_scripts(self) -> bool:
        """Use an independent adaptive script draw with its own physical-game budget."""
        return self.pfsp is not None and self.pfsp.script_sampling == "independent_pfsp"

    @property
    def sampled_counts(self) -> bool:
        """Resolve rounded opponent counts per update before constructing a runtime."""
        return self.unified or self.separate_scripts

    @model_validator(mode="after")
    def validate_pfsp(self) -> "Population":
        """Keep space for a fixed initial control, older history and recent snapshots."""
        if self.pfsp is not None and (
            self.fraction <= 0
            or self.capacity
            < self.pfsp.recent_snapshots + 2 + sum(len(s.checkpoints) for s in self.sources)
        ):
            raise ValueError("PFSP needs historical games and capacity for older snapshots")
        if self.sources and self.pfsp is None and self.fraction > 0:
            raise ValueError("external historical opponents require PFSP")
        if len({source.run for source in self.sources}) != len(self.sources):
            raise ValueError("historical source runs must be unique")
        if self.unified and self.pfsp is None:
            raise ValueError("a unified opponent pool requires PFSP")
        if self.unified and self.separate_scripts:
            raise ValueError("independent scripts must remain outside the unified PFSP pool")
        return self


class Exploration(FrozenSettings):
    """Action-count priors for random initialization, with no demonstration data."""

    market_stop_probability: float = Field(default=0.98, gt=0, lt=1)
    quantity_decay: float = Field(default=1.0, ge=0)
    head_standard_deviation: float = Field(default=0.01, gt=0)


class Evaluation(FrozenSettings):
    """Budget checkpoints and disjoint seed panels fixed before training."""

    games: int = Field(default=64, gt=0, multiple_of=2)
    interval: int = Field(default=4, gt=0)
    selection_seed: int = Field(default=710000000, ge=0)
    confirmation_seed: int = Field(default=720000000, ge=0)
    anchor_seeds: tuple[int, ...] = (91001, 91002)


class RestartCurriculum(RestartSource):
    """Move from later official states toward the complete initial-state task."""

    starts: tuple[int, ...] = (576, 384, 192, 48)
    updates_per_stage: int = Field(default=8, gt=0)
    full_every: int = Field(default=4, ge=2)

    def start(self, update: int) -> int:
        """Keep regular complete games, then finish with exclusively complete games."""
        stage = (update - 1) // self.updates_per_stage
        return (
            0 if update % self.full_every == 0 or stage >= len(self.starts) else self.starts[stage]
        )


class Experiment(FrozenSettings):
    """A random root, an explicit actor weight transfer, or exact continuation.

    Existing weights may initialize a separate BC or PPO run with authenticated ancestry.
    Public scripts may be explicitly declared as opponents, never actor labels.
    An optional authenticated raw dataset initializes this run's random actor;
    its fixed final checkpoint is a separate baseline for measuring online RL.
    Shared policy/runtime code is an implementation dependency, not an artifact
    dependency. All evaluation anchors are also constructed from random seeds.
    """

    output_dir: Path
    resume: bool = False
    pretraining_only: bool = False
    initial_weights: InitialWeights | None = None
    initial_critic: InitialWeights | None = None
    device: str = "cuda:0"
    seed: int = Field(default=41001, ge=0)
    train_seed: int = Field(default=700000000, ge=0)
    updates: int = Field(default=32, gt=0)
    checkpoint_interval: int = Field(default=1, gt=0)
    checkpoint_keep_recent: int | None = Field(default=2, ge=2)
    checkpoint_keep_interval: int | None = Field(default=200, gt=0)
    games: int = Field(default=256, gt=0)
    workers: int = Field(default=16, gt=0)
    cpu_threads: int = Field(default=4, gt=0)
    width: int = Field(default=128, gt=0, multiple_of=4)
    architecture: Literal["work-v1", "grounded-v1", "grounded-v2"] = "work-v1"
    operation_quantity_bias: bool = False
    market_budget: bool = False
    agronomy: bool = False
    derived: bool = False
    gated: bool = False
    memory_turns: int = Field(default=0, ge=0)
    memory_width: int = Field(default=256, gt=0, multiple_of=8)
    memory_layers: int = Field(default=2, gt=0)
    memory_tokens: int = Field(default=4, gt=0)
    joint_units: bool = False
    depth: int = Field(default=2, gt=0)
    heads: int = Field(default=4, gt=0)
    expansion: int = Field(default=3, gt=0)
    critic_width: int = Field(default=128, gt=0, multiple_of=4)
    critic_depth: int = Field(default=2, gt=0)
    unit_limit: int = Field(default=32, gt=0, le=32)
    decision_interval: int = Field(default=4, gt=0)
    quantity_max: int = Field(default=16, gt=0)
    quantity_extra: tuple[int, ...] = (24, 32, 48, 64, 96, 128, 256, 512, 1024, 4096, 1000000)
    environment: dict[str, int | float] = Field(default_factory=default_environment)
    batch_rows: int = Field(default=5760, gt=0)
    sequence_chunk_turns: int = Field(default=48, gt=0)
    sequence_games_per_rank: int = Field(default=4, gt=0)
    microbatch_rows: int = Field(default=256, gt=0)
    epochs: int = Field(default=1, gt=0)
    actor_learning_rate: float = Field(default=0.0001, gt=0)
    critic_learning_rate: float = Field(default=0.0003, gt=0)
    learning_rate_warmup_updates: int = Field(default=0, ge=0)
    gamma: float = Field(default=1.0, gt=0, le=1)
    gae_lambda: float = Field(default=1.0, ge=0, le=1)
    target_kl: float = Field(default=0.01, gt=0)
    kl_control: Literal["rollback", "early_stop"] = "rollback"
    clip: float = Field(default=0.1, gt=0, lt=1)
    entropy_weight: float = Field(default=0.0001, ge=0)
    # Recurrent PPO only: penalize KL(policy || frozen run-initial policy) per decision.
    reference_kl_weight: float = Field(default=0.0, ge=0, allow_inf_nan=False)
    cash_weight: float = Field(default=0.0, ge=0)
    cash_scale: float = Field(default=10000.0, gt=0)
    cash_margin: CashMargin | None = None
    compile: bool = True
    precision: Literal["fp32", "bf16"] = "bf16"
    deterministic: bool = False
    exploration: Exploration = Field(default_factory=Exploration)
    population: Population = Field(default_factory=Population)
    evaluation: Evaluation = Field(default_factory=Evaluation)
    curriculum: RestartCurriculum | None = None
    demonstrations: Demonstrations | None = None
    execution: Execution | None = None
    script_population: PublicPopulation | None = None

    @model_validator(mode="after")
    def validate_experiment(self) -> "Experiment":
        """Reject artifact escape, unbalanced seats, and overlapping seed roles."""
        if (self.gamma != 1 or self.gae_lambda != 1) and (
            self.memory_turns or self.decision_interval != 1 or self.curriculum is not None
        ):
            raise ValueError("temporal GAE currently requires stateless complete single-turn games")
        if self.agronomy and self.architecture != "grounded-v2":
            raise ValueError("agronomy features require grounded-v2")
        if self.derived and not self.agronomy:
            raise ValueError("derived features require agronomy v4 as their preserved prefix")
        if self.memory_turns and (
            self.architecture != "grounded-v2"
            or self.memory_width % self.heads
            or self.decision_interval != 1
            or self.curriculum is not None
            or self.cash_weight != 0
            or self.sequence_chunk_turns > self.memory_turns
        ):
            raise ValueError("memory requires grounded full games and terminal outcome rewards")
        if self.pretraining_only and self.demonstrations is None:
            raise ValueError("pretraining-only runs require demonstrations")
        if (
            self.demonstrations is not None
            and self.demonstrations.loss is not None
            and (self.architecture != "grounded-v2" or self.decision_interval != 1)
        ):
            raise ValueError("grouped BC loss requires single-turn grounded-v2 actions")
        if self.initial_weights is not None and (
            self.output_dir == self.initial_weights.run
            or (not self.pretraining_only and self.demonstrations is not None)
        ):
            raise ValueError("initial weights require separate BC-only or demonstration-free PPO")
        if self.initial_critic is not None and (
            self.output_dir == self.initial_critic.run
            or self.pretraining_only
            or self.demonstrations is not None
        ):
            raise ValueError("initial critic requires a separate demonstration-free PPO run")
        if self.cash_margin is not None and self.cash_weight:
            raise ValueError("bounded cash margin cannot also reward absolute cash")
        if self.width % self.heads or self.critic_width % self.heads:
            raise ValueError("actor and critic widths must divide by attention heads")
        if (
            self.demonstrations is not None
            and self.demonstrations.distributed
            and (
                self.execution is None
                or self.demonstrations.batch_rows % len(self.execution.devices)
            )
        ):
            raise ValueError("distributed BC requires execution devices and divisible batches")
        path = self.output_dir
        pfsp = self.population.pfsp
        unified = self.population.unified
        separate = self.population.separate_scripts
        world = len(self.execution.devices) if self.execution else 1
        if (
            self.memory_turns
            and self.demonstrations is not None
            and self.demonstrations.batch_rows
            % ((int(self.environment["episodeSteps"]) - 1) * world)
        ):
            raise ValueError("recurrent BC batches must contain whole trajectories per rank")
        if separate:
            scripts = self.script_population
            block = 2 * world
            if (
                scripts is None
                or self.games % block
                or self.games * scripts.fraction < block
                or ceil(self.games * scripts.fraction / block)
                + self.games * self.population.fraction / block
                >= self.games / block
            ):
                raise ValueError("separate scripts need balanced pairs and room for self-play")
        if unified and (
            self.games % (2 * world)
            or self.games * min(self.population.fraction, 1 - self.population.fraction) < 2 * world
        ):
            raise ValueError("unified sampling needs balanced pairs and room for both populations")
        if pfsp is not None and self.curriculum is not None:
            raise ValueError("PFSP outcomes require full games without restart curricula")
        if self.script_population is not None:
            scripts = self.script_population
            world = len(self.execution.devices) if self.execution else 1
            count = self.games * scripts.fraction / world
            if (
                self.architecture not in {"grounded-v1", "grounded-v2"}
                or self.curriculum is not None
                or self.population.fraction + scripts.fraction >= 1
                or (
                    not unified
                    and not separate
                    and (not count.is_integer() or int(count) % (2 * len(scripts.agents)))
                )
                or (unified and scripts.fraction != 0)
                or (not unified and scripts.fraction == 0)
            ):
                raise ValueError("public mixtures require grounded full games and balanced seats")
            if (
                pfsp is not None
                and not unified
                and not separate
                and int(count) < 2 * len(scripts.agents) * pfsp.script_min_pairs_per_rank
            ):
                raise ValueError("PFSP script budget cannot cover its minimum seat pairs")
        if self.execution is not None:
            world = len(self.execution.devices)
            if self.device != self.execution.devices[0]:
                raise ValueError("primary device must match the first execution device")
            if self.games % world or self.batch_rows % world:
                raise ValueError("games and logical minibatches must divide across devices")
            history_per_rank = self.games * self.population.fraction / world
            if not unified and (not history_per_rank.is_integer() or int(history_per_rank) % 2):
                raise ValueError("each device must balance both historical opponent seats")
        if (
            self.population.snapshot_interval % self.checkpoint_interval
            or self.evaluation.interval % self.checkpoint_interval
        ):
            raise ValueError("checkpoint interval must divide population and evaluation intervals")
        if self.architecture in {"grounded-v1", "grounded-v2"} and self.decision_interval != 1:
            raise ValueError("grounded policies choose exactly one official turn at a time")
        if (self.market_budget or self.joint_units) and self.architecture != "grounded-v2":
            raise ValueError("market budget and joint units require the typed grounded decoder")
        if self.operation_quantity_bias and self.architecture not in {"grounded-v1", "grounded-v2"}:
            raise ValueError("operation quantity biases require the grounded decoder")
        if self.demonstrations is not None and (
            self.architecture not in {"grounded-v1", "grounded-v2"} or self.curriculum is not None
        ):
            raise ValueError("demonstration initialization requires grounded full-initial-state RL")
        if self.curriculum is not None:
            starts = self.curriculum.starts
            if (
                self.architecture not in {"grounded-v1", "grounded-v2"}
                or not starts
                or tuple(sorted(set(starts), reverse=True)) != starts
                or min(starts) <= 0
                or max(starts) >= self.environment["episodeSteps"] - 1
            ):
                raise ValueError(
                    "restart curriculum requires descending nonterminal turn boundaries"
                )
        if path.is_absolute() or ".." in path.parts or path.parts[:2] != ("outputs", "learning"):
            raise ValueError("new learning runs belong under outputs/learning")
        historical = self.games * self.population.fraction
        if not unified and (not historical.is_integer() or int(historical) % 2):
            raise ValueError("historical games must be integral and balance both learner seats")
        anchors = self.evaluation.anchor_seeds
        if not anchors or len(set(anchors)) != len(anchors) or self.seed in anchors:
            raise ValueError("evaluation anchors require distinct independent initialization seeds")
        spans = sorted(
            [
                (self.train_seed, self.train_seed + self.games * self.updates),
                (
                    self.evaluation.selection_seed,
                    self.evaluation.selection_seed + self.evaluation.games // 2,
                ),
                (
                    self.evaluation.confirmation_seed,
                    self.evaluation.confirmation_seed + self.evaluation.games // 2,
                ),
            ]
        )
        if self.demonstrations is not None and (
            self.demonstrations.behavior_games or self.demonstrations.control_games
        ):
            spans.append(
                (
                    self.demonstrations.behavior_seed,
                    self.demonstrations.behavior_seed
                    + max(
                        self.demonstrations.behavior_games,
                        self.demonstrations.control_games // 2,
                    ),
                )
            )
            spans.sort()
        if any(left[1] > right[0] for left, right in zip(spans, spans[1:], strict=False)):
            raise ValueError("training, selection and confirmation seeds must be disjoint")
        return self
