"""Closed-loop qualification of immediately applied grounded demonstration targets."""

from dataclasses import replace
from typing import Any

import numpy as np
import torch

from kagg_revue.datasets.demonstrations.encoding import encode, quantity_columns
from kagg_revue.datasets.observations import ReplayObservations, difference
from kagg_revue.learning.config import Exploration
from kagg_revue.learning.initialization import random_policy
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import log_probabilities


def verify(
    replay: dict[str, Any], layout: ContractLayout, *, clip_quantities: bool = False
) -> dict[str, Any]:
    """Replay decoded targets and test their probability under a fresh random actor.

    Unsupported rows use the original source action to preserve the reference
    trajectory and are reported separately. Every represented row must match
    the complete state and actor features; no approximate state repair is used.
    """
    torch.set_num_threads(2)
    observations, actions, eligible, counts = encode(replay, layout)
    qfields = quantity_columns(layout)
    if clip_quantities:
        quantities = layout.observation.quantities
        if quantities != tuple(range(1, len(quantities) + 1)):
            raise ValueError("quantity clipping requires a contiguous positive integer vocabulary")
        counts["quantity_clipped_fields"] = int((actions[..., qfields] > quantities[-1]).sum())
        actions[..., qfields] = np.minimum(actions[..., qfields], quantities[-1])
    else:
        quantities = tuple(int(q) for q in np.unique(actions[..., qfields]))
    layout = replace(
        layout,
        observation=replace(layout.observation, quantities=quantities, width=16),
        network=replace(layout.network, depth=1, critic_width=16, critic_depth=1),
    )
    actions[..., qfields] = np.searchsorted(quantities, actions[..., qfields])
    engine = native.Engine(replay["info"]["seed"], replay["configuration"])
    sessions = [
        native.ContractSession(replay["configuration"], layout.observation.units) for _ in range(2)
    ]
    sequences = [ReplayObservations() for _ in range(2)]
    fields = ("player", "step", "day", "hour", "farms", "private", "market", "town")
    packed = np.empty((1, layout.observation.features), np.float16)
    for step, states in enumerate(replay["steps"]):
        selected = []
        for seat in range(2):
            actual = engine.observation(seat)
            expected = sequences[seat].update(states[seat]["observation"], step)
            mismatch = difference(
                {key: actual[key] for key in fields}, {key: expected[key] for key in fields}
            )
            if mismatch:
                raise ValueError(f"grounded target replay mismatch at {step}:{seat}: {mismatch}")
            if step == layout.observation.turns:
                continue
            sessions[seat].update(actual)
            sessions[seat].observe_into(packed)
            np.testing.assert_array_equal(packed[0], observations[step, seat])
            if eligible[step, seat]:
                sessions[seat].set_program(actions[step, seat : seat + 1], 1, list(quantities))
                selected.append(sessions[seat].program_action())
            else:
                selected.append(replay["steps"][step + 1][seat]["action"])
        if selected:
            engine.step(*selected)
    actor = random_policy(layout, 47003, Exploration())
    features = torch.from_numpy(observations[eligible])
    targets = torch.from_numpy(actions[eligible])
    steps = torch.from_numpy(np.nonzero(eligible)[0])
    minimum = 0.0
    with torch.no_grad():
        for start in range(0, len(features), 64):
            section = slice(start, start + 64)
            logits = actor(features[section], steps[section], targets[section])
            probabilities = log_probabilities(logits, targets[section])
            if not torch.isfinite(probabilities).all() or probabilities.min() < -1e8:
                raise ValueError("a retained demonstration target is outside the actor support")
            minimum = min(minimum, float(probabilities.min()))
    return {
        **counts,
        "seed": replay["info"]["seed"],
        "verified_observations": 2 * len(replay["steps"]),
        "minimum_random_actor_log_probability": minimum,
        "random_actor_seed": 47003,
        "terminal_cash": [engine.money(seat) for seat in (0, 1)],
        "matched": True,
    }
