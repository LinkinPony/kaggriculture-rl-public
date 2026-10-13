"""Native demonstration generation into compact, memory-mapped turn shards."""

import json
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native.batches import paired_jobs
from kagg_revue.native.features import Layout
from kagg_revue.opponents.batches import create_batch
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import Settings


def numpy_weights(
    observations: NDArray[np.float16], labels: NDArray[np.int64], layout: Layout
) -> NDArray[np.bool_]:
    """Mask causal BC factors using array operations on a coarse shard."""
    units = observations[
        ..., layout.board_features : layout.board_features + layout.units * layout.unit_features
    ]
    alive = units.reshape(*observations.shape[:-1], layout.units, layout.unit_features)[..., 0] > 0
    operations = labels[..., 0]
    stop = operations[..., layout.units :] == 0
    active = np.concatenate((alive, stop.cumsum(-1) - stop == 0), axis=-1)
    offsets = np.concatenate(
        (np.zeros(layout.units, np.int64), np.full(layout.markets, 44, np.int64))
    )
    tokens = operations + offsets
    quantity = (
        (tokens >= 5) & (tokens < 17)
        | (tokens >= 18) & (tokens < 30)
        | (tokens >= 46) & (tokens < 65)
    )
    return np.stack((active, active & quantity), axis=-1)


def generate(settings: Settings) -> Path:
    """Generate complete teacher games; fail instead of silently truncating labels."""
    directory = settings.bc.source
    manifest_path = directory / "manifest.json"
    layout = Layout.resolve(settings)
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text())
        stored = Layout(**existing["layout"])
        if (
            replace(stored, width=0) != replace(layout, width=0)
            or len(existing["games"]) != settings.bc.games
        ):
            raise ValueError("existing BC dataset has a different action or observation ABI")
        return manifest_path
    directory.mkdir(parents=True, exist_ok=True)
    identity = provenance(settings)
    op_counts = np.zeros((layout.turns, layout.slots, 44), dtype=np.float64)
    q_counts = np.zeros((layout.turns, layout.slots, len(layout.quantities)), dtype=np.float64)
    base = np.arange(layout.turns * layout.slots).reshape(layout.turns, 1, layout.slots)
    shards: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    started = time.perf_counter()
    for offset in range(0, settings.bc.games, settings.bc.shard_games):
        count = min(settings.bc.shard_games, settings.bc.games - offset)
        jobs = paired_jobs(count, settings.bc.seed_start + offset // 2, settings.opponents)
        batch = create_batch(settings, jobs, teacher=True)
        prefix = f"shard-{len(shards):04d}"
        observation_path = directory / f"{prefix}-observations.npy"
        label_path = directory / f"{prefix}-actions.npy"
        observations = np.lib.format.open_memmap(
            observation_path,
            mode="w+",
            dtype=np.float16,
            shape=(layout.turns, count, layout.features),
        )
        labels = np.lib.format.open_memmap(
            label_path, mode="w+", dtype=np.int16, shape=(layout.turns, count, layout.slots, 2)
        )
        current_labels = np.empty((count, layout.slots, 2), dtype=np.int64)
        for turn in range(layout.turns):
            batch.observe_into(observations[turn])
            batch.teacher_into(current_labels)
            labels[turn] = current_labels
            batch.step(current_labels)
        observations.flush()
        labels.flush()
        weights = numpy_weights(observations, labels, layout)
        for head, counts in ((0, op_counts), (1, q_counts)):
            indices = base * counts.shape[-1] + labels[..., head]
            counts += np.bincount(
                indices.ravel(), weights=weights[..., head].ravel(), minlength=counts.size
            ).reshape(counts.shape)
        cash = batch.cash()
        for index, (seed, seat, opponent) in enumerate(jobs):
            results.append(
                {
                    "seed": seed,
                    "seat": seat,
                    "opponent": opponent,
                    "cash": float(cash[index, 0]),
                    "opponent_cash": float(cash[index, 1]),
                }
            )
        shards.append(
            {
                "observations": observation_path.name,
                "actions": label_path.name,
                "games": count,
                "rows": layout.turns * count,
                "observations_sha256": digest(observation_path),
                "actions_sha256": digest(label_path),
            }
        )
        print(
            json.dumps(
                {
                    "phase": "generate",
                    "games": offset + count,
                    "mean_cash": float(cash[:, 0].mean()),
                    "elapsed_seconds": time.perf_counter() - started,
                }
            ),
            flush=True,
        )
        del observations, labels, weights
    np.savez(directory / "prior-counts.npz", operation=op_counts, quantity=q_counts)
    manifest = {
        "schema": "parallel-turn-demonstrations-v1",
        "layout": asdict(layout),
        "source": identity,
        "shards": shards,
        "games": results,
        "elapsed_seconds": time.perf_counter() - started,
    }
    write_json(manifest_path, manifest)
    return manifest_path


def load_shard(
    directory: Path, shard: dict[str, Any], device: torch.device
) -> tuple[Tensor, Tensor, Tensor]:
    """Transfer one compact shard in bounded chunks without materializing the dataset."""
    observations = np.load(directory / shard["observations"], mmap_mode="r")
    labels = np.load(directory / shard["actions"], mmap_mode="r")
    turns, games = observations.shape[:2]
    rows = turns * games
    destination = torch.empty((rows, observations.shape[-1]), dtype=torch.float16, device=device)
    flat = observations.reshape(rows, -1)
    for start in range(0, rows, 8192):
        destination[start : start + 8192].copy_(
            torch.from_numpy(np.array(flat[start : start + 8192]))
        )
    actions = torch.tensor(np.array(labels).reshape(rows, *labels.shape[2:]), device=device)
    steps = torch.arange(turns, device=device).repeat_interleave(games)
    return destination, actions.long(), steps
