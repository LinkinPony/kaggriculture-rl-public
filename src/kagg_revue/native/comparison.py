"""Whole-season official-interpreter parity for newly sampled neural trajectories."""

import json
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.datasets.observations import difference
from kagg_revue.native.reference import OfficialGame, load_reference


class MirrorReference:
    """Drive both actor seats with official observations and compare every native state."""

    def __init__(
        self, directory: Path, environment: dict[str, int | float], seeds: list[int]
    ) -> None:
        """Authenticate one interpreter and construct an independent game for each seed."""
        module = load_reference(directory)
        self.manifest = json.loads((directory / "manifest.json").read_text())
        self.manifest_sha256 = digest(directory / "manifest.json")
        self.games = [OfficialGame(module, environment, seed) for seed in seeds]
        self.checked_observations = 0

    def observations(self, engines: list[Any]) -> list[dict[str, Any]]:
        """Return official actor inputs only after full state and inventory-order parity."""
        fields = ("player", "day", "hour", "farms", "private", "market", "town")
        observations = []
        for index, (engine, game) in enumerate(zip(engines, self.games, strict=True)):
            if engine.step_index != game.step_index:
                raise ValueError("official and native game clocks differ")
            for seat in (0, 1):
                expected, actual = game.observation(seat), engine.observation(seat)
                mismatch = difference(
                    {field: actual[field] for field in fields},
                    {field: expected[field] for field in fields},
                )
                if mismatch:
                    raise ValueError(
                        f"neural parity game {index}, turn {game.step_index}, "
                        f"seat {seat}: {mismatch}"
                    )
                observations.append(expected)
                self.checked_observations += 1
        return observations

    def report(self) -> dict[str, Any]:
        """Record the narrow parity scope separately from official deployment budgets."""
        return {
            "manifest": self.manifest,
            "manifest_sha256": self.manifest_sha256,
            "checked_observations": self.checked_observations,
            "actor_observations_from_official_interpreter": True,
            "matched": True,
            "deployment_budget_qualified": False,
        }
