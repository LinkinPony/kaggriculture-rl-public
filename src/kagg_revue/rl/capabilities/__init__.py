"""Actor-safe capability-search records and SMDP objectives."""

from kagg_revue.rl.capabilities.contract import (
    CAPABILITY_RECORD_SCHEMA_VERSION,
    CapabilityVersionContract,
    FrozenSearchContext,
)
from kagg_revue.rl.capabilities.data import (
    CapabilityCandidateSetRecord,
    CapabilityEpisodeRecord,
    MacroDecisionRecord,
    TensorCapabilityRolloutBatch,
    collate_capability_episodes,
)
from kagg_revue.rl.capabilities.objective import (
    MacroAdvantages,
    MacroPpoLoss,
    episode_balanced_mean,
    joint_macro_log_probability,
    macro_ppo_loss,
    paired_direct_residual_advantages,
    paired_direct_wdl_advantages,
    terminal_wdl_advantages,
)

__all__ = [
    "CAPABILITY_RECORD_SCHEMA_VERSION",
    "CapabilityCandidateSetRecord",
    "CapabilityEpisodeRecord",
    "CapabilityVersionContract",
    "FrozenSearchContext",
    "MacroAdvantages",
    "MacroDecisionRecord",
    "MacroPpoLoss",
    "TensorCapabilityRolloutBatch",
    "collate_capability_episodes",
    "episode_balanced_mean",
    "joint_macro_log_probability",
    "macro_ppo_loss",
    "paired_direct_residual_advantages",
    "paired_direct_wdl_advantages",
    "terminal_wdl_advantages",
]
