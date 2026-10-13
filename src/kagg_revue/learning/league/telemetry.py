"""Physical-game accounting for mutual matches and two-seat self-play tapes."""

from typing import Any

from kagg_revue.learning.league.config import MEMBERS


def combine_pairs(workers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Sum disjoint GPU game shards before deriving rates or cash averages."""
    pairs = {}
    for name in workers[0]["pairs"]:
        values = [worker["pairs"][name] for worker in workers]
        item = {field: sum(value[field] for value in values) for field in values[0]}
        item.update(
            win_fraction=item["wins"] / item["games"],
            mean_cash_left=item["cash_left_sum"] / item["games"],
            mean_cash_right=item["cash_right_sum"] / item["games"],
        )
        if "absolute_cash_difference_sum" in item:
            item["mean_absolute_cash_difference"] = (
                item["absolute_cash_difference_sum"] / item["games"]
            )
        pairs[name] = item
    return pairs


def member_outcomes(pairs: dict[str, Any], member: str) -> dict[str, Any]:
    """Count each model's physical games once; self-play WDL uses seat zero.

    Each self-play seat has half the loss weight, so physical-game fraction
    also describes the optimizer mass. Both trajectories remain on-policy.
    """
    if member not in MEMBERS:
        raise ValueError("unknown league member")
    result = {}
    for name, panel in pairs.items():
        left, right = name.split("_vs_")
        if member not in (left, right):
            continue
        selfplay = left == right
        own_left = member == left
        games = panel["games"]
        own_cash = panel["cash_left_sum" if own_left else "cash_right_sum"]
        other_cash = panel["cash_right_sum" if own_left else "cash_left_sum"]
        result["self_play" if selfplay else right if own_left else left] = {
            "games": games,
            "training_trajectories": games * (2 if selfplay else 1),
            "wins": panel["wins" if own_left else "losses"],
            "ties": panel["draws"],
            "losses": panel["losses" if own_left else "wins"],
            "mean_terminal_cash": (own_cash + other_cash) / (2 * games)
            if selfplay
            else own_cash / games,
            "mean_cash_difference": (own_cash - other_cash) / games,
        }
    total = sum(panel["games"] for panel in result.values())
    for panel in result.values():
        panel["training_fraction"] = panel["games"] / total
    return result
