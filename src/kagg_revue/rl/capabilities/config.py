"""Validated configuration for search-augmented capability PPO."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.rl.capabilities.contract import CapabilityVersionContract

_INTEGER_VOCAB_SIZES = (4, 6, 12, 1024, 64, 8)


def _canonical_identity(value: str, name: str) -> str:
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a nonempty canonical identity")
    return value


def _relative_path_under(path: Path, directory: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != directory:
        raise ValueError(f"{name} must be a repository-relative path under {directory}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class CapabilityAbiSettings(BaseModel):
    """Exact native-to-policy tensor ABI plus runtime K/L capacities."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[1]
    max_candidates: int = Field(ge=2)
    max_edits: int = Field(ge=1)
    mode_tokens: Literal[4]
    integer_fields: Literal[6]
    edit_value_features: Literal[4]
    root_features: Literal[90]
    candidate_features: Literal[32]
    search_features: int = Field(ge=0)
    integer_vocab_sizes: tuple[int, ...]

    @model_validator(mode="after")
    def validate_abi(self) -> CapabilityAbiSettings:
        """Reject a tensor layout that the native capability compiler cannot emit."""
        if self.integer_vocab_sizes != _INTEGER_VOCAB_SIZES:
            raise ValueError("capability integer vocabularies differ from native ABI v1")
        return self


class FrozenCapabilityVersions(BaseModel):
    """Opaque semantic versions frozen for every collected PPO batch."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal: str
    search: str
    executor: str

    @model_validator(mode="after")
    def validate_identities(self) -> FrozenCapabilityVersions:
        """Require exact, non-implicit proposal/search/executor identities."""
        _canonical_identity(self.proposal, "proposal version")
        _canonical_identity(self.search, "search version")
        _canonical_identity(self.executor, "executor version")
        return self

    def contract(self) -> CapabilityVersionContract:
        """Return the durable rollout version contract."""
        return CapabilityVersionContract(
            proposal_version=self.proposal,
            search_version=self.search,
            executor_version=self.executor,
        )


class CapabilitySearchSettings(BaseModel):
    """Fixed-cost exhaustive search driven by a frozen candidate-Q target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_value_scale: float = Field(ge=0.0, allow_inf_nan=False)
    replay_prior_logit: float = Field(ge=0.0, allow_inf_nan=False)
    behavior_exploration_epsilon: float = Field(
        ge=0.0,
        lt=1.0,
        allow_inf_nan=False,
    )
    target_sync_interval: int = Field(gt=0)


class CapabilityModelSettings(BaseModel):
    """Trainable selector widths independent of the native tensor ABI."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    initial_search_gate: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    search_logit_limit: float = Field(gt=0.0, allow_inf_nan=False)


class CapabilityCheckpointSettings(BaseModel):
    """Bounded recovery endpoints and durable lineage milestones."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rolling_interval: int = Field(gt=0)
    rolling_keep: int = Field(gt=0)
    permanent_interval: int = Field(gt=0)


class CapabilityObjectiveSettings(BaseModel):
    """The direct competition objective and SMDP discount semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reward: Literal[
        "terminal_wdl",
        "paired_direct_terminal_wdl",
        "paired_direct_residual_wdl",
    ]
    discount: float = Field(allow_inf_nan=False)
    gae_lambda: float = Field(allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_terminal_semantics(self) -> CapabilityObjectiveSettings:
        """Disallow discounting or bootstrapped proxy returns."""
        if self.discount != 1.0 or self.gae_lambda != 1.0:
            raise ValueError("terminal W/D/L capability PPO requires gamma=1 and lambda=1")
        return self


class CapabilityOptimizationSettings(BaseModel):
    """PPO and W/D/L critic optimization settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ppo_epochs: int = Field(gt=0)
    episodes_per_minibatch: int = Field(gt=0)
    learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    weight_decay: float = Field(ge=0.0, allow_inf_nan=False)
    clip_epsilon: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    value_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    candidate_value_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    entropy_weight: float = Field(ge=0.0, allow_inf_nan=False)
    target_kl: float = Field(gt=0.0, allow_inf_nan=False)
    gradient_clip: float = Field(gt=0.0, allow_inf_nan=False)
    normalize_advantage: bool


