"""Shared run provenance and paired evaluation-seed boundaries."""

import json
from pathlib import Path
from typing import Any

from kagg_revue.learning.config import Experiment


def validated_run(
    directory: Path, *, seed: int, games_per_opponent: int, role: str
) -> tuple[Experiment, dict[str, Any]]:
    """Authenticate a new run and reject overlap with training or reserved seeds."""
    if (
        directory.is_absolute()
        or ".." in directory.parts
        or directory.parts[:2] != ("outputs", "learning")
    ):
        raise ValueError("arena models must come from registered new learning runs")
    state = json.loads((directory / "state.json").read_text())
    if (
        state["schema"] != "random-root-league-v1"
        or state["initialization"] != "random"
        or state["input_weights"]
    ):
        raise ValueError("arena models require an authenticated fresh random root")
    config = Experiment.model_validate(state["protocol"])
    if config.output_dir != directory:
        raise ValueError("arena directory differs from the run's declared artifact location")
    stop = seed + games_per_opponent // 2
    if max(seed, config.train_seed) < min(stop, config.train_seed + config.games * config.updates):
        raise ValueError("arena seeds overlap candidate or opponent training")
    if role == "selection" and max(seed, config.evaluation.confirmation_seed) < min(
        stop, config.evaluation.confirmation_seed + config.evaluation.games // 2
    ):
        raise ValueError("selection arena cannot consume a run's reserved confirmation seeds")
    if config.curriculum is not None:
        manifest = json.loads(config.curriculum.manifest.read_text())
        if any(seed <= episode["seed"] < stop for episode in manifest["episodes"]):
            raise ValueError("arena seed panel overlaps the replay source episodes")
    if config.demonstrations is not None:
        if "rl_initial" not in state:
            raise ValueError("arena requires the declared initialization budget to finish")
        manifest = json.loads(config.demonstrations.manifest.read_text())
        if any(
            seed <= episode["seed"] < stop
            for shard in manifest["shards"]
            for episode in shard["episodes"]
        ):
            raise ValueError("arena seed panel overlaps demonstration episodes")
    return config, state
