"""Bounded evolutionary search over independent economic and scheduling decisions."""

import json
import math
import random
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.opponents.enterprise.agent import DEFAULTS
from kagg_revue.opponents.enterprise.experiment import Panel, run

BOUNDS = {
    "duration_power": (0.0, 1.8),
    "growth_bias": (0.0, 2.5),
    "animal_bias": (0.15, 2.0),
    "animal_limit": (0, 22),
    "initial_workers": (4, 9),
    "workers": (9, 15),
    "plant_priority": (0.3, 4.0),
    "water_priority": (0.05, 2.0),
    "fertilizer_priority": (0.2, 2.0),
    "care_priority": (0.5, 5.0),
    "travel_power": (0.5, 2.0),
    "future_shops": (0.0, 1.5),
}
INTEGERS = {"animal_limit", "initial_workers", "workers"}


def mutate(parent: dict[str, Any], rng: random.Random, scale: float) -> dict[str, Any]:
    """Perturb both production preferences and labor decisions with bounded variation."""
    values = dict(parent)
    for name, (low, high) in BOUNDS.items():
        value = parent.get(name, DEFAULTS[name]) + rng.gauss(0, scale) * (high - low)
        value = min(high, max(low, value))
        values[name] = round(value) if name in INTEGERS else round(value, 5)
    values["crop_bias"] = {
        crop: round(
            min(
                5,
                max(
                    0.2,
                    parent.get("crop_bias", {}).get(crop, 1.0) * math.exp(rng.gauss(0, scale * 3)),
                ),
            ),
            5,
        )
        for crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
    }
    values["central_reserve"] = min(values["animal_limit"], 3)
    values["fertilize"] = rng.random() > 0.2
    return values


def optimize(
    configuration: dict[str, Any],
    root: Path,
    generations: int,
    population: int,
    initial: dict[str, Any] | None = None,
) -> None:
    """Select on declared development worlds and retain all complete failures and wins."""
    root.mkdir(parents=True, exist_ok=False)
    rng = random.Random(1860917201)
    elite = [
        {
            **DEFAULTS,
            "workers": 14,
            "growth_bias": 0.5,
            "animal_limit": 8,
            "crop_bias": {"STRAWBERRY": 2.0},
        }
    ]
    if initial is not None:
        elite = [initial]
    write_json(
        root / "search-protocol.json",
        {
            "configuration": configuration,
            "initial": elite[0],
            "generations": generations,
            "population": population,
            "bounds": BOUNDS,
            "random_seed": 1860917201,
        },
    )
    for generation in range(generations):
        variants = {f"g{generation}_v0": elite[0]}
        for index in range(1, population):
            variants[f"g{generation}_v{index}"] = mutate(
                rng.choice(elite), rng, max(0.08, 0.3 * 0.8**generation)
            )
        directory = root / f"generation-{generation:02d}"
        values = {**configuration, "output": directory, "variants": variants, "trace": False}
        run(Panel.model_validate(values))
        summary = json.loads((directory / "summary.json").read_text())
        ranked = sorted(
            (row for row in summary if row["opponent"] == "all"),
            key=lambda row: row["mean_margin"],
            reverse=True,
        )
        elite = [variants[row["variant"]] for row in ranked[:4]]
        write_json(
            root / "incumbent.json",
            {"generation": generation, "result": ranked[0], "settings": elite[0]},
        )
        print(f"GENERATION {generation}: {ranked[0]}", flush=True)


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="enterprise_evolution"
)
def main(configuration: DictConfig) -> None:
    """Optimize a declared development panel without touching production training."""
    values = OmegaConf.to_container(configuration, resolve=True)
    assert isinstance(values, dict) and isinstance(values["panel"], dict)
    initial = (
        json.loads(Path(str(values["warm_start"])).read_text())["settings"]
        if values.get("warm_start")
        else None
    )
    optimize(
        values["panel"],
        Path(str(values["search_output"])),
        int(str(values["generations"])),
        int(str(values["population"])),
        initial,
    )


if __name__ == "__main__":
    main()
