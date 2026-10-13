"""Final-turn liquidation of every product the farm can still sell."""

from collections.abc import Mapping
from typing import Any

PRODUCTS = (
    "WHEAT",
    "CARROT",
    "TOMATO",
    "STRAWBERRY",
    "MELON",
    "EGG",
    "MILK",
    "WOOL",
    "FERTILIZER",
)
_EVERYTHING = 1000


def liquidate(
    observation: Mapping[str, Any], configuration: Mapping[str, Any], action: dict[str, Any]
) -> dict[str, Any]:
    """Return ``action``, rewritten on the last processed turn to sell every product.

    Money is the only terminal asset, so on that turn carried products are dropped
    from shed-access tiles and all market orders become sell-all orders, largest
    current value first so they fill before the opponent depresses the same price.

    Args:
        observation: The official per-seat observation.
        configuration: The official environment configuration.
        action: The deployed policy action for this turn.

    Returns:
        The original action before the last processed turn, otherwise the rewrite.
    """
    step = observation.get("step")
    if step is None or int(step) < int(configuration["episodeSteps"]) - 2:
        return action
    half = int(configuration["boardSize"]) // 2
    access = {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}
    farm = observation["farms"][int(observation["player"])]
    private = observation["private"]
    stock = {item: int(private["shed"].get(item, 0)) for item in PRODUCTS}
    hands = [list(order) for order in action.get("hands", [])]
    patched = {**action, "hands": hands}
    for index, (position, inventory) in enumerate(
        zip([farm["farmer"], *farm["hands"]], private["inventories"], strict=False)
    ):
        carried = {item: int(inventory.get(item, 0)) for item in PRODUCTS}
        if tuple(position) not in access or not any(carried.values()):
            continue
        stock = {item: stock[item] + carried[item] for item in PRODUCTS}
        if index == 0:
            patched["farmer"] = ["DROP"]
            continue
        hands.extend([["PASS"]] * (index - len(hands)))
        hands[index - 1] = ["DROP"]
    prices = observation["market"]["prices"]
    value = {item: stock[item] * float(prices.get(item, 1)) for item in PRODUCTS}
    patched["market"] = [
        ["SELL", item, _EVERYTHING]
        for item in sorted(PRODUCTS, key=lambda item: -value[item])
        if stock[item] > 0
    ]
    return patched


def expected_action(
    profile: Mapping[str, Any],
    observation: Mapping[str, Any],
    configuration: Mapping[str, Any],
    action: dict[str, Any],
) -> dict[str, Any]:
    """Return the action a package entry point must emit for a native policy action."""
    if profile.get("final_turn_liquidation"):
        return liquidate(observation, configuration, action)
    return action
