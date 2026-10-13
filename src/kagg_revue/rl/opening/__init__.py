"""Continuous episode-locked opening exploration inside PPO."""

from kagg_revue.rl.opening.noise import (
    OpeningNoiseCalibration,
    OpeningNoisePlan,
    OpeningProbe,
    OpeningResidual,
    PerspectiveKey,
    RolloutJob,
    build_opening_noise_plan,
    calibrate_direction_scales,
    materialize_opening_residuals,
    normalized_action_head_direction,
    probe_official_openings,
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
