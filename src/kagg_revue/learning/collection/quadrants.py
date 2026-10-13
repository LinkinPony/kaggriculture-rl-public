"""Passive quadrant statistics from the learner's already collected board features."""

from collections.abc import Sequence
from typing import Any

import torch
from torch import Tensor

from kagg_revue.policy.contracts import ContractLayout

NAMES = ("NW", "NE", "SW", "SE")
COUNTS = ("unlocked", "developed", "productive", "unused", "unlock_step_sum", "peak_tiles_sum")


def _frames(observations: Tensor, layout: ContractLayout) -> Tensor:
    """Count own-board tiles; planes follow actor-observation-v2's fixed ABI."""
    size = layout.board_size
    board = observations[..., : layout.observation.board_features // 2].reshape(
        *observations.shape[:-1], 29, size, size
    )
    # Native planes: locked=1, plant=3, coop=4, pasture=5, has_animal=17.
    planes = board[..., [1, 3, 4, 5, 17], :, :].float()
    quadrants = planes.reshape(*planes.shape[:-2], 2, size // 2, 2, size // 2)
    tiles = quadrants.sum(dim=(-3, -1)).flatten(-2)
    owned = (tiles[..., 0, :] == 0).float()
    developed = tiles[..., 1, :] + tiles[..., 2, :] + tiles[..., 3, :]
    productive = tiles[..., 1, :] + tiles[..., 4, :]
    return torch.stack((owned, developed, productive), dim=-1)


@torch.no_grad()
def measure(observations: Tensor, terminal: Tensor, layout: ContractLayout) -> dict[str, Any]:
    """Reduce complete, every-turn learner trajectories, including final settlement.

    Frozen opponent rows never enter the rollout tape. Unsupported sparse or suffix
    rollouts return no measurement instead of pretending they cover the whole game.
    This consumes no RNG, changes no policy buffers, and copies only compact totals
    back to the host once per collection group.
    """
    if (
        layout.interval != 1
        or observations.shape[0] != layout.observation.turns
        or layout.board_size % 2
        or layout.observation.board_features != 58 * layout.board_size**2
    ):
        return {}
    frames = _frames(observations, layout)
    final = _frames(terminal, layout).to(device=observations.device)
    frames = torch.cat((frames, final.unsqueeze(0)))
    present = frames > 0
    ever = present.any(dim=0)
    first = torch.where(
        present[..., 0],
        torch.arange(len(frames), device=frames.device)[:, None, None],
        len(frames),
    ).amin(dim=0)
    owned = ever[..., 0]
    totals = (
        torch.stack(
            (
                owned.sum(dim=0),
                ever[..., 1].sum(dim=0),
                ever[..., 2].sum(dim=0),
                (owned & ~ever[..., 2]).sum(dim=0),
                torch.where(owned, first, 0).sum(dim=0),
                frames[..., 2].amax(dim=0).sum(dim=0),
            ),
            dim=-1,
        )
        .cpu()
        .tolist()
    )
    return {
        "trajectories": observations.shape[1],
        "quadrants": {
            name: dict(zip(COUNTS, values, strict=True))
            for name, values in zip(NAMES, totals, strict=True)
        },
    }


def combine(panels: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Combine raw counts before calculating rates, including unequal rank/group sizes."""
    if not panels or any(not panel for panel in panels):
        return {}
    count = sum(panel["trajectories"] for panel in panels)
    result: dict[str, Any] = {"trajectories": count, "quadrants": {}}
    for name in NAMES:
        row = {key: sum(panel["quadrants"][name][key] for panel in panels) for key in COUNTS}
        row.update({f"{key}_rate": row[key] / count for key in COUNTS[:4]})
        row["mean_unlock_step"] = (
            row["unlock_step_sum"] / row["unlocked"] if row["unlocked"] else None
        )
        row["mean_peak_productive_tiles"] = row["peak_tiles_sum"] / count
        result["quadrants"][name] = row
    return result
