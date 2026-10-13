"""Bounded official replay and existing BC encoder checks for opening reuse."""

import hashlib
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.daily import audit_episode
from kagg_revue.datasets.demonstrations.encoding import encode, quantity_columns
from kagg_revue.datasets.observations import ReplayObservations
from kagg_revue.datasets.openings.extraction import load
from kagg_revue.native import _revue_core as native
from kagg_revue.native.features import Layout
from kagg_revue.policy.contracts import ContractLayout, NetworkShape


class Validation(FrozenSettings):
    """Use the unchanged BC feature/action ABI and independent official rules."""

    output: Path
    checkpoint: Path
    reference: Path
    per_day: int = Field(default=4, gt=0)
    baseline_episodes: int = Field(default=8, gt=0)
    workers: int = Field(default=8, gt=0)
    seed: int = 1960916401


def _layout(stored: dict[str, Any]) -> ContractLayout:
    return ContractLayout(
        Layout(**stored["observation"]),
        stored["board_size"],
        stored["interval"],
        NetworkShape(**stored["network"]),
        stored["late_start"],
        stored["late_interval"],
    )


def check(job: tuple[dict[str, Any], dict[str, Any], str]) -> dict[str, Any]:
    """Encode the complete real horizon, then verify causal opening slices."""
    task, stored, reference = job
    layout = _layout(stored)
    replay, raw_sha256 = load(task)
    observations, actions, eligible, counts = encode(replay, layout)
    if not np.isfinite(observations[:144]).all():
        raise ValueError("opening features contain nonfinite values")
    clipped = np.asarray(
        (actions[..., quantity_columns(layout)] > max(layout.observation.quantities)).any(-1),
        dtype=np.bool_,
    )
    result = {
        "episode_id": task["episode_id"],
        "date": task["date"],
        "daily": task["daily"],
        "raw_sha256": raw_sha256,
        "counts": counts,
        "prefixes": {
            str(h): {
                "candidate_rows": h * 2,
                "supported_rows": int(eligible[:h].sum()),
                "quantity_clipped_rows": int((clipped[:h] & eligible[:h]).sum()),
                "finite_observations": bool(np.isfinite(observations[:h]).all()),
            }
            for h in (24, 48, 72, 144)
        },
    }
    matched = 0
    for seat in (0, 1):
        session = native.ContractSession(replay["configuration"], layout.observation.units)
        sequence = ReplayObservations()
        features = np.empty((1, layout.observation.features), dtype=np.float16)
        for turn in range(144):
            session.update(sequence.update(replay["steps"][turn][seat]["observation"], turn))
            session.observe_into(features)
            if not np.array_equal(features[0], observations[turn, seat]):
                raise ValueError(
                    "opening slice differs from causal full-horizon observation encoding"
                )
            matched += 1
    result["streaming_matched_rows"] = matched
    if task["daily"]:
        official = audit_episode((task["path"], str(task["episode_id"]), "1.32.7", reference))
        if not official["matched"]:
            raise ValueError(f"official replay verification failed: {official}")
        result["official"] = official
    return result


def run(config: Validation) -> None:
    """Select cases by stable hash before inspecting outcome or procurement events."""
    tasks = orjson.loads((config.output / "tasks.json").read_bytes())

    def priority(task: dict[str, Any]) -> bytes:
        return hashlib.sha256(f"{config.seed}:{task['episode_id']}".encode()).digest()

    selected = []
    for date in sorted({t["date"] for t in tasks if t["daily"]}):
        candidates = [t for t in tasks if t["daily"] and t["date"] == date]
        selected.extend(sorted(candidates, key=priority)[: config.per_day])
    chosen = {t["episode_id"] for t in selected}
    baseline = [t for t in tasks if t["baseline_seats"] and t["episode_id"] not in chosen]
    selected.extend(sorted(baseline, key=priority)[: config.baseline_episodes])
    payload = torch.load(config.checkpoint, map_location="cpu", weights_only=False, mmap=True)
    stored = payload["layout"]
    del payload
    write_json(
        config.output / "validation-protocol.json",
        {
            "configuration": config.model_dump(mode="json"),
            "checkpoint_sha256": digest(config.checkpoint),
            "tasks": selected,
            "layout": stored,
            "runner_sha256": digest(Path(__file__)),
        },
    )
    with ProcessPoolExecutor(
        max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        rows = list(pool.map(check, [(t, stored, str(config.reference)) for t in selected]))
    report = {
        "passed": True,
        "episodes": rows,
        "streaming_matched_rows": sum(r["streaming_matched_rows"] for r in rows),
        "official_full_games": sum("official" in r for r in rows),
        "official_matched_observations": sum(
            r.get("official", {}).get("checked_observations", 0) for r in rows
        ),
        "prefixes": {
            str(h): {
                key: sum(r["prefixes"][str(h)][key] for r in rows)
                for key in ("candidate_rows", "supported_rows", "quantity_clipped_rows")
            }
            for h in (24, 48, 72, 144)
        },
        "scope": "Sampled source-encoding feasibility, not whole-dataset eligible-row counts. "
        "Use original 720-step configuration and full causal history before slicing; no shortened "
        "episode semantics, no parameter optimization or new game-strength samples.",
    }
    write_json(config.output / "validation.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "episodes"}), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="opening_analysis",
)
def main(configuration: DictConfig) -> None:
    """Validate actual encoder reuse without touching live training."""
    run(Validation.model_validate(OmegaConf.to_container(configuration.validation, resolve=True)))


if __name__ == "__main__":
    main()
