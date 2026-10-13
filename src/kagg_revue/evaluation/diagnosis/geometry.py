"""Parameter-space trajectory of a run: drift from the start and step-direction coherence."""

import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch import Tensor


def flat(path: Path) -> Tensor:
    """All floating actor parameters of one checkpoint as a single FP32 vector."""
    payload = torch.load(path, map_location="cpu", weights_only=False, mmap=True)
    tensors = [value for value in payload["model"].values() if value.is_floating_point()]
    return torch.cat([value.float().reshape(-1) for value in tensors])


def trajectory(named: list[tuple[str, Path]]) -> list[dict[str, Any]]:
    """Distance to the first checkpoint and cosine between consecutive steps."""
    points = [(name, flat(path)) for name, path in named]
    start = points[0][1]
    rows: list[dict[str, Any]] = []
    previous_step: Tensor | None = None
    for (name, vector), (_, earlier) in zip(points[1:], points[:-1], strict=True):
        step = vector - earlier
        drift = vector - start
        rows.append(
            {
                "checkpoint": name,
                "distance_from_start": float(drift.norm()),
                "step_norm": float(step.norm()),
                "cosine_with_previous_step": None
                if previous_step is None
                else float(torch.nn.functional.cosine_similarity(step, previous_step, dim=0)),
                "cosine_step_with_drift": float(
                    torch.nn.functional.cosine_similarity(step, drift, dim=0)
                ),
            }
        )
        previous_step = step
    return rows


def main() -> None:
    """Read `name=path` pairs in order and print one JSON row per step."""
    named = [(arg.split("=", 1)[0], Path(arg.split("=", 1)[1])) for arg in sys.argv[1:]]
    for row in trajectory(named):
        print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
