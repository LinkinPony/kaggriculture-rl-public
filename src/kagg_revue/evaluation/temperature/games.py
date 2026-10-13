"""Single-game FP32 inference with the exact submission sampling stream."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.opponents.batches import create_batch

_ACTORS: dict[int, Any] = {}
_SETTINGS: RuntimeSettings | None = None
_PROFILE: dict[str, Any] = {}


def initialize(paths: dict[int, str], settings: dict[str, Any], profile: dict[str, Any]) -> None:
    """Load reusable immutable actors once per CPU worker, with one inference thread."""
    global _SETTINGS, _PROFILE
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    _SETTINGS = RuntimeSettings.model_validate(settings).model_copy(
        update={"workers": 1, "evaluation_games": 1}
    )
    _PROFILE = profile
    for temperature, path in paths.items():
        _ACTORS[temperature] = torch.jit.load(  # type: ignore[no-untyped-call]
            str(Path(path)), map_location="cpu"
        ).eval()


def play(job: tuple[int, int, str, int], sampling_seed: int | None = None) -> dict[str, Any]:
    """Complete one physical game against a native script without Python callbacks."""
    seed, seat, opponent, temperature = job
    assert _SETTINGS is not None
    settings = _SETTINGS
    batch = create_batch(settings, [(seed, seat, opponent)])
    features = np.empty((1, _PROFILE["observation_features"]), dtype=np.float16)
    inputs = torch.from_numpy(features)
    step = torch.zeros(1, dtype=torch.long)
    sampling_seed = (
        int(_PROFILE["sampling_seed"]) + seat if sampling_seed is None else sampling_seed
    )
    torch.manual_seed(sampling_seed)
    trajectory = hashlib.sha256()
    opening_programs = hashlib.sha256()
    opening: list[dict[str, Any]] = []
    daily_cash = []
    started = time.perf_counter()
    with torch.inference_mode():
        for turn in range(settings.turns):
            batch.observe_into(features)
            step.fill_(turn)
            program = _ACTORS[temperature](inputs, step).numpy()
            trajectory.update(program.tobytes())
            batch.advance_programs(program, 1, 1, False)
            if turn < 3 * int(settings.environment["turnsPerDay"]):
                opening_programs.update(program.tobytes())
                obs = batch.observation(0)
                farm = obs["farms"][seat]
                opening.append({"turn": turn, "cash": farm["money"], "hands": len(farm["hands"])})
            if (turn + 1) % int(settings.environment["turnsPerDay"]) == 0:
                daily_cash.append(float(batch.cash()[0][0]))
    if batch.completed_games != 1 or batch.transitions != settings.turns:
        raise RuntimeError("temperature comparison did not complete the official horizon")
    cash, other = map(float, batch.cash()[0])
    return {
        "seed": seed,
        "seat": seat,
        "opponent": opponent,
        "temperature": temperature,
        "sampling_seed": sampling_seed if temperature else None,
        "cash": cash,
        "opponent_cash": other,
        "outcome": int(cash > other) - int(cash < other),
        "trajectory_sha256": trajectory.hexdigest(),
        "opening_programs_sha256": opening_programs.hexdigest(),
        "daily_cash": daily_cash,
        "opening": opening,
        "wall_seconds": time.perf_counter() - started,
    }


def summary(games: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep direct WDL and equal-weight terminal-cash summaries explicit."""
    cash = np.asarray([g["cash"] for g in games])
    outcomes = np.asarray([g["outcome"] for g in games])
    return {
        "games": len(games),
        "wins": int((outcomes > 0).sum()),
        "draws": int((outcomes == 0).sum()),
        "losses": int((outcomes < 0).sum()),
        "win_rate": float((outcomes > 0).mean()),
        "score": float(((outcomes + 1) / 2).mean()),
        "mean_cash": float(cash.mean()),
        "median_cash": float(np.median(cash)),
        "p10_cash": float(np.quantile(cash, 0.1)),
    }


def load_games(path: Path) -> list[dict[str, Any]]:
    """Read completed independent-game records for reporting or safe resume."""
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
