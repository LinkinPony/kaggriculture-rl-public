"""Bounded complete-episode encoding and exact literal quantity accounting."""

import hashlib
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import orjson

from kagg_revue.artifacts.io import digest
from kagg_revue.bc.data_config import ReplayContract
from kagg_revue.bc.replay import EpisodeLocator, _validate_header, daily_episode_metadata
from kagg_revue.datasets.demonstrations.config import Preparation, Source
from kagg_revue.datasets.demonstrations.encoding import encode, quantity_columns
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout


def encode_shard(
    preparation: dict[str, Any], source: dict[str, Any], members: list[str], prefix: str
) -> dict[str, Any]:
    """Read only one shard of immutable source episodes in each worker."""
    config = Preparation.model_validate(preparation)
    daily = Source.model_validate(source)
    layout = ContractLayout.resolve(config.geometry())
    expected = native.Engine(0, config.environment).configuration
    contract = ReplayContract(
        replay_schema_version=1,
        module_version=config.module_version,
        agents=2,
        episode_steps=int(config.environment["episodeSteps"]),
        board_size=layout.board_size,
        max_market_orders=layout.observation.markets,
        unit_limit=config.unit_limit,
    )
    metadata = daily_episode_metadata(daily.archive)
    observations, actions, origins, episodes = [], [], [], []
    rows = 0
    with zipfile.ZipFile(daily.archive) as archive:
        for member in members:
            raw = archive.read(member)
            replay = orjson.loads(raw)
            rating = metadata[Path(member).stem]
            locator = EpisodeLocator(
                daily.archive,
                member,
                daily.date,
                str(rating["create_time"]),
                float(str(rating["average_score"])),
                float(str(rating["minimum_score"])),
            )
            episode_id, environment, _, _, names = _validate_header(replay, locator, contract)
            if native.Engine(0, dict(environment)).configuration != expected:
                raise ValueError(f"demonstration environment differs: {member}")
            encoded, labels, eligible, counts = encode(replay, layout)
            selected = np.asarray(np.nonzero(eligible)).T.astype(np.int16)
            observations.append(encoded[eligible])
            actions.append(labels[eligible])
            origins.append(selected)
            episodes.append(
                {
                    "member": member,
                    "episode_id": episode_id,
                    "seed": replay["info"]["seed"],
                    "raw_sha256": hashlib.sha256(raw).hexdigest(),
                    "agents": names,
                    "row_start": rows,
                    "row_stop": rows + len(selected),
                    **counts,
                }
            )
            rows += len(selected)
    target = Path(prefix)
    files = {}
    for name, arrays in (
        ("observations", observations),
        ("raw_actions", actions),
        ("origins", origins),
    ):
        path = target.with_name(target.name + f"-{name}.npy")
        np.save(path, np.concatenate(arrays))
        files[name] = path.name
    return {
        **files,
        "source_date": daily.date,
        "split": daily.split,
        "archive_sha256": daily.sha256,
        "episodes": episodes,
        "rows": rows,
        "literal_quantities": np.unique(
            np.concatenate(actions)[:, quantity_columns(layout)]
        ).tolist(),
    }


def index_quantities(
    directory: Path,
    record: dict[str, Any],
    layout: ContractLayout,
    *,
    clip: bool = False,
) -> None:
    """Index quantities, optionally capping every split to a fixed integer range."""
    path = directory / record.pop("raw_actions")
    raw = np.load(path, mmap_mode="r")
    vocabulary = np.asarray(layout.observation.quantities, np.int64)
    columns = quantity_columns(layout)
    values = raw[:, columns]
    if clip:
        if not np.array_equal(vocabulary, np.arange(1, len(vocabulary) + 1)):
            raise ValueError("quantity clipping requires a contiguous positive integer vocabulary")
        clipped = values > vocabulary[-1]
        record["quantity_clipped_fields"] = int(clipped.sum())
        record["quantity_clipped_rows"] = int(clipped.any(-1).sum())
        values = np.minimum(values, vocabulary[-1])
    indices = np.searchsorted(vocabulary, values).clip(0, len(vocabulary) - 1)
    covered = np.asarray((vocabulary[indices] == values).all(-1), np.bool_)
    if record["split"] == "train" and not covered.all():
        raise ValueError("training quantity vocabulary dropped a training label")
    labels = raw.copy()
    labels[:, columns] = indices
    labels = labels.astype(np.int16)
    targets = path.with_name(path.name.replace("-raw_actions.npy", "-actions.npy"))
    np.save(targets, labels)
    coverage = targets.with_name(targets.name.replace("-actions.npy", "-quantity_coverage.npy"))
    np.save(coverage, covered)
    record.update(
        actions=targets.name,
        quantity_coverage=coverage.name,
        quantity_uncovered_rows=int((~covered).sum()),
        hashes={
            name: digest(directory / filename)
            for name, filename in {
                "observations": record["observations"],
                "origins": record["origins"],
                "actions": targets.name,
                "quantity_coverage": coverage.name,
            }.items()
        },
    )
    record.pop("literal_quantities")
    path.unlink()
