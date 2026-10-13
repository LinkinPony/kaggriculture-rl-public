"""Independent farm director: marginal production planning and live labor auctions."""

from typing import Any

from kagg_revue.opponents.enterprise.economy import ANIMALS, forecast, investments
from kagg_revue.opponents.enterprise.finance import market_orders
from kagg_revue.opponents.enterprise.tasks import distance, home, movement, operations
from kagg_revue.opponents.enterprise.territories import partition

DEFAULTS: dict[str, Any] = {
    "future_shops": 0.8,
    "duration_power": 1.0,
    "animal_bias": 0.7,
    "animal_last_day": 14,
    "central_reserve": 3,
    "animal_limit": 12,
    "plant_priority": 1.0,
    "water_priority": 1.0,
    "fertilizer_priority": 1.0,
    "care_priority": 1.0,
    "workers": 11,
    "travel_power": 1.2,
    "crop_bias": {},
    "sell_floor": 1,
    "growth_bias": 1.0,
    "initial_workers": 7,
    "fertilize": True,
    "sticky": 2.0,
    "commit": True,
    "crews": True,
    "territories": True,
    "animals_per_worker": 3,
    "efficient_transport": False,
    "buy_fertilizer": False,
}


class Director:
    """Own episode-local plans inferred only from the official observation."""

    def __init__(
        self, configuration: dict[str, Any], settings: dict[str, Any] | None = None
    ) -> None:
        """Bind explicit economic assumptions and preserve no notebook policy state."""
        self.configuration = configuration
        self.settings = {**DEFAULTS, **(settings or {})}
        self.targets: dict[int, tuple[int, int]] = {}
        self.projection: dict[str, list[float]] = {}
        self.ranking: list[tuple[float, str]] = []
        self.areas: list[tuple[int, int]] = []
        self.workforce = -1
        self.delivery = -1

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Reconsider production and assign workers using current farm needs."""
        step, day, hour = (observation["step"], observation["day"], observation["hour"])
        if step == 0:
            self.targets.clear()
        if hour == 0:
            self.targets.clear()
            self.delivery = -1
        farm = observation["farms"][observation["player"]]
        private = observation["private"]
        shed = dict(private["shed"])
        seeds = dict(private["seeds"])
        prices = observation["market"]["prices"]
        tiles = [
            (x, y, tile)
            for y, row in enumerate(farm["tiles"])
            for x, tile in enumerate(row)
            if tile != "LOCKED"
        ]
        animal_count = sum(
            (bool(isinstance(tile, dict) and tile.get("animal")) for _, _, tile in tiles)
        )
        if step % 6 == 0 or not self.projection:
            self.projection = forecast(observation, self.settings)
            self.ranking = investments(
                observation, self.projection, self.configuration["marketParams"], self.settings
            )
        context = {
            "day": day,
            "hour": hour,
            "step": step,
            "prices": prices,
            "settings": self.settings,
            "seeds": seeds,
            "investments": self.ranking,
            "animal_count": animal_count,
        }
        positions = [tuple(farm["farmer"]), *(tuple(p) for p in farm["hands"])]
        inventories = private["inventories"]
        carried_wheat = sum(inv.get("WHEAT", 0) for inv in inventories)
        carried_animals = sum(inv.get(item, 0) for inv in inventories for item in ANIMALS)
        cargo_total = sum(sum(inv.values()) for inv in inventories) + sum(shed.values())
        pending_animals = (
            animal_count + carried_animals + sum(shed.get(item, 0) for item in ANIMALS)
        )
        feeding_workers = min(
            len(positions),
            (pending_animals + self.settings["animals_per_worker"] - 1)
            // self.settings["animals_per_worker"],
        )
        if self.settings["efficient_transport"]:
            if self.delivery >= len(inventories) or (
                self.delivery >= 0 and (not inventories[self.delivery])
            ):
                self.delivery = -1
            if cargo_total > 85 and self.delivery < 0:
                deliveries = [
                    (sum(inv.values()) / (1 + distance(position, home(position))), unit)
                    for unit, (position, inv) in enumerate(zip(positions, inventories, strict=True))
                    if sum(
                        n
                        for item, n in inv.items()
                        if item not in ANIMALS
                        and item != "FERTILIZER"
                        and (unit >= feeding_workers or item != "WHEAT")
                    )
                    >= 5
                ]
                if deliveries:
                    self.delivery = max(deliveries)[1]
        if hour == 0 or self.workforce != len(positions):
            self.areas = partition(tiles, len(positions) - feeding_workers)
            self.workforce = len(positions)
        ownership = {}
        if self.settings["commit"]:
            for unit, target in self.targets.items():
                if (
                    unit < len(positions)
                    and operations(
                        farm["tiles"][target[1]][target[0]], target, inventories[unit], context
                    )
                    is not None
                ):
                    ownership[target] = unit
        actions = []
        reserved = set()
        for unit, position in enumerate(positions):
            inventory = inventories[unit]
            base = home(position)
            cargo_value = sum(
                (
                    n * prices.get(item, 100)
                    for item, n in inventory.items()
                    if item not in ANIMALS and item not in ("WHEAT", "FERTILIZER")
                )
            )
            final_return = day == 29 and 718 - step <= distance(position, base) + 1
            overflow = cargo_total > 85 and sum(inventory.values()) >= 5 and (hour < 20)
            if self.settings["efficient_transport"]:
                overflow = unit == self.delivery
            if sum(inventory.values()) and (
                final_return or overflow or (position == base and cargo_value > 150)
            ):
                action = ["DROP"] if position == base else movement(position, base)
                if action[0] == "DROP":
                    for item, count in inventory.items():
                        shed[item] = shed.get(item, 0) + count
                actions.append(action)
                self.targets.pop(unit, None)
                continue
            if position == base:
                animal = next((item for item in ANIMALS if shed.get(item, 0) > 0), None)
                if animal and (not any(inventory.get(item, 0) for item in ANIMALS)):
                    actions.append(["PICKUP", animal, 1])
                    shed[animal] -= 1
                    continue
                if (
                    unit < feeding_workers
                    and (not inventory.get("WHEAT", 0))
                    and shed.get("WHEAT", 0)
                ):
                    amount = min(4, shed["WHEAT"])
                    actions.append(["PICKUP", "WHEAT", amount])
                    shed["WHEAT"] -= amount
                    continue
                if (
                    self.settings["fertilize"]
                    and (not inventory.get("FERTILIZER", 0))
                    and shed.get("FERTILIZER", 0)
                    and (unit >= feeding_workers)
                ):
                    amount = min(shed["FERTILIZER"], 2 if self.settings["buy_fertilizer"] else 1)
                    actions.append(["PICKUP", "FERTILIZER", amount])
                    shed["FERTILIZER"] -= amount
                    continue
            choices = []
            for x, y, tile in tiles:
                target = (x, y)
                if target in reserved:
                    continue
                if target in ownership and ownership[target] != unit:
                    continue
                operation = operations(tile, target, inventory, context)
                if operation is None:
                    continue
                command, value = operation
                travel = distance(position, target)
                if hour + travel + (2 if command[0] == "PLANT" else 1) > 24:
                    continue
                if (
                    day == 29
                    and command[0] == "HARVEST"
                    and (travel + distance(target, home(target)) + 2 > 718 - step)
                ):
                    continue
                score = value / (travel + 1) ** self.settings["travel_power"]
                animal_task = isinstance(tile, dict) and tile.get("animal")
                if self.settings["crews"] and unit < feeding_workers and animal_task:
                    score *= 10000
                elif self.settings["territories"] and unit >= feeding_workers and self.areas:
                    anchor = self.areas[min(unit - feeding_workers, len(self.areas) - 1)]
                    score /= (1 + distance(target, anchor)) ** 1.0
                if self.targets.get(unit) == target:
                    score *= 1000 if self.settings["commit"] else self.settings["sticky"]
                choices.append((score, -travel, -y, -x, command, target))
            if choices:
                _, _, _, _, command, target = max(choices)
                reserved.add(target)
                self.targets[unit] = target
                action = command if position == target else movement(position, target)
                if action[0] == "PLANT":
                    seeds[action[1]] -= 1
                actions.append(action)
            elif unit < feeding_workers and (not inventory.get("WHEAT", 0)) and (position != base):
                actions.append(movement(position, base))
            else:
                actions.append(["PASS"])
        for command, inventory in zip(actions, inventories, strict=True):
            if command[0] == "PICKUP" and command[1] == "WHEAT":
                carried_wheat += command[2]
            elif command[0] == "FEED":
                carried_wheat -= 1
            elif command[0] == "DROP":
                carried_wheat -= inventory.get("WHEAT", 0)
        orders = market_orders(
            self.settings,
            self.ranking,
            farm,
            shed,
            seeds,
            animal_count + carried_animals,
            len(tiles),
            day,
            hour,
            prices,
            carried_wheat,
        )
        return {"farmer": actions[0], "hands": actions[1:], "market": orders}
