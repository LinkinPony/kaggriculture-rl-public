"""Episode-locked opening parameter noise for on-policy training."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.core.backend import BackendApi
from kagg_revue.rl.outcome import OutcomeActorCritic

PerspectiveKey = tuple[str, int, int]
RolloutJob = tuple[int, int, str]


@dataclass(frozen=True)
class OpeningResidual:
    """One episode-fixed action-head perturbation active for an opening prefix."""

    direction_id: int
    seed: int
    scale: float
    prefix_turns: int

    def __post_init__(self) -> None:
        """Reject residual identities that cannot be reproduced by the learner."""
        if self.direction_id < 0 or self.seed < 0:
            raise ValueError("opening residual identifiers must be nonnegative")
        if not math.isfinite(self.scale) or self.scale <= 0.0:
            raise ValueError("opening residual scale must be finite and positive")
        if self.prefix_turns < 1:
            raise ValueError("opening residual prefix must contain at least one turn")


@dataclass(frozen=True)
class OpeningProbe:
    """Clean opening geometry used to express noise magnitude in action space."""

    hidden: Tensor
    logits: Tensor
    legal_mask: Tensor

    def __post_init__(self) -> None:
        """Validate the compact CPU calibration bank."""
        values = (self.hidden, self.logits, self.legal_mask)
        if any(value.device.type != "cpu" for value in values):
            raise ValueError("opening probe tensors must reside on CPU")
        if self.hidden.ndim != 2 or self.logits.ndim != 2:
            raise ValueError("opening probe hidden states and logits must be rank two")
        if self.legal_mask.ndim != 2 or self.legal_mask.dtype != torch.bool:
            raise ValueError("opening probe legality must be a rank-two boolean tensor")
        if self.hidden.shape[0] != self.logits.shape[0]:
            raise ValueError("opening probe states and logits are not aligned")
        if self.logits.shape != self.legal_mask.shape:
            raise ValueError("opening probe logits and legality are not aligned")
        if self.hidden.shape[0] < 1 or not bool(self.legal_mask.any(dim=-1).all()):
            raise ValueError("opening probe contains an empty legal support")
        if not bool(torch.isfinite(self.hidden).all()):
            raise ValueError("opening probe hidden states are not finite")
        if not bool(torch.isfinite(self.logits).all()):
            raise ValueError("opening probe logits are not finite")


@dataclass(frozen=True)
class OpeningNoiseCalibration:
    """Observed action-space effect and per-episode residual scales."""

    status: str
    target_escape: float
    mean_escape: float
    scales: tuple[float, ...]
    per_direction_escape: tuple[float, ...]
    action_probability: tuple[float, ...]
    unreachable_directions: int

    def __post_init__(self) -> None:
        """Require one finite calibration result per sampled direction."""
        if len(self.scales) != len(self.per_direction_escape):
            raise ValueError("opening scales and measured effects are not aligned")
        if not 0.0 < self.target_escape < 1.0:
            raise ValueError("opening target escape must lie strictly between zero and one")
        if not math.isfinite(self.mean_escape):
            raise ValueError("opening mean escape must be finite")
        if any(not math.isfinite(value) or value < 0.0 for value in self.scales):
            raise ValueError("opening residual scales must be finite and nonnegative")
        if self.unreachable_directions < 0 or self.unreachable_directions > len(self.scales):
            raise ValueError("opening unreachable-direction count is invalid")


@dataclass(frozen=True)
class OpeningNoisePlan:
    """Per-update clean/noisy mixture applied inside the ordinary PPO rollout."""

    assignments: Mapping[PerspectiveKey, OpeningResidual]
    total_perspectives: int
    sampled_perspectives: int
    prefix_turns: int
    calibration: OpeningNoiseCalibration

    def __post_init__(self) -> None:
        """Validate mixture cardinality and residual horizon."""
        if self.total_perspectives < 1:
            raise ValueError("opening noise plan needs at least one training perspective")
        if not 0 <= len(self.assignments) <= self.sampled_perspectives <= (
            self.total_perspectives
        ):
            raise ValueError("opening noise plan has inconsistent perspective counts")
        if self.prefix_turns < 1:
            raise ValueError("opening noise prefix must contain at least one turn")
        if any(
            residual.prefix_turns != self.prefix_turns
            for residual in self.assignments.values()
        ):
            raise ValueError("opening residuals use inconsistent prefix horizons")

    def report(self) -> dict[str, object]:
        """Return small diagnostics without granting them promotion authority."""
        active_scales = [residual.scale for residual in self.assignments.values()]
        return {
            "status": "active" if active_scales else self.calibration.status,
            "training_path": "on_policy_ppo",
            "episode_locked": True,
            "prefix_turns": self.prefix_turns,
            "total_perspectives": self.total_perspectives,
            "noisy_perspectives": len(active_scales),
            "noisy_fraction": len(active_scales) / self.total_perspectives,
            "sampled_perspectives": self.sampled_perspectives,
            "target_escape": self.calibration.target_escape,
            "mean_calibrated_escape": self.calibration.mean_escape,
            "unreachable_directions": self.calibration.unreachable_directions,
            "scale_minimum": min(active_scales, default=0.0),
            "scale_median": float(np.median(active_scales)) if active_scales else 0.0,
            "scale_maximum": max(active_scales, default=0.0),
            "action_probability": list(self.calibration.action_probability),
        }


def normalized_action_head_direction(
    seed: int,
    actions: int,
    width: int,
) -> NDArray[np.float32]:
    """Materialize IID action rows with width-normalized Gaussian entries."""
    if seed < 0 or actions < 1 or width < 1:
        raise ValueError("opening direction shape and seed must be positive")
    generator = np.random.Generator(np.random.PCG64(seed))
    values = generator.standard_normal((actions, width), dtype=np.float32)
    values *= np.float32(width**-0.5)
    return values


def materialize_opening_residuals(
    identities: Sequence[OpeningResidual | None],
    actions: int,
    width: int,
    *,
    force: bool = False,
) -> NDArray[np.float32] | None:
    """Return deterministic per-row residual weights without action offsets."""
    if not identities or (not force and not any(value is not None for value in identities)):
        return None
    result = np.zeros((len(identities), actions, width), dtype=np.float32)
    for row, identity in enumerate(identities):
        if identity is None:
            continue
        result[row] = normalized_action_head_direction(identity.seed, actions, width)
        result[row] *= np.float32(identity.scale)
    return result


def _direction_seeds(count: int, seed: int) -> tuple[int, ...]:
    if count < 1 or seed < 0:
        raise ValueError("opening direction count and seed must be positive")
    generator = np.random.Generator(np.random.PCG64(seed))
    result: list[int] = []
    observed: set[int] = set()
    while len(result) < count:
        value = int(generator.integers(0, np.iinfo(np.int64).max))
        if value not in observed:
            observed.add(value)
            result.append(value)
    return tuple(result)


def _calibration_geometry(
    probe: OpeningProbe,
    correction: Tensor,
    scales: Tensor,
) -> tuple[Tensor, Tensor]:
    clean_logits = probe.logits.float().masked_fill(~probe.legal_mask, -torch.inf)
    clean_top = clean_logits.argmax(dim=-1)
    noisy_logits = (
        probe.logits[None].float() + scales[:, None, None] * correction
    ).masked_fill(~probe.legal_mask[None], -torch.inf)
    probabilities = torch.softmax(noisy_logits, dim=-1)
    top_index = clean_top[None, :, None].expand(correction.shape[0], -1, 1)
    escape = 1.0 - probabilities.gather(-1, top_index).squeeze(-1)
    return escape.mean(dim=1), probabilities.mean(dim=(0, 1))


def calibrate_direction_scales(
    probe: OpeningProbe,
    direction_seeds: Sequence[int],
    *,
    target_escape: float,
    maximum_scale: float,
    bisection_steps: int,
) -> OpeningNoiseCalibration:
    """Normalize every sampled direction by its observed opening action effect."""
    if not direction_seeds or len(set(direction_seeds)) != len(direction_seeds):
        raise ValueError("opening calibration needs unique directions")
    if not 0.0 < target_escape < 1.0:
        raise ValueError("opening target escape must lie strictly between zero and one")
    if not math.isfinite(maximum_scale) or maximum_scale <= 0.0:
        raise ValueError("opening maximum scale must be finite and positive")
    if bisection_steps < 1:
        raise ValueError("opening scale calibration needs at least one bisection step")

    directions = torch.stack(
        [
            torch.from_numpy(
                normalized_action_head_direction(
                    seed,
                    probe.logits.shape[1],
                    probe.hidden.shape[1],
                )
            )
            for seed in direction_seeds
        ]
    )
    correction = torch.einsum("nd,kad->kna", probe.hidden.float(), directions)
    count = len(direction_seeds)
    zeros = torch.zeros(count)
    clean_escape, clean_probability = _calibration_geometry(probe, correction, zeros)
    if float(clean_escape.mean()) >= target_escape:
        return OpeningNoiseCalibration(
            status="clean_support_satisfies_target",
            target_escape=target_escape,
            mean_escape=float(clean_escape.mean()),
            scales=tuple(0.0 for _ in direction_seeds),
            per_direction_escape=tuple(float(value) for value in clean_escape),
            action_probability=tuple(float(value) for value in clean_probability),
            unreachable_directions=0,
        )

    maximum = torch.full((count,), maximum_scale)
    maximum_escape, _ = _calibration_geometry(probe, correction, maximum)
    reachable = maximum_escape >= target_escape
    low = zeros
    high = maximum
    for _ in range(bisection_steps):
        middle = 0.5 * (low + high)
        escape, _ = _calibration_geometry(probe, correction, middle)
        below = escape < target_escape
        low = torch.where(below, middle, low)
        high = torch.where(below, high, middle)
    scales = torch.where(reachable, high, maximum)
    escape, probability = _calibration_geometry(probe, correction, scales)
    unreachable = int((~reachable).sum().item())
    return OpeningNoiseCalibration(
        status="active" if unreachable == 0 else "partly_unreachable",
        target_escape=target_escape,
        mean_escape=float(escape.mean()),
        scales=tuple(float(value) for value in scales),
        per_direction_escape=tuple(float(value) for value in escape),
        action_probability=tuple(float(value) for value in probability),
        unreachable_directions=unreachable,
    )


def _training_perspectives(jobs: Sequence[RolloutJob]) -> tuple[PerspectiveKey, ...]:
    keys: list[PerspectiveKey] = []
    observed: set[PerspectiveKey] = set()
    for seed, seat, opponent in jobs:
        players = (seat, 1 - seat) if opponent == "self_play" else (seat,)
        for player in players:
            key = (opponent, int(seed), int(player))
            if key in observed:
                raise ValueError("opening noise jobs contain a duplicate training perspective")
            observed.add(key)
            keys.append(key)
    if not keys:
        raise ValueError("opening noise needs at least one rollout job")
    return tuple(keys)


def build_opening_noise_plan(
    probe: OpeningProbe,
    jobs: Sequence[RolloutJob],
    *,
    noisy_fraction: float,
    selection_seed: int,
    direction_seed: int,
    prefix_turns: int,
    target_escape: float,
    maximum_scale: float,
    bisection_steps: int,
) -> OpeningNoisePlan:
    """Sample a reproducible episode mixture and calibrate every noisy row."""
    if not 0.0 < noisy_fraction <= 1.0:
        raise ValueError("opening noisy fraction must lie in (0, 1]")
    if selection_seed < 0 or direction_seed < 0:
        raise ValueError("opening noise seeds must be nonnegative")
    if prefix_turns < 1:
        raise ValueError("opening noise prefix must contain at least one turn")
    perspectives = _training_perspectives(jobs)
    sampled = max(1, min(len(perspectives), round(len(perspectives) * noisy_fraction)))
    shuffled = list(perspectives)
    random.Random(selection_seed).shuffle(shuffled)
    selected = shuffled[:sampled]
    seeds = _direction_seeds(sampled, direction_seed)
    calibration = calibrate_direction_scales(
        probe,
        seeds,
        target_escape=target_escape,
        maximum_scale=maximum_scale,
        bisection_steps=bisection_steps,
    )
    assignments = {
        key: OpeningResidual(
            direction_id=index,
            seed=seed,
            scale=scale,
            prefix_turns=prefix_turns,
        )
        for index, (key, seed, scale) in enumerate(
            zip(selected, seeds, calibration.scales, strict=True)
        )
        if scale > 0.0
    }
    return OpeningNoisePlan(
        assignments=assignments,
        total_perspectives=len(perspectives),
        sampled_perspectives=sampled,
        prefix_turns=prefix_turns,
        calibration=calibration,
    )


def _autocast(device: torch.device) -> Any:
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.bfloat16)
    return nullcontext()


def probe_official_openings(
    model: OutcomeActorCritic,
    backend: BackendApi,
    environment: Mapping[str, object],
    unit_limit: int,
    seeds: Sequence[int],
    device: torch.device,
) -> OpeningProbe:
    """Evaluate clean logits and decoder hidden states at initial decisions."""
    if not seeds:
        raise ValueError("opening probe needs at least one environment seed")
    if model.actor.architecture.turn_fact_features:
        raise ValueError("opening probe does not support derived turn facts")
    engines = [backend.engine(seed=int(seed), configuration=dict(environment)) for seed in seeds]
    sessions = [
        engine.policy_session(player, unit_limit) for engine in engines for player in (0, 1)
    ]
    policy_batch = backend.policy_session_batch(sessions, min(8, len(sessions)))
    board_value, unit_value, global_value = policy_batch.encode()
    phase_value, legal_value = policy_batch.decision_inputs()
    architecture = model.actor.architecture
    board = torch.as_tensor(np.asarray(board_value), device=device)
    units = torch.as_tensor(np.asarray(unit_value), device=device)
    globals_ = torch.as_tensor(np.asarray(global_value), device=device)
    phases = torch.as_tensor(np.asarray(phase_value), dtype=torch.long, device=device)
    legal = torch.as_tensor(np.asarray(legal_value), dtype=torch.bool, device=device)
    previous_actions = torch.zeros(
        (len(sessions), architecture.max_decisions),
        dtype=torch.long,
        device=device,
    )
    previous_quantities = torch.zeros_like(previous_actions)
    previous_mask = torch.zeros_like(previous_actions, dtype=torch.bool)
    economic_state = (
        torch.as_tensor(
            np.asarray(policy_batch.gpu_state()),
            dtype=torch.int32,
            device=device,
        )
        if model.actor.economics is not None
        else None
    )
    modes = tuple((module, module.training) for module in model.actor.modules())
    model.actor.eval()
    try:
        with torch.inference_mode(), _autocast(device):
            context, _, _, _ = model.actor.start_turn(
                board,
                units,
                globals_,
                previous_actions,
                previous_quantities,
                previous_mask,
                None,
                economic_state=economic_state,
                strategy_state=None,
                sample_skill=False,
            )
            state = model.actor.action.initial_state(context)
            economic_prefix = (
                model.actor.economics.prefix_features(economic_state, phases)
                if model.actor.economics is not None and economic_state is not None
                else None
            )
            economic_candidates = (
                model.actor.economics.candidate_features(economic_state, phases)
                if model.actor.economics is not None and economic_state is not None
                else None
            )
            logits, hidden, _ = model.actor.action.next_cached(
                None,
                None,
                phases,
                context,
                state,
                economic_prefix_facts=economic_prefix,
                economic_candidate_facts=economic_candidates,
            )
    finally:
        for module, training in modes:
            module.training = training
    return OpeningProbe(
        hidden=hidden.detach().float().cpu(),
        logits=logits.detach().float().cpu(),
        legal_mask=legal.detach().bool().cpu(),
    )


__all__ = [
    "OpeningNoiseCalibration",
    "OpeningNoisePlan",
    "OpeningProbe",
    "OpeningResidual",
    "PerspectiveKey",
    "RolloutJob",
    "build_opening_noise_plan",
    "calibrate_direction_scales",
    "materialize_opening_residuals",
    "normalized_action_head_direction",
    "probe_official_openings",
]
