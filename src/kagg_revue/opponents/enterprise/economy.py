"""Price forecasts and marginal investments derived from the game rules."""

import math
from typing import Any

CROPS = {
    "WHEAT": (10, 2, 4, 0, 6),
    "CARROT": (20, 2, 3, 0, 4),
    "TOMATO": (50, 8, 8, 1, 4),
    "STRAWBERRY": (100, 10, 10, 2, 4),
    "MELON": (80, 10, 12, 0, 6),
}
ANIMALS = {"GOOSE": (300, 4, 1, "EGG"), "COW": (400, 8, 2, "MILK"), "SHEEP": (500, 6, 3, "WOOL")}
SHOPS = {
    "BAKERY": ("EGG", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT", "CARROT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "YARN_STORE": ("WOOL", "WOOL"),
}


def price(parameters: dict[str, Any], stock: float) -> float:
    """Reproduce the public inventory price curve, including the nonlinear hinge."""
    difference = stock - parameters["I0"]
    side = "above" if difference >= 0 else "below"
    shape = parameters[side + "_func"]
    threshold = float(parameters["T"])

    def transform(value: float) -> float:
        if shape == "sqrt":
            return math.sqrt(value)
        if shape == "sq":
            return value * value
        if shape == "log":
            return math.log1p(value)
        if shape == "hinge":
            ratio = value / threshold
            return float(ratio + 8 * max(0.0, ratio - 1) ** 2)
        return value

    change = parameters["base"] * parameters[side + "_target"]
    change *= transform(abs(difference)) / transform(threshold)
    return float(max(1.0, round(parameters["base"] + (-change if difference >= 0 else change))))


def forecast(observation: dict[str, Any], settings: dict[str, Any]) -> dict[str, list[float]]:
    """Project visible existing production and expected future shop demand."""
    day = observation["day"]
    products = observation["market"]["inventory"]
    supply = {item: [0.0] * 31 for item in products}
    demand = {item: float(item != "FERTILIZER") for item in products}
    shops = observation["town"]["unlocked_shops"]
    for shop in shops:
        for item in SHOPS[shop]:
            demand[item] += 6.0
    for seat, farm in enumerate(observation["farms"]):
        own = seat == observation["player"]
        for row in farm["tiles"]:
            for tile in row:
                if not isinstance(tile, dict):
                    continue
                if tile["kind"] == "PLANT":
                    crop = tile["crop"]
                    _, first, last, interval, cap = CROPS[crop]
                    planted = tile["planted_day"]
                    if interval:
                        for production in range(cap):
                            due = planted + first + interval * production - day
                            if 0 < due <= 30:
                                supply[crop][due] += 1.3
                        supply[crop][1] += tile["yield_units"]
                    else:
                        age = day - planted
                        maturity = first if crop == "MELON" else last
                        due = max(1, maturity - age)
                        water_days = max(0, maturity - max(age, (last + 1) // 2) + 1)
                        amount = min(cap, tile["yield_units"] + water_days)
                        supply[crop][due] += amount
                elif tile.get("animal"):
                    animal = tile["animal"]
                    _, first, interval, product = ANIMALS[animal]
                    placed = tile["placed_day"]
                    supply[product][1] += tile["yield_units"]
                    for offset in range(1, 30 - day):
                        age = day + offset - placed
                        supply["FERTILIZER"][offset] += 0.9
                        if age >= first and (age - first) % interval == 0:
                            supply[product][offset] += 1 + interval * (0.9 if own else 0.8)
    expected = {
        item: sum(orders.count(item) for orders in SHOPS.values()) * 0.75 for item in products
    }
    result = {}
    for item, initial in products.items():
        values = [float(initial)]
        future_consumption = 0.0
        count = len(shops)
        for offset in range(1, 31):
            if (day + offset) % 3 == 0 and count < 8:
                future_consumption += expected[item] * settings["future_shops"]
                count += 1
            values.append(values[-1] + supply[item][offset] - demand[item] - future_consumption)
        result[item] = values
    return result


def investments(
    observation: dict[str, Any],
    projection: dict[str, list[float]],
    parameters: dict[str, Any],
    settings: dict[str, Any],
) -> list[tuple[float, str]]:
    """Rank additional producers by expected discounted cash per occupied day."""
    remaining = 29 - observation["day"]
    cash = observation["farms"][observation["player"]]["money"]
    capital = settings["growth_bias"] * max(0.0, 1.0 - cash / 5000)
    scores = []
    for crop, (cost, first, last, interval, cap) in CROPS.items():
        maturity = first if crop == "MELON" else last
        if remaining < first:
            continue
        if interval:
            due = [first + interval * n for n in range(cap) if first + interval * n <= remaining]
            gross = sum(price(parameters[crop], projection[crop][d] + 1) for d in due)
            duration = due[-1] + 1
        else:
            maturity = min(maturity, remaining)
            quantity = min(cap, 1 + max(0, maturity - (last + 1) // 2 + 1))
            gross = sum(
                price(parameters[crop], projection[crop][maturity] + n) for n in range(quantity)
            )
            duration = maturity + 1
        score = (gross - cost) / duration ** settings["duration_power"]
        score *= (100 / (cost + 20)) ** capital * math.exp(-first * capital * 0.12)
        score *= settings.get("crop_bias", {}).get(crop, 1.0)
        scores.append((score, crop))
    if observation["day"] <= settings["animal_last_day"]:
        for animal, (cost, first, interval, product) in ANIMALS.items():
            if remaining <= first + 1:
                continue
            gross = 0.0
            for day in range(1, remaining + 1):
                gross += price(parameters["FERTILIZER"], projection["FERTILIZER"][day] + day)
                gross -= price(parameters["WHEAT"], projection["WHEAT"][day])
                if day >= first and (day - first) % interval == 0:
                    gross += (1 + interval) * price(parameters[product], projection[product][day])
            score = (gross - cost) / (remaining + 1) ** settings["duration_power"]
            score *= settings["animal_bias"]
            scores.append((score, animal))
    return sorted(scores, reverse=True)
