"""Recover ordered inventory semantics from complete, possibly sorted JSON frames."""

from typing import Any


class ReplayObservations:
    """Track one seat causally from its empty initial inventory.

    Daily JSON can alphabetize object keys. Each official unit action adds at
    most one inventory key, so consecutive key sets recover insertion order:
    retain surviving keys in their previous order and append the new key.
    Deletion and day resets discard keys. No future frame or native state is
    used to build this independent reference for the actor features.
    """

    def __init__(self) -> None:
        """Require a complete prefix starting at the initial observation."""
        self.step = -1
        self.seat = -1
        self.orders: list[tuple[str, ...]] = []
        self.reordered_inventories = 0

    def update(self, observation: dict[str, Any], step: int) -> dict[str, Any]:
        """Copy the private mappings with recovered order and an explicit clock."""
        seat = observation["player"]
        if (
            step != self.step + 1
            or observation.get("step", step) != step
            or seat not in (0, 1)
            or self.seat not in (-1, seat)
        ):
            raise ValueError("replay observations require a complete, ordered single-seat prefix")
        inventories = []
        orders = []
        for unit, inventory in enumerate(observation["private"]["inventories"]):
            previous = self.orders[unit] if unit < len(self.orders) else ()
            added = inventory.keys() - set(previous)
            if (step == 0 and inventory) or len(added) > 1:
                raise ValueError("inventory insertion order cannot be recovered from this prefix")
            order = (*(key for key in previous if key in inventory), *added)
            inventories.append({key: inventory[key] for key in order})
            orders.append(order)
            self.reordered_inventories += tuple(inventory) != order
        self.step, self.seat, self.orders = step, seat, orders
        return {
            **observation,
            "step": step,
            "private": {**observation["private"], "inventories": inventories},
        }


def difference(left: Any, right: Any, path: str = "observation") -> str | None:
    """Compare all values, including semantically relevant inventory key order."""
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            return f"{path}: keys differ ({left.keys() ^ right.keys()})"
        if ".inventories[" in path and list(left) != list(right):
            return f"{path}: inventory insertion order differs"
        for key in left:
            found = difference(left[key], right[key], f"{path}.{key}")
            if found:
                return found
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return f"{path}: lengths {len(left)} != {len(right)}"
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            found = difference(a, b, f"{path}[{index}]")
            if found:
                return found
    elif left != right:
        return f"{path}: native={left!r}, replay={right!r}"
    return None
