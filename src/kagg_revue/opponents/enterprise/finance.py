"""Working capital, purchase reservations and market execution for the farm director."""

from typing import Any

from kagg_revue.opponents.enterprise.economy import ANIMALS, CROPS


def market_orders(
    settings: dict[str, Any],
    ranking: list[tuple[float, str]],
    farm: dict[str, Any],
    shed: dict[str, int],
    seeds: dict[str, int],
    animals: int,
    owned: int,
    day: int,
    hour: int,
    prices: dict[str, int],
    carried_wheat: int,
) -> list[list[Any]]:
    """Finance investments while protecting working capital and daily feed."""
    orders: list[list[Any]] = []
    cash = farm["money"]
    fertilizer = 0
    if settings["buy_fertilizer"] and day < 29:
        for row in farm["tiles"]:
            for tile in row:
                if not isinstance(tile, dict) or tile["kind"] != "PLANT":
                    continue
                crop = tile["crop"]
                _, first, last, interval, cap = CROPS[crop]
                age = day - tile["planted_day"]
                productive = interval and first - 2 <= age <= first + interval * (cap - 1)
                productive = productive or (not interval and (last + 1) // 2 - 1 <= age <= last)
                if (
                    productive
                    and tile["fertilized_until_day"] < day + 1
                    and prices[crop] * 1.5 > prices["FERTILIZER"]
                ):
                    fertilizer += 1
        fertilizer = min(12, fertilizer)
    wheat = max(0, animals + 2 - carried_wheat) if day < 29 and animals else 0
    for item, count in sorted(shed.items(), key=lambda pair: prices.get(pair[0], 0), reverse=True):
        reserve = wheat if item == "WHEAT" else 0
        if item == "FERTILIZER" and settings["fertilize"] and (day < 29) and (cash > 2000):
            reserve = max(3, fertilizer)
        amount = count - reserve
        if item not in ANIMALS and amount > 0:
            orders.append(["SELL", item, amount])
            cash += amount * prices[item]
    occupied = sum(
        isinstance(tile, dict) and tile.get("kind") != "WEED"
        for row in farm["tiles"]
        for tile in row
    )
    workers = min(settings["workers"], settings["initial_workers"] + occupied // 7 + animals // 3)
    if hour < 4:
        a, b = (1, 1)
        for _ in range(farm["hires_today"]):
            a, b = (b, a + b)
        for _ in range(max(0, workers - len(farm["hands"]))):
            if cash < a + 40:
                break
            orders.append(["HIRE"])
            cash -= a
            a, b = (b, a + b)
    deficit = max(0, wheat - shed.get("WHEAT", 0))
    if deficit and hour < 20:
        orders.append(["BUY_PRODUCT", "WHEAT", deficit])
        cash -= deficit * prices["WHEAT"]
    if fertilizer > shed.get("FERTILIZER", 0) and hour < 6:
        quantity = min(
            fertilizer - shed.get("FERTILIZER", 0), max(0, int((cash - 300) / prices["FERTILIZER"]))
        )
        if quantity:
            orders.append(["BUY_PRODUCT", "FERTILIZER", quantity])
            cash -= quantity * prices["FERTILIZER"]
    if occupied >= owned * 0.75 and owned < 100 and (day < 23):
        cost = (1000, 2000, 4000)[len(farm["unlocked_quadrants"]) - 1]
        if cash > cost + 600:
            orders.append(["BUY_LAND"])
            cash -= cost
    for score, item in ranking:
        if hour > 18 or score <= 0:
            continue
        if item in CROPS:
            cost = CROPS[item][0]
            if (
                seeds[item] < 3
                and occupied + sum(seeds.values()) < owned
                and (cash > cost * 3 + 100)
            ):
                orders.append(["BUY_SEED", item, 3 - seeds[item]])
                cash -= cost * (3 - seeds[item])
                break
        elif animals + sum(shed.get(item, 0) for item in ANIMALS) < settings["animal_limit"]:
            cost, first, _, _ = ANIMALS[item]
            reserve = 1200 + (animals + 1) * prices["WHEAT"] * min(first, 4)
            if cash > cost + reserve and occupied < owned - 3:
                orders.append(["BUY_ANIMAL", item, 1])
                break
    return orders[:10]
