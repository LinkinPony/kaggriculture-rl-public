"""Translate visible farm needs into independently valued local operations."""

from typing import Any

from kagg_revue.opponents.enterprise.economy import ANIMALS, CROPS


def distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    """Use the unobstructed farm's Manhattan travel time."""
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def home(position: tuple[int, int]) -> tuple[int, int]:
    """Choose the closest of the four central shed access tiles."""
    return (min(5, max(4, position[0])), min(5, max(4, position[1])))


def movement(position: tuple[int, int], target: tuple[int, int]) -> list[Any]:
    """Move along a shortest path, preferring the longer remaining axis."""
    dx, dy = target[0] - position[0], target[1] - position[1]
    if abs(dx) >= abs(dy) and dx:
        return ["EAST" if dx > 0 else "WEST"]
    if dy:
        return ["SOUTH" if dy > 0 else "NORTH"]
    return ["PASS"]


def operations(
    tile: Any,
    position: tuple[int, int],
    inventory: dict[str, int],
    context: dict[str, Any],
) -> tuple[list[Any], float] | None:
    """Price upkeep, harvesting and investment without a precomputed route tape."""
    day, hour = context["day"], context["hour"]
    prices, settings = context["prices"], context["settings"]
    if tile == "LOCKED":
        return None
    animals = [item for item in ANIMALS if inventory.get(item, 0)]
    if tile is None or tile.get("kind") == "WEED":
        if hour >= 21 or day >= 28:
            return None
        if animals:
            if tile is not None:
                return ["DIG"], 110
            return ["BUILD_COOP" if animals[0] == "GOOSE" else "BUILD_PASTURE"], 150
        if (
            distance(position, home(position)) <= 1
            and context["animal_count"] < settings["central_reserve"]
        ):
            return None
        choices = [
            (value, item)
            for value, item in context["investments"]
            if item in CROPS and context["seeds"].get(item, 0) > 0
        ]
        if not choices:
            return None
        value, crop = choices[0]
        return (["DIG"] if tile is not None else ["PLANT", crop]), max(
            5, value * settings["plant_priority"]
        )
    if tile["kind"] == "PLANT":
        crop = tile["crop"]
        _, first, last, interval, cap = CROPS[crop]
        age = day - tile["planted_day"]
        mature = age >= first and tile["yield_units"] > 0
        expiry = tile.get("max_lifespan_step", -1)
        expired = expiry is not None and expiry >= 0 and expiry <= context["step"] + 24
        target_age = first if crop == "MELON" else last
        ready = mature and (interval or age >= target_age or day == 29 or expired)
        bonus = not interval and (last + 1) // 2 <= age <= last and tile["yield_units"] < cap
        bonus = bonus or (interval and first - 1 <= age <= first + interval * (cap - 1))
        if (
            context["settings"]["fertilize"]
            and bonus
            and not tile["watered_today"]
            and tile["fertilized_until_day"] < day
            and inventory.get("FERTILIZER", 0)
            and prices[crop] * (1.5 if interval else 2) > prices["FERTILIZER"]
        ):
            return ["FERTILIZE"], prices[crop] * 2
        if ready:
            if (
                not interval
                and not tile["watered_today"]
                and age <= last
                and tile["yield_units"] < cap
            ):
                return ["WATER"], prices[crop] * (1.1 if tile["consecutive_unwatered"] else 0.9)
            return ["HARVEST"], max(4, tile["yield_units"] * prices[crop]) * (2 if expired else 1)
        if expired:
            return ["DIG"], 30 if day < 27 else 0
        if not tile["watered_today"] and day < 29:
            critical = tile["consecutive_unwatered"] >= 1
            productive = not interval and (last + 1) // 2 <= age <= last
            productive = productive or (interval and age >= first - 1)
            if not critical and not productive:
                return None
            remaining = max(1, first - age)
            value = max(15, prices[crop] * (2 if crop == "MELON" else 1) / remaining**0.3)
            urgency = (4 if critical else 1) + (hour / 24) ** 3 * (8 if critical else 2)
            if tile["planted_day"] == day:
                urgency *= 2
            return ["WATER"], value * urgency * settings["water_priority"]
        return None
    if not tile.get("animal"):
        for animal in animals:
            if (animal == "GOOSE") == (tile["kind"] == "COOP"):
                return ["PLACE", animal, 1], 220
        return None
    animal = tile["animal"]
    _, first, interval, product = ANIMALS[animal]
    if not tile["fed_today"] and inventory.get("WHEAT", 0):
        value = max(50, prices["FERTILIZER"] + prices[product])
        if tile["consecutive_unfed"]:
            value *= 2 + (hour / 24) ** 3 * 10
        return ["FEED"], value
    if tile["yield_units"]:
        return ["HARVEST"], max(5, prices[product] * tile["yield_units"])
    if tile["fertilizer_available"]:
        return ["COLLECT_FERTILIZER"], max(1, prices["FERTILIZER"]) * settings[
            "fertilizer_priority"
        ]
    if not tile["cared_today"] and tile["fed_today"] and day < 29:
        return ["CARE"], max(1, prices[product]) * settings["care_priority"]
    return None
