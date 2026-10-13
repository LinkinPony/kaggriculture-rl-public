"""Causal single-turn demonstration targets over the grounded policy interface."""

from typing import Any

import numpy as np
from numpy.typing import NDArray

from kagg_revue.datasets.observations import ReplayObservations
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout


def quantity_columns(layout: ContractLayout) -> NDArray[np.int64]:
    """Identify literal quantity fields before global vocabulary encoding."""
    return np.concatenate(
        (
            np.arange(2, layout.work_factors, 4),
            np.arange(layout.work_factors + 1, layout.factors, 2),
        )
    )


def encode(
    replay: dict[str, Any], layout: ContractLayout
) -> tuple[NDArray[np.float16], NDArray[np.int64], NDArray[np.bool_], dict[str, Any]]:
    """Encode current observations and the immediately following applied unit action.

    Market requests retain their original ordering and exact quantities. Rows
    whose unit choices require another unit's same-turn inventory transfer are
    excluded if the grounded actor's initial-state support cannot express them.
    No future destination, action sequence, cash target or teacher weight enters
    an input feature. Quantity fields are still literal counts in this output.
    """
    if layout.network.architecture not in {"grounded-v1", "grounded-v2"} or layout.capacity != 1:
        raise ValueError("demonstrations require the single-turn grounded interface")
    base = layout.observation
    steps = replay["steps"]
    if len(steps) != base.turns + 1:
        raise ValueError("demonstrations require a complete official episode")
    sequences = [ReplayObservations() for _ in range(2)]
    normalized = [
        [
            {**state, "observation": sequences[seat].update(state["observation"], step)}
            for seat, state in enumerate(pair)
        ]
        for step, pair in enumerate(steps)
    ]
    observations = np.empty((2, base.turns, base.features), np.float16)
    raw = np.empty((2, base.turns, base.slots, 2), np.int64)
    for seat in (0, 1):
        session = native.ContractSession(replay["configuration"], base.units)
        session.encode_replay_into(normalized, seat, observations[seat], raw[seat])
    observations = observations.transpose(1, 0, 2).copy()
    raw = raw.transpose(1, 0, 2, 3)
    units = observations[
        ..., base.board_features : base.board_features + base.units * base.unit_features
    ].reshape(base.turns, 2, base.units, base.unit_features)
    positions = np.rint(units[..., 2:4].astype(np.float32) * (layout.board_size - 1)).astype(
        np.int64
    )
    support = observations[..., -base.support_features :].reshape(base.turns, 2, base.units, 44)
    op = raw[..., : base.units, 0]
    supported = np.take_along_axis(support, op[..., None], -1).squeeze(-1) > 0
    present = units[..., 0] > 0
    eligible = np.asarray((~present | supported).all(-1), dtype=np.bool_)
    labels = np.zeros((base.turns, 2, layout.factors), np.int64)
    labels[..., quantity_columns(layout)] = 1
    jobs = labels[..., : layout.work_factors].reshape(base.turns, 2, base.units, 2, 4)
    targets = positions.copy()
    targets[..., 0] += (op == 3).astype(np.int64) - (op == 4)
    targets[..., 1] += (op == 2).astype(np.int64) - (op == 1)
    jobs[..., 0, 0] = np.where(
        present & (op != 0), 1 + targets[..., 0] + layout.board_size * targets[..., 1], 0
    )
    jobs[..., 0, 1] = np.where(present & (op >= 5), op, 0)
    jobs[..., 0, 2] = np.maximum(raw[..., : base.units, 1], 1)
    market = labels[..., layout.work_factors :].reshape(base.turns, 2, base.markets, 2)
    market[:] = raw[..., base.units :, :]
    market[..., 1] = np.maximum(market[..., 1], 1)
    return (
        observations,
        labels,
        eligible,
        {
            "candidate_rows": int(eligible.size),
            "eligible_rows": int(eligible.sum()),
            "unsupported_unit_rows": int((~eligible).sum()),
            "inventory_order_reconstructions": sum(s.reordered_inventories for s in sequences),
            "represented_unit_tokens": np.unique(op[present]).tolist(),
        },
    )
