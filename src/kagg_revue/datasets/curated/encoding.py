"""Encode selected whole-episode seats from ZIP members or public GZIP replays."""

import gzip
import hashlib
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import orjson

from kagg_revue.bc.data_config import ReplayContract
from kagg_revue.bc.replay import EpisodeLocator, _validate_header
from kagg_revue.datasets.curated.catalog import Preparation
from kagg_revue.datasets.demonstrations.encoding import encode, quantity_columns
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.settings import GeometrySettings


def encode_shard(
    settings: dict[str, Any], tasks: list[dict[str, Any]], prefix: str
) -> dict[str, Any]:
    """Preserve source identity, true preceding observations and literal requests."""
    config = Preparation.model_validate(settings)
    return encode_selected_shard(config.geometry(), tasks, prefix)


def encode_selected_shard(
    geometry: GeometrySettings, tasks: list[dict[str, Any]], prefix: str
) -> dict[str, Any]:
    """Encode an authenticated selected-seat catalog using shared causal labels."""
    layout = ContractLayout.resolve(geometry)
    expected = native.Engine(0, geometry.environment).configuration
    contract = ReplayContract(
        replay_schema_version=1,
        module_version="1.32.7",
        agents=2,
        episode_steps=int(geometry.environment["episodeSteps"]),
        board_size=layout.board_size,
        max_market_orders=layout.observation.markets,
        unit_limit=layout.observation.units,
    )
    arrays: dict[str, list[np.ndarray[Any, Any]]] = {
        key: [] for key in ("observations", "raw_actions", "origins", "sampling_weights")
    }
    episodes, rows = [], 0
    for task in tasks:
        path = Path(task["path"])
        if task.get("member"):
            with zipfile.ZipFile(path) as archive:
                raw = archive.read(task["member"])
        else:
            raw = gzip.decompress(path.read_bytes())
        replay = orjson.loads(raw)
        locator = EpisodeLocator(path, f"{task['episode_id']}.json", task["date"], "", 0, 0)
        episode_id, environment, _, _, names = _validate_header(replay, locator, contract)
        if (
            native.Engine(0, dict(environment)).configuration != expected
            or replay["info"]["seed"] != task["seed"]
        ):
            raise ValueError("replay differs from the screened source catalog")
        encoded, labels, eligible, _ = encode(replay, layout)
        wanted = np.zeros(2, dtype=np.bool_)
        weights = np.ones(2, dtype=np.float32)
        for seat in task["seats"]:
            if names[seat["seat"]] != seat["name"]:
                raise ValueError("selected teacher does not match the raw replay")
            wanted[seat["seat"]] = True
            weights[seat["seat"]] = seat["weight"]
        candidates = int(len(eligible) * wanted.sum())
        eligible &= wanted[None]
        origins = np.asarray(np.nonzero(eligible)).T.astype(np.int16)
        arrays["observations"].append(encoded[eligible])
        arrays["raw_actions"].append(labels[eligible])
        arrays["origins"].append(origins)
        arrays["sampling_weights"].append(weights[origins[:, 1]])
        episodes.append(
            {
                "episode_id": episode_id,
                "seed": task["seed"],
                "source": task["source"],
                "path": task["path"],
                "member": task.get("member"),
                "date": task["date"],
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "agents": names,
                "selected_seats": task["seats"],
                "row_start": rows,
                "row_stop": rows + len(origins),
                "candidate_rows": candidates,
                "unsupported_unit_rows": candidates - len(origins),
            }
        )
        rows += len(origins)
    target = Path(prefix)
    files = {}
    for name, chunks in arrays.items():
        output = target.with_name(target.name + f"-{name}.npy")
        np.save(output, np.concatenate(chunks))
        files[name] = output.name
    return {
        **files,
        "source_date": "mixed",
        "split": tasks[0]["split"],
        "episodes": episodes,
        "rows": rows,
        "literal_quantities": np.unique(
            np.concatenate(arrays["raw_actions"])[:, quantity_columns(layout)]
        ).tolist(),
    }
