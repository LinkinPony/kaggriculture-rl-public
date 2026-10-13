"""Independent production targets executed by the repository's native task scheduler."""

from collections import Counter
from typing import Any

from kagg_revue.opponents.enterprise.agent import DEFAULTS
from kagg_revue.opponents.enterprise.economy import ANIMALS, CROPS, forecast, investments


class Allocator:
    """Separate economic targets from an existing rules-based execution component."""

    def __init__(self, configuration: dict[str, Any], settings: dict[str, Any]) -> None:
        """Retain the new economic assumptions without importing any notebook policy."""
        self.configuration = configuration
        self.settings = {**DEFAULTS, **settings}
        self.planner: Any = None
        self.ranking: list[tuple[float, str]] = []

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Replan marginal production counts daily and let native scheduling execute them."""
        if self.planner is None or observation["hour"] == 0:
            from kagg_revue.native import _revue_native as native

            farm = observation["farms"][observation["player"]]
            tiles = [tile for row in farm["tiles"] for tile in row if tile != "LOCKED"]
            counts = Counter(
                tile.get("crop", tile.get("animal")) for tile in tiles if isinstance(tile, dict)
            )
            crops = {crop: counts[crop] for crop in CROPS}
            animals = {animal: counts[animal] for animal in ANIMALS}
            projection = forecast(observation, self.settings)
            cash = farm["money"] - 400
            for _ in range(max(0, len(tiles) - sum(crops.values()) - sum(animals.values()))):
                self.ranking = investments(
                    observation, projection, self.configuration["marketParams"], self.settings
                )
                feasible = [
                    (value, item)
                    for value, item in self.ranking
                    if value > 0
                    and (
                        (item in CROPS and cash >= CROPS[item][0])
                        or (
                            item in ANIMALS
                            and sum(animals.values()) < self.settings["animal_limit"]
                            and cash > ANIMALS[item][0] + sum(animals.values()) * 100
                        )
                    )
                ]
                if not feasible:
                    break
                _, item = feasible[0]
                if item in CROPS:
                    cost, first, last, interval, cap = CROPS[item]
                    crops[item] += 1
                    cash -= cost
                    due = (
                        [first + interval * n for n in range(cap)]
                        if interval
                        else [first if item == "MELON" else last]
                    )
                    for time in due:
                        for day in range(time, 31):
                            projection[item][day] += (
                                1.3 if interval else min(cap, 1 + last - (last + 1) // 2 + 1)
                            )
                else:
                    cost, first, interval, product = ANIMALS[item]
                    animals[item] += 1
                    cash -= cost
                    for day in range(1, 31):
                        projection["FERTILIZER"][day] += day
                        projection[product][day] += max(0, (day - first) // interval + 1) * (
                            1 + interval
                        )
            populated = sum(crops.values()) + sum(animals.values())
            options = {
                "scheduler": self.settings.get("scheduler", "route_aware"),
                "task_continuation_mode": "sticky",
                "supply_route_mode": "task_bound",
                "supply_route_capacity": 4,
                "project_layout": "service_zones",
                "animal_zone_cells": 20,
                "crop_zone_cells": 60,
                "strategy": {
                    "strategic_control_mode": "explicit",
                    "target_workers": min(self.settings["workers"] + 1, 6 + populated // 7),
                    "target_plants": sum(crops.values()),
                    "preferred_crop": max(crops, key=lambda item: crops[item]),
                    "preferred_animal": max(animals, key=lambda item: animals[item])
                    if sum(animals.values())
                    else None,
                    "enforce_production_targets": True,
                    "allow_land": len(tiles) < 100 and populated > len(tiles) * 0.8,
                    "allow_crop_investment": True,
                    "allow_animal_investment": True,
                    "liquidation_only": observation["day"] == 29,
                    "target_land_quadrants": min(4, len(farm["unlocked_quadrants"]) + 1),
                    "target_crops": list(crops.values()),
                    "target_animals": list(animals.values()),
                    "cash_reserve_fraction": 0.0,
                    "cash_reserve_amount": 200.0,
                    "product_reserves": [0] * 9,
                    "minimum_sale_prices": [0.0] * 9,
                    "sale_mode": "aggressive",
                    "one_time_harvest": "max_yield",
                    "soft_service_mode": "survival_first",
                },
            }
            self.planner = native.NativePlanner(self.configuration, options)
        return dict(self.planner.act(observation))