class CapabilityRolloutSettings(BaseModel):
    """Production-shaped paired-seat rollout and inference batching."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seeds_per_update: int = Field(gt=0)
    batch_games: int = Field(gt=0)
    cpu_workers: int = Field(gt=0)
    inference_batch_size: int = Field(gt=0)
    host_memory_limit_gib: float = Field(gt=0.0, allow_inf_nan=False)
    gpu_memory_fraction: float = Field(gt=0.0, le=0.9, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_pairing(self) -> CapabilityRolloutSettings:
        """Keep every native rollout batch divisible into paired games."""
        if self.batch_games % 2:
            raise ValueError("capability rollout game batches must contain paired seats")
        return self


class CapabilityRlSettings(BaseModel):
    """One reproducible long-run capability-search PPO experiment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    direct_capability: Literal["kaito_v48"]
    resume_checkpoint: Path | None = None
    public_agent_manifest: Path
    output_dir: Path
    seed: int = Field(ge=0)
    rollout_seed_start: int = Field(ge=0)
    updates: int = Field(gt=0)
    opponents: tuple[str, ...]
    opponent_weights: dict[str, float]
    paired_seats: Literal[True]
    selection_seeds: tuple[int, ...]
    confirmation_seeds: tuple[int, ...]
    abi: CapabilityAbiSettings
    model: CapabilityModelSettings
    versions: FrozenCapabilityVersions
    search: CapabilitySearchSettings
    objective: CapabilityObjectiveSettings
    optimization: CapabilityOptimizationSettings
    rollout: CapabilityRolloutSettings
    checkpoint: CapabilityCheckpointSettings
    devices: tuple[str, ...]
    cpu_threads: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_training(self) -> CapabilityRlSettings:
        """Bind direct WDL training, artifacts, seeds and device topology."""
        _relative_path_under(self.output_dir, "outputs", "capability output_dir")
        _relative_path_under(
            self.public_agent_manifest,
            "data",
            "capability public_agent_manifest",
        )
        if self.public_agent_manifest.parts[:2] != ("data", "external"):
            raise ValueError("capability public_agent_manifest must remain under data/external/")
        if self.resume_checkpoint is not None:
            _relative_path_under(
                self.resume_checkpoint,
                "outputs",
                "capability resume_checkpoint",
            )
        if not self.opponents or len(set(self.opponents)) != len(self.opponents):
            raise ValueError("capability opponents must be nonempty and unique")
        if any(not opponent or opponent != opponent.strip() for opponent in self.opponents):
            raise ValueError("capability opponent identities must be canonical")
        if "self_play" in self.opponents:
            raise ValueError("capability v1 supports only frozen external native opponents")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("capability deployment budget must match official timeout semantics")
        if tuple(self.opponent_weights) != self.opponents:
            raise ValueError("capability opponent weights must follow opponent order")
        weights = tuple(self.opponent_weights.values())
        if any(not math.isfinite(weight) or weight <= 0.0 for weight in weights):
            raise ValueError("capability opponent weights must be finite and positive")
        if not math.isclose(math.fsum(weights), 1.0, abs_tol=1e-9):
            raise ValueError("capability opponent weights must sum to one")
        self._validate_seed_panels()
        self._validate_devices()
        episode_steps = self.environment.get("episodeSteps")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        if (
            not isinstance(episode_steps, int)
            or isinstance(episode_steps, bool)
            or episode_steps < 2
        ):
            raise ValueError("capability environment episodeSteps must allow a transition")
        if (
            not isinstance(market_orders, int)
            or isinstance(market_orders, bool)
            or market_orders < 1
        ):
            raise ValueError("capability environment market order capacity must be positive")
        return self

    def _validate_seed_panels(self) -> None:
        if not self.selection_seeds or not self.confirmation_seeds:
            raise ValueError("capability evaluation seed panels cannot be empty")
        if len(set(self.selection_seeds)) != len(self.selection_seeds) or len(
            set(self.confirmation_seeds)
        ) != len(self.confirmation_seeds):
            raise ValueError("capability evaluation seeds must be unique within each panel")
        if set(self.selection_seeds) & set(self.confirmation_seeds):
            raise ValueError("capability selection and confirmation seeds must be disjoint")
        rollout_end = self.rollout_seed_start + self.updates * self.rollout.seeds_per_update
        for seed in (*self.selection_seeds, *self.confirmation_seeds):
            if self.rollout_seed_start <= seed < rollout_end:
                raise ValueError("capability rollout and evaluation seeds must be disjoint")

    def _validate_devices(self) -> None:
        if not self.devices or len(set(self.devices)) != len(self.devices):
            raise ValueError("capability training devices must be nonempty and unique")
        parsed: list[torch.device] = []
        for value in self.devices:
            try:
                device = torch.device(value)
            except (RuntimeError, ValueError) as error:
                raise ValueError("capability training device is invalid") from error
            if device.type != "cuda" or device.index is None:
                raise ValueError("capability long training requires indexed CUDA devices")
            parsed.append(device)
        world_size = len(parsed)
        for name, numeric_value in (
            ("seeds_per_update", self.rollout.seeds_per_update),
            ("batch_games", self.rollout.batch_games),
            ("inference_batch_size", self.rollout.inference_batch_size),
            ("episodes_per_minibatch", self.optimization.episodes_per_minibatch),
        ):
            if numeric_value % world_size:
                raise ValueError(f"capability {name} must be divisible by device count")

    def checkpoint_contract(self) -> dict[str, object]:
        """Return exact resume semantics while allowing a longer run/output branch."""
        payload = self.model_dump(mode="json")
        for key in ("resume_checkpoint", "output_dir", "updates", "checkpoint"):
            payload.pop(key)
        return payload


class CapabilityRlAppSettings(BaseModel):
    """Hydra root for the independent capability PPO command."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    capability_rl: CapabilityRlSettings


__all__ = [
    "CapabilityAbiSettings",
    "CapabilityCheckpointSettings",
    "CapabilityModelSettings",
    "CapabilityObjectiveSettings",
    "CapabilityOptimizationSettings",
    "CapabilityRlAppSettings",
    "CapabilityRlSettings",
    "CapabilityRolloutSettings",
    "CapabilitySearchSettings",
    "FrozenCapabilityVersions",
]
