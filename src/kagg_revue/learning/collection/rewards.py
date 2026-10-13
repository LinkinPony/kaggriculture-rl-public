"""Check actual recurrent returns against the independent bounded-margin reference."""

import math
from typing import Any

import numpy as np
import torch

from kagg_revue.learning.collection.population import policy_rows
from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.rl.reward import margin_augmented_return


def margin_diagnostics(rollout: Rollout, settings: RuntimeSettings) -> dict[str, Any]:
    """Validate every learned seat and turn, including both self-play seats."""
    options = settings.ppo.cash_margin
    if options is None:
        return {}
    if settings.ppo.cash_weight or settings.ppo.win_weight != 1:
        raise ValueError("bounded cash-margin verification requires a unit WDL base")
    differences = rollout.cash - rollout.cash[:, ::-1]
    reference = np.array(
        [
            [
                margin_augmented_return(
                    int(np.sign(value)),
                    float(value),
                    beta=options.beta,
                    cash_scale=options.cash_scale,
                )
                for value in row
            ]
            for row in differences
        ]
    )
    selfplay = rollout.opponents.count("self_play")
    expected = torch.as_tensor(
        policy_rows(reference, selfplay),
        dtype=rollout.returns.dtype,
        device=rollout.returns.device,
    )
    actual = rollout.returns.reshape(-1, len(expected))
    error = float((actual - expected).abs().max())
    if not math.isfinite(error) or error > 1e-6:
        raise ValueError("collected returns differ from bounded terminal cash-margin rewards")
    return {
        "cash_margin_reward": options.model_dump(mode="json"),
        "terminal_reward_max_error": error,
    }
